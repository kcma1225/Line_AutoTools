# LINE 自動化登入與操作

本專案使用 **FastAPI + Selenium + Celery + HTML/JS/Tailwind CSS**，模擬操作 **LINE** 登入、驗證碼輸入，並可進行自動訊息發送。

---

## **📌 專案架構**
- **後端**：FastAPI（API）
- **自動化**：Selenium（模擬瀏覽器操作）
- **定時任務**：Celery（訊息發送）
- **前端**：HTML + JS + Tailwind CSS（登入 UI）

---

## **📌 安裝與啟動**
### **1️⃣ 安裝依賴**
```bash
pip install -r requirements.txt
```

### **2️⃣ 啟動 FastAPI 及 WebDriver**
```bash
uvicorn app.main:app --reload
```

### **3️⃣ 開啟瀏覽器，訪問**
```bash
http://127.0.0.1:8000/
```

📌 重要注意事項
WebDriver 在 FastAPI 啟動時初始化，避免重複開啟瀏覽器
驗證碼會自動顯示於前端，並監測登入狀態
若啟動失敗，請確保 `line.crx` 已導入，且是最新版本(目前3.6.1)
```
4 -- Line自動傳訊息
├─ app
│  ├─ line.crx
│  ├─ main.py
│  ├─ routers
│  │  ├─ auth.py
│  │  ├─ automation.py
│  │  └─ __init__.py
│  ├─ services
│  │  ├─ line.crx
│  │  ├─ selenium_service.py
│  │  ├─ task_scheduler.py
│  │  └─ webdriver_manager.py
│  └─ templates
│     ├─ dashboard.html
│     └─ index.html
├─ line.crx
├─ README.md
├─ requirements.txt
├─ static
└─ test.py

```