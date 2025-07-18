import asyncio
import websockets
import logging
from typing import Optional
from util.client_cosmic import Cosmic
from util.config import ClientConfig as Config

# Configuration constants
CONNECTION_TIMEOUT = 10  # seconds
PING_TIMEOUT = 5  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

logger = logging.getLogger(__name__)


class WebSocketConnectionError(Exception):
    """Custom exception for WebSocket connection issues"""
    pass


class ConnectionHandler:
    """Enhanced connection handler with proper logging"""
    
    def __init__(self, operation: str = "WebSocket operation"):
        self.operation = operation
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            if exc_type == websockets.exceptions.ConnectionClosed:
                logger.warning(f"{self.operation}: Connection closed - {exc_val}")
            elif exc_type == asyncio.TimeoutError:
                logger.warning(f"{self.operation}: Connection timeout")
            elif exc_type == OSError:
                logger.error(f"{self.operation}: Network error - {exc_val}")
            else:
                logger.error(f"{self.operation}: Unexpected error - {exc_type.__name__}: {exc_val}")
        return True  # Suppress exceptions


async def verify_websocket_health(websocket) -> bool:
    """Verify websocket connection health using ping"""
    try:
        pong_waiter = await asyncio.wait_for(
            websocket.ping(), timeout=PING_TIMEOUT
        )
        await asyncio.wait_for(pong_waiter, timeout=PING_TIMEOUT)
        return True
    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed, OSError):
        return False


async def check_websocket() -> bool:
    """Check and establish WebSocket connection with robust error handling"""
    
    # Validate configuration
    if not Config.addr or not Config.speech_recognition_port:
        logger.error("Invalid WebSocket configuration: missing address or port")
        return False
    
    # Check existing connection
    if Cosmic.websocket:
        # Check if connection is still open using state property
        try:
            if hasattr(Cosmic.websocket, 'state') and Cosmic.websocket.state.name == 'OPEN':
                # Verify connection health
                if await verify_websocket_health(Cosmic.websocket):
                    logger.debug("Existing WebSocket connection is healthy")
                    return True
                else:
                    logger.info("Existing WebSocket connection is unhealthy, reconnecting")
                    Cosmic.websocket = None
            else:
                logger.info("Existing WebSocket connection is not open, reconnecting")
                Cosmic.websocket = None
        except Exception as e:
            logger.warning(f"Error checking WebSocket state: {e}, reconnecting")
            Cosmic.websocket = None
    
    # Attempt to establish new connection
    websocket_url = f"ws://{Config.addr}:{Config.speech_recognition_port}"
    logger.debug(f"Attempting to connect to WebSocket: {websocket_url}")
    logger.error(f"Attempting to connect to WebSocket: {websocket_url}")
    
    for attempt in range(1, MAX_RETRIES + 1):
        with ConnectionHandler(f"Connection attempt {attempt}/{MAX_RETRIES}"):
            try:
                # Establish connection with timeout
                websocket = await asyncio.wait_for(
                    websockets.connect(
                        websocket_url,
                        max_size=None,
                        ping_interval=20,
                        ping_timeout=10
                    ),
                    timeout=CONNECTION_TIMEOUT
                )
                
                # Verify connection immediately
                if await verify_websocket_health(websocket):
                    Cosmic.websocket = websocket
                    logger.info(f"WebSocket connection established successfully on attempt {attempt}")
                    return True
                else:
                    logger.warning(f"WebSocket connection failed health check on attempt {attempt}")
                    await websocket.close()
                    
            except asyncio.TimeoutError:
                logger.warning(f"Connection timeout on attempt {attempt}")
            except websockets.exceptions.InvalidURI:
                logger.error(f"Invalid WebSocket URI: {websocket_url}")
                return False  # Don't retry for invalid URI
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"Connection closed during attempt {attempt}: {e}")
            except OSError as e:
                logger.warning(f"Network error on attempt {attempt}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {type(e).__name__}: {e}")
        
        # Wait before retry (except for last attempt)
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY * attempt)  # Exponential backoff
    
    logger.error(f"Failed to establish WebSocket connection after {MAX_RETRIES} attempts")
    Cosmic.websocket = None
    return False
