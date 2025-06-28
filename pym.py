import requests

url = "https://magisk.suchenqaq.club/xposed_module/download?link=https://github.999222000.xyz/Xposed-Modules-Repo/com.fkzhang.wechatxposed/releases/download/110-2.43/WeXposed.x.110_2.43.apk&id=125"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # 检查请求是否成功
    print(response.text)  # 打印网页源代码
except requests.exceptions.RequestException as e:
    print(f"请求出错: {e}")
