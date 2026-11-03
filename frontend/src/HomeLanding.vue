<template>
  <div class="landing-shell">
    <section class="landing-hero" aria-labelledby="landing-title">
      <img class="landing-photo" src="/hero-field.jpg" alt="" aria-hidden="true" width="1024" height="1024" fetchpriority="high" />
      <div class="landing-shade" aria-hidden="true"></div>

      <header class="landing-header">
        <div class="landing-brand" aria-label="壤脉天玑首页">
          <span class="landing-brand-mark" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none"><path d="M4 20c4-9 10-14 17-14 8 0 14 6 15 14-1 8-7 14-15 14C14 34 8 29 4 20Z"/><path d="M10 20c3-6 7-9 12-9 5 0 9 4 10 9-1 5-5 9-10 9Z"/><path d="M16 20c2-2 4-4 7-4s5 2 6 4c-1 3-3 5-6 5s-5-2-7-5Z"/></svg></span>
          <span><strong>壤脉天玑</strong><small>SOILMATE</small></span>
        </div>
        <nav class="landing-nav" aria-label="首页导航">
          <button type="button" @click="emit('navigate', 'explore')">空间探索</button>
          <button type="button" @click="emit('navigate', 'gold')">数据资源</button>
          <button type="button" @click="emit('navigate', 'assessment')">健康评价</button>
        </nav>
        <a class="landing-account" :href="account ? '/analysis' : '/account/index.html?next=/analysis'">{{ account ? '分析中心' : '登录 / 注册' }} <span aria-hidden="true">↗</span></a>
      </header>

      <div class="landing-content">
        <span class="landing-eyebrow"><span class="landing-eyebrow-line"></span> 土壤数据与健康研究</span>
        <h1 id="landing-title">读懂土地，<br /><em>看见土壤的脉络。</em></h1>
        <p>探索土壤数据，开启地块健康研究。</p>
        <div class="landing-actions">
          <button class="landing-primary" type="button" @click="emit('navigate', 'explore')">探索土壤数据 <span aria-hidden="true">↗</span></button>
          <button class="landing-secondary" type="button" @click="emit('navigate', 'assessment')">开始检测评估 <span aria-hidden="true">→</span></button>
        </div>
      </div>

      <div class="landing-bottom">
        <div class="landing-note"><span class="landing-note-dot"></span><span>探索 · 数据 · 评估</span></div>
        <span class="landing-scroll">向下了解平台 <span aria-hidden="true">↓</span></span>
      </div>
    </section>

    <section class="landing-modules" aria-labelledby="modules-title">
      <div class="landing-section-head"><h2 id="modules-title">从数据到研究</h2><span>选择你的起点</span></div>
      <div class="landing-card-grid">
        <button class="landing-card" type="button" @click="emit('navigate', 'explore')"><span class="landing-card-index">01 / 空间</span><span class="landing-card-icon" aria-hidden="true">◎</span><strong>空间探索</strong><span class="landing-card-copy">在地图上发现土壤指标与空间分布。</span><span class="landing-card-link">进入空间探索 <b aria-hidden="true">↗</b></span></button>
        <button class="landing-card" type="button" @click="emit('navigate', 'gold')"><span class="landing-card-index">02 / 数据</span><span class="landing-card-icon" aria-hidden="true">▦</span><strong>数据资源</strong><span class="landing-card-copy">查找指标，核对来源与网格记录。</span><span class="landing-card-link">浏览现有数据 <b aria-hidden="true">↗</b></span></button>
        <button class="landing-card" type="button" @click="emit('navigate', 'assessment')"><span class="landing-card-index">03 / 评估</span><span class="landing-card-icon" aria-hidden="true">◌</span><strong>健康评估</strong><span class="landing-card-copy">录入检测数据，查看研究估算。</span><span class="landing-card-link">开始检测评估 <b aria-hidden="true">↗</b></span></button>
        <div class="landing-card landing-card-planned"><span class="landing-card-index">04 / 知识</span><span class="landing-card-icon" aria-hidden="true">✳</span><strong>知识库与工具</strong><span class="landing-card-copy">土壤知识与实用工具。</span><span class="landing-card-status">规划中</span></div>
      </div>
    </section>
    <footer class="landing-footer"><strong>壤脉天玑</strong><span>SOILMATE</span><button type="button" @click="emit('navigate', 'explore')">进入地图 ↗</button></footer>
  </div>
</template>

<script setup>
defineProps({ account: { type: Object, default: null } })
const emit = defineEmits(['navigate'])
</script>

<style scoped>
.landing-shell{min-height:100dvh;background:#f4f6f1;color:#213c2d;font-family:var(--font-ui)}
.landing-hero{--page-inset:clamp(24px,5vw,80px);position:relative;isolation:isolate;display:flex;flex-direction:column;min-height:min(880px,calc(100dvh - 32px));margin:16px;overflow:hidden;border-radius:24px;background:#1f3b2c;color:white}
.landing-photo,.landing-shade{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.landing-photo{z-index:-2;object-fit:cover;object-position:center 57%}
.landing-shade{z-index:-1;background:linear-gradient(90deg,#0a1f16b8,#0a1f164d 58%,#0a1f160d),linear-gradient(0deg,#081d138a,transparent 55%)}
.landing-header{display:flex;align-items:center;justify-content:space-between;gap:24px;width:calc(100% - 2 * var(--page-inset));max-width:1280px;margin:24px auto 0;padding:8px 8px 8px 20px;border:1px solid #ffffffa8;border-radius:999px;background:#fffffff2;color:#213c2d}
.landing-brand{display:flex;align-items:center;gap:10px;min-width:160px;text-align:left}.landing-brand-mark{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:#e9f3e8}.landing-brand-mark svg{width:28px;height:28px;stroke:#286747;stroke-width:1.2}.landing-brand strong,.landing-brand small{display:block}.landing-brand strong{font-size:18px;font-weight:600}.landing-brand small{margin-top:2px;color:#65796b;font-size:10px;letter-spacing:.12em}
.landing-nav{display:flex;align-items:center;justify-content:center;gap:4px}.landing-nav button{min-height:44px;padding:0 20px;border:0;border-radius:999px;background:transparent;color:#455e4c;font:600 14px var(--font-ui);cursor:pointer;white-space:nowrap}.landing-nav button:hover{background:#eaf2e8;color:#245e3d}
.landing-account{display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:46px;padding:0 22px;border-radius:999px;background:#286747;color:white;text-decoration:none;font-size:14px;white-space:nowrap}.landing-account:hover{background:#1d5336}
.landing-content{width:calc(100% - 2 * var(--page-inset));max-width:1280px;margin:auto auto 0;padding:100px 0 32px}.landing-eyebrow{display:flex;align-items:center;gap:14px;color:#e1eddf;font-size:14px}.landing-eyebrow-line{width:32px;height:1px;background:#c5dfc4}
.landing-content h1{max-width:920px;margin:24px 0;font:500 clamp(44px,5.5vw,84px)/1.24 var(--font-display);letter-spacing:-.035em}.landing-content h1 em{color:#e3efdc;font-style:normal}.landing-content p{margin:0;color:#e7efe4;font-size:17px;line-height:1.8}
.landing-actions{display:flex;gap:12px;margin-top:36px}.landing-actions button{display:flex;align-items:center;justify-content:space-between;gap:36px;min-width:200px;min-height:54px;padding:0 24px;border:1px solid transparent;border-radius:999px;font:600 14px var(--font-ui);cursor:pointer;transition:background .2s,transform .2s}.landing-actions button:hover{transform:translateY(-2px)}.landing-primary{background:#f4f6ee;color:#254a34}.landing-primary:hover{background:white}.landing-actions .landing-secondary{border-color:#ffffff80;background:#163d2826;color:white}.landing-secondary:hover{background:#ffffff1a}
.landing-bottom{display:flex;align-items:center;justify-content:space-between;gap:16px;width:calc(100% - 2 * var(--page-inset));max-width:1280px;margin:0 auto;padding:64px 0 28px;color:#e0eadd;font-size:12px}.landing-note{display:flex;align-items:center;gap:10px}.landing-note-dot{width:6px;height:6px;border-radius:50%;background:#c4dfb9}.landing-scroll{display:flex;gap:16px}
.landing-modules{width:calc(100% - 32px - 2 * clamp(24px,5vw,80px));max-width:1280px;margin:auto;padding:88px 0}.landing-section-head{display:flex;align-items:baseline;justify-content:space-between;gap:24px;margin-bottom:32px}.landing-section-head h2{margin:0;font:500 clamp(28px,3vw,42px)/1.3 var(--font-display);letter-spacing:-.025em}.landing-section-head>span{color:#617367;font-size:14px}
.landing-card-grid{display:grid;grid-template-columns:1.3fr 1fr 1fr;grid-template-rows:1fr auto;gap:16px}.landing-card{display:flex;flex-direction:column;align-items:flex-start;min-width:0;min-height:290px;padding:28px;border:1px solid #dfe6db;border-radius:18px;background:#fff;color:#213c2d;text-align:left;font-family:inherit;cursor:pointer;transition:background .2s,border-color .2s}.landing-card:not(.landing-card-planned):hover{border-color:#9db79f;background:#f8fbf5}.landing-card:first-child{grid-row:1/3;padding:28px;background:#e7eee2 url('./assets/contours.svg') right center/auto 110% no-repeat}.landing-card-index{color:#586f5d;font-size:12px}.landing-card-icon{display:grid;place-items:center;width:44px;height:44px;margin:32px 0 20px;border:1px solid #dae6d8;border-radius:12px;background:#f1f6ed;color:#356846;font-size:27px;line-height:1}.landing-card:first-child .landing-card-icon{margin-top:32px}.landing-card strong{font:500 26px/1.3 var(--font-display)}.landing-card:first-child strong{font-size:26px}.landing-card-copy{margin-top:12px;color:#5b6e60;font-size:14px;line-height:1.7}.landing-card-link{display:flex;justify-content:space-between;align-items:center;gap:16px;width:100%;margin-top:auto;padding-top:36px;color:#2b6643;font-size:13px;font-weight:600}.landing-card-link b{font-size:20px;font-weight:400}
.landing-card-planned{grid-column:2/4;display:grid;grid-template-columns:1fr auto;gap:8px 20px;min-height:0;padding:22px 28px;background:transparent;cursor:default}.landing-card-planned .landing-card-index,.landing-card-planned .landing-card-icon{display:none}.landing-card-planned strong{font:600 15px var(--font-ui)}.landing-card-planned .landing-card-copy{margin:0;font-size:13px}.landing-card-status{grid-column:2;grid-row:1/3;align-self:center;padding:7px 12px;border:1px solid #dbe4d7;border-radius:999px;color:#5e7263;font-size:12px}
.landing-footer{display:flex;align-items:center;gap:20px;padding:24px max(calc(16px + clamp(24px,5vw,80px)),calc((100vw - 1280px)/2));border-top:1px solid #dfe6db;color:#65786b;font-size:12px}.landing-footer strong{color:#294b34;font-size:16px}.landing-footer button{margin-left:auto;padding:10px 0 10px 20px;border:0;background:transparent;color:#2e6946;font:600 13px var(--font-ui);cursor:pointer}.landing-shell :is(button,a):focus-visible{outline:3px solid #a9cfad;outline-offset:4px}
@media(max-width:1000px){.landing-header{gap:12px;padding-left:14px}.landing-brand{min-width:0}.landing-nav button{padding:0 12px}.landing-account{padding:0 16px;gap:16px}.landing-card{padding:24px}.landing-card:first-child{padding:24px}}
@media(max-width:700px){
.landing-hero{--page-inset:24px;min-height:max(700px,calc(100svh - 16px));margin:8px;border-radius:20px}.landing-photo{object-position:58% center}.landing-shade{background:linear-gradient(0deg,#0b2515bf,#0b25151a),linear-gradient(90deg,#0b251573,transparent)}
.landing-header{width:calc(100% - 32px);flex-wrap:wrap;gap:8px;margin-top:16px;padding:10px;border-radius:22px}.landing-brand{flex:1;gap:8px}.landing-brand strong{font-size:16px}.landing-brand-mark{width:32px;height:32px}.landing-brand small{font-size:9px}.landing-account{min-height:40px;padding:0 14px;font-size:12px}.landing-nav{order:3;width:100%;justify-content:space-between;padding-top:6px;border-top:1px solid #e3e9df}.landing-nav button{flex:1;min-height:38px;padding:0 6px;font-size:13px}
.landing-content{padding:76px 0 12px}.landing-content h1{margin:22px 0;font-size:clamp(36px,8.7vw,58px);line-height:1.3}.landing-content p{font-size:15px}.landing-eyebrow{font-size:12px}.landing-actions{flex-direction:column;gap:10px;margin-top:28px}.landing-actions button{min-width:0;min-height:50px;padding:0 22px}.landing-bottom{padding:42px 0 24px}.landing-scroll{display:none}
.landing-modules{width:calc(100% - 48px);padding:56px 0}.landing-section-head{display:block;margin-bottom:24px}.landing-section-head>span{display:block;margin-top:10px;font-size:13px}.landing-card-grid{grid-template-columns:1fr;grid-template-rows:auto;gap:12px}.landing-card,.landing-card:first-child{grid-row:auto;min-height:260px;padding:26px}.landing-card:first-child .landing-card-icon{margin-top:32px}.landing-card:first-child strong{font-size:28px}.landing-card-planned{grid-column:auto;min-height:0;padding:22px 26px}.landing-footer{flex-wrap:wrap;gap:12px;padding:20px 24px}.landing-footer button{font-size:12px}}
@media(prefers-reduced-motion:reduce){.landing-shell *{transition:none!important}}
</style>
