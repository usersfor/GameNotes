#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
遗忘之海交易行数据更新脚本
流程：读取今日数据 → 写入 SQLite → 生成静态 JSON 供前端读取
用法：
    python scripts/update_data.py
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# ===================== 配置 =====================
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "market.db"
IMAGES_DIR = BASE_DIR / "hyperframes"
PRICES_JSON = BASE_DIR / "prices.json"
HISTORY_JSON = BASE_DIR / "history.json"
# 当前数据对应 7 月 23 日快照，后续可改为 datetime.now().strftime("%Y-%m-%d")
SNAPSHOT_DATE = "2026-07-23"


# ===================== 商品分类 =====================
def classify(name: str) -> str:
    """按商品名归类（用于价格走势分组）"""
    if "织梦星空" in name or "妄想羽翼" in name:
        return "外观"
    if "断章" in name:
        return "断章"
    return "材料"


# ===================== 今日行情数据 =====================
# 价格：None 表示缺货
# quality: red / gold / purple
TODAYS_DATA = [
    # 红色品质 —— 织梦星空
    {"name": "织梦星空·星河入梦", "price": 237500, "stock": 1, "quality": "red", "item_type": "外观"},
    {"name": "织梦星空·星海吟", "price": 171000, "stock": 3, "quality": "red", "item_type": "武器"},
    {"name": "织梦星空·拾星瓶", "price": 135000, "stock": 1, "quality": "red", "item_type": "饰品"},

    # 金色品质 —— 外观 / 武器 / 饰品 / 材料 / 道具 / 断章
    {"name": "妄想羽翼·夜染白翎", "price": 44000, "stock": 42, "quality": "gold", "item_type": "外观"},
    {"name": "妄想羽翼·碎光", "price": 31250, "stock": 39, "quality": "gold", "item_type": "武器"},
    {"name": "妄想羽翼·笼中玫瑰", "price": 25000, "stock": 42, "quality": "gold", "item_type": "饰品"},
    {"name": "飘落轻羽", "price": None, "stock": 0, "quality": "gold", "item_type": "武器"},
    {"name": "蔷薇石", "price": 9, "stock": 9999, "quality": "gold", "item_type": "材料"},
    {"name": "调律纺锤", "price": 10575, "stock": 35, "quality": "gold", "item_type": "道具"},
    {"name": "巡游涂料", "price": 1176, "stock": 9999, "quality": "gold", "item_type": "道具"},
    {"name": '"文明法则"的断章', "price": 4305, "stock": 69, "quality": "gold", "item_type": "断章"},
    {"name": '"狂想曲"的断章', "price": 3202, "stock": 75, "quality": "gold", "item_type": "断章"},
    {"name": '"致哀之花"的断章', "price": 5460, "stock": 49, "quality": "gold", "item_type": "断章"},
    {"name": '"他的战争"的断章', "price": 3044, "stock": 118, "quality": "gold", "item_type": "断章"},
    {"name": '"安眠人偶"的断章', "price": 6839, "stock": 84, "quality": "gold", "item_type": "断章"},
    {"name": '"遗落珠宝"的断章', "price": 3195, "stock": 63, "quality": "gold", "item_type": "断章"},
    {"name": '"缎带泪"的断章', "price": 3150, "stock": 88, "quality": "gold", "item_type": "断章"},
    {"name": '"鱼骨串"的断章', "price": 6720, "stock": 36, "quality": "gold", "item_type": "断章"},

    # 紫色品质 —— 武器 / 消耗品 / 饰品 / 材料 / 断章
    {"name": "蜘蛛之刃", "price": 2244, "stock": 320, "quality": "purple", "item_type": "武器"},
    {"name": "凌乱药剂瓶", "price": 2244, "stock": 31, "quality": "purple", "item_type": "消耗品"},
    {"name": "缝纫之刃", "price": 5253, "stock": 233, "quality": "purple", "item_type": "武器"},
    {"name": "蜘蛛之刃·轻痕", "price": 2244, "stock": 92, "quality": "purple", "item_type": "武器"},
    {"name": "蜘蛛之刃·重痕", "price": 2244, "stock": 331, "quality": "purple", "item_type": "武器"},
    {"name": "凌乱药剂瓶·轻痕", "price": 2244, "stock": 191, "quality": "purple", "item_type": "消耗品"},
    {"name": "凌乱药剂瓶·重痕", "price": 2346, "stock": 72, "quality": "purple", "item_type": "消耗品"},
    {"name": "缝纫之刃·轻痕", "price": 4284, "stock": 26, "quality": "purple", "item_type": "武器"},
    {"name": "缝纫之刃·重痕", "price": 6460, "stock": 3, "quality": "purple", "item_type": "武器"},
    {"name": "宝石和羽毛", "price": 1500, "stock": 207, "quality": "purple", "item_type": "材料"},
    {"name": "宝石和羽毛·轻痕", "price": 1500, "stock": 141, "quality": "purple", "item_type": "材料"},
    {"name": "宝石和羽毛·重痕", "price": 1597, "stock": 32, "quality": "purple", "item_type": "材料"},
    {"name": "编织水母", "price": 1552, "stock": 60, "quality": "purple", "item_type": "饰品"},
    {"name": "编织水母·轻痕", "price": 1653, "stock": 34, "quality": "purple", "item_type": "饰品"},
    {"name": "编织水母·重痕", "price": 2700, "stock": 5, "quality": "purple", "item_type": "饰品"},
    {"name": "别惹猫猫", "price": 1500, "stock": 163, "quality": "purple", "item_type": "饰品"},
    {"name": "别惹猫猫·轻痕", "price": 1500, "stock": 115, "quality": "purple", "item_type": "饰品"},
    {"name": "别惹猫猫·重痕", "price": 1500, "stock": 46, "quality": "purple", "item_type": "饰品"},
    {"name": "一袋悲叹珍珠", "price": 6625, "stock": 4, "quality": "purple", "item_type": "材料"},
    {"name": '"船长的礼物"的断章', "price": 502, "stock": 515, "quality": "purple", "item_type": "断章"},
    {"name": '"沉浮罗盘"的断章', "price": 507, "stock": 579, "quality": "purple", "item_type": "断章"},
    {"name": '"船之美"的断章', "price": 630, "stock": 414, "quality": "purple", "item_type": "断章"},
    {"name": '"白日梦"的断章', "price": 585, "stock": 391, "quality": "purple", "item_type": "断章"},
    {"name": '"昂首之旗"的断章', "price": 600, "stock": 414, "quality": "purple", "item_type": "断章"},
    {"name": '"老将"的断章', "price": 507, "stock": 529, "quality": "purple", "item_type": "断章"},
    {"name": '"鲇鱼号"的断章', "price": 517, "stock": 485, "quality": "purple", "item_type": "断章"},
    {"name": '"机械生命"的断章', "price": 502, "stock": 551, "quality": "purple", "item_type": "断章"},
    {"name": '"偏差之时"的断章', "price": 555, "stock": 407, "quality": "purple", "item_type": "断章"},
    {"name": '"离膛一瞬"的断章', "price": 500, "stock": 551, "quality": "purple", "item_type": "断章"},
    {"name": '"此刻即未来"的断章', "price": 510, "stock": 465, "quality": "purple", "item_type": "断章"},
    {"name": '"划掉一页"的断章', "price": 502, "stock": 460, "quality": "purple", "item_type": "断章"},
]


# ===================== 图片自动扫描 =====================
def normalize(text: str) -> str:
    '''统一处理中英文引号和多余的"的"'''
    return (
        text.replace("\u201c", "").replace("\u201d", "")
            .replace('"', "")
            .replace("的的", "的")
            .replace(" ", "")
            .lower()
    )


def scan_images() -> dict:
    """扫描 hyperframes 目录下的图片，建立商品名到文件名的映射"""
    mapping = {}
    if not IMAGES_DIR.exists():
        return mapping
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        for path in IMAGES_DIR.glob(ext):
            base = path.stem
            mapping[normalize(base)] = path.name
    return mapping


# ===================== 数据库操作 =====================
def init_db():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            item_type TEXT,
            quality TEXT,
            image_file TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            price INTEGER,
            stock INTEGER NOT NULL DEFAULT 0,
            snapshot_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id),
            UNIQUE(item_id, snapshot_date)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_prices_item_date
        ON daily_prices(item_id, snapshot_date)
    """)

    conn.commit()
    conn.close()


def update_database(image_map: dict):
    """把今日数据写入数据库"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now().isoformat()

    # 清空当日旧数据，避免已移除商品残留
    cur.execute("DELETE FROM daily_prices WHERE snapshot_date = ?", (SNAPSHOT_DATE,))

    for item in TODAYS_DATA:
        name = item["name"]
        category = classify(name)
        item_type = item.get("item_type")
        quality = item.get("quality", "purple")
        image_file = image_map.get(normalize(name))

        # 插入或更新商品
        cur.execute("""
            INSERT INTO items (name, category, item_type, quality, image_file, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                category = excluded.category,
                item_type = COALESCE(excluded.item_type, items.item_type),
                quality = COALESCE(excluded.quality, items.quality),
                image_file = COALESCE(excluded.image_file, items.image_file)
        """, (name, category, item_type, quality, image_file, now))

        # 获取 item_id
        cur.execute("SELECT id FROM items WHERE name = ?", (name,))
        item_id = cur.fetchone()[0]

        # 插入今日价格（缺货 price 为 NULL）
        cur.execute("""
            INSERT INTO daily_prices (item_id, price, stock, snapshot_date, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(item_id, snapshot_date) DO UPDATE SET
                price = excluded.price,
                stock = excluded.stock,
                created_at = excluded.created_at
        """, (item_id, item["price"], item["stock"], SNAPSHOT_DATE, now))

    conn.commit()
    conn.close()


# ===================== JSON 生成 =====================
def generate_json():
    """从数据库生成 prices.json 和 history.json"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 今日行情
    cur.execute("""
        SELECT i.id, i.name, i.category, i.item_type, i.quality, i.image_file,
               dp.price, dp.stock
        FROM items i
        JOIN daily_prices dp ON i.id = dp.item_id
        WHERE dp.snapshot_date = ?
        ORDER BY dp.price DESC NULLS LAST, dp.stock DESC
    """, (SNAPSHOT_DATE,))

    today_rows = cur.fetchall()
    prices_items = []
    for row in today_rows:
        prices_items.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "item_type": row["item_type"],
            "quality": row["quality"],
            "price": row["price"],
            "stock": row["stock"],
            "image": f"hyperframes/{row['image_file']}" if row["image_file"] else None
        })

    prices_meta = {
        "snapshot_date": SNAPSHOT_DATE,
        "total_items": len(prices_items),
        "out_of_stock": sum(1 for x in prices_items if x["price"] is None),
        "max_price": max((x["price"] for x in prices_items if x["price"] is not None), default=None),
        "min_price": min((x["price"] for x in prices_items if x["price"] is not None), default=None),
    }

    prices_json = {"meta": prices_meta, "items": prices_items}

    # 历史价格（用于折线图）
    cur.execute("""
        SELECT i.name, dp.snapshot_date, dp.price, dp.stock
        FROM daily_prices dp
        JOIN items i ON i.id = dp.item_id
        WHERE dp.price IS NOT NULL
        ORDER BY i.name, dp.snapshot_date
    """)

    history_rows = cur.fetchall()
    history = {}
    for row in history_rows:
        name = row["name"]
        if name not in history:
            history[name] = []
        history[name].append({
            "date": row["snapshot_date"],
            "price": row["price"],
            "stock": row["stock"]
        })

    history_json = {
        "meta": {"generated_at": SNAPSHOT_DATE},
        "history": history
    }

    conn.close()

    # 写入文件
    with open(PRICES_JSON, "w", encoding="utf-8") as f:
        json.dump(prices_json, f, ensure_ascii=False, indent=2)

    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(history_json, f, ensure_ascii=False, indent=2)

    return prices_meta


# ===================== 主流程 =====================
def main():
    print(f"[INFO] 快照日期: {SNAPSHOT_DATE}")
    print(f"[INFO] 数据库路径: {DB_PATH}")

    init_db()
    print("[OK] 数据库初始化完成")

    image_map = scan_images()
    print(f"[OK] 扫描到 {len(image_map)} 张图片")

    update_database(image_map)
    print("[OK] 数据库更新完成")

    meta = generate_json()
    print(f"[OK] 生成 {PRICES_JSON.name} 和 {HISTORY_JSON.name}")
    print(f"[INFO] 今日商品: {meta['total_items']} 件, 缺货: {meta['out_of_stock']} 件")
    if meta["max_price"]:
        print(f"[INFO] 最高价: {meta['max_price']}, 最低价: {meta['min_price']}")


if __name__ == "__main__":
    main()
