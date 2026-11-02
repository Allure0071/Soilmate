# 健康评价接口契约：前后端确认稿

版本：`0.1.0-draft`。日期：2026-11-02。对应平台流程图 v9。

**状态：前端提出、待后端同学确认。** 只有 `GET /api/auth/me` 为现有接口，其余均为拟新增能力。本目录不包含后端业务实现，不表示微调千问、N+X 或多 Agent 已部署。

## 先看哪些文件

首次接手请先阅读 [对接包说明](00-对接包说明.md)，了解业务目的、开发分工和第一批范围。

| 文件 | 用途 |
|---|---|
| [BACKEND-CHECKLIST.md](BACKEND-CHECKLIST.md) | 后端同学首先确认的事项，包含 P0 和 P1 范围 |
| [openapi.json](openapi.json) | 可导入 OpenAPI 工具的路径、请求、返回及错误定义 |
| [examples.json](examples.json) | 35 组带中文名称的虚构 HTTP 示例，供讨论及后续 Mock 使用 |
| [operations.json](operations.json) | 接口操作索引及优先级 |
| [contract.mjs](contract.mjs) | 契约定义来源，生成 OpenAPI 和前端类型 |
| [examples.mjs](examples.mjs) | 生成示例文件；其中内容不构成科学规则 |
| [前端类型](../../frontend/src/assessment/contracts.d.ts) | 自动生成的类型定义；无运行代码，不要求项目改用 TypeScript |
| [验证脚本](../../scripts/validate_assessment_contract.py) | 离线检查 OpenAPI、示例及关键反例 |

## 1. 本轮分工

前端负责页面、表单、时间线、结果和问题分析展示、追问、反馈交互、请求层以及明确标注的 Mock。

后端负责真实接口、登录和资源归属、数据库、文件解析、指标字典与换算、N+X、微调千问、多 Agent、上下文及任务执行。前端不直接访问模型服务，不保存模型密钥。

本目录落实接口约定、类型和样例。前端已完成分步页面与动态录入，详见 [前端审核说明](FRONTEND-REVIEW.md)。统一请求层和 Mock 运行逻辑尚未接入页面。

## 2. 必须保持的业务规则

1. 快速和深度健康评价都要求登录；地图可公开浏览。
2. 快速试用可先不建地块。深度分析需要地块和种植周期。
3. 至少一项有效实测指标即可保存并发起分析；不能因为少于推荐清单项数就拒绝。
4. 推荐指标、实际输入和未测指标分别返回。指标数量按不同指标代码计，不按样本行数或检测时点计。
5. 低覆盖影响判断范围；仍应返回受已有证据支持的评价、问题分析和建议。`composite_score` 可为 null，不能为凑齐结果而编造分数。
6. 问题的观察事实、可能成因、支持证据和待核实事项分开。模型推测不能冒充实测或确定因果。
7. 地图参考单独放在 `map_context`，不能自动写入 `values`。接口对实测输入只接受 `source_type=user_measurement`。
8. 本时点补测不等于新时点；重新分析不等于重新检测。
9. 真实执行反馈独立于建议；方案调整先形成 draft，用户确认后采用。
10. 快速升级深度保留同一会话及旧分析。关联检测到地块须由用户确认，不改变原始来源与采样信息。

## 3. 共用传输约定

- 建议新前缀：`/api/assessment`。开发时通过现有 Vite 同源代理连接后端。
- 新成功响应统一为 `{data, request_id, data_origin}`；`data_origin` 为 `real` 或 `mock`。
- 新错误响应为 `{error: {code, message, fields, retryable}, request_id, data_origin}`。
- 现有 `/api/auth/me` 保持原有 `{user, csrf_token}`，其失败保持 FastAPI `{detail}`；不为新页面改坏现有登录。
- ID 都是后端生成的不透明字符串，前端不假定 UUID、前缀或递增规则。
- 时间用带时区的 RFC3339 字符串；纯采样日期和计划日期用 `YYYY-MM-DD`。
- 输出字段是否可空、输入字段是否可省略，以 OpenAPI 为准。数组通常用 `[]` 表示没有结果；没有综合分数用 null，不能用 0 替代。
- Schema 对未约定字段默认拒绝，减少拼错字段被默默忽略的情况。新增字段需先更新契约并同步双方。

### 登录、CSRF 和重复提交

沿用 `soilmate_session` HttpOnly Cookie。同源请求携带凭据；新写接口建议统一要求 `X-CSRF-Token`，值来自现有 `/api/auth/me`。新路径的鉴权必须由后端补齐，现有只保护科研路径的中间件不能视为已经保护新路径。

草案同时建议写请求使用 `Idempotency-Key`，由前端为一次用户操作生成并在网络重试时复用。相同用户、方法、路径、key 和请求内容重放应返回原结果；同 key 内容变化返回 409。保留时长待后端确认。

权限由服务端会话决定，客户端不能通过提交 `owner_user_id` 指定数据归属。所有关联的会话、地块、周期、输入、任务、消息和方案都应检查归属和关联关系。

## 4. P0：优先提供快速评价闭环

以下 10 个操作足以优先对接快速模式：

| 顺序 | 请求 | 输入/输出的重点 |
|---|---|---|
| 1 | `GET /api/auth/me`（已有） | 登录用户与 CSRF |
| 2 | `GET /api/assessment/indicators` | 稳定指标代码、名称、可选单位、方法、别名与字典版本 |
| 3 | `POST /api/assessment/sessions` | 输入 `mode=quick`，返回会话；地块可为空 |
| 4 | `POST /api/assessment/measurements` | 保存一批实测；`values` 至少一项，返回独立检测记录 ID |
| 5 | `POST /api/assessment/tasks` | 输入 `type=quick_analysis` 与检测记录 ID，202 返回任务 ID |
| 6 | `GET /api/assessment/tasks/{task_id}` | 轮询运行状态和结构化结果 |
| 7 | `POST /api/assessment/sessions/{session_id}/messages` | 保存追问并创建异步 followup 任务，202 返回消息与任务 ID |
| 8 | `GET /api/assessment/sessions/{session_id}/messages` | 读取对话 |
| 恢复 | `GET /api/assessment/sessions/{session_id}` | 当前模式、步骤、检测记录、方案和最近任务 ID |
| 恢复 | `GET /api/assessment/measurements/{measurement_id}` | 恢复原始及标准化输入 |

调用过程：创建会话 → 保存实测 → 创建任务 → 轮询任务 → 展示结果 → 发送追问 → 轮询答复。

刷新时从会话恢复各个 ID，不重复发起分析。分析结果带独立 ID，历史消息与决策引用不会被后续重新分析覆盖。

## 5. 任务状态和结果

| 状态 | 含义 | result/error |
|---|---|---|
| queued | 已接收、排队 | 都为 null |
| running | 正在执行 | 都为 null；可读取 `current_stage` 和 `agent_tasks` |
| completed | 本次任务完成 | 必须有对应类型结果，error 为 null |
| partial | 已结束，但只形成有限范围的输出 | 必须有对应类型结果，明确缺口或限制 |
| failed | 本次任务失败 | result 为 null，必须有 error |
| interrupted | 重启等原因导致中断 | result 为 null，必须有 error |

`partial` 是终态，不是前端继续无限等待的状态。少测不要求统一返回 partial：只要任务目标是单项说明，completed 也可以有单项范围；不能因此强行升级成综合评价。

任务类型与结果固定对应：

- `quick_analysis` / `deep_analysis` → `result.kind=analysis`。
- `plan_generation` / `replan` → `result.kind=plan`。
- 追问请求产生 `followup` → `result.kind=message`，可附带新的分析，也可只解释原结果。

第一版建议约每 2 秒轮询；后端如需调整间隔，应明确说明。客户端停止等待不等于任务取消，恢复后继续查原 ID。失败后用户主动重新执行使用新提交 key；网络不确定时复用旧 key，避免重复创建任务。

Agent 状态只返回可展示摘要、角色与错误，不返回模型私密推理过程。六种角色为 `manager / data_check / diagnosis / agronomy / process_testing / review`。快速模式 `agent_tasks=[]`，不能把一次直出拆成虚假的多 Agent 进度。

## 6. P1：深度分析与过程检测

1. 通过地块和周期接口建立 `field_id`、`cycle_id`；地理坐标为 EPSG:4326。
2. 创建 `type=plan_generation` 任务。N+X 与模型调用由后端完成，返回含多个 checkpoint 的 draft 方案。
3. 每个 checkpoint 有独立 ID、序号、阶段、推荐指标及采样要求。日期可空，由阶段或触发条件确定；不要求所有阶段等间隔。
4. 用户通过计划确认接口采用方案。`expected_version` 不匹配返回 409，防止前端覆盖他人或其他会话中的更新。
5. 实测可关联具体 checkpoint，少于推荐清单仍可发起 `deep_analysis`。
6. 快速升级通过 `/sessions/{session_id}/upgrade`，同一会话保留旧结果；地块关联和检测归属确认由后端实施。
7. 用户反馈通过 `/management-events` 保存；`replan` 任务引用旧方案、反馈与新检测记录，生成新的 draft。旧方案与原始实测不被覆盖。

N+X 真模型、已确认配置、人工建议和 Mock 用不同来源标识。缺少模型时不能将静态配置改名为模型推理结果。没有报价依据时 `estimated_cost=null`，不能编造检测费用。

### 仍需业务方最终确定的数量规则

“后续检测不超过首次”在多个检测时点下有不同口径。本稿建议比较初始过程方案中对应时点的推荐项数；也可以确认以基线推荐项数作上限。**两种口径都不能以用户第一次实际只填一项锁死后续输入。** 该规则在确认前不写成前端硬性校验。

## 7. 文件导入

草案采用两步：

- `POST /imports`：multipart 上传 CSV/XLSX，返回导入 ID、到期时间、表头、预览行与候选映射；此时不保存正式检测记录。
- `POST /imports/{id}/confirm`：提交映射和归属；按样本拆分检测记录，成功返回 ID 列表。

建议确认导入采用原子提交：任何待修正行使整个确认返回 422，不静默保存一部分。预览到期返回 `IMPORT_EXPIRED`；用户可重新上传。是否允许部分成功及文件上限需后端确认，草案上限为 12,000,000 bytes。

前端使用 FormData，不手工设置 multipart boundary。确认阶段不同样本、日期、土层或方法不能被默默合并；缺少区分信息时应要求用户确认。

## 8. 列表与错误

- 地块列表使用不透明 cursor，默认 limit 20，上限 100。
- 对话页返回最近一页，但页内按 sequence 升序；`next_cursor` 用于取更早一页。前端前插去重后保持顺序。
- 401：登录失效，保存当前输入并提示重新登录。
- 403：无访问权，不能显示其他用户数据。
- 409：重复 key 内容不一致或方案版本冲突，需要刷新/明确重新提交。
- 422：字段问题，通过 `fields[].path` 精确定位；path 使用 JSON Pointer。
- 429：繁忙，提示稍后重试。
- 503：真实模型或所需能力不可用，保留输入；不得自动换成 Mock 成功。
- 500 或任务 failed/interrupted：展示用户可读错误和 request_id，不显示服务堆栈。

## 9. 前端独立开发约定

后续页面只依赖统一请求入口和本目录定义；真实传输与 Mock 返回相同形状，现有账号响应单独适配。开发示例的 `data_origin=mock` 必须在界面明确标注。

本目录的示例不包含真实模型输出、真实地块记录或科学阈值。示例数值只用于界面和结构验证，不能当成土壤健康结论。真实接口失败不自动退回模拟。

## 10. 修改和校验

修改唯一契约来源 `contract.mjs`，再生成：

```powershell
node docs/assessment-api/contract.mjs
node docs/assessment-api/examples.mjs
python scripts/validate_assessment_contract.py
```

验证工具安装在 git 忽略的 `.local-tools/contract-validator`，不改变前后端应用依赖：

```powershell
python -m pip install --target .local-tools/contract-validator jsonschema==4.23.0 openapi-spec-validator==0.7.2
```

修改字段、状态或行为后应一起更新：OpenAPI、前端类型、示例、确认清单和使用说明。类型声明不表达全部运行约束，例如至少一项输入、权限、任务状态关联、跨字段关系仍以契约及后端校验为准。

## 11. 当前确认记录

| 项目 | 状态 |
|---|---|
| 前端接口草案、类型、示例 | 已整理 |
| OpenAPI 与示例离线校验 | 已通过 |
| 后端同学确认 | 待确认；未代为发送任何消息 |
| 实际后端实现及联调 | 未开始；交由后端同学 |
| 页面、模型及数据库变更 | 本次未修改 |

后端确认后登记实际版本、负责人及兼容差异，再将契约状态从 draft 调整为双方确认版本。此前可以据此做明确标注的前端 Mock；若核心约定变化，统一修正而不让两端各自演变。
