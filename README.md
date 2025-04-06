# YouTube视频下载工具

一个基于Python和Flask的YouTube视频下载工具，提供简洁的Web界面，支持高清视频下载和播放列表批量下载。

作者：LeoMusk  
官网：[格子间代码](https://www.gezicode.cn)

## 功能特点

- 🎯 支持单个视频和播放列表下载
- 🎨 美观的Web界面，实时显示下载进度
- 📊 显示详细的下载信息（速度、进度、剩余时间）
- 📁 自动创建独立的下载目录，文件管理更清晰
- 🔍 支持多种视频质量选择（最高支持4K）
- 💫 实时进度条和状态更新
- 🌐 支持局域网访问，可在其他设备使用

## 安装说明

### 环境要求
- Python 3.8+
- pip包管理器

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/youtube_downloader.git
cd youtube_downloader
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 启动服务器：
```bash
python main.py
```
默认端口为8080，可以通过参数修改：
```bash
python main.py -p 8081  # 使用8081端口
```

2. 访问Web界面：
- 本地访问：http://127.0.0.1:8080
- 局域网访问：http://你的IP地址:8080

3. 下载视频：
   - 将YouTube视频链接粘贴到输入框
   - 点击"获取信息"按钮
   - 选择需要的视频质量
   - 点击"开始下载"按钮
   - 等待下载完成

## 命令行参数

```bash
python main.py [选项]

选项：
  -p, --port PORT        指定服务器端口（默认：8080）
  -H, --host HOST        指定服务器地址（默认：0.0.0.0）
  -d, --debug           启用调试模式
  --download-dir DIR    指定下载目录
```

## 特色功能

1. 智能文件管理
   - 每个视频创建独立的下载目录
   - 目录名格式：时间戳_视频标题
   - 自动过滤非法字符，确保文件名有效

2. 实时状态显示
   - 下载速度（动态更新）
   - 已下载大小/总大小
   - 剩余时间（精确到小数点后2位）
   - 进度条显示

3. 多任务支持
   - 支持同时下载多个视频
   - 每个下载任务独立显示状态
   - 自动管理下载队列

## 注意事项

1. 下载限制
   - 受YouTube政策限制，部分视频可能无法下载
   - 下载速度受网络环境和YouTube服务器影响
   - 部分高清视频可能需要较长下载时间

2. 网络要求
   - 需要稳定的网络连接
   - 建议使用代理以提高访问速度
   - 下载高清视频需要较大带宽

3. 存储空间
   - 确保有足够的磁盘空间
   - 4K视频文件较大，请预留足够空间
   - 定期清理不需要的下载文件

## 常见问题

1. Q: 无法获取视频信息？
   A: 检查网络连接和视频链接是否正确，某些视频可能有地区限制。

2. Q: 下载速度很慢？
   A: 可能是网络问题或YouTube服务器限制，建议使用代理或选择较低清晰度。

3. Q: 视频无法播放？
   A: 确保下载完整，检查是否有相应的视频播放器。

## 更新日志

### v1.0.0 (2024-04-06)
- 🎉 首次发布
- ✨ 支持单视频和播放列表下载
- 🎨 全新Web界面设计
- 📁 智能文件管理系统
- 📊 实时下载状态显示
- 🌐 局域网访问支持

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载引擎
- [Flask](https://flask.palletsprojects.com/) - Web框架支持
- [Bootstrap](https://getbootstrap.com/) - 界面设计框架 

## 联系方式

- 作者：LeoMusk
- 官方网站：[www.gezicode.cn](https://www.gezicode.cn)
- 技术支持：访问[格子间代码](https://www.gezicode.cn)获取更多帮助 