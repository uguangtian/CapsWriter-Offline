import time
import winreg
from pathlib import Path


def read_qword_value(root_key, sub_path, value_name):
    try:
        reg_key = winreg.OpenKey(root_key, sub_path)
        value, reg_type = winreg.QueryValueEx(reg_key, value_name)
        if reg_type == winreg.REG_QWORD:
            return value
        else:
            print(f"Value {value_name} is not a QWORD.")
            return None
    except FileNotFoundError:
        print("Registry key or value not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def is_microphone_in_use():
    current_path = Path().cwd()
    sub_path = (
        r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\NonPackaged\\"
        + str(current_path).replace("\\", "#")
        + r"#runtime#pythonw_CapsWriter_Client.exe"
    )
    # print(sub_path)
    value_name = "LastUsedTimeStop"

    qword_value = read_qword_value(winreg.HKEY_CURRENT_USER, sub_path, value_name)
    if qword_value is not None:
        # print(f"QWORD value: {qword_value}")  # 麦克风 上次访问时间戳
        if qword_value == 0:
            # print("Microphone is in use.")
            return True
        else:
            return False
    else:
        # print("Failed to read QWORD value.")
        return None


if __name__ == "__main__":
    while True:
        if is_microphone_in_use():
            print("Microphone is in use.")
        else:
            pass
        time.sleep(1)
