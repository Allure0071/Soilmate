# 健康研究前端任务流程

日期：2026-11-04。依据 `0.1.0-draft` 接口契约；没有修改后端业务或确认契约状态。

## 已接入的前端行为

- 快速模式核对实际检测记录后：读取服务端指标字典 → 创建会话 → 保存实测 → 创建任务 → 轮询任务。仅在服务端确认上一阶段标识后继续。
- 写请求携带现有 HttpOnly 会话对应的 CSRF 和独立的 Idempotency-Key。连接不确定、刷新后继续提交时复用原内容及原 key；已失败或中断的任务经用户操作后使用新任务 key，沿用原检测记录。
- 排队与运行不显示虚构百分比；completed / partial / failed / interrupted 均结束自动轮询。partial 明确显示有限范围；无综合分数保持 null，不补成零。
- 结果分别展示判读、观察事实、可能成因、待核实事项、建议条件、证据与版本信息，拒绝不匹配任务或格式不完整的分析结果。
- 任务会话与标识写入 URL；当前标签页暂存未完成提交，最近 20 个入口按账号保存在本浏览器。刷新仅查询原任务；切换历史记录从所属账号的服务端重新读取，不把本地缓存当结果。
- 离开页面清理请求和轮询计时器，不声称取消服务端执行。401、403、404、409、422、429、503 和网络中断保留草稿并给出对应恢复动作。
- 界面填入的示例不可作为实测提交；匿名审核不发出真实分析请求。

## 当前限制

本机 `/api/assessment/indicators` 仍返回 404，真实健康评价服务和模型未部署，不能据前端状态页声称模型分析已上线。深度分析还需要服务端地块和种植周期；当前录入页保持深度草稿，不编造 field_id / cycle_id，也不降级成快速分析冒充深度结果。已有科研项目视图保留。

原始导入文件、工作表和行号仍由录入草稿保存；当前 API 契约没有导入来源字段，前端不会私自添加请求字段。后端确认导入接口后再扩展服务端来源追踪。

## 开发审核

仅 Vite 开发模式的匿名入口支持以下场景，顶部和结果内持续注明审核示例；示例只使用 `examples.json` 中的虚构接口资料，不发送当前草稿，真实服务错误不会自动切换成示例。

- `/assessment/preview?stage=analysis&assessmentDemo=completed`
- `/assessment/preview?stage=analysis&assessmentDemo=partial`
- `/assessment/preview?stage=analysis&assessmentDemo=failed`（重试后可查看完成状态）
- `/assessment/preview?stage=analysis&assessmentDemo=interrupted`
- `/assessment/preview?stage=analysis&assessmentDemo=running`（可暂停与继续查询）

也可以在匿名录入确认页选择审核场景。示例控制和数据在生产构建中移除。

验证：`node --test frontend/src/assessment/*.test.js frontend/src/dataNavigation.test.js`；生产构建：`npm --prefix frontend run build`。
