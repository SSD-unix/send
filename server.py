# server_groups.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Клиенты: client_id -> {"ip": ip, "port": port}
clients = {}

# Сообщения: list[{"from": client_id, "to": client_id/group_name, "text": str}]
messages = []

# Группы: group_name -> set(client_id)
groups = {}

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

# ===== Отправка сообщения =====
@app.post("/send")
async def send_message(request: Request):
    data = await request.json()
    sender = data.get("from")
    text = data.get("text")
    target = data.get("to")  # client_id, group_name или "all"
    
    message = {"from": sender, "to": target, "text": text}
    messages.append(message)
    print(f"📩 {sender} -> {target}: {text}")
    return {"status": "ok"}

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
