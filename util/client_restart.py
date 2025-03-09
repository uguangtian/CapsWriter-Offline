import subprocess
from time import sleep

from util.check_process import check_process


def stop_exe(exe_name: str):
    print(f"Stopping {exe_name}")
    subprocess.Popen(
        f"taskkill /IM {exe_name} /F",
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True,
    )
    sleep(1)
    if check_process(exe_name):
        stop_exe(exe_name)
    else:
        return


def start_exe(exe_name: str):
    print(f"Starting {exe_name}")
    subprocess.Popen(
        f'start "" "{exe_name}"',
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True,
    )
    sleep(1)
    if not check_process(exe_name):
        start_exe(exe_name)
    else:
        return


def restart_exe(exe_name: str):
    stop_exe(exe_name)
    start_exe(exe_name)


def stop_client():
    exe_name_list = [
        "start_client_gui_admin.exe",
        "start_client_gui.exe",
        "pythonw_CapsWriter_Client.exe",
        "hint_while_recording.exe",
    ]

    for exe_name in exe_name_list:
        stop_exe(exe_name)


def restart_client_admin():
    stop_client()
    start_exe("start_client_gui_admin.exe")


def restart_client():
    stop_client()
    start_exe("start_client_gui.exe")


if __name__ == "__main__":
    if check_process("start_client_gui_admin.exe"):
        restart_client_admin()
    else:
        restart_client()
