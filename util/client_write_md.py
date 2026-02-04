import time
import io
import sys
from os import makedirs
from pathlib import Path
from rich.console import Console
from rich.theme import Theme

from util.hot_kwds import kwd_list
from util.config import ClientConfig
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
my_theme = Theme({"markdown.code": "cyan", "markdown.item.number": "yellow"})
console = Console(highlight=False, soft_wrap=False, theme=my_theme)

# def do_updata_kwd(kwd_text: str):
#     """
#     把关键词文本中的每一行去除多余空格后添加到列表，
#     """
#
#     kwd_list = Cosmic.kwd_list
#     kwd_list.clear(); kwd_list.append('')
#     for kwd in kwd_text.splitlines():
#         kwd = kwd.strip()
#         if not kwd or kwd.startswith('#'): continue
#         kwd_list.append(kwd)
#     return len(kwd_list)

header_md = r"""```txt
正则表达式 Tip

匹配到音频文件链接：\[(.+)\]\((.{10,})\)[\s]*
替换为 HTML 控件：<audio controls><source src="$2" type="audio/mpeg">$1</audio>\n\n

匹配 HTML 控件：<audio controls><source src="(.+)" type="audio/mpeg">(.+)</audio>\n\n
替换为文件链接：[$2]($1) 
```


"""


def create_md(file_md):

    console.print(f"[DEBUG] md 文件路径: {file_md}")

    with open(file_md, "w", encoding="utf-8") as f:
        f.write(header_md)


def write_md(text: str, time_start: float, file_audio: Path):
    time_year = time.strftime("%Y", time.localtime(time_start))
    time_month = time.strftime("%m", time.localtime(time_start))
    time_day = time.strftime("%d", time.localtime(time_start))
    time_hms = time.strftime("%H:%M:%S", time.localtime(time_start))
    # folder_path = Path() / time_year / time_month
    folder_path = Path(ClientConfig.transcription_result_path).expanduser() / time_year / time_month
    console.print(f"[DEBUG] 写入 md 文件开始")
    makedirs(folder_path, exist_ok=True)
    #console.print(f"[DEBUG] 文件夹路径: {folder_path}, file_audio: {file_audio}")


    # 列表内的元素是元组，元组内包含了：关键词、md路径
    md_list = [
        (kwd, folder_path / f'{kwd + "-" if kwd else ""}{time_day}.md')
        for kwd in kwd_list
        if text.startswith(kwd)
    ]

    #console.print(f"[DEBUG] md 文件列表: {md_list}")

    # 为 md 文件写入识别记录
    for kwd, file_md in md_list:
        # 确保 md 文件存在
        if not file_md.exists():
            create_md(file_md)
        #console.print(f"[DEBUG] md 文件路径: {file_md}")

        # 写入 md
        with open(file_md, "a", encoding="utf-8") as f:
            text_ = text[len(kwd) :].lstrip("，。,.")
            try:
                if file_audio is not None:
                    try:
                        # 确保两个路径都是绝对路径
                        abs_file_md_parent = file_md.parent.resolve()
                        abs_file_audio = file_audio.resolve()
                        path_ = abs_file_audio.relative_to(abs_file_md_parent).as_posix().replace(" ", "%20")
                        f.write(f"[{time_hms}]({path_}) {text_}\n\n")
                    except ValueError:
                        # 如果无法计算相对路径，使用绝对路径
                        path_ = file_audio.as_posix().replace(" ", "%20")
                        f.write(f"[{time_hms}]({path_}) {text_}\n\n")
                else:
                    f.write(f"[{time_hms}]() {text_}\n\n")
            except Exception as e:
                console.print(f"[DEBUG] 写入 md 文件失败: {e}")  
            else:
                console.print(f"[DEBUG] 写入 md 文件成功")  
