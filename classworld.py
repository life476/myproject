import os
import re
import json
import sqlite3
import requests
import traceback
import subprocess
import time
import sys
import base64
import html
from urllib.parse import unquote

# 更新请求头
header = {
    "referer": "https://www.bilibili.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}

def create_directory(path):
    """创建目录，如果不存在则创建，返回是否成功"""
    try:
        os.makedirs(path, exist_ok=True)
        print(f"目录已创建: {path}")
        return True
    except OSError as e:
        print(f"创建目录失败: {path} - 错误: {str(e)}")
        return False

def find_browser_cookie_files():
    """查找常见浏览器的Cookie文件路径"""
    cookie_paths = []
    home_dir = os.path.expanduser("~")
    
    # 平台检测
    if sys.platform == "win32":
        # Windows路径
        appdata = os.getenv("LOCALAPPDATA")
        roaming = os.getenv("APPDATA")
        
        # Chrome
        chrome_path = os.path.join(appdata, "Google", "Chrome", "User Data")
        if os.path.exists(chrome_path):
            for root, dirs, files in os.walk(chrome_path):
                if "Cookies" in files:
                    cookie_paths.append({
                        "browser": "Chrome",
                        "path": os.path.join(root, "Cookies"),
                        "profile": os.path.basename(root)
                    })
        
        # Edge
        edge_path = os.path.join(appdata, "Microsoft", "Edge", "User Data")
        if os.path.exists(edge_path):
            for root, dirs, files in os.walk(edge_path):
                if "Cookies" in files:
                    cookie_paths.append({
                        "browser": "Edge",
                        "path": os.path.join(root, "Cookies"),
                        "profile": os.path.basename(root)
                    })
        
        # Firefox
        firefox_path = os.path.join(roaming, "Mozilla", "Firefox", "Profiles")
        if os.path.exists(firefox_path):
            for profile in os.listdir(firefox_path):
                profile_path = os.path.join(firefox_path, profile)
                if os.path.isdir(profile_path):
                    cookies_path = os.path.join(profile_path, "cookies.sqlite")
                    if os.path.exists(cookies_path):
                        cookie_paths.append({
                            "browser": "Firefox",
                            "path": cookies_path,
                            "profile": profile
                        })
    
    elif sys.platform == "darwin":
        # macOS路径
        # Chrome
        chrome_path = os.path.join(home_dir, "Library", "Application Support", "Google", "Chrome")
        if os.path.exists(chrome_path):
            for root, dirs, files in os.walk(os.path.join(chrome_path, "Default")):
                if "Cookies" in files:
                    cookie_paths.append({
                        "browser": "Chrome",
                        "path": os.path.join(root, "Cookies"),
                        "profile": "Default"
                    })
        
        # Edge
        edge_path = os.path.join(home_dir, "Library", "Application Support", "Microsoft Edge")
        if os.path.exists(edge_path):
            for root, dirs, files in os.walk(os.path.join(edge_path, "Default")):
                if "Cookies" in files:
                    cookie_paths.append({
                        "browser": "Edge",
                        "path": os.path.join(root, "Cookies"),
                        "profile": "Default"
                    })
        
        # Firefox
        firefox_path = os.path.join(home_dir, "Library", "Application Support", "Firefox", "Profiles")
        if os.path.exists(firefox_path):
            for profile in os.listdir(firefox_path):
                profile_path = os.path.join(firefox_path, profile)
                if os.path.isdir(profile_path):
                    cookies_path = os.path.join(profile_path, "cookies.sqlite")
                    if os.path.exists(cookies_path):
                        cookie_paths.append({
                            "browser": "Firefox",
                            "path": cookies_path,
                            "profile": profile
                        })
    
    else:
        # Linux/Android路径
        # Chrome
        chrome_path = os.path.join(home_dir, ".config", "google-chrome")
        if os.path.exists(chrome_path):
            for root, dirs, files in os.walk(chrome_path):
                if "Cookies" in files:
                    cookie_paths.append({
                        "browser": "Chrome",
                        "path": os.path.join(root, "Cookies"),
                        "profile": os.path.basename(root)
                    })
        
        # Edge
        edge_path = os.path.join(home_dir, ".config", "microsoft-edge")
        if os.path.exists(edge_path):
            for root, dirs, files in os.walk(edge_path):
                if "Cookies" in files:
                    cookie_paths.append({
                        "browser": "Edge",
                        "path": os.path.join(root, "Cookies"),
                        "profile": os.path.basename(root)
                    })
        
        # Firefox
        firefox_path = os.path.join(home_dir, ".mozilla", "firefox")
        if os.path.exists(firefox_path):
            for profile in os.listdir(firefox_path):
                profile_path = os.path.join(firefox_path, profile)
                if os.path.isdir(profile_path) and profile.endswith(".default"):
                    cookies_path = os.path.join(profile_path, "cookies.sqlite")
                    if os.path.exists(cookies_path):
                        cookie_paths.append({
                            "browser": "Firefox",
                            "path": cookies_path,
                            "profile": profile
                        })
    
    return cookie_paths

def get_cookies_from_browser():
    """从浏览器Cookie文件中提取Bilibili的Cookie"""
    cookies = {}
    print("=" * 60)
    print("正在从浏览器提取Bilibili Cookie...")
    
    # 查找所有可能的Cookie文件
    cookie_files = find_browser_cookie_files()
    
    if not cookie_files:
        print("未找到浏览器Cookie文件")
        return None
    
    print(f"找到 {len(cookie_files)} 个可能的Cookie源")
    
    for cookie_file in cookie_files:
        browser = cookie_file["browser"]
        path = cookie_file["path"]
        profile = cookie_file["profile"]
        
        print(f"\n尝试从 {browser} ({profile}) 获取Cookie...")
        
        try:
            # 创建临时副本以避免锁定问题
            temp_db = "temp_cookies.db"
            shutil.copy(path, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            # 查询Bilibili的Cookie
            if browser == "Firefox":
                # Firefox查询
                cursor.execute("""
                    SELECT name, value, host, path, expiry, isSecure, isHttpOnly 
                    FROM moz_cookies 
                    WHERE host LIKE '%bilibili.com'
                """)
            else:
                # Chrome/Edge查询
                cursor.execute("""
                    SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly 
                    FROM cookies 
                    WHERE host_key LIKE '%bilibili.com'
                """)
            
            found_cookies = False
            for row in cursor.fetchall():
                if browser == "Firefox":
                    name, value, domain, path, expires, secure, http_only = row
                else:
                    name, value, domain, path, expires, secure, http_only = row
                
                if name == 'SESSDATA':
                    cookies['SESSDATA'] = value
                    found_cookies = True
                elif name == 'bili_jct':
                    cookies['bili_jct'] = value
                    found_cookies = True
                
                print(f"找到Cookie: {name}={value[:20]}... (来自 {domain})")
            
            conn.close()
            os.remove(temp_db)
            
            if found_cookies:
                print(f"成功从 {browser} ({profile}) 获取Cookie")
                return cookies
                
        except Exception as e:
            print(f"读取Cookie失败: {str(e)}")
            traceback.print_exc()
    
    print("未能从任何浏览器获取有效的Cookie")
    return None

def get_play_url(url, cookies=None):
    try:
        print("请求视频页面...")
        r = requests.get(url, headers=header, cookies=cookies, timeout=15)
        r.raise_for_status()
        
        # 检查是否被重定向到登录页面
        if "bilibili.com/login" in r.url:
            print("需要登录才能观看此视频！")
            return None, None, "需要登录的视频"
        
        # 增强的匹配方法 - 处理不同页面结构
        match = re.search(r'window\.__playinfo__\s*=\s*({.*?})</script>', r.text, re.DOTALL)
        if match:
            print("成功提取到 __playinfo__")
            info = match.group(1)
            data = json.loads(info)
            
            # 检查是否有DASH格式
            if "data" in data and "dash" in data["data"]:
                video_url = data["data"]["dash"]["video"][0]["baseUrl"]
                audio_url = data["data"]["dash"]["audio"][0]["baseUrl"]
                print("成功获取DASH格式的播放地址")
            else:
                print("未找到DASH格式，尝试备用格式...")
                # 尝试获取FLV格式
                if "data" in data and "durl" in data["data"]:
                    video_url = data["data"]["durl"][0]["url"]
                    audio_url = None  # FLV格式包含音频
                    print("成功获取FLV格式播放地址")
                else:
                    print("无法识别播放格式")
                    return None, None, "未知标题"
        else:
            print("未找到 __playinfo__，尝试备用方法...")
            # 尝试从INITIAL_STATE中提取
            data_match = re.search(r'<script>window\.__INITIAL_STATE__=({.*?});</script>', r.text)
            if data_match:
                initial_state = json.loads(data_match.group(1))
                print("从INITIAL_STATE中提取到数据")
                
                # 提取视频基本信息
                video_data = initial_state.get("videoData", {})
                if not video_data:
                    # 尝试从其他位置获取
                    video_data = initial_state.get("ogv", {}).get("videoInfo", {})
                
                # 获取标题
                filename = video_data.get("title", "未知标题")
                
                # 获取CID
                cid = video_data.get("cid")
                if not cid:
                    # 尝试从页面中提取CID
                    cid_match = re.search(r'"cid":(\d+)', r.text)
                    if cid_match:
                        cid = cid_match.group(1)
                
                if cid:
                    print(f"获取到CID: {cid}")
                    # 使用API获取播放地址
                    bvid = url.split('/')[-1].split('?')[0]
                    api_url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={bvid}&qn=80&type=&otype=json&fnver=0&fnval=4048"
                    
                    # 添加Cookie到API请求
                    api_headers = header.copy()
                    if cookies:
                        api_headers["cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                    
                    api_r = requests.get(api_url, headers=api_headers, timeout=10)
                    api_data = api_r.json()
                    
                    if api_data.get("code") == 0:
                        # 尝试获取DASH格式
                        if "dash" in api_data["data"]:
                            video_url = api_data["data"]["dash"]["video"][0]["baseUrl"]
                            audio_url = api_data["data"]["dash"]["audio"][0]["baseUrl"]
                            print("通过API成功获取DASH格式播放地址")
                        # 尝试获取FLV格式
                        elif "durl" in api_data["data"]:
                            video_url = api_data["data"]["durl"][0]["url"]
                            audio_url = None
                            print("通过API成功获取FLV格式播放地址")
                        else:
                            print("API返回未知格式")
                            return None, None, filename
                    else:
                        print(f"API请求失败: {api_data.get('message')}")
                        return None, None, filename
                else:
                    print("无法获取CID")
                    return None, None, "未知标题"
            else:
                print("页面中未找到视频信息")
                return None, None, "未知标题"
        
        # 提取标题（使用正则表达式替代lxml）
        if 'filename' not in locals():
            # 方法1：从<title>标签提取
            title_match = re.search(r'<title>([^<]+)</title>', r.text)
            if title_match:
                filename = title_match.group(1).split('_哔哩哔哩')[0].strip()
            else:
                # 方法2：从h1标签提取
                title_match = re.search(r'<h1[^>]*?title="([^"]+)"', r.text)
                if title_match:
                    filename = unquote(title_match.group(1)).strip()
                else:
                    # 方法3：从JSON数据提取
                    title_match = re.search(r'"title":"([^"]+)"', r.text)
                    if title_match:
                        filename = title_match.group(1).replace('\\', '')
                    else:
                        filename = "未知标题"
        
        # 清理文件名中的非法字符
        filename = re.sub(r'[\\/:*?"<>|]', '', filename)
        # HTML实体解码
        filename = html.unescape(filename)
        print(f"视频标题: {filename}")
        
        return video_url, audio_url, filename
        
    except Exception as e:
        print(f"获取播放信息失败: {str(e)}")
        traceback.print_exc()
        return None, None, "未知标题"

def download_file(url, file_path, file_type="文件", cookies=None):
    """下载文件并显示进度"""
    try:
        print(f"开始下载{file_type}: {os.path.basename(file_path)}")
        
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if not create_directory(dir_path):
            return False
        
        # 重试机制
        max_retries = 3
        retry_delay = 5  # 秒
        
        for attempt in range(max_retries):
            try:
                # 如果文件已存在，继续下载
                downloaded_size = 0
                if os.path.exists(file_path):
                    downloaded_size = os.path.getsize(file_path)
                
                headers = header.copy()
                if downloaded_size > 0:
                    headers["Range"] = f"bytes={downloaded_size}-"
                
                with requests.get(url, headers=headers, cookies=cookies, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    
                    # 处理部分内容响应
                    mode = 'ab' if downloaded_size > 0 else 'wb'
                    total_size = downloaded_size + int(r.headers.get('content-length', 0))
                    
                    with open(file_path, mode) as f:
                        if total_size == 0:
                            print(f"无法获取{file_type}大小，直接下载...")
                            f.write(r.content)
                        else:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    progress = int(50 * downloaded_size / total_size)
                                    print(f"\r[{'=' * progress}{' ' * (50 - progress)}] {int(100 * downloaded_size / total_size)}%", end='')
                
                print(f"\n{file_type}下载完成: {file_path}")
                return True
                
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    print(f"下载中断 ({str(e)}), {max_retries - attempt - 1}次重试中...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise
        
    except Exception as e:
        print(f"下载{file_type}失败: {str(e)}")
        traceback.print_exc()
        return False

def merge_video_audio(video_path, audio_path, output_path):
    """使用ffmpeg合并视频和音频"""
    try:
        # 检查ffmpeg是否可用
        if not shutil.which('ffmpeg'):
            print("未找到ffmpeg，无法合并视频和音频")
            return False
            
        print("开始合并视频和音频...")
        
        command = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        # 在Termux中，ffmpeg需要显式指定日志级别
        if 'com.termux' in os.environ.get('PREFIX', ''):
            command.insert(1, '-loglevel')
            command.insert(2, 'warning')
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"合并成功: {output_path}")
            return True
        else:
            print(f"合并失败，错误信息:\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"合并过程中出错: {str(e)}")
        return False

def clear_screen():
    """清空控制台屏幕"""
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Linux/Mac/Android
        os.system('clear')

def print_banner():
    """打印程序横幅"""
    clear_screen()
    print("=" * 60)
    print("Bilibili视频下载器".center(60))
    print("仅使用标准库实现".center(60))
    print("=" * 60)
    print("功能:")
    print("- 自动从浏览器文件提取Bilibili登录Cookie")
    print("- 支持Chrome, Edge, Firefox等主流浏览器")
    print("- 自动合并高清视频，支持断点续传")
    print("=" * 60)

def main():
    try:
        # 确定保存路径 (Android 11+ 需要特殊处理)
        if os.path.exists("/storage/emulated/0"):
            base_path = "/storage/emulated/0/BilibiliDownloads"
        else:
            base_path = os.path.join(os.getcwd(), "BilibiliDownloads")
        
        output_path = os.path.join(base_path, "output")
        
        # 创建目录
        if not create_directory(base_path):
            print("无法创建基础目录，程序终止")
            return
            
        if not create_directory(output_path):
            print("无法创建输出目录，程序终止")
            return
        
        # 打印横幅
        print_banner()
        
        # 获取用户输入的BV号
        bv_id = input("请输入Bilibili视频的BV号: ").strip()
        if not bv_id.startswith("BV"):
            print("无效的BV号格式")
            return
        
        url = f'https://www.bilibili.com/video/{bv_id}/'
        
        # 自动获取Cookie
        cookies = get_cookies_from_browser()
        
        if not cookies or 'SESSDATA' not in cookies or 'bili_jct' not in cookies:
            print("\n⚠️ 警告: 未能自动获取有效的Cookie")
            print("可能原因:")
            print("1. 您尚未在浏览器中登录Bilibili")
            print("2. 浏览器Cookie文件位置不标准")
            print("3. 程序没有权限访问浏览器Cookie文件")
            
            manual_cookie = input("\n是否手动输入Cookie? (y/n): ").lower()
            if manual_cookie == 'y':
                print("\n请从浏览器复制Cookie字符串 (包含SESSDATA和bili_jct):")
                print("获取方法: 登录B站后按F12→应用→Cookie→复制全部Cookie字符串")
                cookie_str = input("\n粘贴Cookie字符串: ").strip()
                
                # 从字符串中提取Cookie
                sessdata_match = re.search(r'SESSDATA=([0-9a-fA-F%]+)', cookie_str)
                jct_match = re.search(r'bili_jct=([0-9a-fA-F]+)', cookie_str)
                
                if sessdata_match and jct_match:
                    cookies = {
                        'SESSDATA': sessdata_match.group(1),
                        'bili_jct': jct_match.group(1)
                    }
                    print("成功提取Cookie信息")
                else:
                    print("未找到有效的Cookie，将尝试无Cookie下载")
                    cookies = None
            else:
                print("将尝试无Cookie下载")
                cookies = None
        else:
            print("\n✅ 成功获取Cookie信息")
        
        print("=" * 50)
        print(f"开始处理视频: {url}")
        video_url, audio_url, filename = get_play_url(url, cookies)
        
        if not video_url:
            print("无法获取视频播放地址，程序终止")
            return
        
        print(f"视频标题: {filename}")
        
        # 创建临时文件目录
        temp_path = os.path.join(base_path, "temp")
        if not create_directory(temp_path):
            print("无法创建临时目录，程序终止")
            return
        
        # 设置文件路径
        if audio_url:
            video_ext = ".m4s"
            audio_ext = ".m4a"
        else:
            video_ext = ".flv"
            audio_ext = ""
            
        video_file = os.path.join(temp_path, f"{filename}_video{video_ext}")
        output_file = os.path.join(output_path, f"{filename}.mp4")
        
        # 下载视频
        if not download_file(video_url, video_file, "视频", cookies):
            print("视频下载失败，程序终止")
            return
        
        # 下载音频（如果需要）
        if audio_url:
            audio_file = os.path.join(temp_path, f"{filename}_audio{audio_ext}")
            if not download_file(audio_url, audio_file, "音频", cookies):
                print("音频下载失败，程序终止")
                return
            
            # 合并视频和音频
            if merge_video_audio(video_file, audio_file, output_file):
                # 删除临时文件
                try:
                    os.remove(video_file)
                    os.remove(audio_file)
                    print('已删除临时文件')
                except:
                    print('删除临时文件失败，但合并已完成')
            else:
                print("合并失败，保留临时文件以供手动处理")
                print(f"视频文件: {video_file}")
                print(f"音频文件: {audio_file}")
        else:
            # FLV格式不需要合并，直接移动文件
            try:
                os.rename(video_file, output_file)
                print(f"视频已保存: {output_file}")
            except Exception as e:
                print(f"移动文件失败: {str(e)}")
                print(f"视频文件保留在: {video_file}")
        
        print("=" * 50)
        print("下载完成!")
        print(f"最终视频已保存到: {output_file}")
        
    except Exception as e:
        print(f"主程序出错: {str(e)}")
        traceback.print_exc()
    finally:
        input("\n按Enter键退出...")

if __name__ == '__main__':
    main()