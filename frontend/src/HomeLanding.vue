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
        <a class="landing-account" :href="account ? '/assessment' : '/account/index.html?next=/assessment'">{{ account ? '健康评价' : '登录 / 注册' }} <span aria-hidden="true">↗</span></a>
      </header>

      <div class="landing-content">
        <span class="landing-eyebrow"><span class="landing-eyebrow-line"></span> SOIL INTELLIGENCE · 土壤数据平台</span>
        <h1 id="landing-title">读懂土地，<br /><em>看见土壤的脉络。</em></h1>
        <p>从全国土壤空间数据出发，探索指标、核对来源，并为地块检测建立可追溯的研究路径。</p>
        <div class="landing-actions">
          <button class="landing-primary" type="button" @click="emit('navigate', 'explore')">探索土壤数据 <span aria-hidden="true">↗</span></button>
          <button class="landing-secondary" type="button" @click="emit('navigate', 'assessment')">开始检测评估 <span aria-hidden="true">→</span></button>
        </div>
      </div>

      <div class="landing-bottom">
        <div class="landing-note"><span class="landing-note-dot"></span><span>研究平台 · 数据与评价结果按证据状态展示</span></div>
        <span class="landing-scroll">向下了解平台 <span aria-hidden="true">↓</span></span>
      </div>
    </section>

    <section class="landing-modules" aria-labelledby="modules-title">
      <div class="landing-section-head"><div><span class="landing-section-kicker">从数据到理解</span><h2 id="modules-title">四条路径，一套可追溯的土壤工作流</h2></div><p>选择需要完成的任务。每项数据和分析都保留来源、适用范围与当前状态。</p></div>
      <div class="landing-card-grid">
        <button class="landing-card" type="button" @click="emit('navigate', 'explore')"><span class="landing-card-index">MAP EXPLORER</span><span class="landing-card-icon" aria-hidden="true">◎</span><strong>全域数据探索</strong><span class="landing-card-copy">在地图上查看指标图层、空间覆盖和点位数据。</span><span class="landing-card-link">进入空间探索 <b aria-hidden="true">↗</b></span></button>
        <button class="landing-card" type="button" @click="emit('navigate', 'gold')"><span class="landing-card-index">DATA PRODUCTS</span><span class="landing-card-icon" aria-hidden="true">▦</span><strong>数据资源中心</strong><span class="landing-card-copy">浏览指标目录与网格记录，核对字段和数据来源。</span><span class="landing-card-link">浏览现有数据 <b aria-hidden="true">↗</b></span></button>
        <button class="landing-card" type="button" @click="emit('navigate', 'assessment')"><span class="landing-card-index">ASSESSMENT</span><span class="landing-card-icon" aria-hidden="true">◌</span><strong>土壤健康研究评估</strong><span class="landing-card-copy">录入检测值或导入表格，查看研究估算与限制说明。</span><span class="landing-card-link">开始检测评估 <b aria-hidden="true">↗</b></span></button>
        <div class="landing-card landing-card-planned"><span class="landing-card-index">KNOWLEDGE & TOOLS</span><span class="landing-card-icon" aria-hidden="true">✳</span><strong>知识库与工具</strong><span class="landing-card-copy">土壤概念、指标解释与实用工具正在整理。</span><span class="landing-card-status">规划中</span></div>
      </div>
    </section>
    <footer class="landing-footer"><strong>壤脉天玑</strong><span>SOILMATE · 让每一步判断都有来源</span><button type="button" @click="emit('navigate', 'explore')">返回地图 ↗</button></footer>
  </div>
</template>

<script setup>
defineProps({ account: { type: Object, default: null } })
const emit = defineEmits(['navigate'])
</script>

<style scoped>
.landing-shell{min-height:100vh;background:#f4f6f1;color:#21362b;font-family:'DengXian','PingFang SC','Microsoft YaHei UI',sans-serif}
.landing-hero{position:relative;isolation:isolate;display:flex;flex-direction:column;min-height:min(880px,calc(100dvh - 28px));margin:14px;overflow:hidden;border-radius:24px;background:#1f3b2c;color:#fff}
.landing-photo,.landing-shade{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.landing-photo{z-index:-2;object-fit:cover;object-position:center 58%}
.landing-shade{z-index:-1;background:linear-gradient(90deg,rgba(10,31,22,.78) 0%,rgba(10,31,22,.43) 48%,rgba(10,31,22,.09) 100%),linear-gradient(0deg,rgba(8,29,19,.56),transparent 40%)}
.landing-header{display:flex;align-items:center;gap:24px;width:min(1280px,calc(100% - 88px));margin:28px auto 0;padding:8px 10px 8px 22px;border:1px solid rgba(255,255,255,.7);border-radius:999px;background:rgba(255,255,255,.94);box-shadow:0 14px 46px rgba(5,29,15,.18);color:#22382b}
.landing-brand{display:flex;align-items:center;gap:10px;min-width:190px;color:inherit;text-align:left}.landing-brand-mark{display:grid;place-items:center;width:36px;height:36px;border-radius:50%;background:#e9f3e8}.landing-brand-mark svg{width:27px;height:27px;stroke:#286747;stroke-width:1.2}.landing-brand strong,.landing-brand small{display:block}.landing-brand strong{font-size:17px;letter-spacing:.02em}.landing-brand small{margin-top:1px;color:#75877b;font-size:9px;letter-spacing:.2em}
.landing-nav{display:flex;justify-content:center;gap:3px;flex:1}.landing-nav button{padding:12px 18px;border:0;border-radius:999px;background:transparent;color:#465b4c;font-family:inherit;font-size:13px;font-weight:600;line-height:1.2;white-space:nowrap;cursor:pointer}.landing-nav button:hover{background:#eef5ee;color:#195936}
.landing-account{display:flex;align-items:center;justify-content:center;gap:16px;min-height:44px;padding:0 20px;border-radius:999px;background:#216741;color:#fff;text-decoration:none;font-size:13px;font-weight:700;white-space:nowrap}.landing-account:hover{background:#175331}
.landing-content{width:min(1280px,calc(100% - 88px));margin:auto auto 0;padding:clamp(90px,14vh,160px) 0 40px}.landing-eyebrow{display:flex;align-items:center;gap:12px;color:#d3e9d5;font-size:11px;font-weight:700;letter-spacing:.17em}.landing-eyebrow-line{width:30px;height:1px;background:#b9e0bc}.landing-content h1{max-width:850px;margin:24px 0 20px;font-size:clamp(46px,6vw,91px);font-weight:600;line-height:1.16;letter-spacing:-.055em;text-wrap:balance}.landing-content h1 em{font-style:normal;color:#d8efdb}.landing-content p{max-width:580px;margin:0;color:#edf6ec;font-size:clamp(15px,1.35vw,18px);line-height:1.9;text-wrap:pretty}.landing-actions{display:flex;flex-wrap:wrap;gap:13px;margin-top:34px}.landing-actions button{display:inline-flex;align-items:center;justify-content:space-between;gap:28px;min-height:55px;padding:0 22px;border-radius:999px;font-family:inherit;font-size:14px;font-weight:700;line-height:1;cursor:pointer;transition:transform .2s,background .2s}.landing-actions button:hover{transform:translateY(-2px)}.landing-primary{min-width:203px;border:1px solid #2d8a57;background:#287b4e;color:#fff}.landing-primary:hover{background:#1f6b42}.landing-secondary{min-width:192px;border:1px solid rgba(255,255,255,.6);background:rgba(255,255,255,.11);color:#fff;backdrop-filter:blur(6px)}.landing-secondary:hover{background:rgba(255,255,255,.2)}
.landing-bottom{display:flex;align-items:center;justify-content:space-between;width:min(1280px,calc(100% - 88px));margin:0 auto;padding:68px 0 28px;color:#ecf4e9;font-size:12px}.landing-note{display:flex;align-items:center;gap:10px;padding:11px 15px;border:1px solid rgba(255,255,255,.25);border-radius:999px;background:rgba(12,37,23,.32);backdrop-filter:blur(8px)}.landing-note-dot{width:7px;height:7px;border-radius:50%;background:#b9e9b7;box-shadow:0 0 0 4px rgba(185,233,183,.18)}.landing-scroll{letter-spacing:.08em}
.landing-modules{width:min(1280px,calc(100% - 72px));margin:0 auto;padding:100px 0 108px}.landing-section-head{display:flex;justify-content:space-between;align-items:end;gap:40px;margin-bottom:34px}.landing-section-kicker{color:#2b7550;font-size:11px;font-weight:800;letter-spacing:.17em}.landing-section-head h2{max-width:660px;margin:14px 0 0;font-size:clamp(29px,3.2vw,46px);line-height:1.25;letter-spacing:-.035em}.landing-section-head p{max-width:295px;margin:0 0 5px;color:#6b7b6f;font-size:13px;line-height:1.8}.landing-card-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.landing-card{display:flex;flex-direction:column;align-items:flex-start;min-height:278px;padding:25px;border:1px solid #dce5d9;border-radius:16px;background:#fff;color:#21362b;text-align:left;box-shadow:0 8px 30px rgba(27,55,34,.04);cursor:pointer;transition:transform .22s,box-shadow .22s,border-color .22s}.landing-card:not(.landing-card-planned):hover{transform:translateY(-5px);border-color:#bdd7c4;box-shadow:0 18px 40px rgba(27,55,34,.09)}.landing-card-index{color:#819187;font-size:10px;font-weight:700;letter-spacing:.15em}.landing-card-icon{display:grid;place-items:center;width:48px;height:48px;margin:22px 0 20px;border-radius:13px;background:#e9f4ea;color:#286747;font-size:27px;line-height:1}.landing-card strong{font-size:19px;letter-spacing:-.02em}.landing-card-copy{margin-top:10px;color:#6d7c71;font-size:12px;line-height:1.75}.landing-card-link,.landing-card-status{display:flex;justify-content:space-between;align-items:center;width:100%;margin-top:auto;padding-top:22px;color:#276c49;font-size:12px;font-weight:800}.landing-card-link b{font-size:18px;font-weight:500}.landing-card-planned{cursor:default;background:#f8faf6}.landing-card-status{color:#809085}
.landing-footer{display:flex;align-items:center;gap:18px;padding:27px max(36px,calc((100vw - 1280px)/2));border-top:1px solid #dce5d9;color:#607165;font-size:11px}.landing-footer strong{color:#254631;font-size:15px}.landing-footer button{margin-left:auto;border:0;background:none;color:#286747;font-family:inherit;font-size:12px;font-weight:700;cursor:pointer}
.landing-shell :is(button,a):focus-visible{outline:3px solid #a9dbb4;outline-offset:3px}
.landing-content h1,.landing-section-head h2{font-family:Georgia,'STSong','Songti SC','Noto Serif CJK SC','SimSun',serif;letter-spacing:-.025em}
.landing-card-grid{grid-template-columns:minmax(0,1.35fr) repeat(2,minmax(0,1fr));grid-template-rows:minmax(245px,auto) minmax(175px,auto)}
.landing-card:first-child{grid-row:1/3;min-height:440px;padding:34px;background:#e8f0e7 url('./assets/contours.svg') no-repeat 65% 65%/auto 110%}
.landing-card:first-child .landing-card-icon{width:68px;height:68px;margin:80px 0 28px;background:#f7fbf5;font-size:35px}
.landing-card:first-child strong{max-width:280px;font-size:29px;line-height:1.25}
.landing-card:first-child .landing-card-copy{max-width:300px;font-size:13px}
.landing-card:nth-child(4){grid-column:2/4;min-height:170px;background:#f8faf7}
.landing-card:nth-child(4) .landing-card-icon{margin:12px 0 10px}
.landing-card:nth-child(4) .landing-card-status{padding-top:8px}
@media(max-width:980px){.landing-header{width:calc(100% - 48px);gap:12px}.landing-brand{min-width:auto}.landing-nav button{padding-inline:10px}.landing-content,.landing-bottom{width:calc(100% - 70px)}.landing-card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:980px){.landing-card-grid{grid-template-rows:auto}.landing-card:first-child{grid-row:auto;min-height:278px;padding:25px;background:#e8f0e7}.landing-card:first-child .landing-card-icon{width:48px;height:48px;margin:22px 0 20px;font-size:27px}.landing-card:first-child strong{font-size:19px}.landing-card:nth-child(4){grid-column:auto;min-height:278px}}
@media(max-width:700px){.landing-hero{min-height:750px;min-height:calc(100dvh - 16px);margin:8px;border-radius:16px}.landing-photo{object-position:57% center}.landing-shade{background:linear-gradient(0deg,rgba(9,29,19,.82),rgba(9,29,19,.24) 78%),linear-gradient(90deg,rgba(10,31,22,.3),transparent)}.landing-header{width:calc(100% - 28px);margin-top:14px;padding:7px 7px 7px 12px;flex-wrap:wrap;border-radius:20px}.landing-brand{flex:1}.landing-brand strong{font-size:14px}.landing-brand-mark{width:31px;height:31px}.landing-nav{order:3;width:100%;justify-content:space-around;padding:4px 0 1px;border-top:1px solid #e9eee8}.landing-nav button{padding:9px 5px;font-size:11px}.landing-account{min-height:35px;padding:0 12px;font-size:11px}.landing-content{width:calc(100% - 38px);padding:70px 0 10px}.landing-eyebrow{font-size:9px}.landing-content h1{margin:20px 0 16px;font-size:clamp(40px,11vw,58px);line-height:1.2}.landing-content p{font-size:14px;line-height:1.75}.landing-actions{gap:10px;margin-top:26px}.landing-actions button{width:100%;min-height:50px}.landing-bottom{width:calc(100% - 38px);padding:35px 0 19px}.landing-note{padding:9px 11px;font-size:10px}.landing-scroll{display:none}.landing-modules{width:calc(100% - 32px);padding:66px 0}.landing-section-head{display:block;margin-bottom:24px}.landing-section-head p{margin-top:14px}.landing-card-grid{grid-template-columns:1fr;gap:10px}.landing-card{min-height:220px}.landing-card-icon{margin:14px 0}.landing-footer{flex-wrap:wrap;padding:22px 18px}.landing-footer span{width:100%;order:3}}
@media(prefers-reduced-motion:reduce){.landing-shell *, .landing-shell *::before, .landing-shell *::after{scroll-behavior:auto!important;transition:none!important}}
</style>



