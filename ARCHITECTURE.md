# 咖啡处理溯源与对账系统 — 系统架构与数据流

## 1. 系统架构简图（文字）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           客户端（未来：微信小程序 / PC Web）                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FastAPI 应用层                                                              │
│  /health | /plots | /lots | /events | /files | /lots/{id}/ledger | /lots/..  │
│  （未来鉴权：在此层注入 user/role，MVP 暂不启用）                               │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                     │                     │
                    ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  CRUD 服务        │  │  ledger_service   │  │  file_service    │
│  (plot/lot/event)│  │  聚合事件 → 对账   │  │  上传 + sha256   │
│                  │  │  红灯规则引擎      │  │  uploads/ 存储   │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                    │                     │                     │
                    └─────────────────────┼─────────────────────┘
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PostgreSQL                                                                  │
│  plots | lots | lot_plots | events | files | event_files | devices(预留)     │
│  事实唯一来源：Event 表（event_type + data JSONB + schema 校验）               │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              本地 uploads/          (未来) 电子秤/温湿度/pH/Brix/水分仪
              照片/视频/PDF            → 以 SENSOR_READING 事件写入，不重构库
```

**设计要点：**
- **以 Lot 为主线**：批次从入厂到出库全生命周期由 Lot + 多条 Event 描述，主表不膨胀。
- **Event 为唯一真相**：所有重量、检测、出入库均以“按时间追加”的 Event 记录，对账从事件聚合计算，可审计。
- **可扩展**：新增工艺/传感器只需新增 `event_type` 与对应 Pydantic schema，以及可选设备通道表，无需改主表结构。

---

## 2. 数据流（对账与红灯）

1. **录入流**：创建 Plot → 创建 Lot（可绑定多个 Plot）→ 按时间顺序写入 Event（RECEIVE_CHERRY → FERMENT → DRYING_CHECK → WAREHOUSE_IN → WAREHOUSE_OUT），文件上传后通过 event_files 绑定到事件。
2. **对账流**：请求 `GET /lots/{lot_id}/ledger` → ledger_service 从 events 表按 lot_id 筛选、按 event_time 排序 → 解析 RECEIVE_CHERRY / WAREHOUSE_IN / WAREHOUSE_OUT 等，累加入厂鲜果、入库生豆、出库生豆、留样 → 计算 `balance_kg`，并运行红灯规则（对账不平衡、霉变等）→ 返回 Ledger 摘要与 red_lights 列表。
3. **证据链**：每个事件可挂多个 files（照片/视频/PDF），files 表只存 URL、sha256、meta；真实文件存 uploads/（MVP），便于审计。

---

## 3. 数据库建表与迁移策略

- **引擎**：PostgreSQL；**迁移工具**：Alembic。
- **策略**：在项目内执行 `alembic init`，所有表由 SQLAlchemy 模型定义，通过 `alembic revision --autogenerate` 生成迁移脚本，再 `alembic upgrade head` 应用。
- **首个迁移**：包含 plots, lots, lot_plots, events, files, event_files, devices, device_channels 共 8 张表，字段满足 MVP 需求；devices 表 MVP 可只建表不暴露 API。

**表与职责简述：**
- **plots**：地块卡（plot_id, plot_name, entity_name, admin_division, geo_polygon, area_m2, tenure_type）。
- **lots**：批次卡（lot_id, lot_type, sub_process, received_at, status, notes）。
- **lot_plots**：批次-地块多对多（lot_id, plot_id, share_pct）。
- **events**：事件（event_id, event_type, lot_id, container_code, location_code, actor, event_time, data JSONB, is_locked）。
- **files**：文件元数据（file_id, storage_url, sha256, meta）。
- **event_files**：事件-文件多对多。
- **devices** / **device_channels**：设备与通道，预留；传感器读数以 SENSOR_READING 事件写入。

迁移步骤（见 README）：
1. `alembic revision --autogenerate -m "initial"`
2. `alembic upgrade head`
