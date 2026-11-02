<template>
  <section class="research-page" aria-label="Soilmate 研究工作台">
    <aside class="project-rail" aria-label="项目与数据">
      <label class="field-label">研究项目
        <select v-model="projectId" :disabled="loading"><option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option></select>
      </label>
      <details class="project-tools"><summary>项目与数据管理 <span>{{ datasets.length }} 个数据集</span></summary>
      <form class="project-create" @submit.prevent="createProject"><input v-model.trim="newProject" aria-label="新项目名称" placeholder="新建项目" minlength="2" maxlength="100" /><button type="submit" :disabled="!newProject||busy" aria-label="创建项目">＋</button></form>
      <details class="asset-drawer">
        <summary><b>数据资产</b><span>{{ datasets.length }} 个数据集</span><i aria-hidden="true">＋</i></summary>
        <div class="asset-content"><p v-if="!datasets.length" class="muted">当前项目尚无数据集。</p>
          <details v-for="d in datasets" :key="d.id" class="asset-row"><summary><span class="asset-kind" :class="`kind-${d.kind}`"></span><span><b>{{ d.name }}</b><small>{{ d.kind==='soil'?'土壤数据':'微生物数据' }} · {{ d.data_version }}</small></span><span class="asset-caret">⌄</span></summary><div class="asset-detail">{{ d.id }}<br>SHA-256 {{ d.source_sha256 }}</div></details>
          <label class="import-control">导入 CSV 数据集<input type="file" accept=".csv,text/csv" @change="importFile" :disabled="busy||!projectId" /></label>
          <p class="rail-footnote">不同项目的数据不会自动配对。</p></div>
      </details>
      </details>
    </aside>

    <main class="research-main">
      <header class="workspace-header">
        <div><span class="section-kicker">{{ traceOnly?'证据追溯 / TRACE':'分析中心 / RESEARCH' }}</span><h1>{{ traceOnly?'研究记录':'研究工作台' }}</h1><p class="header-description">{{ traceOnly?'查看分析任务、研究行动与报告版本。':'从当前样本出发，查看已有证据与可执行的下一步。' }}</p></div>
        <button type="button" class="back-link" @click="$emit('back')"><span aria-hidden="true">←</span> 返回地图</button>
      </header>

      <div v-if="mapPoint?.found" class="map-context"><span class="map-pin" aria-hidden="true">⌖</span><span><b>地图选点</b><small>{{ mapPoint.lat?.toFixed(4) }}° N · {{ mapPoint.lon?.toFixed(4) }}° E</small></span><span class="map-caveat">栅格位置尚未证明对应此研究样本</span></div>
      <p v-if="loading" class="loading-state" role="status">正在读取项目与研究记录…</p>
      <p v-if="error" class="error-state" role="alert">{{ error }}</p>

      <template v-if="!loading">
        <section class="subject-bar" aria-label="当前研究对象">
          <label class="sample-picker"><span>研究样本</span><select v-model="sampleId"><option value="">请选择样本</option><option v-for="s in samples" :key="s.id" :value="s.id">{{ s.external_id }} · {{ s.kind==='soil'?'土壤':'微生物' }}</option></select></label>
          <div v-if="currentSample" class="subject-meta"><span class="sample-dot" :class="`dot-${currentSample.kind}`"></span><span><b>{{ currentSample.kind==='soil'?'土壤样本':'微生物样本' }}</b><small>{{ currentSample.external_id }} · 数据集 {{ currentSample.dataset_id }}</small></span></div>
          <label v-if="currentSample?.kind==='microbiome'" class="module-picker"><span>分析过程</span><select v-model="moduleId"><option value="M00528">硝化 · M00528</option><option value="M00529">反硝化 · M00529</option><option value="M00530">DNRA · M00530</option></select></label>
          <button type="button" class="primary-action" :disabled="!sampleId||busy" @click="runAnalysis">{{ busy?'正在分析…':currentSample?.kind==='soil'?'运行健康指标审计':'分析通路结构' }}</button>
        </section>

        <div class="workspace-tabs" role="group" aria-label="工作台内容">
          <button type="button" :aria-pressed="activePanel==='overview'" @click="activePanel='overview'">研究结果</button>
          <button type="button" :aria-pressed="activePanel==='pairing'" @click="activePanel='pairing'">样本配对审核</button>
          <button type="button" :aria-pressed="activePanel==='records'" @click="activePanel='records'">任务与报告</button>
        </div>

        <ol class="research-stages" aria-label="研究流程与当前状态">
          <li v-for="stage in researchStages" :key="stage.id" :class="`stage-${stage.state}`">
            <span class="stage-number">{{ stage.number }}</span><span class="stage-copy"><b>{{ stage.name }}</b><small>{{ stage.status }}</small></span>
          </li>
        </ol>

        <section v-if="activePanel==='overview'" class="overview-layout">
          <div class="finding-column">
            <template v-if="currentRun">
              <article class="finding-lead" :class="`finding-${currentRun.status}`">
                <div class="finding-kicker"><span class="status-dot"></span>{{ currentRun.kind==='nshi'?'土壤健康评价':'微生物功能分析' }} <span>·</span> {{ statusLabel(currentRun.status) }}</div>
                <h2 v-if="currentRun.kind==='nshi'">{{ currentRun.result.nshi_score==null?'现有数据还不能形成综合健康评分':'土壤健康评价已完成' }}</h2>
                <h2 v-else>{{ currentRun.result.steps_observed>0?`在当前 KO 表中观察到 ${currentRun.result.steps_observed} 个通路步骤组合`:'当前分析未观察到通路步骤组合' }}</h2>
                <p v-if="currentRun.kind==='nshi'">缺少完整的生物转化维度与适用的参照阈值；当前结果用于指标审计和探索性筛选，不能作为已验证的健康等级。</p>
                <p v-else>KO 组合是通路结构线索。当前测序质控尚未核验，不能据此推断表达、酶活或氮转化速率。</p>
                <div v-if="currentRun.kind==='mfti'" class="coverage-line"><span>通路步骤覆盖</span><strong>{{ currentRun.result.steps_observed }} / {{ currentRun.result.steps_total }}</strong><div class="coverage-track" role="progressbar" :aria-valuenow="currentRun.result.steps_observed" :aria-valuemin="0" :aria-valuemax="currentRun.result.steps_total" aria-label="有 KO 组合的通路步骤比例"><i :style="{width:`${currentRun.result.steps_total?100*currentRun.result.steps_observed/currentRun.result.steps_total:0}%`}"></i></div><small>仅表示步骤存在 KO 组合，不代表生物活性。</small></div>
                <div v-else class="soil-summary"><span><small>本次审计指标</small><b>{{ currentRun.result.tds?.length || 0 }} 项</b></span><span><small>探索性维度</small><b>{{ currentRun.result.mds?.length || 0 }} 个</b></span><span><small>综合评分</small><b>未计算</b></span></div>
              </article>

              <section class="evidence-section"><h3>已有依据</h3>
                <template v-if="currentRun.kind==='nshi'"><div class="evidence-summary"><span>指标审计</span><b>{{ formatIndicators(currentRun.result.tds) || '没有可用指标' }}</b></div><div v-for="m in currentRun.result.mds" :key="m.domain" class="dimension-row"><span>{{ domainLabel(m.domain) }}</span><span>探索性候选：{{ formatIndicators(m.selected_exploratory) || '未筛出' }}</span><span>Bootstrap 保持率 {{ stabilityLabel(m.bootstrap_same_selection_fraction) }}</span></div><p class="evidence-copy">实际方法：{{ currentRun.result.selection_reason || currentRun.result.algorithm_source || '见运行版本' }}。数据集 {{ currentDataset?.name || currentRun.dataset_id }} · {{ datasetSampleCount(currentDataset) }} 个样本。字段单位与参照阈值尚待来源核实。</p><div v-if="currentRun.result.data_quality" class="quality-table" aria-label="指标数据质量"><div class="quality-row quality-heading"><span>指标</span><span>缺失率</span><span>IQR 异常</span><span>字段单位标记</span></div><div v-for="(q,key) in currentRun.result.data_quality" :key="key" class="quality-row"><b>{{ indicatorLabel(key) }}</b><span>{{ formatFraction(q.missing_fraction) }}</span><span>{{ q.iqr_outlier_count ?? '未计算' }}</span><span>{{ q.unit || '未提供' }} · 待核实</span></div></div><details class="evidence-details"><summary>查看原始值、维度与运行来源</summary><dl><template v-for="(v,k) in currentRun.result.raw_data" :key="k"><dt>{{ indicatorLabel(k) }}</dt><dd>{{ v ?? '缺失' }}</dd></template><dt>维度值</dt><dd>{{ JSON.stringify(currentRun.result.dimensions) }}</dd><dt>分析版本</dt><dd>{{ currentRun.algorithm_version }}</dd><dt>数据版本</dt><dd>{{ currentDataset?.data_version || '未登记' }}</dd><dt>数据来源</dt><dd>{{ currentRun.result.source?.source_uri }}</dd><dt>SHA-256</dt><dd class="hash-value">{{ currentRun.source_sha256 }}</dd></dl></details></template>
                <template v-else><div class="evidence-summary"><span>{{ currentRun.result.module_id }} · {{ currentRun.result.pathway_name || '氮循环通路模块' }}</span><b>{{ currentRun.result.structural_status || statusLabel(currentRun.status) }}</b></div><p class="evidence-copy">BioSample {{ currentRun.result.biosample || '未提供' }} · Run {{ currentRun.result.run_accession || '未提供' }} · 数据集 {{ currentDataset?.name || currentRun.dataset_id }} · {{ datasetSampleCount(currentDataset) }} 个样本</p><details class="evidence-details"><summary>查看注释来源与完整分析版本</summary><dl><dt>数据集</dt><dd>{{ currentRun.result.source?.dataset_id }}</dd><dt>数据版本</dt><dd>{{ currentRun.result.source?.version }}</dd><dt>来源位置</dt><dd>{{ currentRun.result.source?.source_uri }}</dd><dt>SHA-256</dt><dd class="hash-value">{{ currentRun.source_sha256 }}</dd><dt>运行 ID</dt><dd>{{ currentRun.id }}</dd></dl></details><section class="capability-note"><b>已知功能分析（依赖 KO 注释表）</b><p>分析范围限于已有 KO 注释与登记的通路步骤；本次输入能否支持计算，以运行状态和缺口为准。</p><b>未知功能候选挖掘 · 未接入</b><p>需要原始序列（FASTQ）、组装结果或蛋白序列（FASTA/FAA），并完成基因预测与功能注释；当前 KO 计数表不能替代这些输入。</p></section></template>
              </section>

              <section class="gap-section"><div><span class="gap-mark" aria-hidden="true">!</span><h3>结论受到什么限制</h3></div><ul><li v-for="g in currentRun.result.gaps" :key="g">{{ typeof g==='string'?g:JSON.stringify(g) }}</li><li v-if="currentRun.kind==='mfti'">该公开微生物样本未与当前土壤样本可靠配对，不能解释本地地块。</li></ul></section>
            </template>
            <div v-else class="empty-finding"><span class="empty-index">研究起点</span><h2>{{ currentSample?'准备分析当前样本':'先选择一个研究样本' }}</h2><p>{{ currentSample?'运行分析后，这里会显示真实结果、适用范围和仍然缺少的证据。':'选择已有土壤样本开展指标审计，或切换到公开微生物项目查看 KO 通路结构。' }}</p></div>
          </div>

          <aside class="action-column" aria-label="下一步研究行动">
            <p class="action-overline">下一步研究行动</p>
            <template v-if="currentRun">
              <h2>{{ decision?.chosen?.code ? actionLabel(decision.chosen.code) : '根据证据缺口决定下一步' }}</h2>
              <p v-if="!decision">{{ currentRun.kind==='nshi'?'优先补齐指标定义与适用阈值，再判断是否能形成可解释的评价。':'优先核验该 Run 的质控和注释信息；在质控不足时不估计检测概率。' }}</p>
              <p v-else>{{ decision.reason }}</p>
              <div v-if="decision" class="action-rationale"><span>建议动作 · {{ execution?.status || decision.status }}</span><b>{{ actionLabel(decision.chosen.code) }}</b><small>触发运行 {{ decision.run_id }} · {{ decision.chosen.class }}</small><small>{{ decision.chosen.precondition }}</small><small>收益 {{ decision.chosen.benefit }} / 成本 {{ decision.chosen.cost }} / 风险 {{ decision.chosen.risk }}</small></div>
              <button v-if="!decision" type="button" class="agent-primary" :disabled="busy" @click="plan">{{ busy?'正在规划…':'生成行动建议' }}</button>
              <button v-else type="button" class="agent-primary" :disabled="busy" @click="execute">{{ busy?'正在更新状态…':executionLabel(decision.chosen.class) }}</button>
              <p v-if="execution" class="execution-state" role="status">{{ execution.status }}：{{ execution.log.join('；') }}</p>
              <p class="action-footnote">需要人工审核或实验室操作的事项会标记为待处理，不会显示成已完成。</p>
            </template>
            <template v-else><h2>项目进度</h2><div class="project-snapshot" aria-label="项目已登记内容"><span><b>{{ samples.length }}</b><small>样本</small></span><span><b>{{ runs.length }}</b><small>分析运行</small></span><span><b>{{ reports.length }}</b><small>报告</small></span></div><p class="project-progress-note">{{ runs.length ? '已有分析记录，可查看运行与报告。' : '选定样本后运行审计，开始建立可追溯的研究记录。' }}</p><button v-if="runs.length || reports.length" type="button" class="secondary-action" @click="activePanel='records'">查看已有记录</button></template>
          </aside>
        </section>

        <section v-else-if="activePanel==='pairing'" class="single-panel">
          <div class="panel-intro"><h2>土壤与微生物样本是否来自同一研究对象？</h2><p>只有身份、采样日期、土层与来源证据经过核验，才允许地块级联合分析。自填信息只会形成待审核记录。</p></div>
          <div class="pairing-form"><label>土壤样本<select v-model="soilPairId"><option v-for="s in soilSamples" :key="s.id" :value="s.id">{{ s.external_id }}</option></select></label><span aria-hidden="true">↔</span><label>微生物样本<select v-model="microbePairId"><option v-for="s in microbeSamples" :key="s.id" :value="s.id">{{ s.external_id }}</option></select></label><button type="button" class="secondary-action" :disabled="!soilPairId||!microbePairId||busy" @click="auditPair">{{ busy?'正在核验…':'检查配对证据' }}</button></div>
          <div v-if="pairVerdict" class="pair-verdict" :class="`pair-${pairVerdict.status}`"><b>{{ pairVerdict.joint_analysis_allowed?'配对已允许联合分析':'当前禁止联合分析' }}</b><p>{{ pairVerdict.gaps.join('；') }}</p><small>审核状态：{{ pairStatusLabel(pairVerdict.status) }}</small></div>
          <div v-else class="pairing-empty"><b>目前尚无已验证的本地配对</b><p>公开 KO 案例可独立展示算法流程，但不会与土壤样本合并解释。</p></div>
          <section class="joint-checks" aria-labelledby="joint-check-title"><h3 id="joint-check-title">联合验证还需满足</h3><ul><li><b>样本身份、时间、土层与来源</b><span>{{ pairVerdict?.status==='rejected'?'本次审核未通过':'需要独立研究人员核验；自填信息不会自动批准' }}</span></li><li><b>独立氮循环功能目标</b><span>当前样本资产中未登记独立的氮转化速率、过程通量或实验测定目标</span></li><li><b>联合模型与比较方案</b><span>后端联合分析程序尚未接入；即使配对核验通过，也不会生成联合评分</span></li></ul></section>
        </section>

        <section v-else class="records-panel">
          <div class="records-heading"><div><h2>研究记录</h2><p>分析任务、Agent 行动和报告均按项目保存。</p></div><button type="button" class="secondary-action" :disabled="busy||!projectId||!runs.length" @click="makeReport">{{ busy?'正在生成…':'生成报告版本' }}</button></div>
          <label v-if="projectId==='local-soil-74'" class="public-reference"><input v-model="includePublicReference" type="checkbox" /> 在本地土壤报告中引用独立公开 KO 方法案例，并注明未配对</label><p v-if="reportMessage" class="report-message" role="status">{{ reportMessage }}</p>
          <div class="record-columns"><section><h3>分析任务</h3><button v-for="r in runs" :key="r.id" type="button" class="record-item" @click="loadRun(r.id);activePanel='overview'"><b>{{ r.kind==='nshi'?'N-SHI':'MFTI' }} · {{ statusLabel(r.status) }}</b><small>{{ r.id }}</small></button><p v-if="!runs.length" class="muted">尚无分析任务。</p></section><section><h3>Agent 行动</h3><div v-for="a in actions" :key="a.id" class="record-item"><b>{{ a.action_code }} · {{ a.status }}</b><small>{{ a.reason }}</small></div><p v-if="!actions.length" class="muted">尚无行动记录。</p></section><section><h3>报告版本</h3><a v-for="r in reports" :key="r.id" class="record-item report-link" :href="`/api/research/reports/${r.id}/download`" :download="`soilmate-report-v${r.version}.md`"><b>版本 {{ r.version }} · {{ r.created_at.slice(0,10) }}</b><small>下载研究报告 ↓</small></a><p v-if="!reports.length" class="muted">尚无报告版本。</p></section></div>
        </section>
      </template>
    </main>
  </section>
</template>

<script setup>
import {computed,nextTick,onMounted,ref,watch} from 'vue'
const props=defineProps({mapPoint:{type:Object,default:null},traceOnly:{type:Boolean,default:false},csrfToken:{type:String,required:true}})
defineEmits(['back'])
const projects=ref([]),projectId=ref(''),datasets=ref([]),samples=ref([]),soilSamples=ref([]),microbeSamples=ref([]),sampleId=ref(''),moduleId=ref('M00529'),runs=ref([]),reports=ref([]),actions=ref([]),currentRun=ref(null),decision=ref(null),execution=ref(null),pairVerdict=ref(null),soilPairId=ref(''),microbePairId=ref(''),newProject=ref(''),reportMessage=ref(''),includePublicReference=ref(false),loading=ref(true),busy=ref(false),error=ref(''),activePanel=ref(props.traceOnly?'records':'overview')
const currentProject=computed(()=>projects.value.find(p=>p.id===projectId.value))
const currentSample=computed(()=>samples.value.find(s=>s.id===sampleId.value))
const currentDataset=computed(()=>datasets.value.find(d=>d.id===currentRun.value?.dataset_id)||datasets.value.find(d=>d.id===currentSample.value?.dataset_id))
const researchStages=computed(()=>{
  const soilRun=currentRun.value?.kind==='nshi'?currentRun.value:runs.value.find(r=>r.sample_id===sampleId.value&&r.kind==='nshi')
  const microbeRun=currentRun.value?.kind==='mfti'?currentRun.value:runs.value.find(r=>r.sample_id===sampleId.value&&r.kind==='mfti')
  return [
    {id:'data',number:'01',name:'数据检查',status:currentSample.value?`${datasetSampleCount(currentDataset.value)} 个样本 · 来源已登记`:'请选择样本',state:currentSample.value?'ready':'pending'},
    {id:'soil',number:'02',name:'土壤指标筛选',status:soilRun?statusLabel(soilRun.status):'待运行',state:soilRun?'executed':'pending'},
    {id:'microbe',number:'03',name:'微生物功能分析',status:microbeRun?statusLabel(microbeRun.status):(currentSample.value?.kind==='microbiome'?'待运行':'切换公开 KO 项目'),state:microbeRun?'executed':'pending'},
    {id:'pair',number:'04',name:'配对与联合验证',status:pairVerdict?pairStatusLabel(pairVerdict.status):'未核验 · 联合程序待接入',state:pairVerdict?.joint_analysis_allowed?'done':'blocked'},
    {id:'agent',number:'05',name:'科研 Agent 决策',status:decision?.chosen?.code||'基于分析结果规划',state:decision?'done':'pending'}
  ]
})
async function api(path,method='GET',data){const headers=data?{'Content-Type':'application/json'}:{};if(!['GET','HEAD'].includes(method))headers['X-CSRF-Token']=props.csrfToken;const r=await fetch('/api/research'+path,{method,headers,credentials:'same-origin',body:data?JSON.stringify(data):undefined});if(!r.ok){const body=await r.json().catch(()=>({}));throw Error(body.detail||`HTTP ${r.status}`)}return r.json()}
async function refresh(){if(!projectId.value)return;loading.value=true;error.value='';reportMessage.value='';pairVerdict.value=null;try{const q=encodeURIComponent(projectId.value);[datasets.value,samples.value,runs.value,reports.value,actions.value]=await Promise.all([api('/datasets?project_id='+q),api('/samples?project_id='+q),api('/runs?project_id='+q),api('/reports?project_id='+q),api('/actions?project_id='+q)]);sampleId.value=samples.value[0]?.id||'';currentRun.value=null;decision.value=null;execution.value=null}catch(e){error.value=e.message}finally{loading.value=false;await nextTick();if(props.traceOnly)document.getElementById('research-history')?.scrollIntoView({block:'start'})}}
onMounted(async()=>{try{const b=await api('/bootstrap');projects.value=b.projects;projectId.value=b.projects[0]?.id||'';const ids=new Set(b.projects.map(p=>p.id));const [soil,microbe]=await Promise.all([ids.has('local-soil-74')?api('/samples?project_id=local-soil-74'):[],ids.has('public-ko-70')?api('/samples?project_id=public-ko-70'):[]]);soilSamples.value=soil;microbeSamples.value=microbe;soilPairId.value=soil[0]?.id||'';microbePairId.value=microbe[0]?.id||'';if(!projectId.value)loading.value=false}catch(e){error.value='项目目录读取失败：'+e.message;loading.value=false}})
watch(projectId,refresh)
async function createProject(){busy.value=true;error.value='';try{const p=await api('/projects','POST',{name:newProject.value});projects.value.push(p);newProject.value='';projectId.value=p.id}catch(e){error.value='创建失败：'+e.message}finally{busy.value=false}}
async function importFile(event){const file=event.target.files?.[0];if(!file)return;busy.value=true;error.value='';try{if(file.size>2_000_000)throw Error('文件超过 2 MB');const text=await file.text();const kind=text.split(/\r?\n/,1)[0].includes('soil_sample_id')?'soil':'microbiome';await api('/datasets/import','POST',{project_id:projectId.value,kind,name:file.name,source_name:file.name,csv_text:text});await refresh()}catch(e){error.value='导入失败：'+e.message}finally{busy.value=false;event.target.value=''}}
async function runAnalysis(){busy.value=true;error.value='';try{const kind=currentSample.value.kind==='soil'?'nshi':'mfti';currentRun.value=await api('/analyses/'+kind,'POST',{sample_id:sampleId.value,module_id:kind==='mfti'?moduleId.value:null});decision.value=null;execution.value=null;runs.value=await api('/runs?project_id='+encodeURIComponent(projectId.value))}catch(e){error.value='分析失败：'+e.message}finally{busy.value=false}}
async function loadRun(id){try{currentRun.value=await api('/runs/'+encodeURIComponent(id));decision.value=null;execution.value=null}catch(e){error.value=e.message}}
async function auditPair(){busy.value=true;error.value='';try{pairVerdict.value=await api('/pairings/audit','POST',{soil_sample_id:soilPairId.value,microbe_sample_id:microbePairId.value})}catch(e){error.value='配对审核失败：'+e.message}finally{busy.value=false}}
async function plan(){busy.value=true;error.value='';try{decision.value=await api('/actions/plan','POST',{project_id:projectId.value,run_ids:[currentRun.value.id]});execution.value=null}catch(e){error.value='行动规划失败：'+e.message}finally{busy.value=false}}
async function execute(){busy.value=true;error.value='';try{execution.value=await api('/actions/'+decision.value.id+'/execute','POST');actions.value=await api('/actions?project_id='+encodeURIComponent(projectId.value))}catch(e){error.value='执行失败：'+e.message}finally{busy.value=false}}
async function makeReport(){busy.value=true;error.value='';reportMessage.value='正在保存版本…';try{let reference_run_ids=[];if(includePublicReference.value&&projectId.value==='local-soil-74'){const publicRuns=await api('/runs?project_id=public-ko-70&limit=1');if(!publicRuns.length)throw Error('尚无公开 KO 运行记录；请先在公开项目执行 MFTI');reference_run_ids=[publicRuns[0].id]}const r=await api('/reports','POST',{project_id:projectId.value,run_ids:currentRun.value?[currentRun.value.id]:[],reference_run_ids});reports.value=await api('/reports?project_id='+encodeURIComponent(projectId.value));reportMessage.value=`v${r.version} 已保存，可从下方下载` }catch(e){reportMessage.value='失败：'+e.message}finally{busy.value=false}}
function statusLabel(status){return ({raw_data:'仅原始数据',exploratory_assessment:'探索性评价',validated_assessment:'经验证评价',insufficient_data:'数据不足，无法判断'})[status]||status}
function actionLabel(code){return ({CHECK_QC:'核验测序质控',CHECK_PATHWAY:'复核通路关键步骤',VERIFY_PAIRING:'核验样本配对',LAB_VALIDATION:'规划实验室验证',BIO_ASSAY:'补充生物转化指标',VERIFY_UNITS:'核对单位与参照阈值'})[code]||'根据证据缺口规划下一步'}
function domainLabel(domain){return ({nitrogen_supply:'氮素供给',nitrogen_retention:'氮素保持'})[domain]||domain}
function indicatorLabel(code){return ({TN_raw_percent:'全氮 TN',AN_raw_mgkg:'碱解氮 AN',CEC_raw_cmolkg:'阳离子交换量 CEC',BD_raw_gcm3:'土壤容重 BD'})[code]||code}
function formatIndicators(codes){if(typeof codes==='string')codes=codes.split(/[;,]/);return (codes||[]).map(indicatorLabel).join('、')}
function stabilityLabel(value){const n=Number(value);return Number.isFinite(n)?`${Math.round(n*100)}%`:String(value??'未知')}
function formatFraction(value){const n=Number(value);return Number.isFinite(n)?`${(100*n).toFixed(1)}%`:'未计算'}
function datasetSampleCount(dataset){const n=Number(dataset?.metadata?.rows);return Number.isFinite(n)?n:'数量未登记'}
function pairStatusLabel(status){return ({verified:'已独立核验',pending_independent_review:'待独立复核',rejected:'审核未通过'})[status]||status||'未核验'}
function executionLabel(actionClass){return ({computable:'执行这项检查',blocked_input:'登记所需输入',human_review:'登记待人工复核',laboratory:'登记实验验证计划'})[actionClass]||'记录下一步行动'}
</script>

<style scoped>
.research-page{--ink:#26343b;--muted:#6d7a7e;--line:#e1e5e1;--paper:#fff;--canvas:#f6f7f5;--green:#315c46;--green-soft:#eaf0eb;--amber:#92703a;--amber-soft:#f5f0e5;min-height:calc(100vh - 68px);display:grid;grid-template-columns:238px minmax(0,1fr);background:var(--canvas);color:var(--ink);font-family:Inter,"Aptos","Segoe UI","Microsoft YaHei",sans-serif;font-size:15px}
.research-page *{box-sizing:border-box}
.project-rail{min-width:0;background:#f0f2ee;border-right:1px solid var(--line);padding:24px 19px;display:flex;flex-direction:column}
.brand-lockup{display:flex;align-items:center;gap:11px;margin:0 0 31px}
.brand-mark{display:grid;place-items:center;width:34px;height:34px;border-radius:9px;background:#315c46;color:#fff;font-family:Georgia,serif;font-size:22px}
.brand-lockup b,.brand-lockup small{display:block}.brand-lockup b{font-size:15px;letter-spacing:-.02em}.brand-lockup small{margin-top:3px;color:var(--muted);font-size:11px}
.field-label,.sample-picker,.module-picker{display:flex;flex-direction:column;gap:8px;font-size:12px;font-weight:650;color:#59676a}
.research-page select,.research-page input:not([type=file]){width:100%;min-width:0;min-height:42px;padding:9px 11px;border:1px solid #d5dbd5;border-radius:6px;background:#fff;color:var(--ink);font:inherit}
.project-create{display:flex;gap:6px;margin-top:9px}.project-create button{width:42px;flex:0 0 42px;border:1px solid #d5dbd5;border-radius:6px;background:#fff;color:var(--green);font-size:21px}
.rail-rule{height:1px;background:var(--line);margin:25px 0 17px}.asset-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:7px;font-size:13px}.asset-heading span{color:var(--muted);font-variant-numeric:tabular-nums}
.asset-row{border-bottom:1px solid #dfe4de}.asset-row summary{display:flex;align-items:center;gap:9px;padding:12px 0;cursor:pointer;list-style:none}.asset-row summary::-webkit-details-marker{display:none}.asset-row summary>span:nth-child(2){min-width:0;flex:1}.asset-row b,.asset-row small{display:block}.asset-row b{font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.asset-row small{margin-top:3px;color:var(--muted);font-size:11px}.asset-kind{width:8px;height:8px;border-radius:50%;background:#739276}.kind-microbiome{background:#8592a0}.asset-caret{color:var(--muted)}.asset-detail{padding:0 0 12px 17px;color:var(--muted);font:10px/1.7 ui-monospace,Consolas,monospace;overflow-wrap:anywhere}
.import-control{display:block;margin-top:18px;color:var(--green);font-size:12px;font-weight:600}.import-control input{display:block;width:100%;margin-top:8px;font-size:11px}
.rail-footnote,.muted{color:var(--muted);font-size:12px;line-height:1.6}.rail-footnote{margin-top:auto;padding-top:28px}
.research-main{width:100%;max-width:1560px;min-width:0;margin:0 auto;padding:34px clamp(28px,4vw,64px) 88px}
.workspace-header{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:25px}.project-crumb{margin:0 0 8px;color:var(--muted);font-size:12px}.workspace-header h1{margin:0;font-size:32px;line-height:1.15;letter-spacing:-.04em;font-weight:650}.header-description{margin:9px 0 0;color:var(--muted);font-size:14px;line-height:1.6}
.back-link{flex:none;padding:9px 0;border:0;background:transparent;color:var(--green);font-family:inherit;font-size:13px;font-weight:600;cursor:pointer}.back-link span{margin-right:5px}
.map-context{display:flex;align-items:center;gap:11px;padding:11px 14px;margin:0 0 18px;background:#edf0eb;border-left:2px solid #829682;color:#53635b}.map-pin{font-size:18px}.map-context b,.map-context small{display:block}.map-context b{font-size:12px}.map-context small,.map-caveat{font-size:11px;color:var(--muted)}.map-caveat{margin-left:auto}
.loading-state,.error-state{padding:13px 15px;border-radius:5px}.loading-state{background:#edf1ed;color:#52675a}.error-state{background:#f7e9e5;color:#8b3f33}
.subject-bar{display:flex;align-items:end;gap:15px;padding:15px 0 18px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.sample-picker{width:min(330px,34%)}.module-picker{width:190px}.subject-meta{display:flex;align-items:center;gap:9px;min-width:0;flex:1;padding-bottom:5px}.subject-meta>span:last-child{min-width:0}.subject-meta b,.subject-meta small{display:block}.subject-meta b{font-size:12px}.subject-meta small{margin-top:4px;color:var(--muted);font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.sample-dot{width:9px;height:9px;flex:none;border-radius:50%;background:#728b70}.dot-microbiome{background:#73899a}
.primary-action,.agent-primary{min-height:42px;padding:0 16px;border:0;border-radius:6px;background:var(--green);color:white;font-family:inherit;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap}.primary-action:hover,.agent-primary:hover{background:#264b38}.research-page button:disabled{opacity:.45;cursor:not-allowed}
.workspace-tabs{display:flex;gap:27px;margin:0 0 20px;border-bottom:1px solid var(--line)}.workspace-tabs button{position:relative;padding:14px 0 13px;border:0;background:transparent;color:#667378;font-family:inherit;font-size:13px;font-weight:500;cursor:pointer}.workspace-tabs button[aria-pressed="true"]{color:var(--ink);font-weight:650}.workspace-tabs button[aria-pressed="true"]::after{position:absolute;right:0;bottom:-1px;left:0;height:2px;background:var(--green);content:""}
.research-stages{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin:0 0 25px;padding:0 0 19px;border-bottom:1px solid var(--line);list-style:none}.research-stages li{display:flex;gap:9px;min-width:0;align-items:flex-start}.stage-number{display:grid;place-items:center;width:24px;height:24px;flex:none;border:1px solid #cfd6ce;border-radius:50%;color:#697670;font-size:10px;font-variant-numeric:tabular-nums}.stage-copy{min-width:0}.stage-copy b,.stage-copy small{display:block}.stage-copy b{font-size:11px;font-weight:650;line-height:1.4}.stage-copy small{margin-top:4px;color:var(--muted);font-size:10px;line-height:1.45}.stage-ready .stage-number,.stage-executed .stage-number{border-color:#78917b;background:#edf2ed;color:#315c46}.stage-blocked .stage-number{border-color:#c7b18b;background:#f5f0e5;color:#806339}
.overview-layout{display:grid;grid-template-columns:minmax(0,1fr) 282px;gap:clamp(24px,4vw,54px);align-items:start}
.finding-column{min-width:0}.finding-lead{padding:20px 0 27px;border-bottom:1px solid var(--line)}.finding-kicker{display:flex;align-items:center;gap:8px;color:#53645c;font-size:12px;font-weight:600}.status-dot{width:8px;height:8px;border-radius:50%;background:#a1844e}.finding-exploratory_assessment .status-dot,.finding-validated_assessment .status-dot{background:#547d5d}.finding-raw_data .status-dot{background:#7d8985}
.finding-lead h2{max-width:760px;margin:18px 0 11px;font-size:clamp(29px,3vw,40px);line-height:1.19;letter-spacing:-.045em;font-weight:620}.finding-lead>p{max-width:760px;margin:0;color:#59676b;font-size:15px;line-height:1.72}
.coverage-line{max-width:560px;margin-top:27px}.coverage-line>span{color:#56655e;font-size:12px}.coverage-line>strong{float:right;font-size:14px;font-variant-numeric:tabular-nums}.coverage-track{height:6px;clear:both;margin-top:11px;overflow:hidden;border-radius:5px;background:#e1e7e1}.coverage-track i{display:block;height:100%;border-radius:inherit;background:#52795d}.coverage-line>small{display:block;margin-top:8px;color:var(--muted);font-size:11px}
.soil-summary{display:flex;gap:38px;margin-top:26px}.soil-summary span{display:flex;flex-direction:column;gap:5px}.soil-summary small{color:var(--muted);font-size:11px}.soil-summary b{font-size:15px;font-weight:620}
.evidence-section{padding:24px 0 20px}.evidence-section h3,.gap-section h3{margin:0 0 14px;font-size:16px;font-weight:650;letter-spacing:-.015em}.evidence-summary{display:flex;justify-content:space-between;gap:15px;padding:0 0 13px;border-bottom:1px solid var(--line);font-size:12px}.evidence-summary span{color:var(--muted)}.evidence-summary b{font-weight:600;text-align:right}.dimension-row{display:grid;grid-template-columns:minmax(110px,.8fr) minmax(120px,1fr) minmax(150px,1fr);gap:12px;padding:11px 0;border-bottom:1px solid #eaede9;font-size:12px}.dimension-row span:not(:first-child){color:#5b696d}
.evidence-copy{color:#59676b;font-size:13px}.evidence-details{margin-top:13px;color:var(--muted);font-size:12px}.evidence-details summary{width:max-content;max-width:100%;cursor:pointer;color:var(--green)}.evidence-details dl{display:grid;grid-template-columns:130px minmax(0,1fr);gap:7px 15px;margin:14px 0 0;padding:14px;background:#f0f2ef}.evidence-details dt{color:var(--muted)}.evidence-details dd{margin:0;color:var(--ink);overflow-wrap:anywhere}.hash-value{font:11px/1.6 ui-monospace,Consolas,monospace}
.quality-table{margin-top:14px;border-top:1px solid var(--line)}.quality-row{display:grid;grid-template-columns:minmax(115px,1.2fr) repeat(3,minmax(80px,1fr));gap:10px;padding:9px 4px;border-bottom:1px solid #eaede9;color:#4f5e61;font-size:11px}.quality-row b{font-weight:600}.quality-heading{color:var(--muted);font-size:10px}.capability-note{display:grid;grid-template-columns:minmax(150px,.7fr) minmax(0,1.3fr);gap:5px 18px;margin-top:20px;padding:15px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.capability-note>b{font-size:12px}.capability-note>b:nth-of-type(2){color:#806339}.capability-note p{margin:0 0 8px;color:#5e6b6d;font-size:12px;line-height:1.6}
.gap-section{display:grid;grid-template-columns:205px minmax(0,1fr);gap:20px;padding:17px 0 18px;border-top:1px solid #e5e3dc;border-bottom:1px solid #e5e3dc}.gap-section>div{display:flex;align-items:flex-start;gap:9px}.gap-section h3{margin:1px 0 0}.gap-mark{display:grid;place-items:center;width:19px;height:19px;flex:none;border-radius:50%;background:#eee5d3;color:#806339;font-size:12px;font-weight:700}.gap-section ul{margin:0;padding-left:18px;color:#5d6665;font-size:13px;line-height:1.65}.gap-section li+li{margin-top:4px}
.empty-finding{min-height:330px;padding:48px 0;border-bottom:1px solid var(--line)}.empty-index{color:#748079;font-size:12px}.empty-finding h2{max-width:560px;margin:20px 0 10px;font-size:34px;line-height:1.2;letter-spacing:-.04em}.empty-finding p{max-width:560px;color:#667378;font-size:15px;line-height:1.7}
.action-column{position:sticky;top:22px;padding:19px 19px 20px;background:#edf1ed;border-top:2px solid #6e8a73}.action-overline{margin:0 0 15px;color:#5f7564;font-size:11px;font-weight:650}.action-column h2{margin:0 0 10px;font-size:21px;line-height:1.3;letter-spacing:-.025em;font-weight:630}.action-column>p:not(.action-overline):not(.action-footnote){margin:0;color:#5b6963;font-size:13px;line-height:1.7}.agent-primary{width:100%;margin-top:19px}.action-rationale{display:flex;flex-direction:column;gap:7px;margin-top:17px;padding-top:14px;border-top:1px solid #d7dfd7}.action-rationale span,.action-rationale small{color:#65746a;font-size:11px}.action-rationale b{font-size:13px}.action-footnote{margin:13px 0 0;color:#718077;font-size:11px;line-height:1.6}.execution-state{margin:14px 0 0;padding:10px;background:#fff;color:#415b49;font-size:12px;line-height:1.6}.action-hint{display:inline-block;margin-top:16px;padding:5px 8px;background:#fff;color:#596d60;font-size:11px}
.single-panel,.records-panel{padding:18px 0}.panel-intro{max-width:780px}.panel-intro h2,.records-heading h2{margin:0 0 9px;font-size:25px;letter-spacing:-.03em}.panel-intro p,.records-heading p{margin:0;color:#637075;font-size:14px;line-height:1.7}.pairing-form{display:flex;align-items:end;gap:16px;max-width:880px;margin:29px 0;padding:22px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.pairing-form label{display:flex;flex:1;flex-direction:column;gap:8px;color:#59676a;font-size:12px;font-weight:600}.pairing-form>span{padding-bottom:12px;color:#7b8980}.secondary-action{min-height:40px;padding:0 14px;border:1px solid #bac8bc;border-radius:5px;background:transparent;color:#315c46;font-family:inherit;font-size:12px;font-weight:600;cursor:pointer}.secondary-action:hover{background:#edf1ed}.pairing-empty{max-width:740px;padding:14px 0;border-left:2px solid #ad925e}.pairing-empty b,.pairing-empty p{margin-left:15px}.pairing-empty b{font-size:13px}.pairing-empty p{color:#68746f;font-size:13px}.pair-verdict{max-width:840px;padding:16px 18px;border-left:3px solid #9c7e47;background:var(--amber-soft)}.pair-verdict b{font-size:14px}.pair-verdict p{margin:8px 0;color:#5e665f;font-size:13px;line-height:1.6}.pair-verdict small{color:#7b715d;font-size:11px}.pair-approved{border-color:#53795b;background:#edf2ed}
.joint-checks{max-width:840px;margin-top:33px}.joint-checks h3{margin:0 0 12px;font-size:15px}.joint-checks ul{margin:0;padding:0;list-style:none;border-top:1px solid var(--line)}.joint-checks li{display:grid;grid-template-columns:minmax(190px,.8fr) minmax(0,1.2fr);gap:15px;padding:12px 0;border-bottom:1px solid var(--line);font-size:12px}.joint-checks li b{font-weight:600}.joint-checks li span{color:var(--muted);line-height:1.55}
.records-heading{display:flex;justify-content:space-between;align-items:center;gap:22px;padding-bottom:18px;border-bottom:1px solid var(--line)}.public-reference{display:flex;gap:9px;align-items:center;margin:15px 0;color:#596c60;font-size:12px}.public-reference input{width:16px!important;min-height:16px!important}.report-message{color:#53675a;font-size:13px}.record-columns{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px;margin-top:24px}.record-columns h3{margin:0 0 9px;font-size:14px}.record-item{display:block;width:100%;padding:12px 0;border:0;border-top:1px solid var(--line);background:transparent;text-align:left;color:var(--ink);text-decoration:none;cursor:pointer}.record-item b,.record-item small{display:block}.record-item b{font-size:12px;font-weight:600}.record-item small{margin-top:4px;color:var(--muted);font-size:11px;line-height:1.5;overflow-wrap:anywhere}.report-link:hover b{color:var(--green)}
.research-page button:focus-visible,.research-page a:focus-visible,.research-page select:focus-visible,.research-page input:focus-visible,.research-page summary:focus-visible{outline:3px solid rgba(49,92,70,.27);outline-offset:2px}
@media(max-width:1120px){.research-page{grid-template-columns:210px minmax(0,1fr)}.research-main{padding-right:30px;padding-left:30px}.overview-layout{grid-template-columns:minmax(0,1fr) 250px;gap:26px}.subject-bar{flex-wrap:wrap}.sample-picker{width:45%}.subject-meta{flex-basis:45%}.action-column{top:12px}}
@media(max-width:900px){.research-stages{grid-template-columns:repeat(3,minmax(0,1fr));row-gap:13px}}
@media(max-width:850px){.research-page{grid-template-columns:1fr}.project-rail{padding:14px 20px;border-right:0;border-bottom:1px solid var(--line)}.brand-lockup{margin:0 0 13px}.project-rail>.field-label{max-width:420px}.project-create{max-width:420px}.rail-rule{margin:14px 0 8px}.asset-row,.asset-heading,.import-control,.rail-footnote{max-width:520px}.rail-footnote{margin-top:4px;padding-top:12px}.research-main{padding:25px 24px 60px}.overview-layout{grid-template-columns:1fr}.action-column{position:static;grid-row:2}.finding-lead h2{font-size:34px}.map-caveat{max-width:45%;text-align:right}}
@media(max-width:560px){.research-main{padding:21px 17px 45px}.workspace-header h1{font-size:28px}.header-description{font-size:13px}.back-link{font-size:12px}.subject-bar{align-items:stretch;gap:12px}.sample-picker,.module-picker{width:100%}.subject-meta{flex-basis:100%;padding:0}.primary-action{width:100%}.workspace-tabs{gap:19px;overflow-x:auto}.workspace-tabs button{flex:none;font-size:12px}.finding-lead{padding-top:18px}.finding-lead h2{font-size:29px}.finding-lead>p{font-size:14px}.soil-summary{gap:20px;justify-content:space-between}.soil-summary b{font-size:13px}.dimension-row{grid-template-columns:1fr;gap:5px}.gap-section{grid-template-columns:1fr;gap:9px}.gap-section ul{padding-left:18px}.pairing-form{flex-direction:column;align-items:stretch}.pairing-form>span{display:none}.record-columns{grid-template-columns:1fr;gap:20px}.records-heading{align-items:flex-start;flex-direction:column}.evidence-details dl{grid-template-columns:1fr;gap:3px}.evidence-details dd{margin-bottom:9px}.map-context{align-items:flex-start;flex-wrap:wrap}.map-caveat{flex-basis:100%;max-width:none;margin-left:28px;text-align:left}}
@media(max-width:560px){.research-stages{grid-template-columns:repeat(2,minmax(0,1fr));gap:13px 9px}.stage-copy b{font-size:10px}.stage-copy small{font-size:9px}.quality-row{grid-template-columns:minmax(94px,1.1fr) repeat(2,minmax(62px,.8fr));gap:6px;font-size:10px}.quality-row>:last-child{grid-column:2/-1;color:var(--muted)}.quality-heading>:last-child{grid-column:2/-1}.capability-note{grid-template-columns:1fr;gap:4px}.capability-note p{margin-bottom:9px}.joint-checks li{grid-template-columns:1fr;gap:4px}}
.asset-drawer{margin-top:20px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.asset-drawer>summary{display:flex;align-items:center;gap:9px;padding:13px 0;cursor:pointer;list-style:none}.asset-drawer>summary::-webkit-details-marker{display:none}.asset-drawer>summary b{font-size:13px}.asset-drawer>summary span{margin-left:auto;color:var(--muted);font-size:11px}.asset-drawer>summary i{font-style:normal;color:var(--muted);font-size:15px}.asset-drawer[open]>summary i{transform:rotate(45deg)}.asset-content{padding:0 0 14px}.asset-content>.muted{margin:0 0 10px}.rail-footnote{margin:12px 0 0;padding:0;font-size:11px}
@media(max-width:850px){.project-rail{padding:12px 20px}.brand-lockup{margin:0 0 11px}.field-label{display:grid;grid-template-columns:88px minmax(0,1fr);align-items:center;gap:12px}.project-create{margin-top:7px}.asset-drawer{margin-top:11px}.asset-drawer>summary{padding:10px 0}.rail-footnote{margin-top:8px}}
@media(prefers-reduced-motion:reduce){.research-page *{scroll-behavior:auto!important;transition:none!important}}

/* Soilmate research product system. One action hierarchy, quiet data surfaces. */
.research-page {
  --ink: #1f2923;
  --muted: #66736a;
  --line: #e2e8e2;
  --canvas: #f7f9f7;
  --green: #246b46;
  --green-soft: #edf5ee;
  display: block;
  min-height: calc(100dvh - 62px);
  background: var(--canvas);
  color: var(--ink);
  font-family: "DengXian", "PingFang SC", "Microsoft YaHei UI", sans-serif;
  font-size: 14px;
}
.project-rail {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  gap: 20px;
  min-height: 86px;
  padding: 14px max(28px, calc((100vw - 1180px) / 2));
  border-right: 0;
  border-bottom: 1px solid var(--line);
  background: #fff;
}
.project-rail>.field-label { width: min(330px, 100%); flex: none; gap: 6px; text-align: left; align-items: stretch; color: #607067; font-size: 11px; font-weight: 600; }
.research-page select, .research-page input:not([type=file]) {
  min-height: 40px;
  padding: 8px 11px;
  border: 1px solid #d9e2da;
  border-radius: 8px;
  background: #fff;
  box-shadow: none;
  color: var(--ink);
  font-size: 13px;
}
.research-page select:hover, .research-page input:not([type=file]):hover { border-color: #9bbda4; }
.research-page :is(select, input:not([type=file])):focus-visible { outline: 3px solid rgba(36, 107, 70, .22); outline-offset: 1px; border-color: var(--green); }
.project-tools { min-width: 190px; margin: 0 0 2px auto; border: 0; }
.project-tools>summary {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 40px;
  padding: 0 10px;
  border: 1px solid #dfe7e0;
  border-radius: 8px;
  background: #fff;
  color: #4e6654;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  list-style: none;
}
.project-tools>summary::-webkit-details-marker { display: none; }
.project-tools>summary::before { content: "+"; color: var(--green); font-size: 16px; font-weight: 400; }
.project-tools[open]>summary::before { content: "−"; }
.project-tools>summary span { margin-inline-start: auto; color: var(--muted); font-size: 10px; font-weight: 400; }
.project-tools[open] { min-width: 270px; }
.project-tools .project-create { margin-top: 12px; }
.project-create button { width: 40px; flex-basis: 40px; border-color: var(--line); border-radius: 8px; background: #fff; }
.project-tools .asset-drawer { margin-top: 10px; border-color: var(--line); }
.asset-drawer>summary { min-height: 40px; }
.research-main { width: 100%; max-width: 1240px; margin: 0 auto; padding: 28px 30px 80px; }
.workspace-header { align-items: flex-end; margin-bottom: 20px; }
.project-crumb { display: none; }
.workspace-header h1 { margin: 0; font-size: 31px; line-height: 1.17; letter-spacing: -.035em; font-weight: 700; }
.header-description { margin: 7px 0 0; color: var(--muted); font-size: 13px; line-height: 1.55; }
.back-link { min-height: 36px; padding: 0 10px; border: 0; border-radius: 7px; background: transparent; box-shadow: none; color: var(--green); font-size: 12px; }
.back-link:hover { background: #edf3ed; box-shadow: none; }
.subject-bar {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 18px;
  padding: 17px 19px;
  border: 1px solid var(--line);
  border-radius: 11px;
  background: #fff;
  box-shadow: none;
}
.field-label, .sample-picker, .module-picker { gap: 7px; color: #607067; font-size: 11px; font-weight: 600; }
.sample-picker { width: min(330px, 34%); }
.subject-meta { padding-bottom: 0; }
.subject-meta b { font-size: 12px; }
.subject-meta small { color: var(--muted); font-size: 10px; }
.sample-dot { width: 7px; height: 7px; background: var(--green); }
.primary-action, .agent-primary {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 8px;
  background: var(--green);
  box-shadow: none;
  color: #fff;
  font-size: 12px;
  font-weight: 650;
  transition: background-color .16s ease, transform .16s ease;
}
.primary-action:hover:not(:disabled), .agent-primary:hover:not(:disabled) { background: #1b5637; box-shadow: none; }
.primary-action:active:not(:disabled), .agent-primary:active:not(:disabled) { transform: scale(.985); }
.workspace-tabs { width: 100%; gap: 25px; margin-bottom: 0; padding: 0; border: 0; border-bottom: 1px solid var(--line); border-radius: 0; background: transparent; }
.workspace-tabs button { min-height: 42px; padding: 9px 1px 10px; border-radius: 0; color: #69766d; font-size: 12px; }
.workspace-tabs button[aria-pressed="true"] { border-bottom: 2px solid var(--green); background: transparent; box-shadow: none; color: var(--green); font-weight: 700; }
.workspace-tabs button[aria-pressed="true"]::after { content: none; }
.research-stages { gap: 0; margin: 0 0 24px; padding: 17px 0 15px; border: 0; border-bottom: 1px solid var(--line); }
.research-stages li { min-height: 0; gap: 8px; padding: 0 9px 0 0; border-radius: 0; background: transparent !important; }
.stage-number { width: 22px; height: 22px; border: 1px solid #d4dfd5; border-radius: 6px; background: #fff; font-size: 9px; }
.stage-ready .stage-number, .stage-executed .stage-number { background: var(--green-soft); color: var(--green); }
.stage-copy b { color: #3d5042; font-size: 10px; }
.stage-copy small { margin-top: 2px; color: #809087; font-size: 9px; }
.overview-layout { grid-template-columns: minmax(0, 1fr) 272px; gap: 24px; }
.empty-finding, .finding-lead {
  min-height: 0;
  padding: 29px 30px;
  border: 1px solid var(--line);
  border-radius: 11px;
  background: #fff;
  box-shadow: none;
}
.empty-index { color: var(--green); font-size: 11px; font-weight: 600; }
.empty-finding h2 { margin: 13px 0 8px; font-size: 27px; line-height: 1.22; letter-spacing: -.025em; }
.empty-finding p { max-width: 510px; margin: 0; color: var(--muted); font-size: 13px; line-height: 1.6; }
.action-column { padding: 22px; border: 1px solid var(--line); border-radius: 11px; background: #f0f5f0; box-shadow: none; }
.action-overline { margin-bottom: 10px; color: var(--green); font-size: 11px; }
.action-column h2 { margin-bottom: 9px; font-size: 18px; font-weight: 680; }
.project-snapshot { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin: 15px 0; padding: 13px 0; border-top: 1px solid #dbe6dc; border-bottom: 1px solid #dbe6dc; }
.project-snapshot b, .project-snapshot small { display: block; }
.project-snapshot b { font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums; }
.project-snapshot small { margin-top: 2px; color: var(--muted); font-size: 10px; }
.project-progress-note { margin: 0 0 11px !important; color: var(--muted) !important; font-size: 11px !important; line-height: 1.5 !important; }
.action-column .secondary-action { width: 100%; min-height: 36px; border-color: #cbdccb; border-radius: 7px; background: #fff; }
.single-panel, .records-panel { padding: 26px; border: 1px solid var(--line); border-radius: 11px; background: #fff; }
.secondary-action { min-height: 38px; border-radius: 7px; }
.map-context, .loading-state, .error-state, .pair-verdict { border-radius: 8px; }
.research-page :is(button, a, summary):focus-visible { outline: 3px solid rgba(36, 107, 70, .3); outline-offset: 2px; }
@media (max-width: 900px) {
  .research-main { padding-inline: 24px; }
  .overview-layout { grid-template-columns: minmax(0, 1fr) 245px; gap: 16px; }
}
@media (max-width: 700px) {
  .project-rail { display: block; min-height: 0; padding: 13px 18px 8px; }
  .project-rail>.field-label { display: flex; width: 100%; max-width: none; gap: 5px; align-items: stretch; }
  .project-rail select { min-height: 40px; }
  .project-tools { width: 100%; min-width: 0; margin: 6px 0 0; }
  .project-tools>summary { min-height: 31px; padding: 0 3px; border: 0; border-radius: 0; background: transparent; }
  .project-tools[open] { width: 100%; min-width: 0; }
  .research-main { padding: 22px 18px 60px; }
  .workspace-header { position: relative; align-items: flex-start; margin-bottom: 17px; }
  .workspace-header>div { padding-top: 27px; }
  .workspace-header h1 { font-size: 29px; }
  .header-description { max-width: 34ch; font-size: 12px; }
  .back-link { position: absolute; top: 0; left: -9px; min-height: 27px; }
  .subject-bar { display: grid; gap: 11px; margin-bottom: 15px; padding: 14px; }
  .sample-picker, .module-picker { width: 100%; }
  .subject-meta { order: 2; }
  .primary-action { order: 3; width: 100%; min-height: 43px; }
  .workspace-tabs { gap: 17px; overflow-x: auto; }
  .workspace-tabs button { flex: none; font-size: 11px; }
  .research-stages { display: flex; gap: 12px; margin-inline: -18px; padding: 13px 18px; overflow-x: auto; scrollbar-width: none; scroll-snap-type: x proximity; }
  .research-stages::-webkit-scrollbar { display: none; }
  .research-stages li { flex: 0 0 136px; scroll-snap-align: start; }
  .overview-layout { grid-template-columns: 1fr; gap: 13px; }
  .empty-finding, .finding-lead { padding: 22px; }
  .empty-finding h2 { font-size: 24px; }
  .action-column { position: static; padding: 19px; }
  .single-panel, .records-panel { padding: 20px; }
}
@media (prefers-reduced-motion: reduce) {
  .primary-action, .agent-primary { transition: none; }
}

.research-page h1,.research-page h2{font-family:Georgia,'STSong','Songti SC','Noto Serif CJK SC','SimSun',serif;letter-spacing:-.025em}
</style>
