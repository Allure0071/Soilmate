# 地图底图与坐标配置

地图页默认采用高德官方 JS API 2.0，支持标准地图和卫星影像；保留天地图 WMTS 作为可配置的另一来源。不使用 OpenStreetMap 或未知第三方瓦片作为自动兜底。

## 当前高德配置

`src/map/config.json` 是可提交的前端配置，包含默认来源和本项目的高德浏览器 Key。用户已明确要求将这枚 Key 随配置提交。该 Key 已实际加载高德标准地图、卫星影像和服务自身的来源/审图标识；此结论只覆盖已经运行的底图功能，不代表全部高德服务均已验证。

配置文件中的浏览器 Key 会进入前端构建，可以在浏览器中读取。安全密钥、服务器凭据不放入此文件。高德的安全密钥与代理部署方式见[官方说明](https://developer.amap.com/api/javascript-api-v2/guide/abc/jscode)。如后续功能需要安全密钥，优先通过独立服务端代理配置，不把它提交到前端仓库。

本地或部署环境可以覆盖默认值，将 `frontend/.env.example` 复制为 `.env.local` 后填写相应变量：

| 变量 | 用途 |
| --- | --- |
| `VITE_MAP_PROVIDER` | `amap` 或 `tianditu`；默认读取版本化配置 |
| `VITE_AMAP_KEY` | 覆盖默认高德浏览器 Key |
| `VITE_AMAP_SERVICE_HOST` | 可选，高德安全密钥代理的 `/_AMapService` 地址 |
| `VITE_TIANDITU_KEY` | 天地图浏览器端应用 Key |

修改环境文件后重启 Vite；生产环境修改后重新运行 `npm --prefix frontend run build`。本地配置受 Git 忽略。底图未配置或加载失败时显示对应状态，可以重试，不回退到未经核查的其他来源。

## 高德与科学数据之间的坐标边界

高德使用 GCJ-02；项目点位、GeoJSON 与数据 API 继续采用现有 WGS84 约定。`src/map/coordinates.js` 使用 [gcoord](https://github.com/hujiulong/gcoord) 做本地显示转换，MIT 许可原文保存在 `public/assets/licenses/gcoord.txt`。

- Leaflet 对外仍使用 WGS84 LatLng；自定义显示投影转换到 GCJ-02 Web Mercator。标记、参考分区与点选坐标通过同一边界转换。
- 高德官方 SDK 负责底图、地名、Logo 和动态来源/审图标识；与 Leaflet 的中心、缩放和视口同步。卫星模式叠加官方影像与路网，不复制未公开瓦片地址。
- 原土壤瓦片是 WGS84 Web Mercator，不能直接贴到 GCJ-02 显示网格。`src/map/scientificTiles.js` 将原瓦片经网格重投影显示，保留原生数据分辨率、色值含义和后端请求格式；显示转换不生成新的科学观测值。
- 图像网格使用共享边界和抗锯齿覆盖合成，避免三角拼接处出现透明细缝。分类色值采用最近邻图像采样，不对数据值插值。

这些转换是网页地图的显示适配，不是测绘控制点精度鉴定。实际研究需核查源数据的基准、定位精度与空间分辨率。当前后台未提供正式土壤专题瓦片，因此真实专题的完整内容与控制点精度仍待数据可用后核验。

## 天地图配置

在[天地图开发者平台](https://console.tianditu.gov.cn/)申请浏览器端应用 Key，设置 `VITE_MAP_PROVIDER=tianditu` 和 `VITE_TIANDITU_KEY`。未配置时不发起底图请求。

官方 WMTS 服务地址采用 HTTPS 的 `t0` 至 `t7.tianditu.gov.cn`，矩阵为 `TILEMATRIXSET=w`。标准地图组合 `vec_w` / `cva_w`，卫星影像组合 `img_w` / `cia_w`；地名注记置于专题和参考分区上方，不拦截点选。天地图模式使用原有 WGS84 Web Mercator 显示框架，具体大地基准差异仍按数据元信息核验。接口入口见[地图服务说明](https://lbs.tianditu.gov.cn/server/MapService.html)。尚未取得本项目天地图 Key，其线上鉴权和真实底图不在当前验证结论内。

## 版图与验收

保留实际服务提供的 Logo、来源、版权和审图等信息，不自行编造审图号。中国地图内容以官方来源为依据，要求参见[自然资源部《公开地图内容表示规范》](https://www.mfa.gov.cn/web/wjb_673085/zzjg_673183/bjhysws_674671/bhflfg/dtdmxgfl/202303/P020230313585504979937.pdf)。采用官方底图不自动证明专题、附加边界和整个网站已完成审查；公开展示前核对具体成图。

验收区分真实底图和模拟数据：高德底图在实际服务上检查标准/卫星切换、缩放、返回页面、标记和来源标识；合成梯度瓦片仅用于检查重投影的颜色取样与透明接缝，不作为真实土壤数据验证。相关浏览器证据保存在本地忽略的 `frontend/audit/` 目录。
