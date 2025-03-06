from fastapi import APIRouter, Form, BackgroundTasks
from app.services.selenium_service import LineAutoLogin
from app.services.webdriver_manager import get_webdriver
from datetime import datetime, timedelta
import sqlite3, json, time


router = APIRouter()
bot = None  

# ---------------------------- database Create    
def get_db_connection():
    """初始化 SQLite 資料庫，確保表格存在"""
    conn = sqlite3.connect("LineDB.db")
    conn.text_factory = str  # 設置 UTF-8
    cursor = conn.cursor()

    # **更新 target 表結構**
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS target (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            time TEXT,
            week TEXT,
            msg TEXT,
            status INTEGER DEFAULT 1,
            execTimes INTEGER DEFAULT 0,
            last_exec_time TEXT DEFAULT NULL
        )
    ''')

    # **新增 history 表**
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER,
            name TEXT,
            time TEXT,
            msg TEXT,
            exec_time TEXT,
            FOREIGN KEY (target_id) REFERENCES target(id)
        )
    ''')

    conn.commit()
    return conn
#-----------
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
    recipients: str = Form(...),
    time: str = Form(...),
    week: str = Form(...),  # **week 以 JSON 字串存入**
    messages: str = Form(...),
):
    try:
        recipients_list = json.loads(recipients)  # 解析 JSON
        messages_list = json.loads(messages)
        week_list = json.loads(week)  # 解析 `week`

        if not isinstance(week_list, list) or not all(isinstance(i, int) and 1 <= i <= 7 for i in week_list):
            return {"success": False, "error": "week 參數須為 1-7 之間的整數陣列"}

        conn = get_db_connection()
        cursor = conn.cursor()

        # **存入資料庫**
        cursor.execute(
            "INSERT INTO target (name, time, week, msg) VALUES (?, ?, ?, ?)",
            (json.dumps(recipients_list, ensure_ascii=False), time, json.dumps(week_list), json.dumps(messages_list, ensure_ascii=False))
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
        cursor.execute("SELECT id, name, time, week, msg, status, execTimes, last_exec_time FROM target")
        rows = cursor.fetchall()
        conn.close()
        
        scheduled_messages = [
            {
                "id": row[0],
                "name": json.loads(row[1]),
                "time": row[2],
                "week": json.loads(row[3]),
                "msg": json.loads(row[4]),
                "status": row[5],
                "execTimes": row[6],
                "last_exec_time": row[7]  
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
import datetime

def check_and_send_messages():
    """定期檢查資料庫，找出應該發送的訊息"""
    while True:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now()
        current_time_str = now.strftime("%H:%M")
        current_weekday = now.weekday() + 1  # **星期一=1，星期日=7**

        # **取得符合時間的訊息**
        cursor.execute(
            "SELECT id, name, msg, week, status, execTimes, last_exec_time FROM target WHERE time = ? AND status = 1",
            (current_time_str,)
        )

        messages_to_send = cursor.fetchall()

        for msg in messages_to_send:
            msg_id, name, message, week_json, status, exec_times, last_exec_time = msg

            # **解析 `week`**
            try:
                week_list = json.loads(week_json)
            except json.JSONDecodeError:
                print(f"⚠️ [錯誤] 訊息 ID {msg_id} 的 `week` 欄位 JSON 解析失敗，跳過")
                continue

            # **如果 week 為空且 status=1，則發送後關閉**
            if not week_list and status == 1:
                print(f"⚠️ [警告] 訊息 ID {msg_id} 沒有指定發送日期，發送後關閉")
                should_send = True
                auto_disable = True
            else:
                # **檢查當前星期是否在 `week_list` 中**
                should_send = current_weekday in week_list
                auto_disable = False

            # **確保不會重複發送**
            if should_send:
                if last_exec_time:
                    last_exec_date = datetime.datetime.strptime(last_exec_time, "%Y-%m-%d")
                    if now.date() == last_exec_date.date():
                        print(f"⏩ [跳過] 訊息 ID {msg_id} 今天已發送過")
                        continue  # **避免同一天重複發送**

                # **記錄發送時間到 `history`**
                cursor.execute(
                    "INSERT INTO history (target_id, name, time, msg, exec_time) VALUES (?, ?, ?, ?, ?)",
                    (msg_id, name, current_time_str, message, now.strftime("%Y-%m-%d %H:%M:%S"))
                )

                # **更新 `target` 表**
                cursor.execute(
                    "UPDATE target SET execTimes = execTimes + 1, last_exec_time = ? WHERE id = ?",
                    (now.strftime("%Y-%m-%d"), msg_id)
                )

                # **如果 `week` 為空，則自動關閉 `status=0`**
                if auto_disable:
                    cursor.execute(
                        "UPDATE target SET status = 0 WHERE id = ?",
                        (msg_id,)
                    )
                    print(f"🚫 [已關閉] 訊息 ID {msg_id} 執行後已自動停用")

        conn.commit()
        conn.close()
        time.sleep(20)  # **避免過度頻繁檢查**



@router.get("/get-scheduled-by-week")
async def get_scheduled_by_week(day: int):
    """取得特定星期的定時訊息"""
    if day < 0 or day > 6:
        return {"success": False, "error": "請提供 0-6 的星期索引 (0=週一, 6=週日)"}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, time, week, msg, status FROM target")
        rows = cursor.fetchall()
        conn.close()

        filtered_messages = [
            {
                "id": row[0],
                "name": json.loads(row[1]),
                "time": row[2],
                "week": json.loads(row[3]),
                "msg": json.loads(row[4]),
                "status": row[5]
            }
            for row in rows if day in json.loads(row[3])  # **篩選符合的星期**
        ]

        return {"success": True, "data": filtered_messages}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/schedule-message")
def schedule_message(background_tasks: BackgroundTasks):
    """啟動背景任務，監測資料庫並發送訊息"""
    background_tasks.add_task(check_and_send_messages)
    return {"message": "定時傳訊已啟動"}

