from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uuid

app = FastAPI()

# Разрешаем CORS для всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилища
clients = {}   # client_id -> {"ip": ip, "port": port}
messages = []  # list of {"from": str, "to": str, "text": str, "type": "text"|"video"}
groups = {}    # group_name -> set(client_id)

# Папка для хранения видеофайлов
os.makedirs("videos", exist_ok=True)

# ===== Регистрация клиента =====
@app.post("/register")
async def register(request: Request):
    data = await request.json()
    client_id = data.get("id")
    ip = data.get("ip")
    port = data.get("port")

    if not client_id or not ip or port is None:
        return {"status": "error", "message": "Некорректные данные"}

    clients[client_id] = {"ip": ip, "port": port}
    print(f"✅ Зарегистрирован клиент: {client_id}")
    return {"status": "ok"}

# ===== Получение списка клиентов =====
@app.get("/clients")
async def get_clients():
    return {"clients": list(clients.keys())}

# ===== Создание группы =====
@app.post("/group/create")
async def create_group(request: Request):
    data = await request.json()
    group_name = data.get("name")
    members = set(data.get("members", []))

    if not group_name or not members:
        return {"status": "error", "message": "Некорректные данные"}

    groups[group_name] = members
    print(f"✅ Создана группа {group_name} с участниками {members}")
    return {"status": "ok"}

# ===== Отправка текстового сообщения =====
@app.post("/send")
async def send_message(request: Request):
    data = await request.json()
    sender = data.get("from")
    text = data.get("text")
    target = data.get("to")

    if not sender or not target or not text:
        return {"status": "error", "message": "Некорректные данные"}

    message = {"from": sender, "to": target, "text": text, "type": "text"}
    messages.append(message)
    print(f"💬 {sender} -> {target}: {text}")
    return {"status": "ok"}

# ===== Отправка видео =====
@app.post("/send_video")
async def send_video(
    from_id: str = Form(...),
    to: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join("videos", filename)

        with open(path, "wb") as f:
            f.write(await file.read())

        video_url = f"/video/{filename}"

        messages.append({
            "from": from_id,
            "to": to,
            "text": video_url,
            "type": "video"
        })

        print(f"🎥 Видео {file.filename} от {from_id} -> {to}")
        return {"status": "ok", "video_url": video_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ===== Получение видео =====
@app.get("/video/{filename}")
async def get_video(filename: str):
    path = os.path.join("videos", filename)
    if not os.path.exists(path):
        return {"error": "Видео не найдено"}
    return FileResponse(path)

# ===== Получение сообщений =====
@app.get("/messages/{client_id}")
async def get_messages(client_id: str):
    relevant = []
    for msg in messages:
        if msg["to"] == "all" or msg["to"] == client_id:
            relevant.append(msg)
        elif msg["to"] in groups and client_id in groups[msg["to"]]:
            relevant.append(msg)
    return {"messages": relevant}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
