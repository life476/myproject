from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

# 配置Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# 设置下载目录
download_dir = os.path.abspath("mt2_downloads")
os.makedirs(download_dir, exist_ok=True)

# 配置Chrome下载选项
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

# 启动浏览器
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://mt2.cn/download/")

# 等待页面加载
time.sleep(5)

# 这里需要根据实际页面结构定位下载按钮
# 示例：假设下载按钮是一个带有特定class的a标签
try:
    download_buttons = driver.find_elements_by_css_selector("a.download-btn")  # 替换为实际选择器
    for btn in download_buttons:
        btn.click()
        time.sleep(2)  # 等待下载开始
except Exception as e:
    print(f"查找下载按钮时出错: {e}")

# 等待所有下载完成
time.sleep(10)  # 根据文件大小调整等待时间
driver.quit()