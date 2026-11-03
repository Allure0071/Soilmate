<template>
  <figure class="calibration-figure">
    <svg viewBox="0 0 500 260" role="img" aria-labelledby="calibration-plot-title"><title id="calibration-plot-title">标准浓度与响应散点及线性拟合</title>
      <g v-for="t in ticks" :key="t" class="plot-grid"><line x1="64" :y1="sy(ymin + t * (ymax - ymin))" x2="466" :y2="sy(ymin + t * (ymax - ymin))" /><text x="55" :y="sy(ymin + t * (ymax - ymin)) + 4" text-anchor="end">{{ tick(ymin + t * (ymax - ymin)) }}</text><text :x="sx(xmin + t * (xmax - xmin))" y="230" text-anchor="middle">{{ tick(xmin + t * (xmax - xmin)) }}</text></g>
      <path class="plot-axis" d="M64 20V212H466" />
      <line class="plot-fit" :x1="sx(xmin)" :y1="sy(chart.intercept + chart.slope * xmin)" :x2="sx(xmax)" :y2="sy(chart.intercept + chart.slope * xmax)" />
      <circle v-for="(p, index) in chart.points" :key="index" class="plot-point" :cx="sx(p.x)" :cy="sy(p.y)" r="4"><title>{{ p.x }}, {{ p.y }}</title></circle>
      <text x="265" y="254" text-anchor="middle">标准浓度（输入单位）</text><text x="13" y="116" transform="rotate(-90 13 116)" text-anchor="middle">仪器响应</text>
    </svg>
    <figcaption>圆点为输入标准点，实线为普通最小二乘拟合。</figcaption>
  </figure>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ chart: { type: Object, required: true } })
const ticks = [0, 0.25, 0.5, 0.75, 1]
const xmin = computed(() => Math.min(...props.chart.points.map(p => p.x)))
const xmax = computed(() => Math.max(...props.chart.points.map(p => p.x)))
const bounds = computed(() => {
  const values = [...props.chart.points.map(p => p.y), props.chart.intercept + props.chart.slope * xmin.value, props.chart.intercept + props.chart.slope * xmax.value]
  const min = Math.min(...values), max = Math.max(...values), pad = (max - min) * 0.1 || 1
  return [min - pad, max + pad]
})
const ymin = computed(() => bounds.value[0]), ymax = computed(() => bounds.value[1])
function sx(x) { return 64 + (x - xmin.value) / (xmax.value - xmin.value) * 402 }
function sy(y) { return 212 - (y - ymin.value) / (ymax.value - ymin.value) * 192 }
function tick(value) { return Number(value.toPrecision(3)).toString() }
</script>
