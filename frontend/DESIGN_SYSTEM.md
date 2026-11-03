# Soilmate 统一视觉与动效

## 结构与导航

沿用上游共享的 `src/SiteHeader.vue`、`src/siteNavigation.js` 和 `src/site-shell.css`。页面切换保留同一套导航入口、当前状态、账号操作和外框尺寸；模块工具放在内容区。上游品牌名称与路由保持原样。

## 字体

正文、标题、按钮、表单和数字统一使用 HarmonyOS Sans SC。`public/assets/design-system/typography.css` 是字号、行高和字族的入口；`--font-display` 与 `--font-ui` 指向相同字族。真正的代码和序列保留等宽字体。

字体来自[华为官方设计资源](https://developer.huawei.com/consumer/cn/design/resource-V1)的[原始字体包](https://developer.huawei.com/images/download/general/HarmonyOS-Sans.zip)。本项目使用未修改的 Regular、Medium 和 Bold TTF，不转换格式、不裁剪字形。字体文件及原始许可位于 `public/assets/fonts/harmonyos/`，页面页脚提供字体使用声明与许可链接。

## 动效

统一规则位于 `public/assets/design-system/motion.css`；滚动揭示与轻量响应位于 `src/design-system/motion.js`。

| 用途 | 当前实现 |
| --- | --- |
| 工作区进入 | 560 ms；从下方 18 px 进入，轻微越过目标 3 px 后归位 |
| 抽屉展开 | 560 ms，`cubic-bezier(.2,.9,.24,1.18)`，一次轻微过冲 |
| 抽屉退出 | 380 ms，`cubic-bezier(.4,0,.8,.2)` |
| 滚动进入 | 620 ms；进入可见范围时揭示一次，完成后恢复普通静态布局 |
| 滚动响应 | 保留原生滚动；首页卡片追随不超过 8 px 的目标偏移，欠阻尼响应自然收稳 |
| 按下反馈 | 控件短暂缩到 97%，松开后回正 |

贝塞尔过冲和物理弹簧分别命名，不混称。导航、地图、数据读数不随页面卡片漂移。动效结束后不保留额外 transform 层；动画帧、监听和观察器在停止、隐藏或卸载时清理。`prefers-reduced-motion` 直接展示静态终态。

## 文字与验收

标题负责定位，控件名称负责说明操作。删除重复中英标签、常驻操作步骤和填空白的说明；保留单位、来源、质量状态与影响结果解释的条件。补充方法用详情展开。

以桌面网页为主要验收对象。核对共享导航、页面边线、字体真实加载、动画的过冲与归位、原生滚动、反复打开和减少动态效果。构建通过与用户视觉认可分别记录。

动效原则参考本地 Wiki 的动效与艺术规范；未使用其插画、图标、水景或其他素材。
