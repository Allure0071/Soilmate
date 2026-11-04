<template>
  <section class="evidence-chain" aria-label="评价证据链">
    <header class="evidence-chain-head">
      <span class="evidence-chain-kicker">证据链</span>
      <strong>{{ title }}</strong>
      <span v-if="chain.length" class="evidence-chain-count">{{ chain.length }} 个环节</span>
      <button type="button" class="evidence-chain-toggle" :aria-expanded="open" @click="open = !open">{{ open ? '收起' : '展开' }}</button>
    </header>
    <div v-if="!open && chain.length" class="evidence-chain-rail" aria-label="证据链环节">
      <span v-for="node in chain" :key="node.step" class="evidence-chain-chip"><i>{{ node.step }}</i>{{ shortLabel(node.kind) }}</span>
    </div>
    <template v-if="open">
      <ol class="evidence-chain-list">
        <li v-for="node in chain" :key="node.step" class="evidence-chain-node">
          <span class="evidence-chain-index" aria-hidden="true">{{ node.step }}</span>
          <div class="evidence-chain-body">
            <div class="evidence-chain-node-head"><b>{{ node.title }}</b><span v-if="node.kind" class="evidence-chain-kind">{{ kindLabel(node.kind) }}</span></div>
            <p class="evidence-chain-summary">{{ node.summary }}</p>
            <p v-if="node.detail" class="evidence-chain-detail">{{ node.detail }}</p>
            <details v-if="node.items?.length" class="evidence-chain-details">
              <summary>查看 {{ node.items.length }} 条证据</summary>
              <ul>
                <li v-for="(item, index) in node.items" :key="index">
                  <span v-if="item.status" class="evidence-dot" :class="`evidence-dot-${item.status}`" aria-hidden="true"></span>
                  <span class="evidence-item-copy"><b>{{ item.label }}</b><small v-if="item.detail">{{ item.detail }}</small><small v-if="item.source_id" class="evidence-source">来源 {{ item.source_id }}</small></span>
                </li>
              </ul>
            </details>
          </div>
        </li>
      </ol>
      <p v-if="rule" class="evidence-chain-foot">规则版本：{{ rule }} · 重新分析会生成新任务，原结果保留。</p>
    </template>
  </section>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ chain: { type: Array, default: () => [] }, title: { type: String, default: '本次评价证据链' }, rule: { type: String, default: '' }, defaultOpen: { type: Boolean, default: false } })
const open = ref(props.defaultOpen)
const labels = { sample: '数据', indicator: '判读', score: '评分', rule: '规则', boundary: '边界' }
const kindLabel = kind => labels[kind] || kind
const shortLabels = { sample: '样本', indicator: '判读', score: '评分', rule: '规则', boundary: '边界' }
const shortLabel = kind => shortLabels[kind] || kindLabel(kind)
</script>

<style scoped>
.evidence-chain { margin: 4px 24px 14px; padding: 12px 0 2px; border-top: 1px solid #e2eadc; border-bottom: 1px solid #e2eadc; }
.evidence-chain-head { display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px 8px; }
.evidence-chain-kicker { color: #7d9182; font-size: 10px; font-weight: 700; letter-spacing: .08em; }
.evidence-chain-head strong { color: #2b4c38; font-size: 11.5px; font-weight: 600; }
.evidence-chain-count { color: #96a69a; font-size: 10px; }
.evidence-chain-toggle { min-height: 26px; margin-left: auto; padding: 0 4px; border: 0; background: none; color: #34734e; font: inherit; font-size: 10.5px; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
.evidence-chain-toggle:focus-visible { outline: 3px solid #9ac5a5; outline-offset: 2px; border-radius: 4px; }
.evidence-chain-rail { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
.evidence-chain-chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 7px 3px 3px; border: 1px solid #e0e9dc; border-radius: 100px; background: #fbfcf8; color: #5d7464; font-size: 9.5px; white-space: nowrap; }
.evidence-chain-chip i { display: grid; place-items: center; width: 15px; height: 15px; border-radius: 50%; background: #e9f3e4; color: #2f6a4a; font-style: normal; font-size: 8.5px; font-weight: 700; }
.evidence-chain-list { list-style: none; margin: 6px 0 0; padding: 0 2px 0 0; max-height: 300px; overflow-y: auto; overscroll-behavior: contain; scrollbar-width: thin; scrollbar-color: #cfdccb transparent; }
.evidence-chain-node { position: relative; display: grid; grid-template-columns: 22px minmax(0, 1fr); gap: 8px; padding: 9px 0 9px 0; }
.evidence-chain-node + .evidence-chain-node { border-top: 1px solid #edf2ea; }
.evidence-chain-index { display: grid; place-items: center; width: 20px; height: 20px; border-radius: 50%; background: #e9f3e4; color: #2f6a4a; font-size: 10px; font-weight: 700; font-variant-numeric: tabular-nums; }
.evidence-chain-node-head { display: flex; align-items: baseline; gap: 6px; }
.evidence-chain-node-head b { color: #2b4a36; font-size: 11px; font-weight: 600; }
.evidence-chain-kind { padding: 1px 5px; border-radius: 4px; background: #f1f5ee; color: #839b87; font-size: 9px; }
.evidence-chain-summary { margin: 3px 0 0; color: #5d7464; font-size: 10.5px; line-height: 1.6; }
.evidence-chain-detail { margin: 3px 0 0; color: #84978a; font-size: 10px; line-height: 1.55; }
.evidence-chain-details { margin-top: 5px; }
.evidence-chain-details summary { width: fit-content; color: #3f7152; font-size: 10px; cursor: pointer; text-underline-offset: 3px; }
.evidence-chain-details summary:focus-visible { outline: 3px solid #9ac5a5; outline-offset: 2px; border-radius: 3px; }
.evidence-chain-details ul { list-style: none; margin: 5px 0 0; padding: 0; display: grid; gap: 5px; }
.evidence-chain-details li { display: flex; align-items: flex-start; gap: 6px; }
.evidence-dot { flex: none; width: 6px; height: 6px; margin-top: 5px; border-radius: 50%; background: #8bb195; }
.evidence-dot-needs_attention { background: #b9775d; }
.evidence-dot-uncertain { background: #b79a56; }
.evidence-dot-descriptive_only { background: #9aa9a0; }
.evidence-item-copy { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.evidence-item-copy b { color: #4c6555; font-size: 10px; font-weight: 500; line-height: 1.45; }
.evidence-item-copy small { color: #8a9c8d; font-size: 9.5px; line-height: 1.45; }
.evidence-item-copy .evidence-source { color: #a0afa3; font-variant-numeric: tabular-nums; }
.evidence-chain-foot { margin: 7px 0 5px; color: #93a496; font-size: 9.5px; line-height: 1.5; }
</style>
