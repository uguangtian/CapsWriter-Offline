import subprocess


def check_process(name):
    # 使用wmic命令查找进程
    command = ['wmic', 'process', 'get', 'name']

    # 创建STARTUPINFO结构并设置wShowWindow为SW_HIDE
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE

    # 执行命令并捕获输出
    output = subprocess.check_output(command, startupinfo=si).decode('utf-8', errors='replace')

    # 检查进程名称是否在输出中
    return name in output

if __name__ == '__main__':
    print(check_process('Notepad.exe'))