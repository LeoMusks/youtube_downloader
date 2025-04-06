from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid
from threading import Thread
import time
from datetime import datetime

app = Flask(__name__)

# 存储下载任务的状态
tasks = {}

def format_speed(speed):
    if not speed:
        return "0 MB/s"
    speed_mb = speed / (1024 * 1024)  # 转换为MB/s
    return f"{speed_mb:.2f} MB/s"

def download_video_task(url, resolution, task_id):
    try:
        # 获取下载目录的基础路径
        base_download_dir = os.path.join(os.getcwd(), 'downloads')
        
        # 创建基础下载目录（如果不存在）
        if not os.path.exists(base_download_dir):
            os.makedirs(base_download_dir)
            
        # 获取当前时间作为目录名的一部分
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 使用yt-dlp获取视频信息
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'unknown_video')
            # 清理文件名，移除非法字符
            video_title = "".join(x for x in video_title if x.isalnum() or x in (' ', '-', '_')).strip()
            
        # 创建视频专属目录：时间戳_视频标题
        video_dir = f"{timestamp}_{video_title[:50]}"  # 限制目录名长度
        download_path = os.path.join(base_download_dir, video_dir)
        
        # 创建视频专属目录
        os.makedirs(download_path, exist_ok=True)

        # 从分辨率中提取高度数字（例如从"720p"中提取"720"）
        height = int(resolution.replace('p', ''))
        
        # 准备下载选项
        ydl_opts = {
            'format': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best',
            'progress_hooks': [lambda d: progress_hook(d, task_id)],
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',  # 强制输出MP4格式
            'quiet': True,
        }
        
        # 更新任务状态
        tasks[task_id] = {
            'status': '准备中',
            'progress': 0,
            'speed': None,
            'eta': None,
            'current_video': {
                'title': video_title,
                'status': '准备下载',
                'progress': 0,
                'downloaded_bytes': 0,
                'total_bytes': 0,
                'speed': '-',
                'eta': None
            }
        }
        
        # 开始下载
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # 下载完成后更新状态
        tasks[task_id]['status'] = '完成'
        tasks[task_id]['current_video']['status'] = '完成'
        tasks[task_id]['current_video']['progress'] = 100
        
        return {'status': 'success', 'message': '下载完成', 'download_path': download_path}
        
    except Exception as e:
        print(f"下载出错: {str(e)}")
        if task_id in tasks:
            tasks[task_id]['status'] = '失败'
            tasks[task_id]['current_video']['status'] = '失败'
        return {'status': 'error', 'message': f'下载失败: {str(e)}'}

def progress_hook(d, task_id):
    if task_id not in tasks:
        return
        
    try:
        if d['status'] == 'downloading':
            # 更新下载进度
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                progress = (downloaded / total) * 100
            else:
                progress = 0
                
            # 格式化速度显示
            speed = d.get('speed', 0)
            if speed:
                speed = f"{speed / 1024 / 1024:.2f} MB/s"
            else:
                speed = '-'
                
            # 更新任务状态
            tasks[task_id].update({
                'status': '进行中',
                'current_video': {
                    'status': '下载中',
                    'progress': progress,
                    'downloaded_bytes': downloaded,
                    'total_bytes': total,
                    'speed': speed,
                    'eta': d.get('eta'),
                    'title': d.get('filename', '').split('/')[-1]
                }
            })
            
        elif d['status'] == 'finished':
            tasks[task_id]['status'] = '处理中'
            tasks[task_id]['current_video']['status'] = '处理中'
            
    except Exception as e:
        print(f"进度更新出错: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_resolutions', methods=['POST'])
def get_resolutions():
    try:
        url = request.json.get('url')
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            resolutions = set()
            
            # 获取视频标题
            title = info.get('title', '未知标题')
            
            # 处理分辨率
            for f in formats:
                height = f.get('height')
                if height and isinstance(height, (int, float)):
                    resolutions.add(f"{int(height)}p")
            
            # 确保至少有一些常用分辨率选项
            default_resolutions = {'2160p', '1440p', '1080p', '720p', '480p', '360p'}
            available_resolutions = resolutions.union(default_resolutions)
            
            return jsonify({
                'success': True,
                'title': title,
                'resolutions': sorted(list(available_resolutions), key=lambda x: int(x[:-1]), reverse=True)
            })
    except Exception as e:
        print(f"Error in get_resolutions: {str(e)}")
        return jsonify({'success': False, 'error': f'获取视频信息失败：{str(e)}'})

@app.route('/api/start_download', methods=['POST'])
def start_download():
    try:
        url = request.json.get('url')
        resolution = request.json.get('resolution', '720p')
        
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            'status': '进行中',
            'message': '准备下载...',
            'current_video': None
        }
        
        # 创建下载目录
        os.makedirs('downloads', exist_ok=True)
        
        # 启动下载线程
        thread = Thread(target=download_video_task, args=(url, resolution, task_id))
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check_status/<task_id>')
def check_status(task_id):
    if task_id in tasks:
        return jsonify(tasks[task_id])
    return jsonify({'status': '失败', 'message': '任务不存在'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 