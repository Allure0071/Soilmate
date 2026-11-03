<template>
  <details class="assessment-import-source">
    <summary>导入来源 · {{ source.file_name }} · 表格第 {{ source.table_row }} 行</summary>
    <dl><div><dt>样本编号</dt><dd>{{ source.sample_id }}</dd></div><div v-if="source.sheet_name"><dt>工作表</dt><dd>{{ source.sheet_name }}</dd></div><div><dt>带入时间</dt><dd>{{ source.imported_at }}</dd></div></dl>
    <p>下表保留导入时的原始内容；录入检测值可修改，两者分别保存。表格行号包含表头，带换行的单元格按一行记录计。</p>
    <div class="assessment-source-scroll"><table><caption>原始样本行</caption><thead><tr><th>原始字段</th><th>原始值</th><th>带入指标</th></tr></thead><tbody><tr v-for="(cell,i) in source.original" :key="i"><th scope="row">{{ cell.column }}</th><td>{{ cell.value || '空' }}</td><td>{{ mappedName(cell.column) }}</td></tr></tbody></table></div>
  </details>
</template>
<script setup>
import { reviewIndicators } from './measurementDraft.js'
const props=defineProps({source:{type:Object,required:true}})
function mappedName(column) { const field=props.source.fields.find(item=>item.column===column);return field ? (reviewIndicators.find(item=>item.code===field.indicator_code)?.name || field.indicator_code) + (field.unit ? ' · '+field.unit : ' · 无量纲') : '未带入' }
</script>
