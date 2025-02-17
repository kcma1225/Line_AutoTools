from fastapi import APIRouter, Form
from app.services.selenium_service import LineAutoLogin
from app.services.webdriver_manager import global_driver  # ✅ 從 WebDriver 管理模組引入 WebDriver

router = APIRouter()
bot = None  # 存放登入執行中的 Selenium 物件

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    global bot
    if not global_driver:
        return {"success": False, "error": "WebDriver 尚未啟動"}

    bot = LineAutoLogin(global_driver, email, password)
    success = bot.login()
    return {"success": success}

@router.get("/check-status")
async def check_status():
    global bot
    if bot:
        return bot.check_pincode_and_status()
    return {"logged_in": False, "pincode": None}
