<template>
  <svg class="workspace-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path :d="paths[name] || paths.chat" /></svg>
</template>

<script setup>
defineProps({ name: { type: String, default: 'chat' } })
const paths = {
  chat: 'M5 4h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-6 4V6a2 2 0 0 1 2-2ZM8 9h8M8 13h5',
  close: 'm6 6 12 12M18 6 6 18',
  expand: 'M8 5h11v11M19 5 5 19',
  arrow: 'M4 12h16m-6-6 6 6-6 6',
  back: 'M20 12H4m6-6-6 6 6 6',
  plus: 'M12 5v14M5 12h14',
  menu: 'M4 6h16M4 12h16M4 18h16',
  panel: 'M3 4h18v16H3ZM15 4v16',
  send: 'm3 11 18-8-8 18-2-8-8-2ZM11 13 21 3',
  check: 'm5 12 4 4L19 6',
  search: 'M16.5 16.5 21 21M18 10.5a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z',
  map: 'm3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2ZM9 3v16M15 5v16',
  database: 'M20 6c0 2-3.6 3-8 3S4 8 4 6s3.6-3 8-3 8 1 8 3ZM4 6v12c0 2 3.6 3 8 3s8-1 8-3V6M4 12c0 2 3.6 3 8 3s8-1 8-3',
  analysis: 'M4 3h16v18H4ZM8 8h8M8 12h3M8 16h8',
  soil: 'M4 5h16M5 10c3-3 5 3 8 0s4 0 6 0M5 15c3-3 5 3 8 0s4 0 6 0M4 20h16',
  chart: 'M4 3v17h17M8 14l4-5 4 2 5-7',
  convert: 'M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4',
  flask: 'M9 3h6M10 3v7l-5 8a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-8V3M8 14h8',
  calculator: 'M5 3h14v18H5ZM8 6h8M8 11h1M15 11h1M8 15h1M15 15h1M8 18h1M15 18h1',
}
</script>
