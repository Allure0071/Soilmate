<template>
  <component :is="as" ref="root" class="hover-switch">
    <span v-show="selection.visible" class="hover-switch-plate" aria-hidden="true" :style="selectionStyle"></span>
    <slot />
  </component>
</template>

<script setup>
import { ref } from 'vue'
import { useHoverSelection } from './useHoverSelection.js'
defineProps({ as: { type: String, default: 'div' } })
const root = ref(null)
const { selection, selectionStyle } = useHoverSelection(root)
</script>

<style>
#app .hover-switch { position: relative; isolation: isolate; }
#app .hover-switch > .hover-switch-plate {
  position: absolute; top: 0; left: 0; z-index: 0; pointer-events: none;
  border: 1px solid #ffffffb0; border-radius: var(--hover-radius, 10px);
  background: var(--hover-surface, #e5eee1);
  box-shadow: inset 0 1px 0 #ffffffb0, 0 2px 5px #183b2010;
  transition: transform 220ms cubic-bezier(.16,1,.3,1), width 180ms cubic-bezier(.16,1,.3,1), height 180ms cubic-bezier(.16,1,.3,1);
}
#app .hover-switch > :is(button, a) {
  position: relative; z-index: 1;
  background: transparent !important; box-shadow: none !important;
  border-color: transparent !important;
}
#app .hover-switch > :is(button, a):not(:disabled) { color: #31583d !important; }
#app .hover-switch > :is(button, a)::after { background: transparent !important; }
#app .hover-switch.category-tabs { --hover-surface: #fff; --hover-radius: 7px; }
@media (prefers-reduced-motion: reduce) {
  #app .hover-switch > .hover-switch-plate { transition: none; }
}
</style>
