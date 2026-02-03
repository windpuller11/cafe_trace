# 命令清单：从 0 到跑起来 + 验收

## 零、怎么测试（推荐：自动验收脚本）

1. **先启动后端**（二选一）  
   - Docker：在项目根目录执行 `docker compose up --build`，等出现 Uvicorn 启动日志。  
   - 本地：在 `backend` 目录执行 `alembic upgrade head` 和 `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`。

2. **再跑验收脚本**（项目根目录执行）：  
   ```bash
   python scripts/run_acceptance.py
   ```  
   若后端不在本机 8000 端口，可指定：  
   ```bash
   python scripts/run_acceptance.py http://localhost:8000
   ```

3. **看输出**：脚本会依次执行「创建 plot → 创建 lot → 写入四类事件 → 上传文件并绑定 → 获取 ledger」，并打印最终对账结果。最后一行出现「全部步骤完成」即表示闭环验收通过。

---

## 一、从 0 到跑起来

### 方式 1：Docker 一键启动（推荐）

在项目根目录 `P:\coffee_trace` 执行：

```bash
docker compose up --build
```

- 等待终端出现 `Uvicorn running on http://0.0.0.0:8000`
- 打开浏览器访问：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 方式 2：无 Docker，本地 Python + PostgreSQL

**前提：本机已安装并启动 PostgreSQL。** 若未安装，可下载 [PostgreSQL for Windows](https://www.postgresql.org/download/windows/) 安装后，用 pgAdmin 或 psql 执行下面 SQL 建库建用户。

**1. 在 PostgreSQL 里建库、建用户（只做一次）：**
```sql
CREATE USER coffee WITH PASSWORD 'coffee_secret';
CREATE DATABASE coffee_trace OWNER coffee;
```

**2. PowerShell 下执行（在项目里）：**
```powershell
# 进入后端目录
cd P:\coffee_trace\backend

# 安装依赖（若已装过可跳过）
pip install -r requirements.txt

# 设置数据库连接（同步驱动给 Alembic 用）
$env:DATABASE_URL = 'postgresql+asyncpg://coffee:coffee_secret@localhost:5432/coffee_trace'

# 执行迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**3. 浏览器打开：** http://localhost:8000/docs  

**4. 另开一个终端跑验收：**
```powershell
cd P:\coffee_trace
python scripts/run_acceptance.py
```

若 PostgreSQL 不在本机或端口/密码不同，请修改 `$env:DATABASE_URL` 再执行迁移和 uvicorn。

---

## 二、验收 curl（完整闭环）

假设后端已运行，`BASE=http://localhost:8000`。以下用 PowerShell 可执行；bash 用户把 `$PLOT_ID` 等改为自己从响应里取的 ID。

### 1. 创建地块（plot）

```bash
curl -s -X POST http://localhost:8000/plots -H "Content-Type: application/json" -d "{\"plot_name\":\"北坡A区\",\"entity_name\":\"张三种植户\",\"admin_division\":\"云南省某某县\"}"
```

从响应中记下 `plot_id`，例如：`PLOT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 2. 创建批次（lot）并绑定地块

把下面里的 `YOUR_PLOT_ID` 换成上一步的 `plot_id`：

```bash
curl -s -X POST http://localhost:8000/lots -H "Content-Type: application/json" -d "{\"lot_type\":\"washed\",\"received_at\":\"2025-02-02T08:00:00Z\",\"plot_ids\":[{\"plot_id\":\"YOUR_PLOT_ID\"}]}"
```

从响应中记下 `lot_id` → `LOT_ID`

### 3. 写入四类事件

把下面所有 `YOUR_LOT_ID` 换成上一步的 `lot_id`。

**RECEIVE_CHERRY：**

```bash
curl -s -X POST http://localhost:8000/events -H "Content-Type: application/json" -d "{\"event_type\":\"RECEIVE_CHERRY\",\"lot_id\":\"YOUR_LOT_ID\",\"event_time\":\"2025-02-02T09:00:00Z\",\"data\":{\"cherry_weight_kg\":1000,\"float_rate_pct\":5,\"defect_rate_pct\":2,\"ripeness_grade\":1}}"
```

**DRYING_CHECK（mold_flag: false 不触发霉变红灯）：**

```bash
curl -s -X POST http://localhost:8000/events -H "Content-Type: application/json" -d "{\"event_type\":\"DRYING_CHECK\",\"lot_id\":\"YOUR_LOT_ID\",\"event_time\":\"2025-02-02T14:00:00Z\",\"data\":{\"moisture_pct\":12,\"turns_per_day\":2,\"covered_overnight\":true,\"mold_flag\":false}}"
```

**WAREHOUSE_IN：**

```bash
curl -s -X POST http://localhost:8000/events -H "Content-Type: application/json" -d "{\"event_type\":\"WAREHOUSE_IN\",\"lot_id\":\"YOUR_LOT_ID\",\"event_time\":\"2025-02-02T16:00:00Z\",\"data\":{\"in_weight_kg\":200,\"packaging_type\":\"grain_pro\",\"bin_code\":\"B001\"}}"
```

**WAREHOUSE_OUT（留样 1kg，balance 接近 0）：**

```bash
curl -s -X POST http://localhost:8000/events -H "Content-Type: application/json" -d "{\"event_type\":\"WAREHOUSE_OUT\",\"lot_id\":\"YOUR_LOT_ID\",\"event_time\":\"2025-02-02T18:00:00Z\",\"data\":{\"out_weight_kg\":199,\"buyer_name\":\"测试买家\",\"shipment_ref\":\"SHIP001\",\"sample_retained_kg\":1}}"
```

从**第一个**事件的响应中记下 `event_id` → `EVENT_ID_1`（用于下面绑定文件）。

### 4. 上传文件并绑定到事件

**上传（把 `/path/to/photo.jpg` 换成你本机任意小文件）：**

```bash
curl -s -X POST http://localhost:8000/files/upload -F "file=@C:\path\to\photo.jpg"
```

记下返回的 `file_id` → `FILE_ID`。

**绑定到事件（把 EVENT_ID_1 和 FILE_ID 换成上面得到的）：**

```bash
curl -s -X POST "http://localhost:8000/files/bind?event_id=EVENT_ID_1&file_id=FILE_ID"
```

### 5. 获取对账摘要（验收 B）

把 `YOUR_LOT_ID` 换成你的 `lot_id`：

```bash
curl -s http://localhost:8000/lots/YOUR_LOT_ID/ledger
```

**期望：** JSON 中包含 `status`（"green" 或 "red"）、`balance_kg`、`total_receive_cherry_kg`、`total_warehouse_in_kg`、`total_warehouse_out_kg`、`total_sample_retained_kg`、`red_lights`。上述数据下应为 **green**，`balance_kg` 约为 0。

---

## 三、验收 C：422 与 409

**422（data 缺必填字段）：**

```bash
curl -s -X POST http://localhost:8000/events -H "Content-Type: application/json" -d "{\"event_type\":\"RECEIVE_CHERRY\",\"lot_id\":\"YOUR_LOT_ID\",\"event_time\":\"2025-02-02T09:00:00Z\",\"data\":{\"cherry_weight_kg\":1000}}"
```

期望：HTTP 422，body 中为校验错误详情。

**409（批次已锁定）：** 先通过 PATCH 或直接改 DB 将某 lot 的 `is_locked` 设为 true（若暂无 PATCH 接口，可暂用 DB 或后续加接口），再对该 lot 调 POST /events，期望 HTTP 409。

---

## 四、数据库迁移

```bash
cd P:\coffee_trace\backend
alembic upgrade head    # 应用迁移
alembic revision --autogenerate -m "描述"   # 模型改过后生成新迁移
alembic downgrade -1    # 回滚一步
```
