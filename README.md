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

## 数据与功能说明

- `sample-data/soil.sqlite` 和 `sample-data/soil_1km.sqlite` 是合成测试库。`scripts/install_sample_data.py` 不会覆盖 `data/` 中已有的数据库。
- 正式地图瓦片、原始科研数据、账号数据库、本机配置和密钥均不在本仓库中。需要这些数据的功能须在取得相应授权后单独配置。
- 账号注册和登录使用本机后端创建的数据库。每台机器的账号互不共享。
- Soiledge 的 AI 说明需要本机另行安装并启动 Ollama；未启动时，其他接口仍可运行。

## 项目结构

- `frontend/`：Vue 网站。
- `backend/`：FastAPI 服务。
- `scripts/`：数据准备及开发辅助脚本。
- `sample-data/`：合成测试数据库。

项目中的合成示例只适用于开发与演示。正式分析需使用经过核查且获准使用的数据。

## 健康评价改造接口

前端与后端协作的 [接口契约确认稿](docs/assessment-api/README.md) 包含 OpenAPI 定义、前端类型、调用示例及 [后端确认清单](docs/assessment-api/BACKEND-CHECKLIST.md)。

接口契约当前为 `0.1.0-draft`，待后端同学确认。健康评价前端已提供模式选择、地块资料、动态指标录入与录入确认页面，支持本机草稿和分步导航；新分析接口尚未接入，启动方式不变。详见 [前端审核说明](docs/assessment-api/FRONTEND-REVIEW.md)。

## 工具中心

访问 `/tools` 可公开搜索与筛选地图、数据库、Agent 分析和常用工具。顶部保持探索数据、数据资源、健康研究、AI 助手、工具中心五个独立入口；工具条目可打开原有地图与数据库模块，Agent 录入工具登录后继续，均可返回原工具目录。

首批本地计算包括容重与孔隙度、含水率换算、单层有机碳储量、同量纲单位换算、溶液稀释、线性标准曲线与统计速算。每项工具包含输入校验、可主动载入的示例、公式、适用条件、原始参考链接及结果文本下载。计算参数不上传或保存；示例不是实测数据，输出不代表健康等级或标准合规结论。地图测量、仪器资料、盐碱与污染判读等条目仍标记为建设中。

计算定义与参考来源位于 `frontend/src/tools/calculators.js`，目录与接入状态位于 `frontend/src/tools/catalog.js`。在 `frontend/` 下运行 `node --test src/tools/calculators.test.js src/siteNavigation.test.js src/assessment/*.test.js` 可验证公式边界、单位口径、工具路由与现有录入校验。

### 数据体检与质地三角图

- `/tools?tool=data-audit`：读取本地 CSV、TSV、Excel `.xlsx` 或粘贴表格，支持工作表选择、缺失与重复记录、数值格式、单位混用、手动范围和 IQR 离群提示。最多 5,000 行、60 列、5 MB；保留原始值，导出问题清单，不自动删行、填补或换算单位。Excel 读取现有值，不重新计算公式。
- `/tools?tool=texture`：按 USDA 12 类细土体系判别质地，显示三角图样点，导出 SVG 和包含原始输入的判别记录。比例默认须合计 100%，归一化需要手动勾选；不生成健康等级或种植建议。

两个工具均无需登录，文件与参数不上传、不写入账号。算法、来源及适用范围见 `frontend/src/tools/research/SOURCES.md`；运行 `node --test frontend/src/tools/research/research.test.js` 验证分类边界、图形分区、导入和体检规则。
