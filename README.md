# 咖啡处理溯源与对账系统 MVP

让每一批豆子（Lot）从入厂称重到入库出库都有可审计的证据链，自动生成批次卡与对账摘要，并支持地块卡与红灯规则（对账不平衡、霉变等）。

---

## 关键概念（Concepts）

| 概念 | 说明 |
|------|------|
| **Plot（地块卡）** | 地块 ID、名称、主体、行政区划、可选 GIS 边界与权属信息。 |
| **Lot（批次卡）** | 批次主键，工艺类型（washed/natural/honey）、子工艺、状态、来源地块列表。 |
| **Event（事件）** | 按时间追加的操作/检测记录，是系统**唯一事实来源**；事件类型 + `data` JSON 由 Pydantic 校验。 |
| **Ledger（对账摘要）** | 从事件聚合计算出的入厂/入库/出库/留样与 `balance_kg`，以及红灯列表（如对账不平衡、霉变）。 |
| **Device** | 预留：未来传感器；读数以 `SENSOR_READING` 事件写入。 |

---

## 如何测试

后端启动后，在**项目根目录**执行：

```bash
python scripts/run_acceptance.py
```

脚本会自动完成：创建地块 → 创建批次并绑定地块 → 写入 RECEIVE_CHERRY、DRYING_CHECK、WAREHOUSE_IN、WAREHOUSE_OUT 四类事件 → 上传文件并绑定到事件 → 请求 `/lots/{id}/ledger` 并打印结果。若全部成功且对账为绿灯、`balance_kg=0`，即验收通过。更多步骤与手动 curl 见 [COMMANDS.md](COMMANDS.md)。

---

## 本地运行步骤

### 1. 环境要求

- Python 3.11+
- PostgreSQL 16（或使用 Docker 仅跑 DB）

### 2. 后端依赖与数据库

```bash
cd backend
pip install -r requirements.txt
```

配置数据库：设置环境变量 `DATABASE_URL`（默认：`postgresql+asyncpg://coffee:coffee_secret@localhost:5432/coffee_trace`）。  
若本地无 PostgreSQL，可仅启动数据库容器：

```bash
docker compose up -d postgres
# 再在 backend 目录执行迁移与启动
```

### 3. 执行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 4. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

---

## Docker 运行步骤（一键启动）

在项目根目录执行：

```bash
docker compose up --build
```

- 首次会构建后端镜像、启动 PostgreSQL 与 backend；backend 启动前会自动执行 `alembic upgrade head`。
- 后端：<http://localhost:8000>
- 文档：<http://localhost:8000/docs>

---

## 如何迁移数据库

- **生成新迁移**（修改 `app.models` 后）：  
  `cd backend && alembic revision --autogenerate -m "描述"`
- **应用迁移**：  
  `cd backend && alembic upgrade head`
- **回滚一步**：  
  `cd backend && alembic downgrade -1`

---

## 示例 curl（验收闭环）

以下按顺序执行可完成：创建地块 → 创建批次并绑定地块 → 写入四类事件 → 上传文件并绑定到事件 → 获取对账摘要（含红灯/绿灯与 balance_kg）。

**变量（按需替换）：**

```bash
BASE=http://localhost:8000
# 以下 ID 由前面响应中获取后填入
PLOT_ID=<创建地块返回的 plot_id>
LOT_ID=<创建批次返回的 lot_id>
EVENT_ID_1=<第一个事件的 event_id>
```

**1. 创建地块（plot）**

```bash
curl -s -X POST "$BASE/plots" \
  -H "Content-Type: application/json" \
  -d '{"plot_name":"北坡A区","entity_name":"张三种植户","admin_division":"云南省某某县"}'
```

**2. 创建批次（lot）并绑定地块**

```bash
curl -s -X POST "$BASE/lots" \
  -H "Content-Type: application/json" \
  -d "{\"lot_type\":\"washed\",\"received_at\":\"2025-02-02T08:00:00Z\",\"plot_ids\":[{\"plot_id\":\"$PLOT_ID\"}]}"
```

**3. 写入四类事件**

RECEIVE_CHERRY：

```bash
curl -s -X POST "$BASE/events" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\":\"RECEIVE_CHERRY\",\"lot_id\":\"$LOT_ID\",\"event_time\":\"2025-02-02T09:00:00Z\",\"data\":{\"cherry_weight_kg\":1000,\"float_rate_pct\":5,\"defect_rate_pct\":2,\"ripeness_grade\":1}}"
```

DRYING_CHECK（不触发霉变红灯则 mold_flag: false）：

```bash
curl -s -X POST "$BASE/events" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\":\"DRYING_CHECK\",\"lot_id\":\"$LOT_ID\",\"event_time\":\"2025-02-02T14:00:00Z\",\"data\":{\"moisture_pct\":12,\"turns_per_day\":2,\"covered_overnight\":true,\"mold_flag\":false}}"
```

WAREHOUSE_IN：

```bash
curl -s -X POST "$BASE/events" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\":\"WAREHOUSE_IN\",\"lot_id\":\"$LOT_ID\",\"event_time\":\"2025-02-02T16:00:00Z\",\"data\":{\"in_weight_kg\":200,\"packaging_type\":\"grain_pro\",\"bin_code\":\"B001\"}}"
```

WAREHOUSE_OUT（留样 1kg，使 balance 接近 0 或可控）：

```bash
curl -s -X POST "$BASE/events" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\":\"WAREHOUSE_OUT\",\"lot_id\":\"$LOT_ID\",\"event_time\":\"2025-02-02T18:00:00Z\",\"data\":{\"out_weight_kg\":199,\"buyer_name\":\"测试买家\",\"shipment_ref\":\"SHIP001\",\"sample_retained_kg\":1}}"
```

**4. 上传文件并绑定到某事件**

```bash
# 上传
curl -s -X POST "$BASE/files/upload" -F "file=@/path/to/photo.jpg"
# 绑定（将返回的 file_id 与上面任一的 event_id 填入）
curl -s -X POST "$BASE/files/bind?event_id=$EVENT_ID_1&file_id=$FILE_ID"
```

**5. 获取对账摘要（含红灯/绿灯、balance_kg）**

```bash
curl -s "$BASE/lots/$LOT_ID/ledger"
```

期望：返回 `status`（green/red）、`balance_kg`、`total_receive_cherry_kg`、`total_warehouse_in_kg`、`total_warehouse_out_kg`、`total_sample_retained_kg`、`red_lights` 数组。

---

## 命令清单（从 0 到跑起来）

**方式一：Docker 一键启动**

```bash
# 在项目根目录 P:\coffee_trace
docker compose up --build
# 等待 backend 日志出现 "Uvicorn running on http://0.0.0.0:8000"
# 浏览器打开 http://localhost:8000/docs
```

**方式二：本地开发（需已安装 PostgreSQL）**

```bash
# 1. 进入后端目录
cd P:\coffee_trace\backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置数据库 URL（若与默认不同）
# set DATABASE_URL=postgresql+asyncpg://coffee:coffee_secret@localhost:5432/coffee_trace

# 4. 执行迁移
alembic upgrade head

# 5. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验收示例 curl（需先从前一步响应中取出 plot_id、lot_id、event_id 填入变量）：**

见上文「示例 curl（验收闭环）」；核心验收为：`GET /lots/{lot_id}/ledger` 返回 `status`、`balance_kg`、`red_lights`。

---

## 验收标准对照

| 项 | 说明 |
|----|------|
| **A** | `docker compose up --build` 后，后端可访问 http://localhost:8000/docs 并可调通所有接口。 |
| **B** | 能用 curl 完成：创建 plot → 创建 lot 并绑定 plot → 写入 RECEIVE_CHERRY、DRYING_CHECK、WAREHOUSE_IN、WAREHOUSE_OUT → 上传文件并绑定到事件 → 获取 `/lots/{lot_id}/ledger` 得到红灯/绿灯与 balance_kg。 |
| **C** | 事件 `data` 字段缺失或类型错误返回 422；被锁定批次写入事件返回 409。 |
| **D** | README 包含：本地运行、Docker 运行、示例 curl、数据库迁移、关键概念（plot/lot/event/ledger）。 |

---

## 项目结构（概要）

```
coffee_trace/
├── ARCHITECTURE.md       # 系统架构与数据流、迁移策略
├── README.md
├── docker-compose.yml   # postgres + backend
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── alembic.ini
    ├── alembic/
    │   ├── env.py
    │   └── versions/
    │       └── 001_initial.py
    ├── uploads/         # 上传文件存储（MVP）
    └── app/
        ├── main.py
        ├── config.py
        ├── database.py
        ├── api/         # plots, lots, events, files；lots 下含 /lots/{id}/ledger、/lots/{id}/events
        ├── models/      # Plot, Lot, LotPlot, Event, File, EventFile, Device, DeviceChannel
        ├── schemas/     # Pydantic API + 事件 data 校验（event_data.py）
        ├── services/    # ledger_service（对账+红灯）、file_service（上传+sha256）
        └── core/
```

---

## 红灯规则（MVP）

1. **对账不平衡**：`abs(balance_kg) > 1.0` → `LEDGER_IMBALANCE`
2. **干燥霉变**：任意 `DRYING_CHECK.mold_flag == true` → `MOLD_FLAG`
