from fastapi import APIRouter, Form
from app.services.selenium_service import LineAutoLogin
from app.services.webdriver_manager import get_webdriver
import sqlite3, json


router = APIRouter()
bot = None  

# ---------------------------- database Create    
def get_db_connection():
    conn = sqlite3.connect("LineDB.db")
    conn.text_factory = str  # 設置資料庫使用 UTF-8 編碼
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS target (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            time TEXT,
            period INTEGER,
            msg TEXT,
            execTimes INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    return conn
# ----------------------------
@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...)
):
    global bot
    driver = get_webdriver()
    if driver is None:
        return {"success": False, "error": "WebDriver 尚未啟動"}

    bot = LineAutoLogin(driver, email, password)
    success = bot.login()
    return {"success": success}

@router.get("/check-pincode")
async def check_pincode():
    """檢測 PIN 碼，若 5 秒內未出現則回傳登入失敗"""
    global bot
    if bot:
        return bot.get_pincode()
    return {"pincode": None, "logged_in": False, "login_failed": True}

@router.get("/check-login")
async def check_login():
    """檢測是否成功登入，若進入 /friends 則回傳 True，結束檢測"""
    global bot
    if bot:
        return bot.check_login_status()
    return {"logged_in": False, "login_failed": True}

@router.get("/check-webdriver-url")
async def check_webdriver_url():
    """檢測 WebDriver 當前 URL，判斷是否已登入"""
    global bot
    if bot and bot.driver:
        current_url = bot.driver.current_url
        if any(keyword in current_url for keyword in ["friends", "chats", "addFriend"]):
            return {"logged_in": True}
    return {"logged_in": False}

@router.post("/search-target")
async def search_target(target_name: str = Form(...)):
    """透過 Selenium 搜尋好友或群組，回傳名稱與頭像 URL"""
    global bot
    if bot is None:
        return {"success": False, "error": "請先登入後再搜尋"}
    
    search_results = bot.search_target(target_name)
    return {"success": True, "data": search_results}

@router.post("/save-formdata")
async def save_form_data(
    recipients: str = Form(...),  # JSON 格式的字串
    time: str = Form(...),
    frequency: int = Form(...),
    messages: str = Form(...),  # JSON 格式的字串
):
    try:
        recipients_list = json.loads(recipients)  # 解析 JSON 字串為 Python List
        messages_list = json.loads(messages)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO target (name, time, period, msg) VALUES (?, ?, ?, ?)",
            (json.dumps(recipients_list, ensure_ascii=False), time, frequency, json.dumps(messages_list, ensure_ascii=False))
        )
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "資料已成功存入 SQLite"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    

@router.get("/get-scheduled-messages")
async def get_scheduled_messages():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, time, period, msg FROM target")
        rows = cursor.fetchall()
        conn.close()
        
        scheduled_messages = [
            {
                "id": row[0],
                "name": json.loads(row[1]),
                "time": row[2],
                "period": row[3],
                "msg": json.loads(row[4])
            } for row in rows
        ]
        
        return {"success": True, "data": scheduled_messages}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    
@router.post("/delete-scheduled-message")
async def delete_scheduled_message(id: int = Form(...)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM target WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return {"success": True, "message": "定時傳訊已刪除"}
    except Exception as e:
        return {"success": False, "error": str(e)}