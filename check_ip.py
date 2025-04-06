import requests
import time
from urllib3.exceptions import InsecureRequestWarning
import ssl
import yt_dlp

def check_youtube_access():
    print("正在检查YouTube访问状态...")
    
    # 禁用SSL警告
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    
    # 测试URL
    test_url = "https://www.youtube.com"
    
    try:
        # 使用requests测试基本访问
        print("\n1. 测试基本访问...")
        response = requests.get(test_url, verify=False, timeout=10)
        print(f"HTTP状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 基本访问正常")
        else:
            print("❌ 基本访问异常")
        
        # 使用yt-dlp测试视频信息获取
        print("\n2. 测试视频信息获取...")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # 使用一个公开的YouTube视频进行测试
                test_video = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
                info = ydl.extract_info(test_video, download=False)
                print("✅ 视频信息获取正常")
                print(f"视频标题: {info.get('title', '未知')}")
            except Exception as e:
                print(f"❌ 视频信息获取失败: {str(e)}")
        
        # 测试下载功能
        print("\n3. 测试下载功能...")
        try:
            ydl_opts['format'] = 'best[height<=720]'
            ydl_opts['outtmpl'] = 'test_download.%(ext)s'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([test_video])
            print("✅ 下载功能正常")
        except Exception as e:
            print(f"❌ 下载功能异常: {str(e)}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络连接异常: {str(e)}")
    except Exception as e:
        print(f"❌ 发生未知错误: {str(e)}")

if __name__ == "__main__":
    check_youtube_access() 