import subprocess
import httpx, json
from config import ClientConfig as Config
# 启动在线翻译服务端
# 设置启动信息，用于隐藏窗口
info = subprocess.STARTUPINFO()
info.dwFlags = subprocess.STARTF_USESHOWWINDOW
info.wShowWindow = subprocess.SW_HIDE
deeplx_translate_server_proc = subprocess.Popen(['.\\deeplx_windows_amd64.exe'], startupinfo=info) # https://github.com/OwO-Network/DeepLX/releases

def translate_online(text):
    deeplx_api = "http://127.0.0.1:1188/translate"

    data = {
        "text": text,
        "source_lang": "auto",
        "target_lang": Config.trans_online_target_languages
    }

    post_data = json.dumps(data)
    r = httpx.post(url = deeplx_api, data = post_data).text

    # 将JSON字符串解析为Python字典
    data = json.loads(r)

    # 获取alternatives数组中的第一个字符串
    first_alternative = data.get('alternatives', [])[0]

    # 输出第一个替代字符串
    return first_alternative




if __name__ == '__main__':
    text = "有朋自远方来，不亦乐乎"
    online_trans_text = translate_online(text)
    print (online_trans_text)