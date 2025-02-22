from fastapi import APIRouter, Form
from app.services.selenium_service import LineAutoLogin
from app.services.webdriver_manager import get_webdriver

router = APIRouter()
bot = None  

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
