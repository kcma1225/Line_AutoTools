import tkinter as tk
from tkinter import messagebox
import json
import os

# 設定 JSON 檔案路徑
json_path = "config.json"

# 預設 JSON 結構
default_data = {
    "email": "",
    "password": ""
}

def load_config():
    """讀取 JSON 檔案，若無則建立"""
    if not os.path.exists(json_path):
        with open(json_path, "w") as f:
            json.dump(default_data, f, indent=4)
    
    with open(json_path, "r") as f:
        return json.load(f)

def save_config(email, password):
    """更新 JSON 檔案"""
    data = {
        "email": email,
        "password": password
    }
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

class ConfigUI:
    def __init__(self, root):
        self.root = root
        self.root.title("帳號設定")
        self.root.geometry("350x250")
        self.root.resizable(False, False)  # 禁止放大視窗

        # **讀取 JSON 配置**
        self.config = load_config()

        # **標題**
        self.label_title = tk.Label(root, text="帳號設定", font=("Arial", 16))
        self.label_title.pack(pady=10)

        # **帳號輸入**
        self.label_email = tk.Label(root, text="帳號 (Email):")
        self.label_email.pack()
        self.entry_email = tk.Entry(root, width=30)
        self.entry_email.insert(0, self.config["email"])  # 預先載入帳號
        self.entry_email.pack()

        # **密碼輸入**
        self.label_password = tk.Label(root, text="密碼 (Password):")
        self.label_password.pack()
        self.entry_password = tk.Entry(root, width=30)
        self.entry_password.insert(0, self.config["password"])  # 預先載入密碼
        self.entry_password.pack()

        # **確定/修改按鈕**
        self.button_submit = tk.Button(root, text="確定/修改", command=self.update_config)
        self.button_submit.pack(pady=10)

    def update_config(self):
        """更新 JSON 檔案"""
        email = self.entry_email.get().strip()
        password = self.entry_password.get().strip()

        if not email or not password:
            messagebox.showwarning("錯誤", "帳號與密碼不能為空！")
            return

        # **更新 JSON 檔案**
        save_config(email, password)
        messagebox.showinfo("成功", "帳號與密碼已更新！")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigUI(root)
    root.mainloop()
