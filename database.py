import json
import os

DATA_DIR = os.environ.get("FLET_APP_STORAGE_DATA_DIR", os.getcwd())
DB_FILE = os.path.join(DATA_DIR, "budget_data.json")

def init_db():
    """初始化本地数据文件"""
    # 如果目录不存在（某些安卓系统特殊情况），先创建目录
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        
    if not os.path.exists(DB_FILE):
        default_data = {
            "balance": 0.0,
            "budget": 0.0,      #  新增：本月总额度
            "budget_month": "", #  新增：记录额度所属月份（如 "2026-07"）
            "records": []
        }
        save_data(default_data)

def get_data():
    """获取所有数据"""
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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
        "date": date_str,
        "type": record_type,
        "category": category,
        "amount": amount,
        "remark": remark
    })
    save_data(data)