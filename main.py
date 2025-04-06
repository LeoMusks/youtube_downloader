#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
from web import app
import yt_dlp
import re
import time
import ssl
from urllib.error import HTTPError
from tqdm import tqdm
import concurrent.futures
from datetime import datetime

def sanitize_filename(filename):
    """清理文件名中的非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def get_ydl_opts(resolution='720p', output_path='downloads'):
    """获取通用的yt-dlp选项"""
    return {
        'format': f'bestvideo[height<={resolution[:-1]}]+bestaudio/best[height<={resolution[:-1]}]/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'socket_timeout': 30,  # 设置超时时间
        'retries': 3,  # 重试次数
    }

class DownloadProgressBar:
    def __init__(self, total=None, desc=None, task_id=None, download_status=None):
        self.pbar = None
        self.last_downloaded = 0
        self.total = total
        self.desc = desc
        self.current_stage = "初始化"
        self.start_time = time.time()
        self.task_id = task_id
        self.download_status = download_status
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.current_file = ""

    def __call__(self, d):
        if d['status'] == 'downloading':
            # 更新下载进度
            self.total_bytes = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            self.downloaded_bytes = d.get('downloaded_bytes', 0)
            self.current_file = d.get('filename', '')
            
            if self.total_bytes:
                progress = (self.downloaded_bytes / self.total_bytes) * 100
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                # 更新下载状态
                if self.task_id and self.download_status:
                    self.download_status[self.task_id] = {
                        'status': '正在下载',
                        'progress': progress,
                        'message': (
                            f'正在下载: {os.path.basename(self.current_file)}\n'
                            f'速度: {self._format_speed(speed)}\n'
                            f'剩余时间: {self._format_eta(eta)}'
                        ),
                        'downloaded': self._format_bytes(self.downloaded_bytes),
                        'total': self._format_bytes(self.total_bytes),
                        'speed': self._format_speed(speed),
                        'eta': self._format_eta(eta)
                    }
                
        elif d['status'] == 'finished':
            if self.task_id and self.download_status:
                self.download_status[self.task_id] = {
                    'status': '处理中',
                    'progress': 100,
                    'message': '正在处理文件...'
                }
        elif d['status'] == 'error':
            if self.task_id and self.download_status:
                self.download_status[self.task_id] = {
                    'status': '错误',
                    'progress': 0,
                    'message': f'下载错误: {d.get("error")}'
                }

    def _format_bytes(self, bytes):
        """格式化字节大小"""
        if bytes == 0:
            return "0B"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while bytes >= 1024 and i < len(units)-1:
            bytes /= 1024
            i += 1
        return f"{bytes:.2f}{units[i]}"

    def _format_speed(self, speed):
        """格式化下载速度"""
        if not speed:
            return "0 B/s"
        return f"{self._format_bytes(speed)}/s"

    def _format_eta(self, eta):
        """格式化剩余时间"""
        if not eta:
            return "未知"
        minutes, seconds = divmod(eta, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"

def download_video(url, resolution='720p', output_path='downloads', max_retries=3, task_id=None, download_status=None):
    """下载单个视频"""
    for attempt in range(max_retries):
        try:
            print(f"\n尝试下载 (第 {attempt + 1} 次)...")
            ydl_opts = get_ydl_opts(resolution, output_path)
            progress_hook = DownloadProgressBar(task_id=task_id, download_status=download_status)
            ydl_opts['progress_hooks'] = [progress_hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("正在获取视频信息...")
                info = ydl.extract_info(url, download=False)
                print(f"视频标题: {info['title']}")
                print("开始下载...")
                ydl.download([url])
                print(f"\n下载完成: {info['title']}")
                return True
        except HTTPError as e:
            print(f"\nHTTP错误: {e.code}")
            if attempt < max_retries - 1:
                print(f"等待重试 ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            else:
                return False
        except Exception as e:
            print(f"\n错误: {str(e)}")
            if attempt < max_retries - 1:
                print(f"等待重试 ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            else:
                return False
    return False

def get_playlist_info(url, max_retries=3):
    """获取播放列表信息"""
    for attempt in range(max_retries):
        try:
            print(f"\n正在获取播放列表信息 (第 {attempt + 1} 次尝试)...")
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("正在解析播放列表...")
                info = ydl.extract_info(url, download=False)
                playlist_title = info.get('title', '未知播放列表')
                playlist_title = sanitize_filename(playlist_title)
                
                print("正在获取视频列表...")
                entries = []
                for entry in info.get('entries', []):
                    if entry and 'url' in entry:
                        entries.append({
                            'url': entry['url'],
                            'title': entry.get('title', '未知标题'),
                            'duration': entry.get('duration', 0)
                        })
                        print(f"已获取视频: {entry.get('title', '未知标题')}")
                
                return {
                    'title': playlist_title,
                    'entries': entries,
                    'total': len(entries)
                }
        except Exception as e:
            print(f"\n获取播放列表信息失败: {str(e)}")
            if attempt < max_retries - 1:
                print(f"等待重试 ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            else:
                return None
    return None

def download_playlist(url, resolution='720p', max_retries=3, batch_size=5):
    """下载播放列表中的所有视频"""
    # 首先获取播放列表信息
    print("\n正在获取播放列表信息...")
    playlist_info = get_playlist_info(url)
    if not playlist_info:
        return False
    
    playlist_title = playlist_info['title']
    entries = playlist_info['entries']
    total_videos = playlist_info['total']
    
    if total_videos == 0:
        print("播放列表为空或无法访问")
        return False
    
    # 创建播放列表专属文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    playlist_dir = os.path.join('downloads', f"{playlist_title}_{timestamp}")
    if not os.path.exists(playlist_dir):
        os.makedirs(playlist_dir)
    
    print(f"\n开始下载播放列表: {playlist_title}")
    print(f"共 {total_videos} 个视频")
    print(f"每批次下载 {batch_size} 个视频")
    
    success_count = 0
    failed_videos = []
    
    # 分批下载视频
    for batch_start in range(0, total_videos, batch_size):
        batch_end = min(batch_start + batch_size, total_videos)
        current_batch = entries[batch_start:batch_end]
        
        print(f"\n开始下载第 {batch_start + 1} 到 {batch_end} 个视频:")
        
        for i, entry in enumerate(current_batch, batch_start + 1):
            video_url = entry['url']
            video_title = entry['title']
            duration = entry['duration']
            
            print(f"\n准备下载第 {i}/{total_videos} 个视频:")
            print(f"标题: {video_title}")
            print(f"时长: {duration}秒")
            print(f"URL: {video_url}")
            
            if download_video(video_url, resolution, playlist_dir, task_id=i, download_status=failed_videos):
                success_count += 1
                print(f"\n第 {i} 个视频下载成功: {video_title}")
            else:
                failed_videos.append(video_title)
                print(f"\n第 {i} 个视频下载失败: {video_title}")
            
            # 下载完一个视频后暂停一下，避免请求过于频繁
            time.sleep(1)
        
        # 每批次下载完成后暂停一段时间
        if batch_end < total_videos:
            print(f"\n当前批次下载完成，等待30秒后继续下一批次...")
            for remaining in range(30, 0, -1):
                print(f"\r等待时间: {remaining}秒", end='')
                time.sleep(1)
            print("\n继续下载下一批次...")
    
    print(f"\n播放列表下载完成！")
    print(f"成功下载: {success_count}/{total_videos} 个视频")
    if failed_videos:
        print("以下视频下载失败:")
        for video in failed_videos:
            print(f"- {video}")
    return True

def get_available_resolutions(url, max_retries=3):
    """获取视频可用的分辨率"""
    for attempt in range(max_retries):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                resolutions = sorted(set(f.get('height', 0) for f in formats if f.get('height')), reverse=True)
                return [f"{res}p" for res in resolutions if res > 0]
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"\n获取分辨率失败，正在重试 ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            else:
                print(f"获取分辨率失败: {str(e)}")
                return []
    return []

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='YouTube视频下载工具')
    parser.add_argument('-p', '--port', type=int, default=8080,
                      help='服务器端口号 (默认: 8080)')
    parser.add_argument('-H', '--host', type=str, default='0.0.0.0',
                      help='服务器主机地址 (默认: 0.0.0.0)')
    parser.add_argument('-d', '--debug', action='store_true',
                      help='启用调试模式')
    parser.add_argument('--download-dir', type=str, default='downloads',
                      help='下载目录路径 (默认: downloads)')
    return parser.parse_args()

def setup_environment(args):
    """设置运行环境"""
    # 确保在正确的目录下运行
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 创建下载目录
    os.makedirs(args.download_dir, exist_ok=True)
    
    # 设置下载目录环境变量
    os.environ['DOWNLOAD_DIR'] = args.download_dir

def print_startup_message(args):
    """打印启动信息"""
    print("\n=== YouTube视频下载工具 ===")
    print(f"服务器地址: http://{args.host if args.host != '0.0.0.0' else '127.0.0.1'}:{args.port}")
    if args.host == '0.0.0.0':
        import socket
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"局域网地址: http://{local_ip}:{args.port}")
        except:
            pass
    print(f"下载目录: {os.path.abspath(args.download_dir)}")
    print(f"调试模式: {'开启' if args.debug else '关闭'}")
    print("\n按 Ctrl+C 停止服务器")
    print("="*30 + "\n")

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    try:
        # 设置环境
        setup_environment(args)
        
        # 打印启动信息
        print_startup_message(args)
        
        # 启动Flask应用
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 