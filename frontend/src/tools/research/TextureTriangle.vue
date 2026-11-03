<template>
  <figure class="texture-figure">
    <svg ref="svg" viewBox="0 0 540 470" role="img" aria-labelledby="texture-chart-title texture-chart-desc" xmlns="http://www.w3.org/2000/svg">
      <title id="texture-chart-title">USDA 土壤质地三角图</title><desc id="texture-chart-desc">三个顶点分别代表百分之百砂粒、粉粒和黏粒。{{ result ? `当前点为${result.name}，砂粒${result.sand.toFixed(2)}%、粉粒${result.silt.toFixed(2)}%、黏粒${result.clay.toFixed(2)}%。` : '填写组分并判别后显示样点。' }}</desc>
      <g v-for="(item,index) in textureClasses" :key="item.id">
        <polygon :points="points(item.vertices)" :fill="result?.id===item.id ? '#c4dfbd' : ['#f1f5e9','#e6efe3','#f7f5e9'][index%3]" stroke="#8da58a" stroke-width="1"><title>{{ item.name }} · {{ item.english }}</title></polygon>
        <text :x="center(item).x" :y="center(item).y" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="11" fill="#35543b">{{ item.id }}</text>
      </g>
      <g v-for="t in [20,40,60,80]" :key="t" stroke="#ffffff90" stroke-width=".7" pointer-events="none"><line v-for="(line,index) in grid(t)" :key="index" :x1="line[0].x" :y1="line[0].y" :x2="line[1].x" :y2="line[1].y" /></g>
      <g font-family="sans-serif" font-size="12" fill="#425e47"><text x="270" y="24" text-anchor="middle">黏粒 100%</text><text x="60" y="435" text-anchor="middle">砂粒 100%</text><text x="480" y="435" text-anchor="middle">粉粒 100%</text><text x="270" y="456" text-anchor="middle">组分为细土部分的质量百分比</text></g>
      <g v-if="result"><circle :cx="marker.x" :cy="marker.y" r="8" fill="#245c3a" stroke="#fff" stroke-width="3"/><circle :cx="marker.x" :cy="marker.y" r="11" fill="none" stroke="#245c3a" stroke-width="1"/></g>
    </svg>
    <figcaption>边界共享同一条线；边界点按下方列明的数值判别规则归类。</figcaption>
  </figure>
</template>
<script setup>
import { computed, ref } from 'vue'
import { textureClasses, texturePoint } from './texture.js'
const props=defineProps({ result:{type:Object,default:null} })
const svg=ref(null)
const points=vertices=>vertices.map(v=>{const p=texturePoint(v);return `${p.x},${p.y}`}).join(' ')
const center=item=>texturePoint([0,1,2].map(index=>item.vertices.reduce((sum,v)=>sum+v[index],0)/item.vertices.length))
const marker=computed(()=>props.result?texturePoint([props.result.sand,props.result.silt,props.result.clay]):null)
const grid=t=>[[[100-t,0,t],[0,100-t,t]],[[t,0,100-t],[t,100-t,0]],[[0,t,100-t],[100-t,t,0]]].map(line=>line.map(texturePoint))
defineExpose({ serialize:()=>new XMLSerializer().serializeToString(svg.value) })
</script>
