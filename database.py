import json
import os
import uuid  # 新增：用于给每笔账单生成唯一身份证(ID)

DATA_DIR = os.environ.get("FLET_APP_STORAGE_DATA_DIR", os.getcwd())
DB_FILE = os.path.join(DATA_DIR, "budget_data.json")

def init_db():
    """初始化本地数据文件"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        
    if not os.path.exists(DB_FILE):
        default_data = {
            "balance": 0.0,
            "budget": 0.0,      #  本月总额度
            "budget_month": "", #  记录额度所属月份（如 "2026-07"）
            "records": []
        }
        save_data(default_data)

def get_data():
    """获取所有数据（含自动迁移逻辑）"""
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 自动兼容：如果历史账单没有唯一 ID，在此处自动补充生成
    updated = False
    for r in data.get("records", []):
        if "id" not in r:
            r["id"] = str(uuid.uuid4())
            updated = True
    if updated:
        save_data(data)
        
    return data

def save_data(data):
    """保存数据"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def set_budget(amount, month_str):
    """设置某个月的预算额度"""
    data = get_data()
    data["budget"] = float(amount)
    data["budget_month"] = month_str
    save_data(data)

def add_record(record_type, category, amount, remark, date_str):
    """新增一笔账单记录"""
    data = get_data()
    amount = float(amount)
    
    if record_type == "收入":
        data["balance"] += amount
    else:
        data["balance"] -= amount
        
    data["records"].insert(0, {
        "id": str(uuid.uuid4()),  # 核心改动：新增时带上唯一 ID
        "date": date_str,
        "type": record_type,
        "category": category,
        "amount": amount,
        "remark": remark
    })
    save_data(data)

def delete_record(record_id):
    """根据 ID 删除一笔账单记录"""
    data = get_data()
    target_idx = -1
    for idx, r in enumerate(data.get("records", [])):
        if r.get("id") == record_id:
            target_idx = idx
            break
            
    if target_idx != -1:
        r = data["records"][target_idx]
        amount = r["amount"]
        # 撤销对余额 balance 的影响
        if r["type"] == "收入":
            data["balance"] -= amount
        else:
            data["balance"] += amount
        
        # 从列表中移除
        data["records"].pop(target_idx)
        save_data(data)

def update_record(record_id, record_type, category, amount, remark):
    """根据 ID 修改一笔账单记录"""
    data = get_data()
    target_idx = -1
    for idx, r in enumerate(data.get("records", [])):
        if r.get("id") == record_id:
            target_idx = idx
            break
            
    if target_idx != -1:
        r = data["records"][target_idx]
        old_amount = r["amount"]
        old_type = r["type"]
        
        # 1. 先撤销旧账单对余额的影响
        if old_type == "收入":
            data["balance"] -= old_amount
        else:
            data["balance"] += old_amount
            
        # 2. 应用新修改后的余额影响
        amount = float(amount)
        if record_type == "收入":
            data["balance"] += amount
        else:
            data["balance"] -= amount
            
        # 3. 覆盖写入新内容 (日期维持原账单日期不变)
        r["type"] = record_type
        r["category"] = category
        r["amount"] = amount
        r["remark"] = remark
        save_data(data)