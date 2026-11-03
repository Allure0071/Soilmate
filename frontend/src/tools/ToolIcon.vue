<template>
  <img class="tool-directory-icon" :src="source" width="40" height="40" alt="" aria-hidden="true" />
</template>

<script setup>
import { computed } from 'vue'
import gold from './icons/gold.svg'
import experiment from './icons/experiment.svg'
import container from './icons/container.svg'
import interaction from './icons/interaction.svg'
import fund from './icons/fund.svg'
import pieChart from './icons/pie-chart.svg'
import environment from './icons/environment.svg'
import database from './icons/database.svg'
import profile from './icons/profile.svg'
import fileText from './icons/file-text.svg'
import bulb from './icons/bulb.svg'

const props = defineProps({ toolId: { type: String, required: true } })
const sources = {
  density: gold, moisture: experiment, carbon: container, dilution: experiment,
  'data-audit': profile, texture: pieChart,
  units: interaction, curve: fund, statistics: pieChart,
  'map-layers': environment, 'indicator-catalog': profile, 'database-browser': database,
  'quick-assessment': fileText, 'deep-assessment': bulb,
}
const source = computed(() => sources[props.toolId] || container)
</script>
