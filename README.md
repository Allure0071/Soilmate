# 沃壤知行（Soilmate）土壤健康数据平台

本仓库包含 Vue 前端、FastAPI 后端、开发脚本和两份合成测试数据库。`sample-data/` 中的点位和指标数值由固定公式生成，仅供界面及接口开发；它们不是实测数据，也不能作为正式地图或研究结论。

## 本地运行

需要 Python 3.9 或更新版本、Node.js 和 npm。在仓库根目录运行：

```powershell
python -m pip install -r backend/requirements.txt
python scripts/install_sample_data.py
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 18000
```

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问 `http://localhost:5173/`。Vite 将 `/api` 和 `/tiles` 请求转发到本地后端。生产构建运行 `npm run build`；FastAPI 可在根路径提供生成的 `frontend/dist`。

地图底图默认使用高德官方 JS API，支持标准地图与卫星影像；已按用户要求在前端配置中提供本项目浏览器 Key。天地图可作为另一配置来源；本地覆盖、坐标适配和验证范围见 [地图配置](frontend/MAP_SETUP.md)。地图加载失败时显示状态，不回退到未经核查的其他底图。

地图已接入 **ISRIC SoilGrids 2.0 公开土壤属性数据**（CC BY 4.0）：工具栏「公开数据」可切换 pH、有机碳、全氮、CEC、容重、黏粒、砂粒、粉粒 8 个真实属性图层，点击地图在右侧查看真实点位属性，并按平台评价规则给出点位健康评价（分数、短板与建议）。瓦片与点位均经后端代理并缓存，说明见 [公开土壤数据说明](docs/soilgrids-data/README.md)。

## 答辩演示模式（/demo）

访问 `/demo`（首页页脚也有入口）可打开独立的答辩演示模式：8 步演示"案例与来源 → 数据接入与核验 → N+X 选测 → 稳健评分 → 证据化解释 → 多 Agent 复核 → 报告 → 对照地块与可比性"，支持下一步按钮、键盘 `←/→` 切换、`Esc` 退出和自动播放。

- **纯前端、可离线**：不请求后端、不写数据库、不依赖模型服务；开发服务器和生产构建均可用（FastAPI 已加 `/demo` 路由）。
- **公开数据案例**：数据来自 ISRIC SoilGrids 2.0（250 m 全球土壤属性栅格，CC BY 4.0）REST 查询，案例点为广东湛江雷州（110.00°E, 21.40°N）与惠州（114.30°E, 23.10°N），属性为 pH、SOC、全氮、CEC、容重、黏粒，深度 0–5 cm；查询参数与引用写入界面和报告。
- **演示规则计算**：SMAF 型评分曲线 + 三套演示规则集在浏览器内确定性计算，输出功能分、区间、等级稳定性与稳定短板；规则参数标注"演示规则、未经独立验证"。
- **不越科学边界**：不把区域预测值当作本地实测、不输出健康等级诊断、不给施肥剂量；报告带“DEMO · 案例计算”水印与数据来源、限制声明。
- 演示数据与报告模板位于 `frontend/src/assessment/demoShowcase.js`，界面在 `frontend/src/assessment/DemoShowcase.vue`；说明与演示脚本见 [演示模式说明](docs/demo-mode/README.md)。

## 数据与功能说明

- `sample-data/soil.sqlite` 和 `sample-data/soil_1km.sqlite` 是合成测试库。`scripts/install_sample_data.py` 不会覆盖 `data/` 中已有的数据库。
- 正式地图瓦片、原始科研数据、账号数据库、本机配置和密钥均不在本仓库中。需要这些数据的功能须在取得相应授权后单独配置。
- 账号注册和登录使用本机后端创建的数据库。每台机器的账号互不共享；本地工作区提供邮箱 + 新密码直接重置（无需邮件服务），登录页「忘记密码？」入口可用。
- 研究助手通过平台后端连接独立的 Qwen3-8B LoRA 推理服务；配置、基础模型要求与研究试用边界见 [模型接入说明](docs/model-integration/README.md)。模型服务未连接时，研究助手自动使用本地知识库与当前评价任务结果回答（不声称模型输出，Soiledge AI 解读仍需模型服务），其他数据接口不受影响。

## 项目结构

- `frontend/`：Vue 网站。
- `backend/`：FastAPI 服务。
- `scripts/`：数据准备及开发辅助脚本。
- `sample-data/`：合成测试数据库。

项目中的合成示例只适用于开发与演示。正式分析需使用经过核查且获准使用的数据。

## 健康评价接口（P0 已接入）

前端与后端协作的 [接口契约确认稿](docs/assessment-api/README.md) 包含 OpenAPI 定义、前端类型、调用示例及 [实现说明](docs/assessment-api/BACKEND-IMPLEMENTATION.md)。

健康研究工作区的快速试用已接通后端 P0 流程：指标字典 → 建会话 → 保存检测记录 → 创建分析任务（202）→ 轮询任务 → 结构化结果；结果页、依据与版本、报告与记录三个页面共用同一任务，刷新可恢复，报告可下载为 HTML（可打印 PDF）。深度分析会同时关联地块与种植周期。

- 接口实现：`backend/app/api/assessment.py`；存储：`backend/app/assessment/store.py`；评价引擎：`backend/app/assessment/engine.py`。
- 评价引擎是**确定性研究预览实现**（SMAF 型评分曲线 + 功能权重），未经过独立验证；结果页与报告均保留规则版本、证据缺口与限制说明，不输出施肥剂量或正式健康等级。
- 输入校验：指标代码、报告单位、有限数值与重复指标在服务端校验；写请求支持 `Idempotency-Key` 重放，所有读写按账号隔离。
- 测试：`python -m pytest -q backend/tests`（49 项通过），其中 `backend/tests/test_assessment_api.py` 覆盖快速评价完整链路、幂等冲突、单位校验、深度模式地块要求与跨账号隔离。

## 工具中心

访问 `/tools` 可公开搜索与筛选地图、数据库、Agent 分析和常用工具。顶部保持探索数据、数据资源、健康研究、AI 助手、工具中心五个独立入口；工具条目可打开原有地图与数据库模块，Agent 录入工具登录后继续，均可返回原工具目录。

首批本地计算包括容重与孔隙度、含水率换算、单层有机碳储量、同量纲单位换算、溶液稀释、线性标准曲线与统计速算。每项工具包含输入校验、可主动载入的示例、公式、适用条件、原始参考链接及结果文本下载。计算参数不上传或保存；示例不是实测数据，输出不代表健康等级或标准合规结论。工具目录当前全部为已接入工具，不再保留"建设中"条目。

计算定义与参考来源位于 `frontend/src/tools/calculators.js`，目录与接入状态位于 `frontend/src/tools/catalog.js`。在 `frontend/` 下运行 `node --test src/tools/calculators.test.js src/siteNavigation.test.js src/assessment/*.test.js` 可验证公式边界、单位口径、工具路由与现有录入校验。

### 数据体检与质地三角图

- `/tools?tool=data-audit`：读取本地 CSV、TSV、Excel `.xlsx` 或粘贴表格，支持工作表选择、缺失与重复记录、数值格式、单位混用、手动范围和 IQR 离群提示。最多 5,000 行、60 列、5 MB；保留原始值，导出问题清单，不自动删行、填补或换算单位。Excel 读取现有值，不重新计算公式。
- `/tools?tool=texture`：按 USDA 12 类细土体系判别质地，显示三角图样点，导出 SVG 和包含原始输入的判别记录。比例默认须合计 100%，归一化需要手动勾选；不生成健康等级或种植建议。

两个工具均无需登录，文件与参数在浏览器内处理。数据体检完成后，可确认字段映射和单位，选择一行检测记录带入健康研究（需登录）；同名样本不合并、冲突单位不自动换算、合成问题示例不能带入实测录入。跳转暂存仅限当前标签页，有效期 30 分钟；确认替换后，检测值及文件名、工作表、表格行号、字段映射和原始样本行保存在当前浏览器草稿，刷新可恢复，不上传、不写入账号。分析服务仍待接入。算法、来源及适用范围见 `frontend/src/tools/research/SOURCES.md`；运行 `node --test frontend/src/tools/research/research.test.js` 验证分类边界、图形分区、导入和体检规则。

## 地图与数据资源互通

地图的当前图层资料可打开对应资源详情，保留指标、1/5 km 分辨率和地图位置；资源详情也可回到地图，并恢复目录搜索、类别、来源、排序与页码。缺失的覆盖率、年份、土层和许可仍明确显示待核验，不因跳转补造元数据。
