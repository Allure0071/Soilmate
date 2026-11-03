<template>
  <div class="research-tool">
    <div class="texture-layout">
      <section class="texture-input">
        <div class="calculator-section-heading"><h2>组分比例</h2><button type="button" class="tool-text-button" @click="example">载入示例</button></div>
        <p class="tool-intro">采用 USDA 12 类体系。请输入同一样本中砂、粉、黏粒的质量百分比。</p>
        <p v-if="demo" class="calculator-example-note">当前为演示参数，不代表实测数据。</p>
        <form class="calculator-fields" @submit.prevent="run">
          <label v-for="(label,key) in labels" :key="key"><span>{{ label }}<small>%</small></span><input v-model="values[key]" type="text" inputmode="decimal" :aria-label="`${label}百分比`" maxlength="20" /></label>
          <p class="texture-total">当前合计 <strong>{{ total }}%</strong></p>
          <label class="tool-checkbox"><input v-model="normalize" type="checkbox" />按总量归一化到 100%（保留原始输入）</label>
          <p v-if="error" class="calculator-error" role="alert">{{ error }}</p>
          <div class="research-actions"><button type="submit" class="tool-primary-button">判别并标记</button><button type="button" class="tool-text-button" @click="reset">清空</button></div>
        </form>
        <section v-if="result" class="texture-verdict" aria-live="polite"><span>USDA 质地类别</span><h3>{{ result.name }}</h3><p>{{ result.english }} · {{ result.id }}</p><p>砂 {{ fmt(result.sand) }}% · 粉 {{ fmt(result.silt) }}% · 黏 {{ fmt(result.clay) }}%</p><p v-if="result.normalized">已按原始合计 {{ fmt(result.total) }}% 归一化；分类使用归一化后的比例。</p><div class="research-actions"><button type="button" class="tool-text-button" @click="saveText">下载判别记录</button><button type="button" class="tool-text-button" @click="saveSvg">下载三角图 SVG</button></div></section>
        <p v-else class="tool-note">输入有效比例后，分类和样点会一起显示。参数仅在本页处理。</p>
      </section>
      <section class="texture-chart-panel"><h2>质地三角图</h2><TextureTriangle ref="triangle" :result="result" /><ul class="texture-legend"><li v-for="item in textureClasses" :key="item.id" :class="{ 'is-current':result?.id===item.id }"><b>{{ item.id }}</b>{{ item.name }}</li></ul></section>
    </div>
    <section class="research-method"><h2>分类口径与使用范围</h2><p>仅针对小于 2 mm 的细土部分：砂粒 0.05～2 mm，粉粒 0.002～0.05 mm，黏粒小于 0.002 mm。大于 2 mm 的砾石不计入这三个比例。不同体系的粒径界限可能不同，请先核对检测报告。</p><p>这是粒级组成分类，不代表土壤健康、肥力或种植适宜性。中文名称为阅读辅助，英文类名和 USDA 体系共同标识结果。</p><details><summary>查看数值分类规则</summary><pre class="texture-rules">{{ rules }}</pre></details><ul class="tool-sources"><li><a :href="source" target="_blank" rel="noopener noreferrer">USDA NRCS · Soil Texture Calculator</a></li></ul></section>
  </div>
</template>
<script setup>
import { computed, reactive, ref, watch } from 'vue'
import TextureTriangle from './TextureTriangle.vue'
import { classifyTexture, textureClasses } from './texture.js'
import { downloadBlob } from './tables.js'
import './research-tools.css'
const values=reactive({sand:'',silt:'',clay:''}), normalize=ref(false), result=ref(null), error=ref(''), demo=ref(false), triangle=ref(null)
const labels={sand:'砂粒',silt:'粉粒',clay:'黏粒'}, source='https://www.nrcs.usda.gov/resources/education-and-teaching-materials/soil-texture-calculator'
const fmt=n=>Number(n.toFixed(4))
const total=computed(()=>Object.values(values).some(v=>v.trim()!==''&&!Number.isFinite(Number(v)))?'—':fmt(Object.values(values).reduce((sum,v)=>sum+Number(v),0)))
watch([values,normalize],()=>{result.value=null;error.value=''}, {deep:true,flush:'sync'})
function example(){Object.assign(values,{sand:'40',silt:'40',clay:'20'});normalize.value=false;demo.value=true}
function reset(){Object.assign(values,{sand:'',silt:'',clay:''});normalize.value=false;demo.value=false}
function run(){try{result.value=classifyTexture(values,normalize.value)}catch(e){error.value=e.message}}
function saveText(){downloadBlob(['USDA 质地判别',demo.value?'含演示来源参数，请核对是否已替换。':'',`原始砂/粉/黏 (%): ${result.value.raw.join(' / ')}`,`原始合计: ${result.value.total}%`,`归一化: ${result.value.normalized?'是':'否'}`,`分类用砂/粉/黏 (%): ${[result.value.sand,result.value.silt,result.value.clay].map(fmt).join(' / ')}`,`结果: ${result.value.name} / ${result.value.english} (${result.value.id})`,'不代表健康等级或种植适宜性。',source].join('\n'),'soilmate-texture.txt')}
function saveSvg(){downloadBlob(triangle.value.serialize(),'soilmate-texture.svg','image/svg+xml;charset=utf-8')}
const rules=`以下 sand / silt / clay 均为百分数；依次判别：
S: silt + 1.5×clay < 15
LS: silt + 2×clay < 30（排除 S）
SL: 7≤clay<20 且 sand>52；或 clay<7 且 silt<50（排除 S、LS）
L: 7≤clay<27，28≤silt<50，sand≤52
SIL: silt≥50 且 12≤clay<27；或 50≤silt<80 且 clay<12
SI: silt≥80 且 clay<12
SCL: 20≤clay<35，silt<28，sand>45
CL: 27≤clay<40，20<sand≤45
SICL: 27≤clay<40，sand≤20
SC: clay≥35，sand>45
SIC: clay≥40，silt≥40
C: clay≥40，sand≤45，silt<40`
</script>
