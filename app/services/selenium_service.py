import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LineAutoLogin:
    def __init__(self, driver, email, password):
        """初始化，直接使用已啟動的 WebDriver"""
        self.driver = driver
        self.email = email
        self.password = password
        self.pincode = None
        self.logged_in = False

    def login(self):
        """執行 LINE 登入"""
        try:
           

            # 輸入 Email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.clear()  # 清除舊輸入
            email_input.send_keys(self.email)

            # 輸入密碼
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.clear()  # 清除舊輸入
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)

            return True
        except Exception as e:
            print(f"登入失敗: {e}")
            return False

    def check_pincode_and_status(self):
        """持續監測是否有驗證碼 & 是否登入成功"""
        for _ in range(30):  # 最多檢測 30 次（60 秒）
            try:
                # 檢測驗證碼
                pincode_element = self.driver.find_element(By.CLASS_NAME, "pinCodeModal-module__pincode__bFKMn")
                self.pincode = pincode_element.text.strip()
                print(f"🔑 驗證碼: {self.pincode}")

                # 檢測登入狀態（是否跳轉到好友列表）
                if self.driver.current_url.endswith("/friends"):
                    self.logged_in = True
                    return {"logged_in": True, "pincode": self.pincode}

            except:
                pass

            time.sleep(2)  # 每 2 秒檢查一次

        return {"logged_in": self.logged_in, "pincode": self.pincode}
