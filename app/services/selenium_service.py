import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LineAutoLogin:
    def __init__(self, driver, email, password):
        self.driver = driver
        self.email = email
        self.password = password
        self.pincode = None
        self.logged_in = False
        self.login_failed = False  

    def login(self):
        try:
            self.driver.get("chrome-extension://ophjlpahpchlmihnnnihgmmeilfjmjjc/index.html#/")

            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.clear()
            email_input.send_keys(self.email)

            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.clear()
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)

            return True
        except Exception as e:
            print(f"登入失敗: {e}")
            self.login_failed = True
            return False

    def get_pincode(self):
        """檢測 PIN 碼，若有則回傳，登入成功後結束檢測"""
        for _ in range(30):  # 最多等待 60 秒
            try:
                if self.logged_in:
                    return {"pincode": None, "logged_in": True}

                pincode_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "pinCodeModal-module__pincode__bFKMn"))
                )
                self.pincode = pincode_element.text.strip()
                print(f"🔑 驗證碼: {self.pincode}")
                return {"pincode": self.pincode, "logged_in": False}

            except:
                pass

            time.sleep(2)

        return {"pincode": None, "logged_in": self.logged_in}

    def check_login_status(self):
        """檢測是否成功登入，若進入 /friends 則回傳 True"""
        for _ in range(30):  # 最多等待 60 秒
            if self.driver.current_url.endswith("/friends"):
                self.logged_in = True
                return {"logged_in": True}
            time.sleep(2)

        return {"logged_in": False}
