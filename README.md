# 遗忘之海 · 交易行行情站 使用手册

## 一、项目结构

```
补偿/
├── index.html                 # 前端页面（读取 JSON，不要直接改）
├── prices.json                # 今日行情数据（自动生成）
├── history.json               # 历史价格数据（自动生成，用于折线图）
├── README.md                  # 本手册
├── data/
│   └── market.db              # SQLite 数据库（自动生成）
├── scripts/
│   └── update_data.py         # 唯一需要手动运行的脚本
└── hyperframes/               # 商品图片文件夹
    ├── 金砖.svg               # 货币符号图标
    ├── 织梦星空·星河入梦.png
    ├── “鱼骨串”的断章.png
    └── ... 其他商品图片
```

---

## 二、核心文件说明

### 1. 数据更新脚本

**位置：** `scripts/update_data.py`

这是唯一需要手动编辑和运行的文件，负责：
- 读取你填写的今日行情数据
- 自动扫描 `hyperframes/` 文件夹里的商品图片并匹配
- 把数据写入 `data/market.db`（SQLite 数据库）
- 生成 `prices.json` 和 `history.json` 供网页读取

### 2. 今日行情数据

**位置：** `scripts/update_data.py` 里的 `TODAYS_DATA` 列表

每天只需要改这个地方：

```python
TODAYS_DATA = [
    {"name": "织梦星空·星河入梦", "price": 212500, "stock": 3},
    {"name": "翼声轻羽", "price": None, "stock": 0},  # None 表示缺货
    # ... 其他商品
]
```

规则：
- `name`：商品完整名称，必须和图片文件名对应
- `price`：整数价格；写 `None` 表示缺货
- `stock`：库存数量
- 断章类商品名称保持 `"xxx"的断章` 格式，双引号用英文 `"`

### 3. 快照日期

**位置：** `scripts/update_data.py` 里的 `SNAPSHOT_DATE`

```python
SNAPSHOT_DATE = "2026-07-21"  # 改成你要发布数据的日期
```

---

## 三、每日更新流程

### 步骤 1：准备数据

打开 `scripts/update_data.py`，修改：
1. `SNAPSHOT_DATE` 为今天的日期
2. `TODAYS_DATA` 里的价格、库存

### 步骤 2：运行脚本

在 CMD 或 PowerShell 里执行：

```cmd
cd /d "e:\笔记仓库\new\遗忘之海\补偿"
python scripts/update_data.py
```

脚本会自动：
- 扫描 `hyperframes/` 下所有图片
- 把新数据写入数据库
- 更新 `prices.json` 和 `history.json`

### 步骤 3：查看网页

启动本地服务器（必须，不能双击打开）：

```cmd
cd /d "e:\笔记仓库\new\遗忘之海\补偿"
python -m http.server 8123
```

浏览器访问：

```
http://localhost:8123/index.html
```

---

## 四、补充商品图片

### 图片放哪里

所有图片放在 `hyperframes/` 文件夹里。

### 图片命名规则

**文件名必须和商品名一致**（扩展名 `.png`、`.jpg`、`.jpeg`、`.webp` 都可以）。

| 商品名 | 正确文件名 | 错误文件名 |
|--------|-----------|-----------|
| 织梦星空·星河入梦 | `织梦星空·星河入梦.png` | `星河入梦.png` |
| "鱼骨串"的断章 | `“鱼骨串”的断章.png` 或 `鱼骨串的断章.png` | `鱼骨串.png` |
| 翼声轻羽 | `翼声轻羽.png` | `飘落轻羽.png` |

### 自动匹配规则

脚本会忽略以下差异：
- 中英文引号（`"` 和 `“”`）
- 文件名里多写的"的"（例如 `“安眠人偶”的的断章.png` 会匹配 `"安眠人偶"的断章`）
- 空格
- 大小写

### 补图后操作

1. 把新图片放进 `hyperframes/`
2. 重新运行 `python scripts/update_data.py`
3. 刷新网页即可

---

## 五、分类规则

脚本按商品名自动分类：

| 分类 | 匹配规则 |
|------|---------|
| 外观 | 名称包含 `织梦星空` 或 `妄想羽翼` |
| 断章 | 名称包含 `断章` |
| 材料 | 其他 |

如需修改分类规则，编辑 `scripts/update_data.py` 里的 `classify()` 函数。

---

## 六、常见问题

### Q1：网页空白，表格没数据？

你可能是双击 `index.html` 用 `file://` 协议打开的。`fetch()` 在本地文件协议下会被浏览器拦截。

**解决：** 用本地服务器打开：

```cmd
cd /d "e:\笔记仓库\new\遗忘之海\补偿"
python -m http.server 8123
```
然后访问 `http://localhost:8123/index.html`。

### Q2：某个商品没有显示图片？

1. 检查 `hyperframes/` 下是否有对应图片
2. 检查文件名和商品名是否一致
3. 运行脚本时看输出是否显示 `[OK] 扫描到 x 张图片`
4. 打开 `prices.json` 搜索该商品，看 `image` 字段是否为 `null`

### Q3：折线图为什么是一条平线？

目前只有 2026-07-21 一天的数据。`history.json` 需要多天记录才能画出涨跌折线。

**解决：** 每天坚持运行 `update_data.py`，填入当日价格。数据库会自动累积历史数据。

### Q4：商品价格显示错误？

检查 `TODAYS_DATA` 中该商品的 `price` 和 `stock` 是否写对。价格填 `None` 会在网页显示"缺货"。

### Q5：最高/最低单价统计不对？

统计只统计有货商品（`price` 不为 `None`）。如果最低价看起来异常，检查是否有商品误填了低价。

---

## 七、数据表结构（供参考）

数据库文件：`data/market.db`

### items 表
| 字段 | 说明 |
|------|------|
| id | 商品 ID |
| name | 商品名称 |
| category | 分类 |
| image_file | 图片文件名 |
| created_at | 创建时间 |

### daily_prices 表
| 字段 | 说明 |
|------|------|
| id | 记录 ID |
| item_id | 关联商品 ID |
| price | 价格（NULL 表示缺货） |
| stock | 库存 |
| snapshot_date | 快照日期 |
| created_at | 写入时间 |

---

## 八、小技巧

- 可以用 SQLite 浏览器工具（如 [DB Browser for SQLite](https://sqlitebrowser.org/)）直接查看 `data/market.db`
- `prices.json` 和 `history.json` 是给人读的，也可以用脚本二次处理
- 想恢复初始状态：直接删除 `data/market.db`，然后重新运行 `update_data.py`
