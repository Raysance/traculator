import os
import json
import uuid
from datetime import datetime
import random
import string
from fastapi import FastAPI, HTTPException, Request, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import redis
from typing import List, Optional

app = FastAPI(title="Traculator", openapi_url="/traculator/api/openapi.json", docs_url="/traculator/api/docs")

# 挂载静态文件
app.mount("/traculator/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")

# 获取 Redis 实例
redis_path = str(os.environ.get('REDIS_CONF', 'redis_conf.json'))
try:
    with open(redis_path, 'r', encoding='utf-8') as file:
        varia = json.load(file)
        queue = redis.Redis(
            host=varia.get('REDIS_HOST', '127.0.0.1'), 
            port=varia.get('REDIS_PORT', 6379), 
            db=varia.get('REDIS_TRACULATOR_QUEUE', 8),
            decode_responses=True
        )
except Exception as e:
    # 回退机制，或者直接在加载时抛出
    queue = redis.Redis(host='127.0.0.1', port=6379, db=8, decode_responses=True)

# ----------------- Models -----------------

class RecordCreate(BaseModel):
    details: str
    payer: str
    price: float
    repayers: List[str]
    location: Optional[str] = None

class UserLogin(BaseModel):
    code: str

# ----------------- Helpers -----------------

def get_group_data(code: str):
    data = queue.hget(f"traculator:group:{code}", "data")
    if data:
        return json.loads(data)
    return {"members": [], "records": [], "middleman": ""}

def save_group_data(code: str, data: dict):
    queue.hset(f"traculator:group:{code}", "data", json.dumps(data))

def calculate_settlement(data: dict):
    # 采用类似 main.py 的逻辑
    direct_payset = {}
    records = data.get("records", [])
    members = data.get("members", [])
    middleman = data.get("middleman", "")

    for record in records:
        details, payer, price, repayers = record["details"], record["payer"], record["price"], record["repayers"]
        AA_divisor = len(repayers)
        if AA_divisor == 0: continue
        
        for repayer in repayers:
            if repayer == payer: continue
            direct_paytuple = f"{repayer}->{payer}"
            if direct_paytuple in direct_payset:
                direct_payset[direct_paytuple] += price / AA_divisor
            else:
                direct_payset[direct_paytuple] = price / AA_divisor

    final_payset = {}
    def add_final(person, amount):
        if person in final_payset:
            final_payset[person] += amount
        else:
            final_payset[person] = amount

    # 中转计算 (如果存在 middleman)
    if middleman and middleman in members:
        for k, v in direct_payset.items():
            repayer, payer = k.split("->")
            if middleman in [repayer, payer]:
                if middleman == repayer:
                    add_final(payer, v)
                if middleman == payer:
                    add_final(repayer, -v)
            else:
                add_final(repayer, -v)
                add_final(payer, v)
    else:
        # 如果没有指定 middleman，直接输出账单 (可简化处理)
        return {"direct": direct_payset, "final": {}}

    return {"direct": direct_payset, "final": final_payset}

# ----------------- APIs -----------------

@app.post("/traculator/api/login")
def login(login_data: UserLogin):
    code = login_data.code
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=400, detail="数字码必须为6位数字")
    
    is_new = False
    if not queue.exists(f"traculator:group:{code}"):
        # 创建新的
        save_group_data(code, {"members": [], "records": [], "middleman": ""})
        is_new = True
    
    msg = "注册成功！这是您的全新账本。" if is_new else "登录成功"
    response = JSONResponse(content={"message": msg, "code": code, "is_new": is_new})
    response.set_cookie(key="traculator_code", value=code)
    return response

@app.get("/traculator/api/data")
def get_data(traculator_code: Optional[str] = Cookie(None)):
    if not traculator_code:
        raise HTTPException(status_code=401, detail="请先登录")
    data = get_group_data(traculator_code)
    settlement = calculate_settlement(data)
    return {"data": data, "settlement": settlement}

@app.post("/traculator/api/members")
def add_member(member: dict, traculator_code: Optional[str] = Cookie(None)):
    if not traculator_code:
        raise HTTPException(status_code=401, detail="请先登录")
    
    name = member.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="名字不能为空")
        
    data = get_group_data(traculator_code)
    if name not in data["members"]:
        data["members"].append(name)
        if not data["middleman"]:
            data["middleman"] = name # 默认第一个人为中间人
        save_group_data(traculator_code, data)
    return {"message": "添加成功"}

@app.put("/traculator/api/middleman")
def set_middleman(member: dict, traculator_code: Optional[str] = Cookie(None)):
    if not traculator_code:
        raise HTTPException(status_code=401, detail="请先登录")
        
    name = member.get("name")
    data = get_group_data(traculator_code)
    if name in data["members"]:
        data["middleman"] = name
        save_group_data(traculator_code, data)
        return {"message": "设置成功"}
    raise HTTPException(status_code=400, detail="非有效成员")

@app.post("/traculator/api/records")
def add_record(record: RecordCreate, traculator_code: Optional[str] = Cookie(None)):
    if not traculator_code:
        raise HTTPException(status_code=401, detail="请先登录")
        
    data = get_group_data(traculator_code)
    data["records"].append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": record.details,
        "payer": record.payer,
        "price": record.price,
        "repayers": record.repayers,
        "location": record.location
    })
    save_group_data(traculator_code, data)
    return {"message": "添加成功"}

@app.put("/traculator/api/records/{record_id}")
def update_record(record_id: str, record: RecordCreate, traculator_code: Optional[str] = Cookie(None)):
    if not traculator_code:
        raise HTTPException(status_code=401, detail="请先登录")
        
    data = get_group_data(traculator_code)
    for r in data["records"]:
        if r.get("id") == record_id:
            r["details"] = record.details
            r["payer"] = record.payer
            r["price"] = record.price
            r["repayers"] = record.repayers
            if getattr(record, "location", None) is not None:
                r["location"] = record.location
            save_group_data(traculator_code, data)
            return {"message": "修改成功"}
    
    raise HTTPException(status_code=404, detail="未找到账单")

@app.delete("/traculator/api/group")
def delete_group(traculator_code: Optional[str] = Cookie(None)):
    if not traculator_code:
        raise HTTPException(status_code=401, detail="请先登录")
        
    queue.delete(f"traculator:group:{traculator_code}")
    response = JSONResponse(content={"message": "账本已删除"})
    response.delete_cookie(key="traculator_code")
    return response

# ----------------- Pages -----------------

@app.get("/traculator/", response_class=HTMLResponse)
@app.get("/traculator", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)