import subprocess
import sys

def check_process(name):
    if sys.platform == "win32":
        # Windows 平台：使用tasklist命令查找进程
        command = ['tasklist', '/FO', 'CSV', '/NH']  # 使用CSV格式输出，不显示标题行

        # 创建STARTUPINFO结构并设置wShowWindow为SW_HIDE
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE

        try:
            # 执行命令并捕获输出
            output = subprocess.check_output(command, startupinfo=si).decode('utf-8', errors='replace')
        except FileNotFoundError:
            print("未找到命令，检查是否安装在环境中。")
            return False

        # 清洗输出并检查进程名称是否在输出中
        for line in output.splitlines():
            # 解析输出，获取进程名称
            parts = line.split('",')  
            if len(parts) > 1:
                process_name = parts[0].replace('"', '').lower()
                if process_name == name.lower():
                    return True
    else:
        # macOS/Linux 平台：使用ps命令查找进程
        try:
            # 使用ps命令查找进程
            output = subprocess.check_output(['ps', 'aux']).decode('utf-8', errors='replace')
            for line in output.splitlines():
                if name.lower() in line.lower():
                    return True
        except FileNotFoundError:
            print("未找到ps命令。")
            return False
        except Exception as e:
            # 在某些 macOS 环境下（如沙盒或打包后），ps 可能无权限执行
            # 此时我们假设进程未运行，或者无法检测，避免程序崩溃
            # print(f"无法执行 ps 命令: {e}")
            return False
                
    return False

if __name__ == '__main__':
    print(check_process('notepad.exe'))
