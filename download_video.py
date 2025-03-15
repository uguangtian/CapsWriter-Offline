

# 有一个下载工具，类似这样的一个调用方法，直接传入url
#  yt-dlp --cookies-from-browser 'Chrome' 'https://www.youtube.com/watch?v=dXAkywP0DdU'
# 实现下载完视频之后调用相应函数的解析视频功能来处理视频，跟下面类似
#    asyncio.run(main_file(file_paths))

import subprocess
import tempfile
import shutil
from pathlib import Path

async def download_and_transcribe(url, browser='Chrome', output_dir=None):
    """
    下载YouTube视频并进行转录
    
    参数:
        url: YouTube视频URL
        browser: 从哪个浏览器获取cookies，默认为Chrome
        output_dir: 输出目录，默认为临时目录
    """
    print(f"开始下载视频: {url}")
    
    # 创建临时目录用于存放下载的视频
    if output_dir is None:
        temp_dir = tempfile.mkdtemp()
        output_path = Path(temp_dir)
    else:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    
    try:
        # 构建yt-dlp命令
        cmd = [
            'yt-dlp',
            '--cookies-from-browser', browser,
            '-o', str(output_path / '%(title)s.%(ext)s'),
            '--restrict-filenames',  # 避免特殊字符
            url
        ]
        
        # 执行下载命令
        print("执行下载命令...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"下载失败: {result.stderr}")
            return
        
        print("下载完成，开始查找下载的视频文件...")
        
        # 查找下载的视频文件
        media_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm', '.mp3', '.wav']
        downloaded_files = []
        
        for ext in media_extensions:
            files = list(output_path.glob(f'*{ext}'))
            if files:
                downloaded_files.extend(files)
        
        if not downloaded_files:
            print("未找到下载的媒体文件")
            return
        
        print(f"找到 {len(downloaded_files)} 个媒体文件，开始转录...")
        
        # 转录下载的视频
        await main_file(downloaded_files)
        
        print("转录完成")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
    finally:
        # 如果使用临时目录，则在完成后清理
        # 只有在使用临时目录且temp_dir存在时才清理
        if output_dir is None and 'temp_dir' in locals():
            print("清理临时文件...")
            shutil.rmtree(temp_dir, ignore_errors=True)

# 使用示例
# asyncio.run(download_and_transcribe('https://www.youtube.com/watch?v=dXAkywP0DdU'))
