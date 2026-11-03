<template>
  <header class="site-header" :class="{ 'site-header-home': home }">
    <a class="site-brand" href="/" aria-label="沃壤知行首页" title="返回首页" :aria-current="active === 'home' ? 'page' : undefined" @click="navigate($event, 'home')">
      <span class="site-brand-mark" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none"><path d="M4 20c4-9 10-14 17-14 8 0 14 6 15 14-1 8-7 14-15 14C14 34 8 29 4 20Z"/><path d="M10 20c3-6 7-9 12-9 5 0 9 4 10 9-1 5-5 9-10 9-5 0-9-3-12-9Z"/><path d="M16 20c2-2 4-4 7-4s5 2 6 4c-1 3-3 5-6 5s-5-2-7-5Z"/></svg></span>
      <span class="site-brand-copy"><strong>沃壤知行</strong></span>
    </a>
    <nav ref="navigation" class="site-primary-nav" aria-label="主站导航">
      <span v-show="selection.visible" class="site-nav-selection" aria-hidden="true" :style="selectionStyle"></span>
      <a v-for="link in primaryLinks" :key="link.id" :href="link.href" :class="{ active: link.views.includes(active) }" :aria-current="link.views.includes(active) ? 'page' : undefined" @click="navigate($event, link.id)">{{ link.label }}</a>
    </nav>
    <div class="site-account">
      <span v-if="preview" class="site-preview">审核预览</span>
      <template v-else-if="account"><span class="site-account-email" :title="account.email">{{ account.email }}</span><button type="button" @click="$emit('logout')">退出</button></template>
      <a v-else :href="loginHref">登录 / 注册</a>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useHoverSelection } from './design-system/useHoverSelection.js'
import { primaryLinks } from './siteNavigation.js'
const props = defineProps({ active: { type: String, default: 'home' }, home: { type: Boolean, default: false }, account: { type: Object, default: null }, preview: { type: Boolean, default: false }, loginHref: { type: String, default: '/account/index.html?next=%2Fresearch' } })
const emit = defineEmits(['navigate', 'logout'])
const navigation = ref(null)
const { selection, selectionStyle } = useHoverSelection(navigation)
function navigate(event, view) {
  if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return
  event.preventDefault()
  emit('navigate', view)
}
</script>

<style scoped>
.site-header { display: flex; align-items: center; gap: 24px; position: relative; z-index: 1200; flex: none; min-height: var(--site-header-height); height: var(--site-header-height); margin-bottom: var(--site-frame-gap); padding: 0 26px; border-radius: 18px; background: #fff; color: #263d2d; font-family: var(--font-ui); box-shadow: 0 6px 20px #15362112; }
.site-header-home { width: 100%; }
.site-brand { display: inline-flex; align-items: center; gap: 10px; flex: none; min-height: 32px; padding-right: 24px; border-right: 1px solid #dce6d8; color: #285b3e; text-decoration: none; }
.site-brand-mark { display: grid; place-items: center; width: 32px; height: 32px; flex: none; }
.site-brand-mark svg { width: 30px; height: 30px; stroke: currentColor; stroke-width: 1.6; }
.site-brand-copy { display: flex; flex-direction: column; gap: 3px; }
.site-brand-copy strong { font: inherit; font-size: 18px; line-height: 1.4; font-weight: 700; white-space: nowrap; }
.site-primary-nav { display: flex; align-items: center; gap: 6px; flex: none; min-width: 0; }
.site-primary-nav a { display: inline-flex; align-items: center; justify-content: center; min-height: 40px; padding: 8px 18px; border-radius: 8px; color: #354f3e; text-decoration: none; font-size: var(--text-body); font-weight: 600; white-space: nowrap; }
.site-primary-nav a:hover { background: #dfead8; color: #245d3b; }
.site-primary-nav a.active { background: #285b3e; color: #fff; font-weight: 600; }
.site-primary-nav a.active:hover { background: #204c33; }
.site-account { display: flex; align-items: center; justify-content: flex-end; gap: 10px; min-width: 0; max-width: 100%; margin-left: auto; font-size: var(--text-label); }
.site-account-email { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #4d6755; font-size: var(--text-caption); }
.site-account :is(a, button) { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 8px 14px; border: 1px solid #cbdcc8; border-radius: 999px; background: #f4f8f0; color: #28583e; text-decoration: none; font: inherit; font-weight: 600; white-space: nowrap; cursor: pointer; }
.site-account :is(a, button):hover { background: #e5efdf; border-color: #9cba9e; }
.site-preview { color: #526d59; white-space: nowrap; }
.site-header :is(a, button):focus-visible { outline: 3px solid #80af89; outline-offset: 3px; }
@media (max-width: 1180px) {
  .site-header { gap: 18px; padding-inline: 20px; }
  .site-brand { padding-right: 18px; }
  .site-primary-nav a { padding-inline: 14px; }
  .site-account-email { max-width: 100px; }
}
@media (min-width: 781px) and (max-width: 1000px) {
  .site-header { gap: 14px; }
  .site-brand { gap: 8px; padding-right: 14px; }
  .site-primary-nav { gap: 2px; }
  .site-account-email { display: none; }
  .site-primary-nav a { padding-inline: 8px; }
}
@media (max-width: 780px) {
  .site-header { display: flex; flex-wrap: wrap; gap: 0 12px; min-height: var(--site-header-height); height: auto; margin-bottom: 8px; padding: 9px 10px 5px; border-radius: 16px; }
  .site-header-home { width: 100%; }
  .site-brand-mark { width: 32px; height: 32px; }
  .site-brand { flex: none; padding-right: 0; border-right: 0; }
  .site-brand-mark svg { width: 26px; height: 26px; }
  .site-brand-copy strong { font-size: var(--text-subheading); }
  .site-account { gap: 8px; min-width: 0; margin-left: auto; }
  .site-account-email { max-width: 105px; font-size: var(--text-caption); }
  .site-account :is(a, button) { min-height: 36px; padding: 8px 12px; font-size: var(--text-caption); }
  .site-primary-nav { display: grid; grid-template-columns: repeat(5, minmax(max-content, 1fr)); order: 3; flex: 0 0 100%; gap: 4px; width: 100%; margin-top: 4px; padding: 3px 0 4px; border-top: 1px solid #e4ece0; overflow-x: auto; scrollbar-width: thin; }
  .site-primary-nav a { min-height: 44px; padding: 9px 4px; font-size: var(--text-label); white-space: nowrap; }
}
@media (max-width: 360px) {
  .site-account-email { display: none; }
  .site-primary-nav a { padding-inline: 2px; }
}
</style>
