from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import APIRouter, Form, BackgroundTasks
from app.services.selenium_service import LineAutoLogin
from app.services.webdriver_manager import get_webdriver
from datetime import datetime, timedelta
import sqlite3, json, time


router = APIRouter()
bot = None  

# 初始化排程器
scheduler = BackgroundScheduler()
scheduler_running = False  # **確保排程器不會重複啟動**

# ---------------------------- schedule-message
@router.on_event("shutdown")
async def shutdown_event():
    """FastAPI 關閉時，關閉 Scheduler"""
    global scheduler_running
    if scheduler_running:
        scheduler.shutdown()
        scheduler_running = False
        print("🛑 Scheduler 已關閉")
    else:
        print("⚠️ Scheduler 未運行，跳過關閉")

# **啟動 Scheduler（確保不會重複啟動）**
def start_scheduler():
    """啟動 Scheduler，確保不會重複啟動"""
    global scheduler_running
    if not scheduler_running:
        scheduler.add_job(check_and_send_messages, "interval", seconds=30)  # **每 60 秒執行一次**
        scheduler.start()
        scheduler_running = True
        print("✅ Scheduler 啟動成功")
    else:
        print("⚠️ Scheduler 已在運行，跳過啟動")
        
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
            name TEXT,
            msg TEXT,
            timestamp TEXT,
            status INTEGER DEFAULT 1,   -- 新增狀態 1: 成功, 0: 失敗
            error_msg TEXT DEFAULT NULL -- 失敗時記錄錯誤訊息
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
    """檢查是否登入"""
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
        
        # **確保 Scheduler 啟動**
        start_scheduler()
        
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
    """根據資料庫的設定，定期發送訊息"""
    global bot
    conn = sqlite3.connect("LineDB.db")
    cursor = conn.cursor()

    # **取得當前時間（時:分）**
    current_time_str = datetime.datetime.now().strftime("%H:%M")
    current_weekday = datetime.datetime.now().weekday() + 1  # **星期一=1，星期日=7**

    # **取得所有 `status=1`，且 `time` 符合當前時間的訊息**
    cursor.execute(
        "SELECT id, name, msg, week, time, status, execTimes, last_exec_time FROM target WHERE status = 1 AND time = ?",
        (current_time_str,)
    )
    messages_to_send = cursor.fetchall()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not messages_to_send:
        print(f" ✅  {now} 沒有符合條件的訊息")
        conn.close()
        return

    # **確保 `bot` 已登入**
    if bot is None or not bot.logged_in:
        print("⚠️ Bot 未登入，無法發送訊息")
        conn.close()
        return

    for msg in messages_to_send:
        msg_id, name_json, message_json, week_json, time_str, status, exec_times, last_exec_time = msg

        # **解析 JSON**
        try:
            name_list = json.loads(name_json)
            msg_list = json.loads(message_json)
            week_list = json.loads(week_json)
        except json.JSONDecodeError:
            print(f"❌ 訊息 ID {msg_id} JSON 解析失敗，跳過")
            continue

        # **檢查是否符合當前星期**
        if current_weekday not in week_list:
            continue  # 當前星期不在指定 `week`，跳過

        # **確保不會重複發送**
        if last_exec_time:
            last_exec_date = datetime.datetime.strptime(last_exec_time, "%Y-%m-%d")
            if datetime.datetime.now().date() == last_exec_date.date():
                print(f"⏩ [跳過] 訊息 ID {msg_id} 今天已發送過")
                continue  # **避免同一天重複發送**

        # **發送訊息**
        print(f"📩 發送訊息給 {name_list}: {msg_list}")
        send_status = 1  # **預設為成功**
        error_msg = None

        try:
            bot.send_message_via_selenium(name_list, msg_list)  # **執行 Selenium 發送**
        except Exception as e:
            print(f"❌ 訊息 ID {msg_id} 發送失敗: {e}")
            send_status = 0  # **失敗**
            error_msg = str(e)

        # **更新 `execTimes` 和 `last_exec_time`**
        cursor.execute(
            "UPDATE target SET execTimes = execTimes + 1, last_exec_time = ? WHERE id = ?",
            (datetime.datetime.now().strftime("%Y-%m-%d"), msg_id)
        )

    conn.commit()
    conn.close()

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

@router.post("/save-history")
async def save_history_api(
    name: str = Form(...),  # 單獨的 name
    msg_list: str = Form(...),   # 這裡 msg_list 會是 JSON 字串
    timestamp: str = Form(...),  # 訊息時間
    status: int = Form(...),  # 1: 成功, 0: 失敗
    error_msg: str = Form(None)  # 預設為 NULL，失敗時才會有錯誤訊息
):
    """儲存發送訊息的歷史記錄（允許 `selenium_service.py` 呼叫）"""
    try:
        conn = sqlite3.connect("LineDB.db")
        cursor = conn.cursor()

        # **確保 msg_list 是 JSON**
        try:
            msg_list_json = json.loads(msg_list)  # 解析 JSON
            if not isinstance(msg_list_json, list):
                raise ValueError("msg_list 應為 list")
        except (json.JSONDecodeError, ValueError):
            return {"success": False, "error": "msg_list 必須是 JSON 格式的 list"}

        # **存入 history**
        cursor.execute(
            """
            INSERT INTO history (name, msg, timestamp, status, error_msg) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, json.dumps(msg_list_json, ensure_ascii=False), timestamp, status, error_msg)
        )

        conn.commit()
        conn.close()
        return {"success": True, "message": "歷史記錄已成功儲存"}

    except Exception as e:
        return {"success": False, "error": str(e)}





"""
@router.post("/send-test-messages")
async def send_test_messages():
   #忽略時間與日期，直接發送所有 `status=1` 的訊息
    global bot

    if bot is None or not bot.logged_in:
        return {"success": False, "error": "請先登入後再發送訊息"}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 取得所有 `status=1` 的訊息
        cursor.execute("SELECT id, name, msg FROM target WHERE status = 1")
        messages_to_send = cursor.fetchall()
        
        if not messages_to_send:
            return {"success": False, "message": "沒有可發送的訊息"}

        for msg in messages_to_send:
            msg_id, name_json, message_json = msg
            
            # 解析 JSON
            try:
                name_list = json.loads(name_json)
                msg_list = json.loads(message_json)
            except json.JSONDecodeError:
                print(f"⚠️ 訊息 ID {msg_id} JSON 解析失敗，跳過")
                continue
            
            # 呼叫 Selenium 發送訊息
            bot.send_message_via_selenium(name_list, msg_list)

        conn.close()
        return {"success": True, "message": "已成功發送所有訊息"}

    except Exception as e:
        return {"success": False, "error": str(e)}
"""