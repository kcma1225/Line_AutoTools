from fastapi import APIRouter, Form, BackgroundTasks
from app.services.selenium_service import LineAutoLogin
from app.services.webdriver_manager import get_webdriver
from datetime import datetime, timedelta
import sqlite3, json, time


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
            status INTEGER DEFAULT 1,
            execTimes INTEGER DEFAULT 0,
            last_exec_time TEXT DEFAULT NULL
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
        cursor.execute("SELECT id, name, time, period, msg, status, execTimes, last_exec_time FROM target")
        rows = cursor.fetchall()
        conn.close()
        
        scheduled_messages = [
            {
                "id": row[0],
                "name": json.loads(row[1]),
                "time": row[2],
                "period": row[3],
                "msg": json.loads(row[4]),
                "status": row[5],
                "execTimes": row[6],
                "last_exec_time": row[7]  # 新增 last_exec_time 回傳
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
    
    
@router.post("/update-status")
async def update_status(id: int = Form(...), status: int = Form(...)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE target SET status = ? WHERE id = ?", (status, id))
        conn.commit()
        conn.close()
        return {"success": True, "message": "狀態已更新"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    

# ---------------------------- schedule-message


@router.post("/schedule-message")
def schedule_message(background_tasks: BackgroundTasks):
    """啟動背景任務，監測資料庫並發送訊息"""
    background_tasks.add_task(check_and_send_messages)
    return {"message": "定時傳訊已啟動"}


def check_and_send_messages():
    """定期檢查資料庫，找出應該發送的訊息"""
    while True:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        cursor.execute("SELECT id, name, msg, period, execTimes, last_exec_time FROM target WHERE time = ? AND status = 1", (current_time_str,))
        messages_to_send = cursor.fetchall()
        
        for msg in messages_to_send:
            msg_id, name, message, period, exec_times, last_exec_time = msg
            
            should_send = False
            if last_exec_time:
                last_exec_date = datetime.strptime(last_exec_time, "%Y-%m-%d")
                next_exec_date = last_exec_date + timedelta(days=period)
                if now.date() >= next_exec_date.date():
                    should_send = True
            else:
                should_send = True
            
            if should_send:
                #send_message_via_selenium(name, message)
                cursor.execute("UPDATE target SET execTimes = execTimes + 1, last_exec_time = ? WHERE id = ?", (now.strftime("%Y-%m-%d"), msg_id))
                if period == 0:
                    cursor.execute("UPDATE target SET status = 0 WHERE id = ?", (msg_id,))
        
        conn.commit()
        conn.close()
        
        time.sleep(20)  # 休眠 20 秒，避免過度頻繁檢查

@router.post("/schedule-message")
def schedule_message(background_tasks: BackgroundTasks):
    """啟動背景任務，監測資料庫並發送訊息"""
    background_tasks.add_task(check_and_send_messages)
    return {"message": "定時傳訊已啟動"}

