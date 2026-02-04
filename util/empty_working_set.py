import ctypes
import platform

def empty_working_set(pid: int):
    # 仅在 Windows 下执行
    if platform.system() != "Windows":
        return

    try:
        # 获取 pid 的句柄
        handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)

        # 清空工作集
        ctypes.windll.psapi.EmptyWorkingSet(handle)

        # 关闭进程句柄
        ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        pass


def empty_current_working_set():
    # 仅在 Windows 下执行
    if platform.system() != "Windows":
        return
        
    try:
        # 获取当前进程ID
        pid = ctypes.windll.kernel32.GetCurrentProcessId()
        empty_working_set(pid)
    except Exception:
        pass