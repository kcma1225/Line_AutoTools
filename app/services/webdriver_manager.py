from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# **全域 WebDriver 變數**
global_driver = None

def initialize_webdriver():
    """初始化 WebDriver，確保只執行一次"""
    global global_driver
    if global_driver is None:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_extension("line.crx")  # 重要：載入擴充功能
        options.add_experimental_option("detach", True)

        global_driver = webdriver.Chrome(service=service, options=options)
        global_driver.get("chrome-extension://ophjlpahpchlmihnnnihgmmeilfjmjjc/index.html#/")
        print("✅ WebDriver 已啟動")

def shutdown_webdriver():
    """關閉 WebDriver"""
    global global_driver
    if global_driver:
        global_driver.quit()
        print("🛑 WebDriver 已關閉")
