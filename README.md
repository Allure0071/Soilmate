# Soilmate 土壤健康数据平台

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
