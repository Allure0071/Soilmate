# 健康评价 P0 后端实现说明

版本：2026-11-04。范围：快速试用闭环；深度分析已可提交（需先填写地块与种植周期）。

## 1. 已实现接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/assessment/indicators` | 指标字典（代码、名称、可选单位、是否必需单位、字典版本） |
| POST | `/api/assessment/sessions` | 创建研究会话（quick/deep，可带作物、背景、field_id/cycle_id） |
| GET | `/api/assessment/sessions/{id}` | 会话恢复：测量记录、最近任务 |
| POST | `/api/assessment/measurements` | 保存一批检测记录（逐项校验代码/单位/数值/来源） |
| GET | `/api/assessment/measurements/{id}` | 检测记录恢复 |
| POST | `/api/assessment/tasks` | 创建分析任务，返回 202 + task_id |
| GET | `/api/assessment/tasks/{id}` | 任务状态与结果（queued/running/completed） |

- 成功响应使用 `{data, request_id, data_origin:"real"}`；错误使用 `{error:{code,message,fields,retryable}, request_id, data_origin:"real"}`。
- 所有写接口支持 `Idempotency-Key`：同 key 同内容重放原响应，同 key 不同内容返回 409 `IDEMPOTENCY_CONFLICT`。
- `/api/assessment/` 已加入登录与 CSRF 中间件保护；会话、检测记录与任务均按 `user_id` 隔离。

## 2. 存储

SQLite（`data/research_v2.sqlite`）新增四张表：`assessment_sessions`、`assessment_measurements`、`assessment_tasks`、`assessment_idempotency`。表在首次访问时创建，不改动既有研究表。

## 3. 评价引擎（研究预览）

- 输入先换算到统一口径（%，μS/cm，kg/m³ 等），再套用 SMAF 型评分曲线（适宜区间、越高越好、越低越好）得到单指标得分。
- 按生产支持、养分供给、土壤结构、水分调节四项功能加权，得到功能分与综合分；至少 3 项有效指标且覆盖 2 项功能才输出综合分，否则只做指标级描述。
- 输出契约要求的结构化结果：覆盖范围、指标判读与证据引用、问题与待核实事项、建议与核对目标、证据缺口、限制声明、模型/规则版本。
- **边界**：规则集为演示参数，未经独立验证；不提供施肥剂量、不输出正式健康等级。结果页、依据页与下载报告均保留限制说明。

## 4. 任务状态

任务创建后 `queued`；约 1.2 秒后轮询返回 `running`（含角色进度摘要）；约 3 秒后 `completed` 并写入结果。状态由服务端按创建时间推进，客户端只轮询、不本地造状态。

## 5. 测试与运行

```bash
python -m pytest -q backend/tests            # 49 passed
cd frontend && node --test                   # 56 passed
```

启动方式与 README 一致；修改后端代码后需重启 uvicorn。
