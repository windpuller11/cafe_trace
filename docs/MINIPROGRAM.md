# 微信小程序对接说明 — 员工上传数据

后端已部署到腾讯云后，员工可通过微信小程序完成：**选择批次 → 录入事件（入厂/干燥检测/入库/出库等）→ 可选上传照片并绑定到事件**。本文说明如何让小程序调用后端 API。

---

## 1. 微信公众平台配置（必做）

1. 登录 [微信公众平台](https://mp.weixin.qq.com/) → 进入你的小程序。
2. **开发** → **开发管理** → **开发设置** → **服务器域名**。
3. 在 **request 合法域名** 中新增你的后端域名，例如：
   - `https://你的腾讯云域名.com`
   - 不要加路径或端口，不要写 `http://`（必须 HTTPS）。
4. 若小程序里会**上传文件**（照片/PDF），在 **uploadFile 合法域名** 中填写同一域名。
5. 保存后，重新打开小程序开发者工具或重新编译后生效。

---

## 2. 后端 Base URL

把下面所有示例里的 `BASE` 换成你在腾讯云上的实际地址，例如：

```javascript
const BASE = 'https://你的腾讯云域名.com';
```

确保该域名已备案、已配置 HTTPS，且 8000 端口对外（若用 Nginx 反向代理，则对外是 443，BASE 不写端口）。

---

## 3. API 清单（小程序常用）

| 用途           | 方法 | 路径                    | 说明 |
|----------------|------|-------------------------|------|
| 拉取地块列表   | GET  | `/plots`                | 创建批次时选地块 |
| 拉取批次列表   | GET  | `/lots`                 | 录入事件前选批次 |
| 拉取某批次事件 | GET  | `/lots/{lot_id}/events` | 查看该批次已录事件 |
| 创建事件       | POST | `/events`               | 员工录入入厂/干燥/入库/出库等 |
| 上传文件       | POST | `/files/upload`         | multipart/form-data，字段名 `file` |
| 绑定文件到事件 | POST | `/files/bind`           | Query: `event_id`, `file_id` |
| 对账摘要       | GET  | `/lots/{lot_id}/ledger` | 查看批次红灯/绿灯、balance_kg |

如需**创建地块、创建批次**，可同样用 `POST /plots`、`POST /lots`，一般由管理员在后台或 PC 完成，员工端小程序可只做「选批次 + 录事件 + 上传照片」。

---

## 4. 小程序请求示例

### 4.1 拉取批次列表（GET）

```javascript
wx.request({
  url: `${BASE}/lots`,
  method: 'GET',
  data: { skip: 0, limit: 20 },
  success(res) {
    if (res.statusCode === 200) {
      const { items, total } = res.data;
      // items: [{ lot_id, lot_type, received_at, status, ... }]
    }
  }
});
```

### 4.2 创建事件（POST）— 入厂鲜果 RECEIVE_CHERRY

```javascript
wx.request({
  url: `${BASE}/events`,
  method: 'POST',
  header: { 'Content-Type': 'application/json' },
  data: {
    event_type: 'RECEIVE_CHERRY',
    lot_id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', // 从批次列表选的 lot_id
    event_time: '2025-02-03T10:00:00.000Z',       // ISO 8601，建议用 new Date().toISOString()
    actor: '张三',                                  // 可选，操作人
    data: {
      cherry_weight_kg: 1000,
      float_rate_pct: 5,
      defect_rate_pct: 2,
      ripeness_grade: 1
    }
  },
  success(res) {
    if (res.statusCode === 200) {
      const event = res.data; // { event_id, event_type, lot_id, ... }
      // 若需上传照片绑定到该事件，记下 event.event_id
    }
  }
});
```

### 4.3 干燥检测 DRYING_CHECK

```javascript
// event_type: 'DRYING_CHECK'
data: {
  moisture_pct: 12,
  turns_per_day: 2,
  covered_overnight: true,
  mold_flag: false   // true 会触发霉变红灯
}
```

### 4.4 入库 WAREHOUSE_IN

```javascript
// event_type: 'WAREHOUSE_IN'
data: {
  in_weight_kg: 200,
  packaging_type: 'grain_pro',
  bin_code: 'B001'
}
```

### 4.5 出库 WAREHOUSE_OUT

```javascript
// event_type: 'WAREHOUSE_OUT'
data: {
  out_weight_kg: 199,
  buyer_name: '测试买家',
  shipment_ref: 'SHIP001',
  sample_retained_kg: 1   // 可选，留样重量
}
```

### 4.6 上传照片并绑定到事件

先上传文件，再绑定到刚创建的事件：

```javascript
// 第一步：上传文件（小程序用 wx.uploadFile）
wx.uploadFile({
  url: `${BASE}/files/upload`,
  filePath: tempFilePath,  // 从 wx.chooseImage 得到的临时路径
  name: 'file',
  success(res) {
    const data = JSON.parse(res.data);
    const fileId = data.file_id;
    // 第二步：绑定到事件
    wx.request({
      url: `${BASE}/files/bind`,
      method: 'POST',
      data: {},
      header: { 'Content-Type': 'application/json' },
      success: function() {
        // 绑定接口用 Query 传参，需在 url 上带 event_id 和 file_id
      }
    });
  }
});
```

**注意**：`/files/bind` 是 Query 参数，小程序应这样调用：

```javascript
wx.request({
  url: `${BASE}/files/bind?event_id=${eventId}&file_id=${fileId}`,
  method: 'POST',
  success(res) {
    if (res.statusCode === 200) console.log('绑定成功');
  }
});
```

上传接口返回示例：`{ "file_id": "uuid", "storage_url": "/uploads/...", "sha256": "...", "meta": null }`。

---

## 5. 事件类型与 data 字段速查

| event_type     | 必填 data 字段 |
|----------------|----------------|
| RECEIVE_CHERRY | cherry_weight_kg, float_rate_pct, defect_rate_pct, ripeness_grade (0–3) |
| DRYING_CHECK   | moisture_pct, turns_per_day, covered_overnight, mold_flag |
| WAREHOUSE_IN   | in_weight_kg, packaging_type, bin_code |
| WAREHOUSE_OUT  | out_weight_kg, buyer_name, shipment_ref；可选 sample_retained_kg |
| FERMENT        | mode, start_time, end_time；可选 temp_series, ph_series 等 |
| SENSOR_READING | device_id, metric, value, unit |

更多字段与校验规则见后端 API 文档：`https://你的域名/docs`（Swagger）。

---

## 6. 建议的录入流程（员工端）

1. **首页**：拉取 `/lots`，展示批次列表（可只显示未锁定、近期）。
2. **选批次**：进入某批次后，拉取 `/lots/{lot_id}/events` 看已录事件；提供「录入新事件」。
3. **录事件**：选择事件类型（入厂鲜果 / 干燥检测 / 入库 / 出库等）→ 表单填写对应 `data` → 提交 `POST /events`。
4. **选填照片**：若需拍照留证，先 `wx.chooseImage`，再 `wx.uploadFile` 到 `/files/upload`，拿到 `file_id` 后调用 `/files/bind?event_id=xx&file_id=xx`。
5. **对账**：可提供「查看对账」按钮，请求 `GET /lots/{lot_id}/ledger`，展示 status（green/red）、balance_kg、red_lights。

---

## 7. 错误处理

- **404**：lot_id / plot_id / event_id 不存在，提示「批次不存在」等。
- **409**：批次已锁定，无法再录事件，提示「该批次已锁定」。
- **422**：请求体格式错误或 `data` 不符合该事件类型（如缺必填、类型错），以返回的 `detail` 提示用户修正。

---

## 8. 当前后端说明

- **鉴权**：MVP 阶段未启用登录鉴权，任何人只要知道 Base URL 即可调用。若需只允许员工使用，后续可加微信登录（code2session）或 token，在 FastAPI 层做校验。
- **HTTPS**：微信小程序要求 request/uploadFile 域名必须为 HTTPS，部署时请确保腾讯云已配置 SSL。

按上述配置好**服务器域名**并替换 **BASE** 后，即可在小程序内完成员工端数据上传与照片绑定。
