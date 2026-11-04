# 地图公开土壤数据（ISRIC SoilGrids 2.0）

版本：2026-11-04。用途：地图上的真实公开土壤属性图层与点位取值。

## 数据来源

- 数据集：ISRIC SoilGrids 2.0，250 m 全球土壤属性栅格（0–5 cm 预测值）
- 许可：CC BY 4.0
- 引用：Poggio et al. (2021). SoilGrids 2.0. SOIL, 7, 217–240. https://doi.org/10.5194/soil-7-217-2021
- 类型：**区域预测值，不是田间实测**；与平台登记的科研图层、实测样本分开使用

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/soilgrids/layers` | 图层目录（pH/SOC/全氮/CEC/容重/黏粒/砂粒/粉粒）与数据来源 |
| GET | `/api/soilgrids/tiles/{code}/{z}/{x}/{y}.png` | WMS 栅格瓦片代理，返回 256×256 PNG，按 XYZ 规则计算 EPSG:3857 BBOX |
| GET | `/api/soilgrids/point?lon=&lat=` | 点位取值：WMS GetFeatureInfo 读取各属性值，统一单位后返回；结果缓存到 SQLite |

- 瓦片与点位请求均由后端代理，前端不直接访问 ISRIC；瓦片缓存在 `data/soilgrids_cache/`，点位缓存在研究库 `soilgrids_points` 表。
- 首次访问需要外网；缓存后同一瓦片/点位可离线读取。

## 前端

- 图层选择：地图工具栏「公开数据」下拉框（默认土壤酸碱度 pH），通过 `createScientificTileLayer` 做 GCJ02→WGS84 瓦片纠正后叠加在高德底图上。
- 点位取值：点击地图后在右侧「公开土壤属性」卡片显示 8 项属性与来源说明。
- 图例与底图标注注明数据来源与 CC BY 4.0 许可。

## 边界

- 0–5 cm 表层预测值，不能代表根区实测，也不能作为健康等级或农艺处方依据。
- 与平台合成测试网格（`SYNTHETIC_TEST_DATA`）是两套数据：公开图层开启时，点位面板优先展示公开数据，避免混用。
