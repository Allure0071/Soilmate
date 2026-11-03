<template>
  <section class="audit-handoff" aria-labelledby="audit-handoff-title">
    <div class="calculator-section-heading"><h2 id="audit-handoff-title">带入健康研究</h2><span class="tool-note">每次带入一行，不合并同名样本</span></div>
    <p class="tool-intro">先确认字段与报告单位，再选择本次检测。未知字段可跳过，缺失值不填补；原始值和表格行号会随样本保留。</p>
    <p v-if="demo" class="calculator-example-note">当前为合成问题示例，不能带入实测录入。请先导入自己的检测表。</p>
    <div class="research-table-scroll"><table class="research-table"><caption>字段映射与单位确认</caption><thead><tr><th>原始字段</th><th>健康研究指标</th><th>报告单位</th></tr></thead><tbody><tr v-for="(item,i) in mapping" :key="i"><th scope="row">{{ table.headers[i] }}</th><td><select v-model="item.code" :aria-label="`${table.headers[i]}映射指标`" @change="item.unit='' "><option value="">跳过此列</option><option v-for="indicator in reviewIndicators" :key="indicator.code" :value="indicator.code">{{ indicator.name }}</option></select></td><td><select v-if="indicatorFor(item)?.units.length" v-model="item.unit" :aria-label="`${table.headers[i]}导入单位`"><option value="">请选择单位</option><option v-for="unit in indicatorFor(item).units" :key="unit" :value="unit">{{ unit }}</option></select><span v-else class="tool-note">{{ item.code ? '无量纲' : '—' }}</span></td></tr></tbody></table></div>
    <div class="audit-options"><label>选择样本<select v-model.number="selected" aria-label="选择要带入的样本"><option :value="-1">请选择一行检测记录</option><option v-for="(row,i) in table.rows" :key="i" :value="i">{{ sampleLabel(row,i) }}</option></select></label></div>
    <template v-if="selected>=0">
      <p class="tool-note">来源：{{ fileName || '粘贴内容' }}{{ sheetName ? ` · ${sheetName}` : '' }} · 表格第 {{ selected+2 }} 行（表头为第 1 行）。{{ rowIssues.length ? `该行有 ${rowIssues.length} 条体检记录，请核对后决定是否带入。` : '当前设置下，该行没有体检记录。' }}</p>
      <ul v-if="rowIssues.length" class="audit-import-issues"><li v-for="(issue,i) in rowIssues" :key="i">{{ issue.column }} · {{ issue.type }}：{{ issue.message }}</li></ul>
      <div v-if="inspection.rows.length" class="research-table-scroll"><table class="research-table"><caption>待带入检测值</caption><thead><tr><th>指标</th><th>检测值</th><th>报告单位</th></tr></thead><tbody><tr v-for="row in inspection.rows" :key="row.id"><th scope="row">{{ indicatorFor({code:row.indicator_code}).name }}</th><td>{{ row.value }}</td><td>{{ row.unit || '无量纲' }}</td></tr></tbody></table></div>
      <ul v-if="inspection.errors.length" class="calculator-error"><li v-for="item in inspection.errors" :key="item">{{ item }}</li></ul>
      <label class="tool-checkbox audit-import-confirm"><input v-model="confirmed" type="checkbox" :disabled="demo || inspection.errors.length>0" />我已核对字段、单位与体检提示，确认所选行来自自己的实际检测记录。</label>
    </template>
    <div class="research-actions"><button type="button" class="tool-primary-button" :disabled="demo || !confirmed || inspection.errors.length>0 || selected<0" @click="proceed">带入健康研究录入页</button><span class="tool-note">需要登录；确认带入后，所选样本及原始行会保存在当前浏览器草稿，不会发起分析。</span></div>
    <p v-if="error" role="alert" class="calculator-error">{{ error }}</p>
  </section>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
import { reviewIndicators } from '../../assessment/measurementDraft.js'
import { buildImport, inspectImport, stageImport, suggestMapping } from '../../assessment/measurementImport.js'
const props=defineProps({table:{type:Object,required:true},output:{type:Object,required:true},idColumn:{type:Number,default:-1},fileName:{type:String,default:''},sheetName:{type:String,default:''},demo:{type:Boolean,default:false}})
const emit=defineEmits(['open-research'])
const mapping=ref(suggestMapping(props.table.headers)),selected=ref(-1),confirmed=ref(false),error=ref('')
const indicatorFor=item=>reviewIndicators.find(indicator=>indicator.code===item.code)
const sampleLabel=(row,i)=>`表格第 ${i+2} 行${props.idColumn>=0 ? ' · '+(row[props.idColumn] || '编号缺失').slice(0,80) : ''}`
const inspection=computed(()=>inspectImport(props.table,mapping.value,selected.value,props.idColumn))
const rowIssues=computed(()=>props.output.issues.filter(issue=>issue.row===selected.value+2))
watch([mapping,selected],()=>{confirmed.value=false;error.value=''}, {deep:true,flush:'sync'})
function proceed(){
  if(!confirmed.value || props.demo)return
  try {
    const payload=buildImport(props.table,mapping.value,selected.value,props.idColumn,props)
    const token=stageImport(payload)
    emit('open-research',token)
  } catch(e){error.value=e.message}
}
</script>
