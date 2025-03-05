from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from app.routers import auth
from app.services.webdriver_manager import initialize_webdriver, shutdown_webdriver
import asyncio

# 初始化 FastAPI
app = FastAPI()

# 設定靜態文件夾（JS & CSS）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 設定 Jinja2 模板（渲染 HTML）
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def startup_event():
    """FastAPI 啟動時，初始化 WebDriver"""
    initialize_webdriver()

@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI 關閉時，關閉 WebDriver"""
    shutdown_webdriver()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# **載入 `auth.py` API**
app.include_router(auth.router)
