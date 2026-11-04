<template>
  <div ref="landingRoot" class="landing-shell">
    <SiteHeader home active="home" :account="account" @navigate="emit('navigate', $event)" @logout="emit('logout')" />
    <section class="landing-hero" aria-labelledby="landing-title">
      <img class="landing-photo" src="/hero-field.jpg" alt="" aria-hidden="true" width="1024" height="1024" fetchpriority="high" />
      <div class="landing-shade" aria-hidden="true"></div>


      <div class="landing-content">
        <span class="landing-eyebrow"><span class="landing-eyebrow-line"></span> 土壤数据与健康研究</span>
        <h1 id="landing-title">读懂土地，<br /><em>看见土壤的脉络。</em></h1>
        <p>探索土壤数据，开启地块健康研究。</p>
        <div class="landing-actions">
          <button class="landing-primary" type="button" @click="emit('navigate', 'explore')">探索土壤数据 <span aria-hidden="true">↗</span></button>
          <button class="landing-secondary" type="button" @click="emit('navigate', 'assessment')">开始检测评估 <span aria-hidden="true">→</span></button>
        </div>
      </div>

    </section>

    <section class="landing-modules" aria-labelledby="modules-title">
      <div class="landing-section-head" data-reveal><h2 id="modules-title">从数据到研究</h2></div>
      <div class="landing-card-grid">
        <button class="landing-card" data-reveal type="button" @click="emit('navigate', 'explore')"><span class="landing-card-icon" aria-hidden="true"><WorkspaceIcon name="map" /></span><strong>空间探索</strong><span class="landing-card-copy">查看指标与空间分布。</span><span class="landing-card-link">进入空间探索 <WorkspaceIcon name="arrow" /></span></button>
        <button class="landing-card" data-reveal type="button" @click="emit('navigate', 'gold')"><span class="landing-card-icon" aria-hidden="true"><WorkspaceIcon name="database" /></span><strong>数据资源</strong><span class="landing-card-copy">查找指标，核对来源。</span><span class="landing-card-link">浏览现有数据 <WorkspaceIcon name="arrow" /></span></button>
        <button class="landing-card" data-reveal type="button" @click="emit('navigate', 'assessment')"><span class="landing-card-icon" aria-hidden="true"><WorkspaceIcon name="flask" /></span><strong>健康研究</strong><span class="landing-card-copy">录入检测数据，开展研究。</span><span class="landing-card-link">开始检测评估 <WorkspaceIcon name="arrow" /></span></button>
        <button class="landing-card" data-reveal type="button" @click="emit('navigate', 'tools')"><span class="landing-card-icon" aria-hidden="true"><WorkspaceIcon name="calculator" /></span><strong>工具中心</strong><span class="landing-card-copy">土壤计算与常用工具。</span><span class="landing-card-link">查找与使用工具<WorkspaceIcon name="arrow" /></span></button>
      </div>
    </section>
    <section v-if="account" class="landing-recent" aria-labelledby="recent-title">
      <div class="landing-section-head recent-head"><h2 id="recent-title">最近研究任务</h2><button type="button" class="recent-more" @click="emit('navigate', 'assessment')">进入健康研究 <WorkspaceIcon name="arrow" /></button></div>
      <p v-if="recentLoading" class="recent-state">正在读取已保存任务…</p>
      <p v-else-if="recentError" class="recent-state">任务记录暂不可用，稍后重试。</p>
      <p v-else-if="!recentTasks.length" class="recent-state">完成一次健康评价后，任务状态会显示在这里。</p>
      <ul v-else class="recent-list">
        <li v-for="run in recentTasks" :key="run.id">
          <span class="recent-copy"><b>{{ run.kind === 'assessment' ? '土壤健康评价' : run.kind === 'nshi' ? '土壤指标筛选' : 'KO 通路结构分析' }}</b><small>{{ run.project_name }} · {{ run.dataset_id }}</small></span>
          <em class="recent-status" :class="`recent-status-${run.status}`">{{ statusLabel(run.status) }}</em>
        </li>
      </ul>
    </section>
    <footer class="landing-footer"><strong>沃壤知行</strong><a class="font-credit" href="/assets/fonts/harmonyos/LICENSE.txt" target="_blank" rel="noopener">字体 HarmonyOS Sans</a><button type="button" @click="emit('navigate', 'explore')">进入地图 ↗</button></footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { revealOnScroll, attachScrollResponse } from './design-system/motion.js'
import SiteHeader from './SiteHeader.vue'
import WorkspaceIcon from './WorkspaceIcon.vue'
defineProps({ account: { type: Object, default: null }, recentTasks: { type: Array, default: () => [] }, recentLoading: { type: Boolean, default: false }, recentError: { type: String, default: '' } })
const statusLabel = status => ({ queued: '排队中', running: '分析中', completed: '已完成', partial: '有限结果', failed: '未完成', interrupted: '已中断', raw_data: '仅原始数据', exploratory_assessment: '探索性评价', validated_assessment: '经验证评价', insufficient_data: '数据不足' })[status] || status || '状态未登记'
const emit = defineEmits(['navigate', 'logout'])
const landingRoot = ref(null)
let stopReveal, stopScroll
onMounted(() => {
  stopReveal = revealOnScroll(landingRoot.value)
  stopScroll = attachScrollResponse(landingRoot.value.closest('.site-content-home'), landingRoot.value)
})
onBeforeUnmount(() => { stopReveal?.(); stopScroll?.() })
</script>

<style scoped>
.landing-shell{min-height:100vh;box-sizing:border-box;padding:var(--site-frame-top) var(--site-frame-inline) var(--site-frame-bottom);background:var(--site-frame-color);color:#21362b;font-family:var(--font-ui)}
.landing-hero{position:relative;isolation:isolate;display:flex;flex-direction:column;min-height:calc(100dvh - var(--site-frame-top) - var(--site-frame-bottom) - var(--site-header-height) - var(--site-frame-gap));margin:0;overflow:hidden;border-radius:var(--site-surface-radius);background:#1f3b2c;color:#fff}
.landing-photo,.landing-shade{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.landing-photo{z-index:-2;object-fit:cover;object-position:center 58%}
.landing-shade{z-index:-1;background:linear-gradient(90deg,rgba(10,31,22,.78) 0%,rgba(10,31,22,.43) 48%,rgba(10,31,22,.09) 100%),linear-gradient(0deg,rgba(8,29,19,.56),transparent 40%)}




.landing-content{width:min(1280px,calc(100% - 88px));margin:auto auto 0;padding:clamp(90px,14vh,160px) 0 40px}.landing-eyebrow{display:flex;align-items:center;gap:12px;color:#d3e9d5;font-size:var(--text-caption);font-weight:700;letter-spacing:.17em}.landing-eyebrow-line{width:30px;height:1px;background:#b9e0bc}.landing-content h1{max-width:850px;margin:24px 0 20px;font-size:clamp(2.875rem,6vw,5.6875rem);font-weight:600;line-height:1.16;letter-spacing:-.055em;text-wrap:balance}.landing-content h1 em{font-style:normal;color:#d8efdb}.landing-content p{max-width:580px;margin:0;color:#edf6ec;font-size:var(--text-item-title);line-height:1.8;text-wrap:pretty}.landing-actions{display:flex;flex-wrap:wrap;gap:13px;margin-top:34px}.landing-actions button{display:inline-flex;align-items:center;justify-content:space-between;gap:28px;min-height:55px;padding:0 22px;border-radius:999px;font-family:inherit;font-size:var(--text-body);font-weight:700;line-height:1;cursor:pointer;transition:transform .2s var(--motion-standard),background .2s var(--motion-standard)}.landing-actions button:hover{transform:translateY(-2px)}.landing-primary{min-width:203px;border:1px solid #2d8a57;background:#287b4e;color:#fff}.landing-primary:hover{background:#1f6b42}.landing-secondary{min-width:192px;border:1px solid rgba(255,255,255,.6);background:rgba(255,255,255,.11);color:#fff;backdrop-filter:blur(6px)}.landing-secondary:hover{background:rgba(255,255,255,.2)}
.landing-note{display:flex;align-items:center;gap:10px;padding:11px 15px;border:1px solid rgba(255,255,255,.25);border-radius:999px;background:rgba(12,37,23,.32);backdrop-filter:blur(8px)}.landing-note-dot{width:7px;height:7px;border-radius:50%;background:#b9e9b7;box-shadow:0 0 0 4px rgba(185,233,183,.18)}
.landing-modules{box-sizing:border-box;width:100%;margin:var(--site-frame-gap) auto 0;padding:80px max(32px,calc((100% - 1280px)/2)) 88px;border-radius:var(--site-surface-radius);background:#f4f6f1}.landing-section-head{display:flex;justify-content:space-between;align-items:end;gap:40px;margin-bottom:34px}.landing-section-kicker{color:#2b7550;font-size:var(--text-caption);font-weight:800;letter-spacing:.17em}.landing-section-head h2{max-width:660px;margin:14px 0 0;font-size:var(--text-page-title);line-height:var(--leading-title);letter-spacing:-.035em}.landing-section-head p{max-width:295px;margin:0 0 5px;color:#6b7b6f;font-size:var(--text-label);line-height:1.8}.landing-card-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.landing-card{display:flex;flex-direction:column;align-items:flex-start;min-height:278px;padding:25px;border:1px solid #dce5d9;border-radius:16px;background:#fff;color:#21362b;text-align:left;box-shadow:0 8px 30px rgba(27,55,34,.04);cursor:pointer;transition:transform .22s var(--motion-standard),box-shadow .22s var(--motion-standard),border-color .22s var(--motion-standard)}.landing-card:not(.landing-card-planned):hover{transform:translateY(-5px);border-color:#bdd7c4;box-shadow:0 18px 40px rgba(27,55,34,.09)}.landing-card-index{color:#819187;font-size:var(--text-caption);font-weight:700;letter-spacing:.15em}.landing-card-icon{display:grid;place-items:center;width:48px;height:48px;margin:22px 0 20px;border-radius:13px;background:#e9f4ea;color:#286747;font-size:27px;line-height:1}.landing-card strong{font-size:var(--text-panel-title);letter-spacing:-.02em}.landing-card-copy{margin-top:10px;color:#6d7c71;font-size:var(--text-caption);line-height:1.75}.landing-card-link,.landing-card-status{display:flex;justify-content:space-between;align-items:center;width:100%;margin-top:auto;padding-top:22px;color:#276c49;font-size:var(--text-caption);font-weight:800}.landing-card-link b{font-size:18px;font-weight:500}.landing-card-planned{cursor:default;background:#f8faf6}.landing-card-status{color:#809085}
.landing-footer{margin-top:var(--site-frame-gap);border-radius:var(--site-surface-radius);background:#f4f6f1;display:flex;align-items:center;gap:18px;padding:27px max(36px,calc((100vw - 1280px)/2));border-top:1px solid #dce5d9;color:#607165;font-size:var(--text-caption)}.landing-footer strong{color:#254631;font-size:var(--text-body)}.landing-footer button{margin-left:auto;border:0;background:none;color:#286747;font-family:inherit;font-size:var(--text-caption);font-weight:700;cursor:pointer}
.landing-footer .demo-entry{color:#286747;font-size:var(--text-caption);font-weight:700;text-decoration:none;border-bottom:1px dashed rgba(40,103,71,.35);padding-bottom:1px}
.landing-footer .demo-entry:hover{color:#1f5438;border-bottom-color:#286747}
.landing-footer .demo-entry{margin-left:auto}
.landing-footer .demo-entry + button{margin-left:18px}
.landing-shell :is(button,a):focus-visible{outline:3px solid #a9dbb4;outline-offset:3px}
.landing-content h1,.landing-section-head h2{font-family:var(--font-display);letter-spacing:-.025em}
.landing-card-grid{grid-template-columns:minmax(0,1.35fr) repeat(2,minmax(0,1fr));grid-template-rows:minmax(245px,auto) minmax(175px,auto)}
.landing-card:first-child{grid-row:1/3;min-height:440px;padding:34px;background:#e8f0e7 url('./assets/contours.svg') no-repeat 65% 65%/auto 110%}
.landing-card:first-child .landing-card-icon{width:68px;height:68px;margin:80px 0 28px;background:#f7fbf5;font-size:35px}
.landing-card:first-child strong{max-width:280px;font-size:var(--text-section-title);line-height:var(--leading-title)}
.landing-card:first-child .landing-card-copy{max-width:300px;font-size:var(--text-label)}
.landing-card:nth-child(4){grid-column:2/4;min-height:170px;background:#f8faf7}
.landing-card:nth-child(4) .landing-card-icon{margin:12px 0 10px}
.landing-card:nth-child(4) .landing-card-status{padding-top:8px}
@media(max-width:980px){.landing-content{width:calc(100% - 70px)}.landing-card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:980px){.landing-card-grid{grid-template-rows:auto}.landing-card:first-child{grid-row:auto;min-height:278px;padding:25px;background:#e8f0e7}.landing-card:first-child .landing-card-icon{width:48px;height:48px;margin:22px 0 20px;font-size:27px}.landing-card:first-child strong{font-size:var(--text-panel-title)}.landing-card:nth-child(4){grid-column:auto;min-height:278px}}
@media(max-width:700px){.landing-photo{object-position:57% center}.landing-shade{background:linear-gradient(0deg,rgba(9,29,19,.82),rgba(9,29,19,.24) 78%),linear-gradient(90deg,rgba(10,31,22,.3),transparent)}.landing-content{width:calc(100% - 40px);padding:48px 0 10px}.landing-eyebrow{font-size:var(--text-caption)}.landing-content h1{margin:20px 0 16px;font-size:clamp(2rem,9.5vw,2.5rem);line-height:1.3}.landing-content p{font-size:var(--text-body);line-height:1.75}.landing-actions{gap:10px;margin-top:26px}.landing-actions button{width:100%;min-height:50px}.landing-note{padding:9px 11px;font-size:var(--text-caption)}.landing-modules{width:100%;padding:48px 22px}.landing-section-head{display:block;margin-bottom:24px}.landing-section-head p{margin-top:14px}.landing-card-grid{grid-template-columns:1fr;gap:10px}.landing-card{min-height:220px}.landing-card-icon{margin:14px 0}.landing-footer{flex-wrap:wrap;padding:22px 18px}.landing-footer span{width:100%;order:3}}
@media(prefers-reduced-motion:reduce){.landing-shell *, .landing-shell *::before, .landing-shell *::after{scroll-behavior:auto!important;transition:none!important var(--motion-standard)}}

/* Same baseline, same family; the featured card is distinguished by its surface. */
.landing-eyebrow{font-size:var(--text-label);font-weight:500;letter-spacing:.02em}
.landing-content h1{font-weight:500;letter-spacing:-.04em;line-height:1.22}

.landing-section-head h2{margin:0;font-weight:500}
.landing-card,.landing-card:first-child{padding:28px;translate:0 var(--scroll-drift,0px)}
.landing-card .landing-card-icon,.landing-card:first-child .landing-card-icon{width:48px;height:48px;margin:8px 0 24px;font-size:28px}
.landing-card strong,.landing-card:first-child strong{font-size:var(--text-panel-title);font-weight:500;line-height:1.4}
.landing-card-copy,.landing-card:first-child .landing-card-copy{font-size:var(--text-body)}
.landing-card:nth-child(4){min-height:170px}
.landing-card:nth-child(4) .landing-card-icon{margin:8px 0 24px}
.landing-card{transition:transform 420ms var(--motion-pop),box-shadow 240ms var(--motion-standard),border-color 240ms var(--motion-standard)}
.landing-actions button{transition:transform 300ms var(--motion-pop),background 200ms var(--motion-standard)}
.landing-footer .font-credit{font-size:var(--text-caption)}
.landing-card-icon .workspace-icon{width:27px;height:27px}
.landing-card-link .workspace-icon{width:18px;height:18px}

.landing-recent{box-sizing:border-box;width:100%;margin:var(--site-frame-gap) auto 0;padding:34px max(32px,calc((100% - 1280px)/2)) 38px;border-radius:var(--site-surface-radius);background:#f4f6f1;color:#21362b}
.landing-recent .landing-section-head{margin-bottom:12px}
.landing-recent .landing-section-head h2{margin:0;font-size:var(--text-section-title)}
.recent-head{align-items:flex-end}
.recent-more{display:inline-flex;align-items:center;gap:8px;min-height:36px;padding:0;border:0;background:none;color:#286747;font:inherit;font-size:var(--text-caption);font-weight:700;cursor:pointer}
.recent-more:hover{color:#1f5438;text-decoration:underline;text-underline-offset:4px}
.recent-more:focus-visible{outline:3px solid #9ac5a5;outline-offset:3px;border-radius:4px}
.recent-state{margin:0;color:#7b8c7d;font-size:var(--text-body)}
.recent-list{list-style:none;margin:0;padding:0}
.recent-list li{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 0;border-top:1px solid #dfe8dc}
.recent-list li:last-child{padding-bottom:0}
.recent-copy{display:flex;flex-direction:column;gap:2px;min-width:0}
.recent-copy b{color:#2a4a34;font-size:13px}
.recent-copy small{color:#809184;font-size:11px}
.recent-status{display:inline-flex;align-items:center;gap:7px;color:#4f7a5e;font-size:11px;font-style:normal;white-space:nowrap}
.recent-status:before{content:'';width:6px;height:6px;border-radius:50%;background:#5fa678}
.recent-status-running:before,.recent-status-queued:before{background:#c69a4a}
.recent-status-failed:before,.recent-status-interrupted:before{background:#b4685c}
</style>
