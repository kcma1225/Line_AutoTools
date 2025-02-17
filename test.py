import os
import time
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class LineAutoLogin:
    def __init__(self):
        """初始化 WebDriver 及 設定"""
        load_dotenv()  # 載入 .env 檔案

        self.config = {
            "extension_url": "chrome-extension://ophjlpahpchlmihnnnihgmmeilfjmjjc/index.html#/",
            "friends_url": "chrome-extension://ophjlpahpchlmihnnnihgmmeilfjmjjc/index.html#/friends",
            "chrome_extension_path": "line.crx",
            "login": {
                "email": os.environ.get("EMAIL"),  # 從 .env 讀取
                "password": os.environ.get("PASSWORD")  # 從 .env 讀取
            },
            "selectors": {
                "email_input": (By.NAME, "email"),
                "password_input": (By.NAME, "password"),
                "pincode_modal": (By.CLASS_NAME, "pinCodeModal-module__modal__DHXh8"),
                "pincode": (By.CLASS_NAME, "pinCodeModal-module__pincode__bFKMn")
            }
        }

        # 設定 Chrome WebDriver
        self.service = Service(ChromeDriverManager().install())
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--start-maximized")
        self.options.add_extension(self.config["chrome_extension_path"])
        self.options.add_experimental_option("detach", True)  # 防止 WebDriver 自動關閉
        
        # 設定 Network Logging (修正 `desired_capabilities` 錯誤)
        self.options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # 啟動 WebDriver
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def open_browser(self):
        """開啟 Line 擴充功能頁面"""
        self.driver.get(self.config["extension_url"])

    def login(self):
        """執行登入流程"""
        try:
            # 輸入 Email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.config["selectors"]["email_input"])
            )
            email_input.send_keys(self.config["login"]["email"])

            # 輸入密碼
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.config["selectors"]["password_input"])
            )
            password_input.send_keys(self.config["login"]["password"])
            password_input.send_keys(Keys.RETURN)

            print("✅ 登入請求發送，等待彈出驗證碼...")

        except Exception as e:
            print(f"⚠️ 登入失敗: {e}")

    def handle_pincode_popup(self):
        """偵測並處理 PIN 碼驗證視窗"""
        try:
            # 等待最多 100 秒來確認 PIN 碼彈窗出現
            WebDriverWait(self.driver, 100).until(
                EC.presence_of_element_located(self.config["selectors"]["pincode_modal"])
            )
            
            # 獲取 PIN 碼
            pincode_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.config["selectors"]["pincode"])
            )
            pincode = pincode_element.text.strip()

            print(f"🔢 你的驗證碼為: {pincode}")
            print("📱 請在手機上輸入此驗證碼，等待系統自動檢測跳轉...")

        except Exception as e:
            print(f"⚠️ 無法偵測到驗證碼彈窗: {e}")

    def wait_for_redirect(self):
        """自動偵測頁面是否跳轉到好友列表"""
        max_wait_time = 100  # 最大等待時間 (秒)
        check_interval = 2    # 每 2 秒檢測一次
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            current_url = self.driver.current_url
            if current_url == self.config["friends_url"]:
                print("🎉 登入成功，已進入好友列表頁面！")
                return
            time.sleep(check_interval)
            elapsed_time += check_interval
            print(f"⏳ 等待頁面跳轉中... ({elapsed_time}s)")

        print("❌ 等待超時，未成功登入。")

    def capture_target_network_request(self):
        """搜尋直到找到 `getAllContactIds` 封包，擷取指定的 header"""
        print("\n🔍 [Network Sniffer] 等待 `getAllContactIds` 封包...")
        
        while True:
            logs = self.driver.get_log("performance")
            _privacyData = dict.fromkeys(['x_line_chrome_version', 'x_line_access', 'cookie'])
            for entry in logs:
            
                try:
                    message = json.loads(entry.get("message", "{}"))
                    params = message.get("message", {}).get("params", {})
                    request = params.get("request", {})

                    # 取得 URL
                    url = request.get("url", "")

                    # 如果找到 `getAllContactIds` 封包
                    # if "getAllContactIds" in url:
                    headers = request.get("headers", {})
                    
                    # 取得指定 headers
                    x_line_chrome_version = headers.get("X-Line-Chrome-Version")
                    x_line_access = headers.get("X-Line-Access")
                    cookie = params.get("headers" , {}).get("cookie",{})

                    if x_line_chrome_version and _privacyData.get('x_line_chrome_version') == None:
                        _privacyData['x_line_chrome_version'] = x_line_chrome_version
                    
                    if x_line_access and _privacyData.get('x_line_access') == None:
                        _privacyData['x_line_access'] = x_line_access
                        
                    if cookie and _privacyData.get('cookie') == None:
                        _privacyData['cookie'] = cookie

                    isAllDataGet = all(_privacyData.values())
                    if isAllDataGet:
                        print(_privacyData)
                        return _privacyData

                except json.JSONDecodeError:
                    continue  # 忽略解析錯誤的封包

            time.sleep(2)  # 每 2 秒檢測一次，減少資源消耗
            
    def close_browser(self):
        """關閉瀏覽器"""
        self.driver.quit()  


# ================== 測試執行 ==================
if __name__ == '__main__':
    bot = LineAutoLogin()
    bot.open_browser()
    bot.login()
    bot.handle_pincode_popup()
    bot.wait_for_redirect()
    
    # 搜尋 `getAllContactIds` 封包，擷取指定的 header
    bot.capture_target_network_request()

    # 註解掉關閉瀏覽器，讓開發者手動查看
    # bot.close_browser()
