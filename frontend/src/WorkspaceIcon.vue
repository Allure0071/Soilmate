<template>
  <svg class="workspace-icon" :viewBox="icon.viewBox" fill="currentColor" stroke="none" aria-hidden="true" focusable="false"><path v-for="(attributes, index) in icon.paths" :key="index" v-bind="attributes" /></svg>
</template>

<script setup>
import { computed } from 'vue'
import icons from './icons/ant-design-outlined.json'

const props = defineProps({ name: { type: String, default: 'chat' } })
const icon = computed(() => icons[props.name] || icons.chat)
</script>
