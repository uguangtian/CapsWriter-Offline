# 启动智能体代理服务

import asyncio
from multiprocessing import Process

from agent.agent_service import AgentService


def run_agent_service(host="127.0.0.1", port=6020):
    """启动智能体代理服务
    
    Args:
        host: 服务主机地址
        port: 服务端口
    """
    # 创建并启动代理服务
    agent_service = AgentService(host=host, port=port)
    
    # 在新进程中启动服务
    process = Process(target=_start_agent_service, args=(host, port))
    process.start()
    print(f"[AgentService] 已在进程中启动服务，监听地址: {host}:{port}")
    return process


def _start_agent_service(host, port):
    """在新进程中启动代理服务的辅助函数"""
    agent_service = AgentService(host=host, port=port)
    agent_service.start()


if __name__ == "__main__":
    run_agent_service()