import sys
import os
# import pytest
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from util.config import ClientConfig, ServerConfig, get_config_dict

def test_client_config_fallback():
    """Test that ClientConfig falls back to ServerConfig values where appropriate."""
    
    # These values were removed from [client] in config.toml and should fallback to [server]
    # or be correctly read from [server] via the fallback logic in util/config.py
    
    # Check speech_recognition_port
    # ServerConfig has it as int(6016)
    assert ServerConfig.speech_recognition_port == 6016
    assert ClientConfig.speech_recognition_port == 6016
    assert isinstance(ClientConfig.speech_recognition_port, int)
    
    # Check offline_translate_port
    # ServerConfig has it as "6017"
    assert ServerConfig.offline_translate_port == "6017"
    assert ClientConfig.offline_translate_port == "6017"
    
    # Check shrink_automatically_to_tray
    # ServerConfig has it as True (based on toml)
    # config.toml: shrink_automatically_to_tray = true (line 34)
    # ClientConfig should fallback
    assert ClientConfig.shrink_automatically_to_tray == ServerConfig.shrink_automatically_to_tray
    
    # Check only_run_once
    assert ClientConfig.only_run_once == ServerConfig.only_run_once

def test_get_config_dict():
    """Test that get_config_dict returns the expected structure."""
    config_dict = get_config_dict()
    
    assert "server" in config_dict
    assert "model_paths" in config_dict
    assert "paraformer_args" in config_dict
    assert "sensevoice_args" in config_dict
    assert "funasr_nano_args" in config_dict
    
    # Check server config content
    assert config_dict["server"]["model"] == ServerConfig.model
    assert config_dict["server"]["format_num"] == ServerConfig.format_num
    
    # Check paths
    assert "paraformer_path" in config_dict["model_paths"]
    
    # Check args
    assert "paraformer" in config_dict["paraformer_args"]

if __name__ == "__main__":
    # Manually run tests if pytest is not available
    try:
        test_client_config_fallback()
        print("test_client_config_fallback passed")
        test_get_config_dict()
        print("test_get_config_dict passed")
    except AssertionError as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
