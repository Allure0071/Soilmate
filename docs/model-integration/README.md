# Soilmate Qwen3-8B LoRA 接入

模型标识：`soilmate-qwen3-8b-lora-r32`。状态：**研究试用**，未验收为正式土壤健康评价模型。

当前实现：独立推理服务、适配器与基础模型元数据校验、平台后端连接、AI 助手和 Soiledge 解读入口。没有实现或宣称已部署 `/api/assessment` 的评分、任务数据库与 N+X 科研算法。语言模型解释不能代替这些能力。

## 产物与校验

收到的 `soilmate_8b_results (1).tar.gz` 包含 LoRA 适配器、分词器、训练日志与评测；不含基础模型权重、训练集、完整 benchmark 和人工评审规程。配置保存在 `backend/model_profiles/soilmate-qwen3-8b.json`，权重放在 Git 忽略的 `data/models/`，不进入仓库。

```bash
python scripts/install_soilmate_adapter.py '/path/to/soilmate_8b_results (1).tar.gz'
```

安装器在临时目录提取允许的文件，拒绝越界路径与链接，校验适配器和配置的 SHA-256 后再完成安装；不执行压缩包内脚本。训练服务器已有原产物时可直接使用原 `adapter_final`，无需重复上传权重。

## 在训练云服务器启动

先确认 GPU 空闲及原训练 Python 环境。不要在平台的 Python 3.9 环境或当前 8 GB Intel Mac 上安装、加载此 CUDA 8B 服务。以下命令在包含本仓库 `backend/inference/` 与 `backend/model_profiles/` 的服务器项目根目录执行。

优先复用原训练环境，先检查版本；需要独立环境时用 Python 3.10 或更新版本创建 venv，再安装 `backend/inference/requirements.txt`。依赖范围是接入约束，实际可复现发布应保存训练环境/部署环境的 `pip freeze` 和 CUDA 版本。

```bash
python -m pip install -r backend/inference/requirements.txt
export SOILMATE_BASE_MODEL_PATH=/mnt/workspace/models/models/Qwen--Qwen3-8B/snapshots/master
export SOILMATE_ADAPTER_PATH=/mnt/workspace/soilmate_train_bundle/runs/8b_sft/adapter_final
export SOILMATE_LOAD_4BIT=true
export SOILMATE_INFERENCE_API_KEY='替换为随机密钥'
python -m uvicorn backend.inference.app:app --host 127.0.0.1 --port 18100 --workers 1
```

基础模型和适配器仅从本地文件加载；不隐式下载、不启用远程模型代码。会核对训练记录中的 config/tokenizer/index 等元数据 SHA-256 和适配器 SHA-256。元数据核对不等于完整基础模型分片校验；原评测未提供每个基础权重分片的 SHA-256，应继续使用训练时的原快照。

服务健康接口 `GET /v1/health`、模型列表 `GET /v1/models` 和非流式 `POST /v1/chat/completions` 均要求 `Authorization: Bearer <密钥>`。未加载成功的服务不会返回 `ready=true`，也不会声称已加载微调权重。单进程一次生成一条请求，忙时返回 429；输入超过 3072 tokens 则拒绝，不截断任务证据；输出上限为 512 tokens，并返回是否达到上限。

## 平台连接

本地平台通过 SSH 转发连接时，另开终端使用真实服务器信息：

```bash
ssh -N -L 127.0.0.1:18100:127.0.0.1:18100 -p SSH端口 用户名@主机地址
```

在平台后端启动环境中设置（不能放进前端或 `VITE_*` 变量）：

```bash
export SOILMATE_MODEL_BASE_URL=http://127.0.0.1:18100/v1
export SOILMATE_MODEL_API_KEY='与云端服务相同的密钥'
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 18000
```

`.env.example` 是配置示例，不会被此应用自动加载。修改运行环境后需要重启相应后端进程。网页仅请求同源平台 API，不能直接访问云端模型密钥。

- `GET /api/agent/model/status`：登录后查看连接和模型身份。
- `POST /api/agent/expert`：登录与 CSRF 校验后提问，可选关联本人 `task_id`。只读取归属核验和文件校验通过的 Artifact；缺少任务证据时返回明确的补证据提示，不让模型补造结果。
- `POST /api/soiledge/ai`：同样要求登录和 CSRF，仅解释原 Soiledge 研究估算，不重新评分。

连接状态、适配器 SHA-256 和模型身份必须匹配；不自动换回基础模型或旧 Ollama。旧 `/api/agent/messages` 的任务路由职责保留。生成内容显示为研究试用解释，结果、建议和引用仍需人工复核；模型自写的引文不作为系统已核验引用。

## 评测边界与验收

47 道相同测试题和相同 benchmark SHA-256 下，微调产物自动通过为 7/13，拒答为 2/8，JSON schema 为 5/5；34 题待人工复核。基础模型对应为 10/13、5/8、5/5。自动关键词信号不等于正确率或人工确认幻觉率。基础模型 35/47 条输出达到 512 token 上限，微调产物平均输出也明显更短，因此不能把响应时间缩短解释为同等回答质量下的推理吞吐提升。

本服务使用非 thinking 模板、确定性生成；服务提示词有证据边界约束，**不是对原评测结果的逐字复现**。部署后需要重新评测、人工审阅拒答退化样本，正式验收前保留研究试用标识。

先核对服务 `ready` 和平台模型身份，再实际提问验证返回来源、超时、并发忙、超长上下文、未授权任务和服务离线；客户端不会因服务失败显示模拟成功。

参考：[Qwen3-8B 官方模型卡](https://huggingface.co/Qwen/Qwen3-8B)、[Hugging Face PEFT 加载适配器](https://huggingface.co/docs/peft/guides/peft_model_config)。
