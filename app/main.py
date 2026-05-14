from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.database import db
from app.routers import clients, horses, stables, admins, dashboard, auth, ai, owners, chatbot, yolo, vlm
import os
import asyncio
import shutil

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(title='HCS Backend', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(clients.router)
app.include_router(horses.router)
app.include_router(stables.router)
app.include_router(admins.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(owners.router)
app.include_router(chatbot.router)
app.include_router(yolo.router)
app.include_router(vlm.router)

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
admin_dir = os.path.join(base_path, 'admin')
user_dir = os.path.join(base_path, 'user')

if os.path.exists(admin_dir):
    if os.path.exists(os.path.join(admin_dir, 'css')):
        app.mount('/admin/css', StaticFiles(directory=os.path.join(admin_dir, 'css')), name='admin_css')
    if os.path.exists(os.path.join(admin_dir, 'js')):
        app.mount('/admin/js', StaticFiles(directory=os.path.join(admin_dir, 'js')), name='admin_js')
    if os.path.exists(os.path.join(admin_dir, 'components')):
        app.mount('/admin/components', StaticFiles(directory=os.path.join(admin_dir, 'components')), name='admin_components')
    if os.path.exists(os.path.join(admin_dir, 'assets')):
        app.mount('/admin/assets', StaticFiles(directory=os.path.join(admin_dir, 'assets')), name='admin_assets')
    if os.path.exists(os.path.join(admin_dir, 'pages')):
        app.mount('/admin/pages', StaticFiles(directory=os.path.join(admin_dir, 'pages')), name='admin_pages')

    @app.get('/admin')
    @app.get('/admin/')
    async def admin_root():
        return FileResponse(os.path.join(admin_dir, 'pages', 'dashboard.html'))

    @app.get('/admin/{page}')
    async def serve_admin_page(page: str):
        if page.endswith('.html'):
            page = page[:-5]
        html_path = os.path.join(admin_dir, 'pages', f'{page}.html')
        if os.path.exists(html_path):
            return FileResponse(html_path)
        return {'error': 'Page not found'}

if os.path.exists(user_dir):
    if os.path.exists(os.path.join(user_dir, 'js')):
        app.mount('/user/js', StaticFiles(directory=os.path.join(user_dir, 'js')), name='user_js')
    if os.path.exists(os.path.join(user_dir, 'assets')):
        app.mount('/user/assets', StaticFiles(directory=os.path.join(user_dir, 'assets')), name='user_assets')

    @app.get('/user')
    @app.get('/user/')
    async def user_root():
        return FileResponse(os.path.join(user_dir, 'stables.html'))

    @app.get('/user/login')
    async def user_login_page():
        return FileResponse(os.path.join(user_dir, 'login.html'))

    @app.get('/user/stables')
    async def user_stables_page():
        return FileResponse(os.path.join(user_dir, 'stables.html'))

    @app.get('/user/dashboard')
    async def user_dashboard_page():
        return FileResponse(os.path.join(user_dir, 'dashboard.html'))

    @app.get('/user/horse-view')
    async def user_horse_view_page():
        return FileResponse(os.path.join(user_dir, 'horse-view.html'))

@app.websocket("/ws/stream")
async def rtsp_websocket(websocket: WebSocket, url: str = ""):
    await websocket.accept()
    if not url:
        await websocket.close(code=1008)
        return

    ffmpeg_path = shutil.which("ffmpeg") or r"C:\Users\ahmed\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"
    process = await asyncio.create_subprocess_exec(
        ffmpeg_path,
        "-rtsp_transport", "tcp",
        "-i", url,
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-q:v", "8",
        "-r", "15",
        "-an",
        "pipe:1",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    buffer = b""
    try:
        while True:
            chunk = await process.stdout.read(65536)
            if not chunk:
                break
            buffer += chunk
            while True:
                soi = buffer.find(b'\xff\xd8')
                if soi == -1:
                    break
                eoi = buffer.find(b'\xff\xd9', soi)
                if eoi == -1:
                    break
                frame = buffer[soi:eoi + 2]
                await websocket.send_bytes(frame)
                buffer = buffer[eoi + 2:]
            if len(buffer) > 2 * 1024 * 1024:
                buffer = buffer[-1024 * 1024:]
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        try:
            process.kill()
        except Exception:
            pass


@app.get('/')
async def serve_index():
    index_path = os.path.join(admin_dir, 'pages', 'landing-page.html')
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {'message': 'Welcome to HCS API'}
