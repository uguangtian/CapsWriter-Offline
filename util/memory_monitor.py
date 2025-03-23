# 内存监控和管理模块

import gc
import os
import sys
import time
import logging
import threading
import psutil
from platform import system
from typing import Optional, Dict, List, Tuple, Callable

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MemoryMonitor")


class MemoryMonitor:
    """内存监控和管理类
    
    监控程序内存使用情况，并在需要时执行内存清理操作。
    支持定期检查、阈值触发清理和手动清理。
    
    Attributes:
        threshold_percent: 内存使用阈值百分比，超过此值触发清理
        check_interval: 检查间隔时间（秒）
        is_monitoring: 是否正在监控
        _monitor_thread: 监控线程
        _callbacks: 清理回调函数列表
    """
    
    def __init__(self, threshold_percent: float = 75.0, check_interval: int = 30):
        """初始化内存监控器
        
        Args:
            threshold_percent: 内存使用阈值百分比，默认75%
            check_interval: 检查间隔时间（秒），默认30秒
        """
        self.threshold_percent = threshold_percent
        self.check_interval = check_interval
        self.is_monitoring = False
        self._monitor_thread = None
        self._callbacks: List[Callable] = []
        
        # 初始化时执行一次垃圾回收
        self.collect_garbage()
        
    def start_monitoring(self):
        """启动内存监控"""
        if self.is_monitoring:
            logger.warning("内存监控已经在运行")
            return
            
        self.is_monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"内存监控已启动，阈值: {self.threshold_percent}%，检查间隔: {self.check_interval}秒")
        
    def stop_monitoring(self):
        """停止内存监控"""
        self.is_monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        logger.info("内存监控已停止")
        
    def _monitor_loop(self):
        """监控循环，定期检查内存使用情况"""
        while self.is_monitoring:
            try:
                memory_info = self.get_memory_info()
                percent_used = memory_info['percent']
                
                if percent_used > self.threshold_percent:
                    logger.warning(f"内存使用率 {percent_used:.1f}% 超过阈值 {self.threshold_percent}%，执行清理")
                    self.cleanup_memory()
                    
                    # 清理后再次检查
                    memory_info = self.get_memory_info()
                    logger.info(f"清理后内存使用率: {memory_info['percent']:.1f}%")
                    
            except Exception as e:
                logger.error(f"内存监控出错: {str(e)}")
                
            # 等待下一次检查
            time.sleep(self.check_interval)
    
    def get_memory_info(self) -> Dict:
        """获取当前内存使用情况
        
        Returns:
            Dict: 包含内存使用信息的字典
        """
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # 获取系统内存信息
        system_memory = psutil.virtual_memory()
        
        # 计算当前进程内存使用百分比
        process_percent = (memory_info.rss / system_memory.total) * 100
        
        return {
            'rss': memory_info.rss,  # 物理内存使用（字节）
            'vms': memory_info.vms,  # 虚拟内存使用（字节）
            'percent': process_percent,  # 进程内存使用百分比
            'system_percent': system_memory.percent,  # 系统内存使用百分比
            'system_available': system_memory.available,  # 系统可用内存（字节）
            'system_total': system_memory.total  # 系统总内存（字节）
        }
    
    def collect_garbage(self):
        """执行Python垃圾回收"""
        gc.collect()
        
    def empty_working_set(self):
        """清空工作集（仅Windows平台有效）"""
        if system() == "Windows":
            try:
                from util.empty_working_set import empty_current_working_set
                empty_current_working_set()
                logger.info("已清空工作集")
            except Exception as e:
                logger.error(f"清空工作集失败: {str(e)}")
    
    def cleanup_memory(self):
        """执行内存清理操作"""
        # 执行Python垃圾回收
        collected = gc.collect()
        logger.info(f"垃圾回收完成，回收了 {collected} 个对象")
        
        # 清空工作集（仅Windows平台）
        self.empty_working_set()
        
        # 执行注册的回调函数
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"执行回调函数出错: {str(e)}")
    
    def register_cleanup_callback(self, callback: Callable):
        """注册清理回调函数
        
        Args:
            callback: 无参数的回调函数，在清理内存时调用
        """
        if callable(callback) and callback not in self._callbacks:
            self._callbacks.append(callback)
            return True
        return False
    
    def unregister_cleanup_callback(self, callback: Callable) -> bool:
        """取消注册清理回调函数
        
        Args:
            callback: 要取消的回调函数
            
        Returns:
            bool: 是否成功取消
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            return True
        return False


# 全局内存监控器实例
_memory_monitor: Optional[MemoryMonitor] = None


def get_memory_monitor(threshold_percent: float = 75.0, check_interval: int = 30) -> MemoryMonitor:
    """获取全局内存监控器实例
    
    Args:
        threshold_percent: 内存使用阈值百分比
        check_interval: 检查间隔时间（秒）
        
    Returns:
        MemoryMonitor: 内存监控器实例
    """
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor(threshold_percent, check_interval)
    return _memory_monitor


def start_memory_monitoring(threshold_percent: float = 75.0, check_interval: int = 30):
    """启动内存监控
    
    Args:
        threshold_percent: 内存使用阈值百分比
        check_interval: 检查间隔时间（秒）
    """
    monitor = get_memory_monitor(threshold_percent, check_interval)
    monitor.start_monitoring()
    

def stop_memory_monitoring():
    """停止内存监控"""
    global _memory_monitor
    if _memory_monitor is not None:
        _memory_monitor.stop_monitoring()


def cleanup_memory():
    """手动执行内存清理"""
    monitor = get_memory_monitor()
    monitor.cleanup_memory()
    return monitor.get_memory_info()


def register_cleanup_callback(callback: Callable) -> bool:
    """注册清理回调函数
    
    Args:
        callback: 无参数的回调函数，在清理内存时调用
        
    Returns:
        bool: 是否成功注册
    """
    monitor = get_memory_monitor()
    return monitor.register_cleanup_callback(callback)


def get_memory_usage() -> Dict:
    """获取当前内存使用情况
    
    Returns:
        Dict: 包含内存使用信息的字典
    """
    monitor = get_memory_monitor()
    return monitor.get_memory_info()


if __name__ == "__main__":
    # 测试代码
    print("内存监控模块测试")
    
    # 获取当前内存使用情况
    memory_info = get_memory_usage()
    print(f"当前内存使用: {memory_info['rss'] / 1024 / 1024:.1f} MB ({memory_info['percent']:.1f}%)")
    
    # 执行内存清理
    print("执行内存清理...")
    memory_info = cleanup_memory()
    print(f"清理后内存使用: {memory_info['rss'] / 1024 / 1024:.1f} MB ({memory_info['percent']:.1f}%)")
    
    # 启动监控（测试用，短时间）
    print("启动内存监控（5秒）...")
    start_memory_monitoring(threshold_percent=0, check_interval=1)  # 设置阈值为0确保会触发清理
    time.sleep(5)
    stop_memory_monitoring()
    print("测试完成")