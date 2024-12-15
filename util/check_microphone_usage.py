import threading
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
            # print(f"Value {value_name} is not a QWORD.")
            return None
    except FileNotFoundError:
        # print("Registry key or value not found.")
        return None
    except Exception:
        # print(f"An error occurred: {e}")
        return None


def is_microphone_in_use():
    # Static variables
    if not hasattr(is_microphone_in_use, "last_check_time"):
        is_microphone_in_use.last_check_time = 0
    if not hasattr(is_microphone_in_use, "cached_result"):
        is_microphone_in_use.cached_result = False
    if not hasattr(is_microphone_in_use, "lock"):
        is_microphone_in_use.lock = threading.RLock()

    now = time.time()
    with is_microphone_in_use.lock:
        if now - is_microphone_in_use.last_check_time >= 1:
            try:
                current_path = Path().cwd()
                sub_path = (
                    r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\NonPackaged\\"
                    + str(current_path).replace("\\", "#")
                    + r"#runtime#pythonw_CapsWriter_Client.exe"
                )
                value_name = "LastUsedTimeStop"

                qword_value = read_qword_value(
                    winreg.HKEY_CURRENT_USER, sub_path, value_name
                )
                if qword_value is not None:
                    if qword_value == 0:
                        actual_result = True
                    else:
                        actual_result = False
                else:
                    actual_result = False
            except Exception:
                # print(f"Error checking microphone status: {e}")
                actual_result = is_microphone_in_use.cached_result
            is_microphone_in_use.cached_result = actual_result
            # print(send_signal_result)
            is_microphone_in_use.last_check_time = now
        return is_microphone_in_use.cached_result


def test():
    while True:
        time.sleep(0.1)
        is_microphone_in_use()


if __name__ == "__main__":
    test()
