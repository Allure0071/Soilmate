<template>
  <div ref="shell" class="demo-shell" role="application" aria-label="沃壤知行答辩演示模式">
    <header class="demo-topbar">
      <div class="demo-brand">
        <span class="demo-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.4">
            <circle cx="16" cy="16" r="11.4" />
            <ellipse cx="16" cy="16" rx="11.4" ry="5.2" transform="rotate(-24 16 16)" />
            <ellipse cx="16" cy="16" rx="5.2" ry="11.4" transform="rotate(-24 16 16)" />
            <circle cx="16" cy="16" r="1.7" fill="currentColor" stroke="none" />
          </svg>
        </span>
        <span class="demo-brand-copy"><strong>沃壤知行</strong><small>答辩演示模式</small></span>
      </div>
      <span class="demo-sim-badge"><i aria-hidden="true"></i>公开数据案例 · 规则计算</span>
      <div class="demo-scenario">
        <span class="demo-scenario-label">案例地块</span>
        <strong>{{ scenario.fieldName }}</strong>
        <span>{{ scenario.sampledAt }} · {{ scenario.depth }}</span>
      </div>
      <div class="demo-topbar-actions">
        <button type="button" class="demo-ghost" :aria-pressed="autoplay" @click="toggleAutoplay">{{ autoplay ? '暂停自动演示' : '自动播放' }}</button>
        <button type="button" class="demo-ghost" @click="restart">重新开始</button>
        <button type="button" class="demo-exit" @click="exitDemo">退出演示 <span aria-hidden="true">↗</span></button>
      </div>
    </header>

    <div class="demo-body">
      <nav class="demo-rail" aria-label="演示步骤">
        <p class="demo-rail-title">演示流程</p>
        <button
          v-for="(item, index) in steps"
          :key="item.id"
          type="button"
          class="demo-rail-step"
          :class="{ active: index === current, done: index < current }"
          :aria-current="index === current ? 'step' : undefined"
          @click="goTo(index)"
        >
          <span class="rail-no">{{ item.no }}</span>
          <span class="rail-copy"><b>{{ item.label }}</b><small>{{ item.short }}</small></span>
          <span class="rail-state" aria-hidden="true">{{ index < current ? '✓' : index === current ? '●' : '' }}</span>
        </button>
        <div class="demo-rail-note">
          <strong>演示边界</strong>
          <p>真实可跑：地图、数据资源、工具、录入核验、研究工作台审计报告。</p>
          <p>案例计算：N+X、评分区间、解释模板、多 Agent 流程；数据为公开区域预测值。</p>
        </div>
      </nav>

      <main class="demo-main">
        <div class="demo-stage">
          <transition name="demo-fade" mode="out-in">
            <section :key="currentStep.id" class="demo-step" :aria-labelledby="`demo-step-${currentStep.id}`">
              <p class="demo-kicker">{{ currentStep.no }} · 演示流程</p>
              <h1 :id="`demo-step-${currentStep.id}`" class="demo-title">{{ stepTitles[currentStep.id] }}</h1>
              <p class="demo-lead">{{ stepLeads[currentStep.id] }}</p>

              <!-- 01 场景与边界 -->
              <template v-if="currentStep.id === 'scene'">
                <div class="scene-grid">
                  <article class="panel field-card">
                    <span class="sim-tag">公开数据案例</span>
                    <h2>{{ scenario.fieldName }}</h2>
                    <dl class="field-meta">
                      <div><dt>区域</dt><dd>{{ scenario.region }}</dd></div>
                      <div><dt>作物</dt><dd>{{ scenario.crop }}</dd></div>
                      <div><dt>土层</dt><dd>{{ scenario.depth }}</dd></div>
                      <div><dt>数据版本</dt><dd>{{ scenario.sampledAt }}</dd></div>
                      <div><dt>数据来源</dt><dd class="mono">{{ scenario.lab }}</dd></div><div><dt>查询时间</dt><dd class="mono">{{ scenario.accessedAt }}</dd></div>
                      <div><dt>运行标识</dt><dd class="mono">{{ scenario.runId }}</dd></div>
                    </dl>
                  </article>
                  <article class="panel">
                    <span class="panel-kicker">案例输入</span>
                    <h2>6 项土壤属性</h2>
                    <ul class="input-chips">
                      <li v-for="item in indicators" :key="item.code"><b>{{ item.label }}</b><span>{{ item.value }} {{ item.unit }}</span></li>
                    </ul>
                    <p class="panel-note">数值来自 ISRIC SoilGrids 2.0（250 m，0–5 cm 区域预测值），查询 2026-11-04；不是本地实测。</p>
                  </article>
                  <article class="panel">
                    <span class="panel-kicker">演示目标</span>
                    <h2>一条完整证据链</h2>
                    <ol class="goal-list">
                      <li><b>N+X 选测</b><span>共享指标 + 区域增补，预算 5 项</span></li>
                      <li><b>稳健评分</b><span>功能分 + 区间 + 等级稳定性</span></li>
                      <li><b>证据解释</b><span>每条结论挂来源与缺口</span></li>
                      <li><b>多 Agent 复核</b><span>版本冲突自动回退</span></li>
                      <li><b>报告与复测</b><span>可下载报告 + 可比性检查</span></li>
                    </ol>
                  </article>
                </div>
                <div class="boundary-grid">
                  <div class="boundary good"><strong>真实可跑</strong><p>探索数据地图与点位查询、数据资源库、工具中心、健康研究录入与核验、研究工作台土样审计与报告版本。</p></div>
                  <div class="boundary warn"><strong>公开数据计算</strong><p>N+X 选测、功能评分与区间、规则解释、多 Agent 流程、报告与对照比较。数据来源与规则版本均在界面标注。</p></div>
                  <div class="boundary stop"><strong>明确不承诺</strong><p>不把公开预测值当作本地实测、不输出健康等级结论、不给施肥剂量；演示规则尚未独立验收。</p></div>
                </div>
              </template>

              <!-- 02 录入与核验 -->
              <template v-else-if="currentStep.id === 'input'">
                <div class="table-card">
                  <div class="table-head">
                    <div><span class="panel-kicker">数据记录</span><h2>原始值与来源</h2></div>
                    <span class="sim-tag">公开数据来源</span>
                  </div>
                  <div class="data-table-wrap">
                    <table class="data-table">
                      <thead><tr><th>指标</th><th>数值</th><th>单位</th><th>数据属性</th><th>数据字段</th><th>选测角色</th></tr></thead>
                      <tbody>
                        <tr v-for="item in indicators" :key="item.code">
                          <td><b>{{ item.label }}</b><small>{{ item.code }}</small></td>
                          <td class="num">{{ item.value }}</td>
                          <td>{{ item.unit }}</td>
                          <td>{{ item.method }}</td>
                          <td class="mono">{{ item.source }}</td>
                          <td><span class="role-chip" :class="`role-${item.role}`">{{ item.selected ? (item.role === 'N' ? 'N 共享' : 'X 区域') : '预算外' }}</span></td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <div class="audit-grid">
                  <div v-for="check in auditChecks" :key="check.title" class="audit-item" :class="{ warn: !check.ok }">
                    <span class="audit-icon" aria-hidden="true">{{ check.ok ? '✓' : '!' }}</span>
                    <div><b>{{ check.title }}</b><p>{{ check.detail }}</p></div>
                  </div>
                </div>

                <div v-if="!analyzing" class="action-row">
                  <button type="button" class="demo-primary" @click="runAnalysis">开始计算（案例） <span aria-hidden="true">→</span></button>
                  <p>本页使用公开数据集与演示规则独立计算，不写入研究数据库；正式评价仍需本地采样与规则验收。</p>
                </div>
                <div v-else class="analysis-progress" role="status" aria-live="polite">
                  <div class="progress-head"><strong>正在生成演示结果</strong><span>{{ progress }}%</span></div>
                  <div class="progress-track"><span :style="{ width: progress + '%' }"></span></div>
                  <ul class="progress-stages">
                    <li v-for="stage in stages" :key="stage.label" :class="{ done: progress >= stage.at, active: progress < stage.at && progress >= stage.at - 20 }">
                      <i aria-hidden="true">{{ progress >= stage.at ? '✓' : '·' }}</i>{{ stage.label }}
                    </li>
                  </ul>
                  <p class="progress-note">演示流程：核验 → 选测 → 评分 → 解释 → 复核。真实后端接入后，这些阶段由任务队列与证据文件驱动。</p>
                </div>
              </template>

              <!-- 03 N+X 选测 -->
              <template v-else-if="currentStep.id === 'select'">
                <div class="innovation-banner"><span>创新一</span><b>自适应 N+X 跨区指标筛选</b><p>共享指标保证跨区可比，区域增补按预算分配；被挤出的信息显式记录，不静默丢弃。</p></div>
                <div class="select-top">
                  <div class="budget-card panel">
                    <span class="panel-kicker">预算约束</span>
                    <div class="budget-value"><strong>{{ scenario.budget }}</strong><span>项检测名额</span></div>
                    <div class="budget-slots" aria-label="预算名额占用">
                      <span v-for="slot in scenario.budget" :key="slot" class="slot" :class="{ used: slot <= selection.n.length + selection.x.length }">{{ slot }}</span>
                    </div>
                    <p class="panel-note">已选 {{ selection.n.length + selection.x.length }} / {{ scenario.budget }} 项；合计检测成本约 {{ totalCost }} 元（示例报价）。CEC 因名额已满被挤出。</p>
                  </div>
                  <div class="panel">
                    <span class="panel-kicker">N · 跨区共享指标</span>
                    <ul class="select-chips">
                      <li v-for="code in selection.n" :key="code"><b>{{ labelOf(code) }}</b><span>{{ valueOf(code) }}</span></li>
                    </ul>
                    <span class="panel-kicker spaced">X · 区域增补指标</span>
                    <ul class="select-chips x">
                      <li v-for="code in selection.x" :key="code"><b>{{ labelOf(code) }}</b><span>{{ valueOf(code) }}</span></li>
                      <li class="extra"><b>{{ labelOf(selection.extra[0]) }}</b><span>{{ valueOf(selection.extra[0]) }} · 预算外</span></li>
                    </ul>
                  </div>
                </div>
                <div class="table-card">
                  <div class="table-head"><div><span class="panel-kicker">入选依据</span><h2>边际贡献与替代方案</h2></div><span class="sim-tag">演示规则</span></div>
                  <div class="data-table-wrap">
                    <table class="data-table">
                      <thead><tr><th>指标</th><th>角色</th><th>边际贡献（分）</th><th>检测成本</th><th>入选依据</th></tr></thead>
                      <tbody>
                        <tr v-for="row in selection.rationale" :key="row.code">
                          <td><b>{{ labelOf(row.code) }}</b></td>
                          <td><span class="role-chip" :class="row.role.startsWith('N') ? 'role-N' : row.role.startsWith('X') ? 'role-X' : 'role-extra'">{{ row.role }}</span></td>
                          <td class="num">{{ row.gain }}</td>
                          <td class="num">{{ row.cost }} 元</td>
                          <td>{{ row.reason }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <p class="callout">{{ selection.tradeoff }}</p>
                </div>
              </template>

              <!-- 04 稳健评分 -->
              <template v-else-if="currentStep.id === 'score'">
                <div class="innovation-banner"><span>创新二</span><b>功能约束的稳健土壤健康评分</b><p>先定规则集，再输出区间与等级稳定性；高分不能掩盖稳定短板。</p></div>
                <div class="score-grid">
                  <article class="panel radar-panel">
                    <span class="panel-kicker">分功能评分（0–100，规则 A 计算）</span>
                    <svg class="radar" viewBox="0 0 260 240" role="img" aria-label="四项土壤功能的雷达图">
                      <g class="radar-grid">
                        <polygon v-for="ring in radarRings" :key="ring" :points="radarRingPoints(ring)" />
                        <line v-for="axis in radarAxes" :key="axis.i" :x1="120" :y1="120" :x2="axis.x" :y2="axis.y" />
                      </g>
                      <polygon class="radar-data" :points="radarPoints" />
                      <circle v-for="(item, index) in functions" :key="item.id" class="radar-dot" :cx="radarPoint(item.score, index)[0]" :cy="radarPoint(item.score, index)[1]" r="3.4" />
                      <text v-for="(item, index) in functions" :key="`${item.id}-label`" class="radar-label" :x="radarLabel(item.score, index)[0]" :y="radarLabel(item.score, index)[1]" :text-anchor="radarLabel(item.score, index)[2]">{{ item.label }}</text>
                      <text v-for="(item, index) in functions" :key="`${item.id}-score`" class="radar-score" :x="radarLabel(item.score, index)[0]" :y="radarLabel(item.score, index)[1] + 13" :text-anchor="radarLabel(item.score, index)[2]">{{ item.score }}</text>
                    </svg>
                  </article>
                  <article class="panel score-summary-card">
                    <span class="panel-kicker">综合结果</span>
                    <div class="score-range">
                      <div class="score-range-value"><strong>{{ scoreSummary.rangeLow }}</strong><span>–</span><strong>{{ scoreSummary.rangeHigh }}</strong></div>
                      <p>总分区间（中值 {{ scoreSummary.median }}）</p>
                    </div>
                    <div class="range-bar" aria-hidden="true">
                      <span class="range-fill" :style="{ left: scoreSummary.rangeLow + '%', width: (scoreSummary.rangeHigh - scoreSummary.rangeLow) + '%' }"></span>
                      <i class="range-tick" :style="{ left: scoreSummary.median + '%' }"></i>
                    </div>
                    <div class="range-labels"><span>0</span><span>50</span><span>100</span></div>
                    <p class="grade-line"><span class="grade-pill">{{ scoreSummary.grade }}</span></p>
                    <p class="panel-note">{{ scoreSummary.explanation }}</p>
                  </article>
                </div>

                <div class="table-card">
                  <div class="table-head"><div><span class="panel-kicker">规则扰动</span><h2>等级稳定性</h2></div><span class="sim-tag">3 套规则</span></div>
                  <div class="data-table-wrap">
                    <table class="data-table">
                      <thead><tr><th>规则集</th><th>依据</th><th>综合分</th><th>等级</th><th>备注</th></tr></thead>
                      <tbody>
                        <tr v-for="rule in rules" :key="rule.id">
                          <td><b>{{ rule.name }}</b></td>
                          <td>{{ rule.basis }}</td>
                          <td class="num">{{ rule.score }}</td>
                          <td><span class="grade-pill" :class="rule.grade === '较好' ? 'good' : 'mid'">{{ rule.grade }}</span></td>
                          <td>{{ rule.note }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <p class="callout warn">等级翻转 {{ stability.flips }} 处：{{ stability.sensitive }} {{ stability.conclusion }}</p>
                </div>

                <div class="shortboard-grid">
                  <article v-for="item in shortboards" :key="item.id" class="shortboard" :class="item.level === '稳定' ? 'stable' : 'sensitive'">
                    <span class="shortboard-level">{{ item.level }}</span>
                    <h3>{{ item.title }}</h3>
                    <p>{{ item.detail }}</p>
                    <code>{{ item.evidence }}</code>
                  </article>
                </div>
                <p class="caveat-note">分数由三套演示规则计算；规则参数未经独立验证，本页仅展示规则内部行为，不构成健康等级诊断。</p>
              </template>

              <!-- 05 证据化解释 -->
              <template v-else-if="currentStep.id === 'explain'">
                <div class="innovation-banner"><span>创新三</span><b>证据约束的土壤领域模型解释</b><p>模型只做解释与表达，数值和阈值由确定性规则工具完成；每条结论必须能回溯到证据。</p></div>
                <div class="evidence-list">
                  <article v-for="item in evidenceItems" :key="item.id" class="evidence-card" :class="`type-${item.type === '事实' ? 'fact' : item.type === '推断' ? 'infer' : item.type === '证据缺口' ? 'gap' : 'advice'}`">
                    <div class="evidence-head"><span class="type-chip">{{ item.type }}</span><code>{{ item.id }}</code></div>
                    <p class="evidence-claim">{{ item.claim }}</p>
                    <ul class="evidence-refs"><li v-for="ref in item.refs" :key="ref">{{ ref }}</li></ul>
                    <p v-if="item.caveat" class="evidence-caveat">{{ item.caveat }}</p>
                  </article>
                </div>
                <div class="model-bar">
                  <div><span class="panel-kicker">解释生成</span><b>{{ modelInfo.label }}</b><p>{{ modelInfo.status }} · 提示词版本 {{ modelInfo.promptVersion }}</p></div>
                  <span class="sim-tag">规则模板</span>
                </div>
                <p class="caveat-note">{{ modelInfo.note }}</p>
              </template>

              <!-- 06 多 Agent 复核 -->
              <template v-else-if="currentStep.id === 'agents'">
                <div class="innovation-banner"><span>创新四</span><b>证据契约驱动的多 Agent 协作</b><p>角色之间只通过带来源、参数和版本的不可变结果文件交接；生成者不能验收自己的结论。</p></div>
                <div class="agent-grid">
                  <article v-for="agent in agents" :key="agent.id" class="agent-card" :class="`status-${agent.status}`">
                    <div class="agent-head"><span class="agent-dot" aria-hidden="true"></span><b>{{ agent.role }}</b><span class="agent-status">{{ agentStatusLabel(agent.status) }}</span></div>
                    <p>{{ agent.output }}</p>
                    <code>{{ agent.fp }}</code>
                  </article>
                </div>
                <div class="conflict-card">
                  <span class="conflict-tag">复核拦截 · 演示事件</span>
                  <h2>版本冲突 → 阻止发布 → 回退重算</h2>
                  <ol>
                    <li>解释稿 v1 引用规则 <code>v0.2</code> 的阈值文字，与当前激活的 <code>v0.3-demo</code> 不一致。</li>
                    <li>独立复核角色不参与生成，检出后阻止报告发布。</li>
                    <li>回退到评分步骤重算，解释稿 v2 重新生成，复核通过并封存报告版本。</li>
                  </ol>
                </div>
                <div class="timeline">
                  <div v-for="(entry, index) in agentTimeline" :key="index" class="timeline-row"><span class="timeline-time">{{ entry.at }}</span><span class="timeline-dot" aria-hidden="true"></span><p>{{ entry.text }}</p></div>
                </div>
                <p class="caveat-note">任务图、角色与指纹为演示内容；真实运行时由后端 runtime 进程驱动，需单独启动并持有执行日志。</p>
              </template>

              <!-- 07 报告 -->
              <template v-else-if="currentStep.id === 'report'">
                <div class="report-layout">
                  <article class="report-paper">
                    <span class="report-watermark" aria-hidden="true">DEMO · CASE</span>
                    <header>
                      <p class="report-kicker">沃壤知行 · 案例计算报告</p>
                      <h2>农田土壤健康评价 · 案例地块 {{ scenario.field }}</h2>
                      <p class="report-sub">{{ scenario.crop }} · {{ scenario.depth }} · 数据版本 {{ scenario.sampledAt }} · 报告版本 {{ report.version }}</p>
                      <span class="report-badge">公开数据案例 · 演示规则计算 · 不构成健康诊断或农艺处方</span>
                    </header>
                    <dl class="report-meta">
                      <div><dt>运行标识</dt><dd class="mono">{{ scenario.runId }}</dd></div>
                      <div><dt>规则版本</dt><dd class="mono">{{ scenario.rulesVersion }}</dd></div>
                      <div><dt>生成时间</dt><dd>{{ report.generatedAt }}</dd></div>
                      <div><dt>复核状态</dt><dd>{{ report.status }}</dd></div>
                    </dl>
                    <section>
                      <h3>报告目录</h3>
                      <ol class="report-sections"><li v-for="section in report.sections" :key="section">{{ section }}</li></ol>
                    </section>
                    <section>
                      <h3>适用范围与限制</h3>
                      <ul class="report-limits"><li v-for="limit in report.limits" :key="limit">{{ limit }}</li></ul>
                    </section>
                    <footer class="report-foot">本报告由公开数据案例与演示规则计算生成，可打印或另存为 PDF；正式报告需在评分规则验收后重新生成。</footer>
                  </article>
                  <aside class="report-actions">
                    <div class="panel">
                      <span class="panel-kicker">交付物</span>
                      <h2>可下载报告</h2>
                      <p>HTML 报告含来源、方法、规则版本、复核记录与限制声明；在浏览器中打开后可打印为 PDF。</p>
                      <button type="button" class="demo-primary" @click="downloadReport">下载案例报告 <span aria-hidden="true">↓</span></button>
                      <p v-if="downloaded" class="download-state" role="status">已下载：沃壤知行_案例评价报告_A-07_v2.html</p>
                      <p class="panel-note">报告带 “DEMO · 案例计算” 水印与数据来源说明；不写入研究数据库。</p>
                    </div>
                    <div class="panel">
                      <span class="panel-kicker">版本记录</span>
                      <ul class="version-list">
                        <li><b>v1</b><span>复核拦截：解释稿引用规则 v0.2</span></li>
                        <li class="current"><b>v2</b><span>回退重算后通过，当前版本</span></li>
                      </ul>
                    </div>
                  </aside>
                </div>
              </template>

              <!-- 08 对照与可比性 -->
              <template v-else>
                <div class="retest-head">
                  <div class="panel">
                    <span class="panel-kicker">对照地块</span>
                    <h2>{{ retest.sampledAt }}</h2>
                    <p>对照不是复测：先核对数据源、深度、分辨率与地块身份，再决定能否比较。</p>
                  </div>
                  <div class="panel verdict-card">
                    <span class="panel-kicker">可比性判定</span>
                    <strong>{{ retest.verdict }}</strong>
                    <p>{{ retest.note }}</p>
                  </div>
                </div>
                <div class="retest-grid">
                  <div class="panel">
                    <span class="panel-kicker">可比性检查</span>
                    <ul class="check-list">
                      <li v-for="check in retest.checks" :key="check.label" :class="{ warn: !check.ok }"><span aria-hidden="true">{{ check.ok ? '✓' : '!' }}</span>{{ check.label }}</li>
                    </ul>
                  </div>
                  <div class="panel">
                    <span class="panel-kicker">两块地并列（不做改善或因果推断）</span>
                    <table class="data-table compact">
                      <thead><tr><th>指标</th><th>A-07</th><th>B-02</th><th>差值</th></tr></thead>
                      <tbody><tr v-for="row in retest.values" :key="row.code"><td>{{ row.label }}</td><td class="num">{{ row.before }}</td><td class="num">{{ row.after }}</td><td class="num">{{ delta(row) }}</td></tr></tbody>
                    </table>
                  </div>
                </div>
                <div class="final-card">
                  <h2>演示结束 · 三条边界</h2>
                  <div class="final-grid">
                    <div><b>真做真</b><p>地图、数据库、工具、录入、审计报告是真实功能，现场可独立操作。</p></div>
                    <div><b>来源可查</b><p>数据来自 SoilGrids 2.0 公开查询，规则与缺口均在报告注明；预测值不当实测用。</p></div>
                    <div><b>不越边界</b><p>不输出健康等级结论、不给施肥剂量；正式评分规则与模型验收后再替换。</p></div>
                  </div>
                </div>
              </template>

              <p class="demo-tip"><span>讲解提示</span>{{ currentStep.tip }}</p>
            </section>
          </transition>
        </div>

        <footer class="demo-controls">
          <p class="demo-disclaimer"><span aria-hidden="true">●</span> 演示模式 · 公开数据案例 + 演示规则计算，不构成健康诊断或农艺处方。真实账号与数据不受影响。</p>
          <div class="demo-nav">
            <span class="demo-keys" aria-hidden="true">← → 切换 · Esc 退出</span>
            <span class="demo-counter">{{ current + 1 }} / {{ steps.length }}</span>
            <button type="button" class="demo-secondary" :disabled="current === 0" @click="prev">上一步</button>
            <button v-if="current < steps.length - 1" type="button" class="demo-primary" @click="next">下一步 <span aria-hidden="true">→</span></button>
            <button v-else type="button" class="demo-primary" @click="restart">重新演示 <span aria-hidden="true">↻</span></button>
          </div>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  scenario, indicators, auditChecks, selection, functions, scoreSummary,
  rules, stability, shortboards, evidenceItems, modelInfo, agents, agentTimeline,
  report, retest, steps, buildReportHtml,
} from './demoShowcase.js'

const emit = defineEmits(['exit'])

const current = ref(0)
const shell = ref(null)
const currentStep = computed(() => steps[current.value])
const analyzing = ref(false)
const progress = ref(0)
const downloaded = ref(false)
const autoplay = ref(false)
let analysisTimer = null
let autoplayTimer = null

const stepTitles = {
  scene: '一块案例地块的完整健康评价链路',
  input: '数据接入与核验：先让来源可信',
  select: 'N+X 选测：在预算内选择测什么',
  score: '稳健评分：输出区间，而不是一个精确分数',
  explain: '证据化解释：每条结论都能回溯',
  agents: '多 Agent 复核：生成者不能验收自己',
  report: '报告与版本：可下载、可追溯、可复核',
  retest: '对照地块与可比性：先判断能不能比',
}
const stepLeads = {
  scene: '数据来自 ISRIC SoilGrids 2.0 公开查询（250 m，0–5 cm）；本页用固定规则把数据接成一条可复核的评价链路，数据与规则边界均标注在界面。',
  input: '六项指标先进入同一条数据来源与版本记录：单位换算、深度、版本与许可核验通过后，系统主动暴露证据缺口。',
  select: '在 5 项检测预算内，共享指标 N 保跨区可比，区域增补 X 按本地收益分配；被挤出的 CEC 不静默丢弃，而是记录为补测候选。',
  score: '综合分以区间呈现：三套演示规则的计算结果不同，同时识别在全部规则下都成立的稳定短板。',
  explain: '解释了为什么，不等同于重新评分：每条结论附数据查询、规则版本与缺口说明；规则模板不修改任何数值。',
  agents: '五个角色按依赖图交接不可变结果文件；独立复核角色检出解释稿引用旧规则版本，阻止发布并回退重算。',
  report: '报告包含数据来源、查询参数、规则版本、复核记录与限制声明，可下载后打印为 PDF。',
  retest: '对照先做可比性检查：同数据源、同深度、同分辨率通过；不同地块与预测值身份被标为不可做复测。',
}

const stages = [
  { label: '读取并核验检测记录', at: 10 },
  { label: '生成 N+X 选测清单', at: 35 },
  { label: '拟合稳健评分与区间', at: 60 },
  { label: '生成证据化解释', at: 80 },
  { label: '独立复核与版本封存', at: 95 },
]

const totalCost = computed(() => selection.rationale.filter(row => row.role !== '预算外').reduce((sum, row) => sum + row.cost, 0))
const labelOf = code => indicators.find(item => item.code === code)?.label || code
const valueOf = code => {
  const item = indicators.find(entry => entry.code === code)
  return item ? `${item.value} ${item.unit}` : ''
}
const delta = row => {
  const diff = Number((row.after - row.before).toFixed(2))
  return diff > 0 ? `+${diff}` : String(diff)
}
const agentStatusLabel = status => ({ done: '完成', reworked: '已重算', reviewed: '复核通过' }[status] || status)

/* Radar chart geometry */
const radarCenter = 120
const radarRadius = 78
function radarPoint(score, index) {
  const angle = -Math.PI / 2 + (index * Math.PI) / 2
  const radius = (Math.max(0, Math.min(100, score)) / 100) * radarRadius
  return [radarCenter + Math.cos(angle) * radius, radarCenter + Math.sin(angle) * radius]
}
function radarRingPoints(ratio) {
  return functions.map((item, index) => {
    const angle = -Math.PI / 2 + (index * Math.PI) / 2
    const radius = radarRadius * ratio
    return `${radarCenter + Math.cos(angle) * radius},${radarCenter + Math.sin(angle) * radius}`
  }).join(' ')
}
const radarRings = [0.25, 0.5, 0.75, 1]
const radarAxes = functions.map((item, index) => {
  const angle = -Math.PI / 2 + (index * Math.PI) / 2
  return { i: item.id, x: radarCenter + Math.cos(angle) * radarRadius, y: radarCenter + Math.sin(angle) * radarRadius }
})
const radarPoints = computed(() => functions.map((item, index) => radarPoint(item.score, index).join(',')).join(' '))
function radarLabel(score, index) {
  const angle = -Math.PI / 2 + (index * Math.PI) / 2
  const radius = radarRadius + 24
  const x = radarCenter + Math.cos(angle) * radius
  const y = radarCenter + Math.sin(angle) * radius + 4
  const anchor = Math.abs(Math.cos(angle)) < 0.2 ? 'middle' : Math.cos(angle) > 0 ? 'start' : 'end'
  return [x, y, anchor]
}

function clearAnalysisTimer() {
  if (analysisTimer) { clearInterval(analysisTimer); analysisTimer = null }
  analyzing.value = false
  progress.value = 0
}
function runAnalysis() {
  if (analyzing.value) return
  clearAnalysisTimer()
  analyzing.value = true
  progress.value = 0
  analysisTimer = setInterval(() => {
    progress.value = Math.min(100, progress.value + 4)
    if (progress.value >= 100) {
      clearInterval(analysisTimer)
      analysisTimer = null
      setTimeout(() => {
        if (progress.value >= 100) { analyzing.value = false; goTo(2) }
      }, 420)
    }
  }, 80)
}
function goTo(index) {
  if (index < 0 || index >= steps.length) return
  if (analyzing.value) clearAnalysisTimer()
  current.value = index
  downloaded.value = false
}
function next() { goTo(current.value + 1) }
function prev() { goTo(current.value - 1) }
function restart() {
  goTo(0)
  downloaded.value = false
}
function exitDemo() {
  pauseAutoplay()
  emit('exit')
}
function toggleAutoplay() { autoplay.value = !autoplay.value }
function pauseAutoplay() { autoplay.value = false }
function scheduleAutoplay() {
  if (autoplayTimer) { clearTimeout(autoplayTimer); autoplayTimer = null }
  if (!autoplay.value) return
  autoplayTimer = setTimeout(() => {
    if (!autoplay.value) return
    if (current.value < steps.length - 1) { next(); scheduleAutoplay() } else { autoplay.value = false }
  }, 7000)
}
watch(autoplay, value => {
  if (value) scheduleAutoplay()
  else if (autoplayTimer) { clearTimeout(autoplayTimer); autoplayTimer = null }
})
watch(current, () => {
  if (shell.value) shell.value.scrollTo({ top: 0, behavior: 'auto' })
  if (autoplay.value) scheduleAutoplay()
})

function downloadReport() {
  const blob = new Blob([buildReportHtml()], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `沃壤知行_案例评价报告_${scenario.field}_${report.version}.html`
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 4000)
  downloaded.value = true
}

function onKeydown(event) {
  if (event.defaultPrevented) return
  const target = event.target
  if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) return
  if (event.key === 'ArrowRight') { event.preventDefault(); next() }
  else if (event.key === 'ArrowLeft') { event.preventDefault(); prev() }
  else if (event.key === 'Escape') { event.preventDefault(); exitDemo() }
}

onMounted(() => { window.addEventListener('keydown', onKeydown) })
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  if (analysisTimer) clearInterval(analysisTimer)
  if (autoplayTimer) clearTimeout(autoplayTimer)
})
</script>

<style scoped>
.demo-shell {
  --demo-ink: #24382c;
  --demo-muted: #63776a;
  --demo-line: #dfe7dc;
  --demo-paper: #f8faf5;
  --demo-green: #2f6a4a;
  --demo-deep: #163b2c;
  --demo-cream: #f3f4ec;
  --demo-warn: #a35a3d;
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
  background:
    radial-gradient(1200px 520px at 15% -10%, rgba(196, 219, 191, .38), transparent 60%),
    radial-gradient(900px 460px at 96% 8%, rgba(224, 232, 208, .5), transparent 55%),
    #f2f5ed;
  color: var(--demo-ink);
  font: var(--text-body)/var(--leading-body) var(--font-ui);
}
.demo-shell *, .demo-shell *::before, .demo-shell *::after { box-sizing: border-box; }
.demo-shell :is(button, a, summary):focus-visible { outline: 3px solid #78a981; outline-offset: 2px; }

.demo-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 12px 26px;
  border-bottom: 1px solid rgba(206, 218, 202, .9);
  background: rgba(249, 251, 245, .92);
  backdrop-filter: blur(16px);
}
.demo-brand { display: flex; align-items: center; gap: 11px; }
.demo-mark { width: 34px; height: 34px; display: grid; place-items: center; border: 1px solid #c9dcc7; border-radius: 11px; color: #3c7352; background: #fff; }
.demo-mark svg { width: 26px; height: 26px; }
.demo-brand-copy { display: flex; flex-direction: column; line-height: 1.2; }
.demo-brand-copy strong { font-size: 16px; font-weight: 600; letter-spacing: .04em; color: #1f4030; }
.demo-brand-copy small { color: #84978a; font-size: 11px; letter-spacing: .02em; }
.demo-sim-badge { display: inline-flex; align-items: center; gap: 8px; padding: 5px 13px; border: 1px solid #cbb08c; border-radius: 999px; background: #fbf4e8; color: #8a5a2b; font-size: 12px; font-weight: 600; letter-spacing: .04em; }
.demo-sim-badge i { width: 7px; height: 7px; border-radius: 50%; background: #c98a3c; box-shadow: 0 0 0 4px rgba(201, 138, 60, .14); }
.demo-scenario { display: flex; align-items: baseline; gap: 10px; min-width: 0; color: #5c7061; font-size: 12px; }
.demo-scenario strong { color: #2c4d38; font-size: 13px; font-weight: 600; white-space: nowrap; }
.demo-scenario-label { color: #8b9c8f; letter-spacing: .12em; }
.demo-scenario span:last-child { white-space: nowrap; }
.demo-topbar-actions { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.demo-ghost, .demo-exit { min-height: 34px; padding: 6px 13px; border: 1px solid #cfdbcc; border-radius: 8px; background: #fff; color: #3d5a46; font: inherit; font-size: 12px; cursor: pointer; transition: background .18s, border-color .18s; }
.demo-ghost:hover { background: #f1f6ed; border-color: #b7cdb6; }
.demo-ghost[aria-pressed="true"] { background: #e8f2e4; border-color: #9fc2a1; color: #2b6040; }
.demo-exit { border-color: #2f6a4a; background: #2f6a4a; color: #fff; }
.demo-exit:hover { background: #245639; }

.demo-body { flex: 1; display: grid; grid-template-columns: 224px minmax(0, 1fr); min-height: 0; width: min(1480px, 100%); margin: 0 auto; padding: 22px 26px 26px; gap: 22px; }
.demo-rail { position: sticky; top: 82px; align-self: start; display: flex; flex-direction: column; gap: 4px; padding: 16px; border: 1px solid #dde6d8; border-radius: 16px; background: rgba(252, 253, 248, .86); box-shadow: 0 10px 30px rgba(28, 62, 40, .05); }
.demo-rail-title { margin: 2px 6px 8px; color: #8b9b8d; font-size: 11px; font-weight: 700; letter-spacing: .2em; }
.demo-rail-step { display: flex; align-items: center; gap: 10px; width: 100%; padding: 9px 10px; border: 1px solid transparent; border-radius: 10px; background: transparent; color: #52685a; text-align: left; cursor: pointer; transition: background .18s, border-color .18s; }
.demo-rail-step:hover { background: #f0f5ec; }
.demo-rail-step.active { border-color: #c4dbc3; background: #eef6ea; color: #1f4b31; }
.demo-rail-step.done .rail-no { color: #46795a; }
.rail-no { width: 22px; color: #9aa99c; font-size: 11px; font-weight: 700; font-variant-numeric: tabular-nums; }
.demo-rail-step.active .rail-no { color: #2f6a4a; }
.rail-copy { display: flex; flex-direction: column; min-width: 0; line-height: 1.35; }
.rail-copy b { font-size: 12.5px; font-weight: 600; }
.rail-copy small { color: #93a295; font-size: 10.5px; letter-spacing: .02em; }
.rail-state { margin-left: auto; color: #4c8a64; font-size: 11px; }
.demo-rail-note { margin-top: 12px; padding: 12px 11px; border-top: 1px dashed #d8e2d5; color: #7d8f80; font-size: 10.5px; line-height: 1.6; }
.demo-rail-note strong { display: block; margin-bottom: 4px; color: #5f7666; font-size: 11px; letter-spacing: .08em; }
.demo-rail-note p { margin: 0 0 5px; }
.demo-rail-note p:last-child { margin-bottom: 0; }

.demo-main { min-width: 0; display: flex; flex-direction: column; }
.demo-stage { flex: 1; min-width: 0; }
.demo-step { position: relative; padding: 26px 30px 24px; border: 1px solid #dde6d8; border-radius: 20px; background: rgba(255, 255, 255, .86); box-shadow: 0 16px 46px rgba(26, 58, 37, .07); }
.demo-kicker { margin: 0 0 10px; color: #6f8a76; font-size: 11px; font-weight: 700; letter-spacing: .22em; }
.demo-title { margin: 0; color: #1c3c2a; font: 500 clamp(1.55rem, 2.2vw, 2rem)/1.28 var(--font-display); letter-spacing: -.02em; }
.demo-lead { max-width: 74ch; margin: 12px 0 22px; color: #5b7163; font-size: 13.5px; line-height: 1.8; }
.demo-step h2 { margin: 0; color: #24422f; font-size: 17px; font-weight: 600; }
.demo-step h3 { margin: 0; color: #2a4a35; font-size: 14px; font-weight: 600; }
.demo-step p { margin: 0; }
.demo-fade-enter-active, .demo-fade-leave-active { transition: opacity .18s ease, transform .18s ease; }
.demo-fade-enter-from { opacity: 0; transform: translateY(6px); }
.demo-fade-leave-to { opacity: 0; transform: translateY(-4px); }

.panel { min-width: 0; padding: 18px 19px; border: 1px solid #e1e8dc; border-radius: 14px; background: #fff; }
.panel-kicker { display: block; margin-bottom: 8px; color: #7b8f7f; font-size: 10.5px; font-weight: 700; letter-spacing: .16em; }
.panel-kicker.spaced { margin-top: 16px; }
.panel-note { margin-top: 10px !important; color: #809184; font-size: 11.5px; line-height: 1.65; }
.mono, code { font-family: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace; font-size: 11px; color: #5c7565; }
.sim-tag { display: inline-flex; align-items: center; gap: 6px; padding: 3px 9px; border: 1px solid #d8c1a0; border-radius: 999px; background: #fbf5ea; color: #8a602f; font-size: 10.5px; font-weight: 600; letter-spacing: .04em; white-space: nowrap; }

.scene-grid { display: grid; grid-template-columns: 1.15fr 1fr 1fr; gap: 14px; }
.field-card { background: linear-gradient(160deg, #f2f8ee, #fbfcf8 62%); border-color: #d6e5d0; }
.field-card h2 { margin: 10px 0 14px; }
.field-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 9px 16px; margin: 0; }
.field-meta div { min-width: 0; }
.field-meta dt { color: #8b9c8f; font-size: 10.5px; letter-spacing: .06em; }
.field-meta dd { margin: 2px 0 0; color: #35523e; font-size: 12.5px; overflow-wrap: anywhere; }
.input-chips { display: flex; flex-wrap: wrap; gap: 7px; margin: 0; padding: 0; list-style: none; }
.input-chips li { display: flex; flex-direction: column; padding: 6px 10px; border: 1px solid #e2e9de; border-radius: 8px; background: #f9fbf6; }
.input-chips b { color: #3c5a46; font-size: 11px; font-weight: 600; }
.input-chips span { color: #6f8574; font-size: 11px; font-variant-numeric: tabular-nums; }
.goal-list { margin: 4px 0 0; padding: 0; list-style: none; counter-reset: goal; }
.goal-list li { position: relative; padding: 6px 0 6px 26px; border-bottom: 1px dashed #edf0ea; counter-increment: goal; }
.goal-list li:last-child { border-bottom: 0; }
.goal-list li::before { content: counter(goal, decimal-leading-zero); position: absolute; left: 0; top: 7px; color: #8cb095; font-size: 10px; font-weight: 700; }
.goal-list b { display: block; color: #35523e; font-size: 12px; font-weight: 600; }
.goal-list span { color: #7d8f80; font-size: 11px; }
.boundary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.boundary { padding: 13px 15px; border-radius: 12px; border: 1px solid #e3e9de; background: #fbfcf8; }
.boundary strong { display: block; margin-bottom: 5px; font-size: 12px; }
.boundary p { color: #6f8374; font-size: 11.5px; line-height: 1.65; }
.boundary.good { border-color: #cfe3c8; background: #f4faf0; }
.boundary.good strong { color: #2f6a4a; }
.boundary.warn { border-color: #ecdcbc; background: #fdf9f0; }
.boundary.warn strong { color: #8a5f26; }
.boundary.stop { border-color: #e8d4cd; background: #fdf6f3; }
.boundary.stop strong { color: #95563f; }

.table-card { margin-top: 14px; padding: 18px 19px; border: 1px solid #e1e8dc; border-radius: 14px; background: #fff; }
.table-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 12px; }
.data-table-wrap { overflow: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.data-table th, .data-table td { padding: 8px 9px; border-bottom: 1px solid #edf0ea; text-align: left; vertical-align: top; }
.data-table th { color: #7b8d80; font-size: 10.5px; font-weight: 600; letter-spacing: .04em; background: #f7f9f3; }
.data-table td b { display: block; color: #33513d; font-size: 12px; font-weight: 600; }
.data-table td small { display: block; margin-top: 1px; color: #9aa99d; font-size: 10px; }
.data-table .num { font-variant-numeric: tabular-nums; color: #2c4f39; font-weight: 600; white-space: nowrap; }
.data-table.compact { font-size: 11.5px; }
.role-chip { display: inline-flex; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 600; white-space: nowrap; }
.role-N { background: #e7f3e6; color: #2f6a4a; }
.role-X { background: #e8eef8; color: #3c5c8a; }
.role-extra { background: #f4f1e6; color: #8a7440; }

.audit-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
.audit-item { display: flex; gap: 10px; padding: 11px 13px; border: 1px solid #dce9d6; border-radius: 11px; background: #f8fbf4; }
.audit-item.warn { border-color: #eadfc6; background: #fdf9ef; }
.audit-icon { display: grid; place-items: center; width: 18px; height: 18px; flex: none; margin-top: 1px; border-radius: 50%; background: #dcecd7; color: #2f6a4a; font-size: 11px; font-weight: 700; }
.audit-item.warn .audit-icon { background: #f3e3c6; color: #96652a; }
.audit-item b { display: block; color: #35523e; font-size: 12px; font-weight: 600; }
.audit-item p { margin-top: 2px !important; color: #748877; font-size: 11px; line-height: 1.6; }
.action-row { display: flex; align-items: center; gap: 16px; margin-top: 16px; flex-wrap: wrap; }
.action-row p { color: #809184; font-size: 11.5px; line-height: 1.6; max-width: 62ch; }
.demo-primary, .demo-secondary { display: inline-flex; align-items: center; gap: 8px; min-height: 40px; padding: 9px 17px; border-radius: 9px; font: inherit; font-size: 12.5px; font-weight: 600; cursor: pointer; transition: background .18s, border-color .18s, transform .18s; }
.demo-primary { border: 1px solid #2f6a4a; background: #2f6a4a; color: #fff; }
.demo-primary:hover { background: #245639; transform: translateY(-1px); }
.demo-secondary { border: 1px solid #cfdbcc; background: #fff; color: #3d5a46; }
.demo-secondary:hover { background: #f1f6ed; }
.demo-secondary:disabled { opacity: .45; cursor: default; transform: none; }

.analysis-progress { margin-top: 16px; padding: 16px 18px; border: 1px solid #d9e6d3; border-radius: 13px; background: #f7fbf3; }
.progress-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 9px; }
.progress-head strong { color: #2c5039; font-size: 13px; }
.progress-head span { color: #4a7a5c; font-size: 12px; font-variant-numeric: tabular-nums; }
.progress-track { height: 6px; border-radius: 999px; background: #e3ecdf; overflow: hidden; }
.progress-track span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #5f9a70, #2f6a4a); transition: width .12s linear; }
.progress-stages { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; margin: 13px 0 0; padding: 0; list-style: none; }
.progress-stages li { display: flex; align-items: center; gap: 6px; color: #93a396; font-size: 10.5px; line-height: 1.4; }
.progress-stages li.done { color: #2f6a4a; }
.progress-stages li.active { color: #6b8a72; }
.progress-stages i { display: grid; place-items: center; width: 15px; height: 15px; flex: none; border-radius: 50%; background: #e6eee2; font-style: normal; font-size: 9px; }
.progress-stages li.done i { background: #d7ead2; }
.progress-note { margin-top: 11px !important; color: #809184; font-size: 11px; line-height: 1.6; }

.innovation-banner { display: grid; grid-template-columns: auto auto 1fr; align-items: center; gap: 12px; margin-bottom: 16px; padding: 12px 16px; border: 1px solid #d6e5d0; border-radius: 12px; background: linear-gradient(100deg, #eef6e9, #fafcf6); }
.innovation-banner span { padding: 3px 9px; border-radius: 999px; background: #2f6a4a; color: #fff; font-size: 10px; font-weight: 600; letter-spacing: .08em; }
.innovation-banner b { color: #23472f; font-size: 13px; font-weight: 600; white-space: nowrap; }
.innovation-banner p { color: #6b8071; font-size: 11.5px; line-height: 1.6; }

.select-top { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 14px; }
.budget-value { display: flex; align-items: baseline; gap: 8px; margin: 2px 0 12px; }
.budget-value strong { color: #2a5c3e; font-size: 42px; font-weight: 600; line-height: 1; letter-spacing: -.04em; }
.budget-value span { color: #75897a; font-size: 12px; }
.budget-slots { display: flex; gap: 6px; }
.slot { display: grid; place-items: center; width: 26px; height: 26px; border: 1px dashed #cfdccb; border-radius: 7px; color: #a8b6a8; font-size: 10.5px; font-variant-numeric: tabular-nums; }
.slot.used { border-style: solid; border-color: #b9d6b5; background: #e9f3e4; color: #2f6a4a; font-weight: 600; }
.select-chips { display: flex; flex-wrap: wrap; gap: 7px; margin: 0; padding: 0; list-style: none; }
.select-chips li { display: flex; flex-direction: column; padding: 7px 11px; border: 1px solid #d9e8d3; border-radius: 9px; background: #f4faf0; }
.select-chips.x li { border-color: #d8e2ee; background: #f4f7fb; }
.select-chips li.extra { border-color: #e6dfc9; background: #fbf8ee; }
.select-chips b { color: #35523e; font-size: 11.5px; font-weight: 600; }
.select-chips span { color: #708575; font-size: 10.5px; font-variant-numeric: tabular-nums; }
.callout { margin-top: 13px !important; padding: 11px 14px; border-left: 3px solid #8fb999; border-radius: 0 8px 8px 0; background: #f5f9f1; color: #5e7566; font-size: 11.5px; line-height: 1.7; }
.callout.warn { border-left-color: #c99a55; background: #fdf9ef; color: #7c6236; }

.score-grid { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: 14px; }
.radar-panel { display: flex; flex-direction: column; }
.radar { width: 100%; max-height: 280px; margin-top: 4px; }
.radar-grid polygon { fill: rgba(63, 110, 79, .04); stroke: #dfe8da; stroke-width: 1; }
.radar-grid line { stroke: #e6ece2; stroke-width: 1; }
.radar-data { fill: rgba(73, 132, 92, .18); stroke: #3f7a55; stroke-width: 1.6; }
.radar-dot { fill: #2f6a4a; stroke: #fff; stroke-width: 1.4; }
.radar-label { fill: #5e7667; font-size: 10.5px; }
.radar-score { fill: #2f6a4a; font-size: 11px; font-weight: 700; }
.score-summary-card { display: flex; flex-direction: column; }
.score-range { margin-top: 2px; }
.score-range-value { display: flex; align-items: baseline; gap: 8px; color: #1f4b31; }
.score-range-value strong { font-size: 44px; font-weight: 600; line-height: 1; letter-spacing: -.04em; font-variant-numeric: tabular-nums; }
.score-range-value span { color: #9bb09d; font-size: 22px; }
.score-range p { margin-top: 4px !important; color: #7d9182; font-size: 11.5px; }
.range-bar { position: relative; height: 10px; margin-top: 14px; border-radius: 999px; background: linear-gradient(90deg, #e9d9c8, #dfe9d6 40%, #cfe4cd 70%, #b7d6b3); }
.range-fill { position: absolute; top: -3px; height: 16px; border-radius: 999px; border: 1px solid #4f8a64; background: rgba(111, 170, 126, .32); }
.range-tick { position: absolute; top: -6px; width: 2px; height: 22px; background: #2f6a4a; }
.range-labels { display: flex; justify-content: space-between; margin-top: 7px; color: #9aab9d; font-size: 10px; font-variant-numeric: tabular-nums; }
.grade-line { margin-top: 13px !important; }
.grade-pill { display: inline-flex; padding: 3px 10px; border-radius: 999px; background: #f2ecdc; color: #8a6a33; font-size: 11px; font-weight: 600; }
.grade-pill.good { background: #e6f2e2; color: #2f6a4a; }
.grade-pill.mid { background: #f2ecdc; color: #8a6a33; }
.shortboard-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.shortboard { position: relative; padding: 15px 16px; border: 1px solid #e1e8dc; border-radius: 13px; background: #fff; }
.shortboard.stable { border-left: 3px solid #b9824c; }
.shortboard.sensitive { border-left: 3px solid #6d8fa8; }
.shortboard-level { display: inline-flex; margin-bottom: 7px; padding: 2px 8px; border-radius: 999px; background: #f6efe2; color: #8a6531; font-size: 10px; font-weight: 600; }
.shortboard.sensitive .shortboard-level { background: #eaf0f5; color: #4a6c86; }
.shortboard h3 { font-size: 12.5px; }
.shortboard p { margin-top: 5px !important; color: #6f8374; font-size: 11px; line-height: 1.6; }
.shortboard code { display: block; margin-top: 7px; color: #93a396; font-size: 10px; overflow-wrap: anywhere; }
.caveat-note { margin-top: 13px !important; padding: 10px 13px; border: 1px dashed #dfe5d8; border-radius: 9px; color: #8a9a8d; font-size: 11px; line-height: 1.65; background: #fbfcf8; }

.evidence-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.evidence-card { padding: 14px 16px; border: 1px solid #e1e8dc; border-left: 3px solid #9ab99f; border-radius: 12px; background: #fff; }
.evidence-card.type-infer { border-left-color: #6d8fa8; }
.evidence-card.type-gap { border-left-color: #c99a55; }
.evidence-card.type-advice { border-left-color: #8a74a8; }
.evidence-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.type-chip { padding: 2px 8px; border-radius: 999px; background: #edf4e8; color: #3f7a55; font-size: 10px; font-weight: 600; }
.type-infer .type-chip { background: #eaf0f5; color: #4a6c86; }
.type-gap .type-chip { background: #f8f0df; color: #8a6531; }
.type-advice .type-chip { background: #f0ebf5; color: #6b5686; }
.evidence-head code { color: #a2b0a4; font-size: 10px; }
.evidence-claim { margin-top: 8px !important; color: #33513d; font-size: 12.5px; line-height: 1.65; }
.evidence-refs { display: flex; flex-wrap: wrap; gap: 5px; margin: 9px 0 0; padding: 0; list-style: none; }
.evidence-refs li { padding: 2px 7px; border: 1px solid #e4eadd; border-radius: 6px; background: #f9fbf6; color: #7b8f7f; font-family: "SFMono-Regular", ui-monospace, Menlo, monospace; font-size: 9.5px; }
.evidence-caveat { margin-top: 8px !important; color: #9a8a70; font-size: 10.5px; line-height: 1.6; }
.model-bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 14px; padding: 13px 16px; border: 1px solid #e1e8dc; border-radius: 12px; background: #fbfcf8; }
.model-bar b { display: block; color: #2f4d3a; font-size: 12.5px; }
.model-bar p { margin-top: 3px !important; color: #829286; font-size: 11px; }
.model-bar .panel-kicker { margin-bottom: 4px; }

.agent-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.agent-card { padding: 13px 14px; border: 1px solid #e1e8dc; border-radius: 12px; background: #fff; }
.agent-head { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
.agent-head b { color: #2f4d3a; font-size: 12px; font-weight: 600; }
.agent-dot { width: 7px; height: 7px; border-radius: 50%; background: #6fae7c; box-shadow: 0 0 0 3px rgba(111, 174, 124, .14); }
.status-reworked .agent-dot { background: #d2994e; box-shadow: 0 0 0 3px rgba(210, 153, 78, .15); }
.status-reviewed .agent-dot { background: #4f86a8; box-shadow: 0 0 0 3px rgba(79, 134, 168, .15); }
.agent-status { margin-left: auto; color: #97a799; font-size: 9.5px; }
.agent-card p { margin-top: 7px !important; color: #6f8374; font-size: 10.5px; line-height: 1.55; }
.agent-card code { display: block; margin-top: 6px; color: #a0aea2; font-size: 9px; overflow-wrap: anywhere; }
.conflict-card { margin-top: 14px; padding: 16px 18px; border: 1px solid #e8d8c4; border-radius: 13px; background: #fdf8f0; }
.conflict-tag { display: inline-flex; margin-bottom: 8px; padding: 3px 9px; border-radius: 999px; background: #f3e2c6; color: #8a5a2b; font-size: 10px; font-weight: 600; }
.conflict-card h2 { color: #6f4a22; font-size: 15px; }
.conflict-card ol { margin: 9px 0 0; padding-left: 20px; color: #7c6236; font-size: 11.5px; line-height: 1.8; }
.conflict-card code { color: #8a6531; }
.timeline { margin-top: 14px; padding: 6px 2px; }
.timeline-row { display: grid; grid-template-columns: 64px 12px 1fr; align-items: start; gap: 8px; padding: 5px 0; }
.timeline-time { color: #9aaa9c; font-size: 10px; font-variant-numeric: tabular-nums; }
.timeline-dot { width: 6px; height: 6px; margin-top: 5px; border-radius: 50%; background: #a9c7ac; }
.timeline-row p { color: #6f8374; font-size: 11.5px; line-height: 1.6; }

.report-layout { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr); gap: 14px; align-items: start; }
.report-paper { position: relative; overflow: hidden; padding: 26px 30px; border: 1px solid #e0e7db; border-radius: 12px; background: #fff; box-shadow: 0 12px 34px rgba(24, 52, 34, .08); }
.report-watermark { position: absolute; right: -46px; top: 34px; transform: rotate(24deg); color: rgba(180, 60, 40, .1); font-size: 22px; font-weight: 700; letter-spacing: .3em; pointer-events: none; }
.report-kicker { color: #8a9b8d; font-size: 10px; font-weight: 700; letter-spacing: .22em; }
.report-paper h2 { margin-top: 8px; font-size: 20px; }
.report-sub { margin-top: 6px !important; color: #6f8374; font-size: 11.5px; }
.report-badge { display: inline-flex; margin-top: 11px; padding: 3px 10px; border: 1px solid #cbb08c; border-radius: 999px; background: #fbf4e8; color: #8a5a2b; font-size: 10px; font-weight: 600; }
.report-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 18px; margin: 16px 0 0; padding: 12px 0; border-top: 1px solid #edf0ea; border-bottom: 1px solid #edf0ea; }
.report-meta div { min-width: 0; }
.report-meta dt { color: #93a295; font-size: 9.5px; letter-spacing: .06em; }
.report-meta dd { margin: 2px 0 0; color: #415b4a; font-size: 11px; overflow-wrap: anywhere; }
.report-paper section { margin-top: 14px; }
.report-paper h3 { margin-bottom: 7px; font-size: 12.5px; }
.report-sections { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 20px; margin: 0; padding-left: 18px; color: #5f7567; font-size: 11px; line-height: 1.7; }
.report-limits { margin: 0; padding-left: 18px; color: #7c6a4c; font-size: 10.5px; line-height: 1.7; }
.report-foot { margin-top: 15px; padding-top: 10px; border-top: 1px solid #edf0ea; color: #93a295; font-size: 10px; line-height: 1.6; }
.report-actions { display: flex; flex-direction: column; gap: 12px; }
.version-list { margin: 0; padding: 0; list-style: none; }
.version-list li { display: flex; align-items: baseline; gap: 9px; padding: 7px 0; border-bottom: 1px dashed #edf0ea; color: #7b8f80; font-size: 11px; }
.version-list li b { color: #47644f; font-size: 11px; }
.version-list li.current { color: #2f6a4a; }
.version-list li.current b { color: #2f6a4a; }
.download-state { margin-top: 10px !important; padding: 8px 11px; border-radius: 8px; background: #edf6e8; color: #2f6a4a; font-size: 11px; }

.retest-head { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 14px; }
.verdict-card { display: flex; flex-direction: column; justify-content: center; border-color: #d6e5d0; background: linear-gradient(150deg, #f2f9ee, #fbfcf8); }
.verdict-card strong { color: #2a5c3e; font-size: 26px; font-weight: 600; letter-spacing: -.02em; }
.verdict-card p { margin-top: 6px !important; color: #748877; font-size: 11.5px; line-height: 1.65; }
.retest-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr); gap: 14px; margin-top: 14px; }
.check-list { margin: 4px 0 0; padding: 0; list-style: none; }
.check-list li { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px dashed #edf0ea; color: #5f7567; font-size: 11.5px; }
.check-list li span { display: grid; place-items: center; width: 16px; height: 16px; border-radius: 50%; background: #dcecd7; color: #2f6a4a; font-size: 9px; font-weight: 700; }
.check-list li.warn span { background: #f3e3c6; color: #96652a; }
.check-list li.warn { color: #8a6a33; }
.final-card { margin-top: 14px; padding: 18px 20px; border-radius: 14px; border: 1px solid #d6e5d0; background: linear-gradient(120deg, #f1f8ec, #fbfcf7); }
.final-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 12px; }
.final-grid b { display: block; margin-bottom: 4px; color: #2f5a3f; font-size: 12px; }
.final-grid p { color: #6f8374; font-size: 11px; line-height: 1.65; }

.demo-tip { margin-top: 16px !important; padding-top: 13px; border-top: 1px dashed #e4eadf; color: #93a295; font-size: 11px; line-height: 1.65; }
.demo-tip span { display: inline-flex; margin-right: 9px; padding: 1px 7px; border-radius: 5px; background: #f1f5ec; color: #6f8a76; font-size: 9.5px; font-weight: 700; letter-spacing: .09em; }

.demo-controls { position: sticky; bottom: 0; z-index: 15; display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-top: 16px; padding: 12px 18px; border: 1px solid #dde6d8; border-radius: 14px; background: rgba(250, 252, 246, .94); backdrop-filter: blur(14px); box-shadow: 0 -10px 26px rgba(28, 60, 40, .07); }
.demo-disclaimer { color: #8a9b8d; font-size: 10.5px; line-height: 1.5; }
.demo-disclaimer span { margin-right: 7px; color: #c98a3c; font-size: 8px; }
.demo-nav { display: flex; align-items: center; gap: 8px; flex: none; }
.demo-counter { margin-right: 6px; color: #93a295; font-size: 11px; font-variant-numeric: tabular-nums; }
.demo-keys { margin-right: 8px; color: #a3b1a5; font-size: 10px; letter-spacing: .04em; }
@media (max-width: 900px) { .demo-keys { display: none; } }

@media (max-width: 1180px) {
  .demo-body { grid-template-columns: 1fr; padding: 16px; }
  .demo-rail { position: static; flex-direction: row; flex-wrap: wrap; align-items: center; gap: 4px; padding: 10px; }
  .demo-rail-title, .demo-rail-note { display: none; }
  .demo-rail-step { width: auto; padding: 7px 10px; }
  .rail-copy small { display: none; }
  .rail-state { display: none; }
  .scene-grid, .boundary-grid, .shortboard-grid, .evidence-list, .retest-head, .retest-grid, .report-layout { grid-template-columns: 1fr; }
  .agent-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .score-grid { grid-template-columns: 1fr; }
  .demo-scenario { display: none; }
}
@media (max-width: 760px) {
  .demo-topbar { flex-wrap: wrap; gap: 10px; padding: 10px 14px; }
  .demo-topbar-actions { width: 100%; margin-left: 0; }
  .demo-step { padding: 18px 16px; border-radius: 15px; }
  .demo-body { padding: 10px; }
  .demo-controls { flex-direction: column; align-items: flex-start; }
  .select-top, .audit-grid, .final-grid, .agent-grid { grid-template-columns: 1fr; }
  .progress-stages { grid-template-columns: 1fr 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .demo-fade-enter-active, .demo-fade-leave-active { transition: none; }
  .demo-shell * { animation-duration: .01ms !important; }
}
</style>
