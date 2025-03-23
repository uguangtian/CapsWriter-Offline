

# 有一个下载工具，类似这样的一个调用方法，直接传入url
#  yt-dlp --cookies-from-browser 'Chrome' 'https://www.youtube.com/watch?v=dXAkywP0DdU'
# 实现下载完视频之后调用相应函数的解析视频功能来处理视频，跟下面类似
#    asyncio.run(main_file(file_paths))

import subprocess
import tempfile
import shutil
import time  # 确保这里导入了time模块
from pathlib import Path
from core_client import main_file  # 导入 main_file 函数

# 添加一个函数来处理 watchdog 异常
def handle_watchdog_exception():
    """处理 watchdog 库可能抛出的异常"""
    import sys
    
    # 重定向标准错误输出，捕获但不显示 watchdog 的错误
    class WatchdogErrorFilter:
        def __init__(self, original_stderr):
            self.original_stderr = original_stderr
        
        def write(self, message):
            # 过滤掉 watchdog 相关的错误消息
            if "Unhandled exception in FSEventsEmitter" not in message and \
               "Cannot add watch" not in message and \
               "it is already scheduled" not in message:
                self.original_stderr.write(message)
        
        def flush(self):
            self.original_stderr.flush()
    
    # 应用过滤器
    sys.stderr = WatchdogErrorFilter(sys.stderr)

async def download_and_transcribe(url, browser='Chrome', output_dir=None):
    """
    下载YouTube视频并进行转录
    
    参数:
        url: YouTube视频URL
        browser: 从哪个浏览器获取cookies，默认为Chrome
        output_dir: 输出目录，默认为临时目录
    """
    # 处理 watchdog 异常
    handle_watchdog_exception()
    
    print("进入 download_and_transcribe 函数", flush=True)
    temp_dir = None
    # 确保输出目录存在
    if output_dir is not None:
        output_path = Path(output_dir)
        print(f"输出目录: {output_path}","是否存在:",output_path.exists(), flush=True)
        if not output_path.exists():  # 检查路径是否存在
            print(f"输出目录不存在，正在创建: {output_path}", flush=True)
            output_path.mkdir(parents=True, exist_ok=True)  # 创建目录
    else:
        temp_dir = tempfile.mkdtemp()
        output_path = Path(temp_dir)
        print(f"使用临时目录: {output_path}", flush=True)
    
    try:
        # 获取视频标题
        print("准备获取视频标题...", flush=True)
        title_cmd = [
            'yt-dlp',
            '--cookies-from-browser', browser,
            '--get-title',
            url
        ]
        print(f"执行命令: {' '.join(title_cmd)}", flush=True)
        
        # 使用 subprocess.run 的超时参数，避免无限等待
        try:
            result = subprocess.run(title_cmd, capture_output=True, text=True, timeout=30)
            print(f"获取标题命令返回码: {result.returncode}", flush=True)
            if result.returncode != 0:
                print(f"无法获取视频标题: {result.stderr}", flush=True)
                video_title = "unknown_video"
            else:
                video_title = result.stdout.strip()
                # 空格换成下划线
                video_title = video_title.replace(' ', '_')
                print(f"获取视频文件名: {video_title}", flush=True)
        except subprocess.TimeoutExpired:
            print("获取视频标题超时，使用默认文件名", flush=True)
            import time
            video_title = f"video_{int(time.time())}"
        except Exception as e:
            print(f"获取视频标题时出错: {e}", flush=True)
            import time
            video_title = f"video_{int(time.time())}"

        # 构建文件路径
        file_path = output_path / f'{video_title}.%(ext)s'
        print(f"文件将保存为: {file_path}", flush=True)
        
        # 查找下载的视频文件
        media_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm', '.mp3', '.wav']
        downloaded_files = []
        
        # 检查文件是否已存在
        print("检查文件是否已存在...", flush=True)
        for ext in media_extensions:
            possible_file = output_path / f'{video_title}{ext}'
            print(f"检查文件: {possible_file}", flush=True)
            if possible_file.exists():
                print(f"文件已存在，跳过下载: {possible_file}", flush=True)
                downloaded_files.append(possible_file)
                break
        else:
            # 如果文件不存在，则执行下载命令
            print("文件不存在，准备下载...", flush=True)
            cmd = [
                'yt-dlp',
                '--cookies-from-browser', browser,
                '-o', str(file_path),  # 使用视频标题作为文件名
                '--restrict-filenames',  # 避免特殊字符
                url
            ]
            
            print(f"执行下载命令: {' '.join(cmd)}", flush=True)
            
            # 使用 Popen 实时获取输出
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # 行缓冲
            )
            
            print("开始下载，实时输出进度:", flush=True)
            # 实时读取输出
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                print(line.strip(), flush=True)
            
            # 检查下载结果
            return_code = process.poll()
            print(f"下载命令返回码: {return_code}", flush=True)
            
            if return_code != 0:
                print(f"下载失败: 返回码 {return_code}", flush=True)
                return
            
            print("下载完成，开始查找下载的视频文件...", flush=True)
            
            # 查找下载的视频文件
            for ext in media_extensions:
                files = list(output_path.glob(f'*{ext}'))
                if files:
                    print(f"找到文件: {files}", flush=True)
                    downloaded_files.extend(files)
        
        if not downloaded_files:
            print("未找到下载的媒体文件", flush=True)
            return
        
        print(f"找到 {len(downloaded_files)} 个媒体文件: {downloaded_files}", flush=True)
        
        # 对于每个下载的文件，检查是否已经有对应的字幕文件
        files_to_transcribe = []
        for file in downloaded_files:
            srt_file = file.with_suffix('.srt')
            if srt_file.exists():
                print(f"文件 {file} 已有对应的字幕文件 {srt_file}，跳过转录", flush=True)
            else:
                files_to_transcribe.append(file)
        
        if not files_to_transcribe:
            print("所有文件都已有字幕，无需转录", flush=True)
            return
            
        print(f"需要转录的文件: {files_to_transcribe}", flush=True)
        
        # 对于长视频，可以考虑分段处理
        for file in files_to_transcribe:
            print(f"开始转录文件: {file}", flush=True)
            try:
                # 转录单个文件，添加重试机制
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        # 使用单独的文件列表调用 main_file
                        await main_file([file])
                        print(f"成功转录文件: {file}", flush=True)
                        break  # 成功则跳出重试循环
                    except Exception as e:
                        retry_count += 1
                        print(f"转录文件 {file} 时出错 (尝试 {retry_count}/{max_retries}): {e}", flush=True)
                        if retry_count < max_retries:
                            wait_time = 5 * retry_count  # 递增等待时间
                            print(f"等待 {wait_time} 秒后重试...", flush=True)
                            # 这里使用导入的time模块
                            import time as time_module  # 添加这一行，确保time模块可用
                            time_module.sleep(wait_time)  # 修改这一行，使用time_module而不是time
                        else:
                            print(f"达到最大重试次数，跳过文件: {file}", flush=True)
            except Exception as e:
                print(f"处理文件 {file} 时发生未捕获的异常: {e}", flush=True)
                import traceback
                print(traceback.format_exc(), flush=True)
        
        print("所有文件转录完成", flush=True)
        
    except Exception as e:
        print(f"处理过程中出错: {e}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
    finally:
        # 如果使用临时目录，则在完成后清理
        if output_dir is None and temp_dir:
            print("清理临时文件...", flush=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
        print("函数执行完毕", flush=True)

# 使用示例
# asyncio.run(download_and_transcribe('https://www.youtube.com/watch?v=dXAkywP0DdU'))
