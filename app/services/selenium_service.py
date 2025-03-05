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
        """清除輸入框並立即填入新的 email 和 password"""
        try:
            self.driver.refresh()
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
            print(f"登入操作失敗: {e}")
            return False

    def get_pincode(self):
        """檢測 PIN 碼，若 5 秒內未出現則視為登入失敗"""
        try:
            pincode_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pinCodeModal-module__pincode__bFKMn"))
            )
            self.pincode = pincode_element.text.strip()
            print(f"🔑 驗證碼: {self.pincode}")
            return {"pincode": self.pincode, "logged_in": False, "login_failed": False}
        except:
            print("❌ 5 秒內未偵測到 PIN 碼，登入失敗")
            self.login_failed = True
            return {"pincode": None, "logged_in": False, "login_failed": True}

    def check_login_status(self):
        """檢測是否成功登入，若進入 /friends 則回傳 True"""
        for _ in range(30):
            if self.driver.current_url.endswith("/friends"):
                self.logged_in = True
                return {"logged_in": True, "login_failed": False}
            time.sleep(2)
        return {"logged_in": False, "login_failed": True}

    def search_target(self, target_name):
        """搜尋好友或群組名稱，回傳名稱、URL 及對應的圖片 URL"""
        search_results = {"groups": [], "friends": []}
        try:
            # 定位搜尋框並輸入 target_name
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "searchInput-module__input__ekGp7"))
            )
            search_box.clear()
            search_box.send_keys(target_name)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)  # 等待結果顯示
            
            # 判斷是否沒有任何搜尋結果
            error_message = self.driver.find_elements(By.CLASS_NAME, "errorMessage-module__message_area__Hyidf")
            if error_message:
                return search_results  # 空結果回傳

            # 定位好友與群組列表
            friend_list_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "friendlist-module__inner__d3xFH"))
            )
            items = friend_list_section.find_elements(By.CLASS_NAME, "friendlistItem-module__item__1tuZn")
            
            for item in items:
                item_id = item.get_attribute("data-mid")
                img_element = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                name_element = item.find_element(By.CLASS_NAME, "friendlistItem-module__text__YxSko").text.strip()
                
                # 檢查是否為群組 (是否包含成員數量的 class)
                if len(item.find_elements(By.CLASS_NAME, "friendlistItem-module__member_count__Eh52G")) > 0:
                    search_results["groups"].append({
                        "g_name": name_element,
                        "g_url": item_id,
                        "g_thumbnail": img_element
                    })
                else:
                    search_results["friends"].append({
                        "f_name": name_element,
                        "f_url": item_id,
                        "f_thumbnail": img_element
                    })
            
        except Exception as e:
            print(f"搜尋失敗: {e}")
        
        return search_results
    
    
    def send_message_via_selenium(self, name_list, msg_list):
        """使用 Selenium 操控 LINE Web 介面發送訊息"""
        for name in name_list:
            try:
                # 定位搜尋框並輸入目標名稱
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "searchInput-module__input__ekGp7"))
                )
                search_box.clear()
                search_box.send_keys(name)
                time.sleep(2)  # 等待搜尋結果

                # 判斷是否有搜尋結果
                error_message = self.driver.find_elements(By.CLASS_NAME, "errorMessage-module__message_area__Hyidf")
                if error_message:
                    print(f"❌ 找不到 {name}，跳過...")
                    continue

                # 定位好友列表並點擊第一個結果
                friend_list_section = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "friendlist-module__inner__d3xFH"))
                )
                items = friend_list_section.find_elements(By.CLASS_NAME, "friendlistItem-module__item__1tuZn")
                if not items:
                    print(f"⚠️ 未找到 {name} 的好友條目，跳過...")
                    continue
                items[0].find_element(By.CLASS_NAME, "friendlistItem-module__button_friendlist_item__xoWur").click()

                time.sleep(2)  # 等待頁面加載

                # 判斷是否有聊天按鈕（第一種情況）
                chat_button = self.driver.find_elements(By.CLASS_NAME, "startChat-module__button_start__FjvEK")
                if chat_button:
                    chat_button[0].click()
                    time.sleep(2)  # 等待輸入框顯示

                # 定位輸入框
                input_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "chatroomEditor-module__textarea__yKTlH"))
                )

                # 依次輸入訊息並發送
                for message in msg_list:
                    input_box.send_keys(message)
                    input_box.send_keys(Keys.RETURN)
                    time.sleep(1)

                print(f"✅ 訊息已成功發送給 {name}")
            except Exception as e:
                print(f"❌ 無法發送訊息給 {name}，錯誤: {e}")
                continue