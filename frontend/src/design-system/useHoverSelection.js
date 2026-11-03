import { computed, nextTick, onBeforeUnmount, onMounted, onUpdated, ref } from 'vue'

// A visual preview only: hovering never changes the group's actual selection.
// Retain the last preview after pointer exit, and resync when selection changes.
export function useHoverSelection(root) {
  const selection = ref({ visible: false, x: 0, y: 0, width: 0, height: 0 })
  let target = null, selected = null, observer
  const items = () => [...(root.value?.children || [])].filter(element => element.matches('button, a'))
  const enabled = element => element && !element.disabled && element.getAttribute('aria-disabled') !== 'true'
  function align() {
    const children = items()
    const current = children.find(element => element.matches('.active, [aria-selected="true"], [aria-pressed="true"], [aria-current]:not([aria-current="false"])')) || null
    if (current !== selected) { selected = current; target = current }
    if (!children.includes(target) || !enabled(target)) target = enabled(current) ? current : null
    const next = target && target.offsetWidth && target.offsetHeight
      ? { visible: true, x: target.offsetLeft, y: target.offsetTop, width: target.offsetWidth, height: target.offsetHeight }
      : { ...selection.value, visible: false }
    if (Object.keys(next).some(key => next[key] !== selection.value[key])) selection.value = next
  }
  function preview(event) {
    if (event.type === 'pointerover' && event.pointerType === 'touch') return
    const item = event.target.closest?.('button, a')
    if (item?.parentElement !== root.value || !enabled(item)) return
    if (event.type === 'focusin' && !item.matches(':focus-visible')) return
    if (target === item) return
    target = item
    align()
  }
  onMounted(() => {
    align()
    observer = new ResizeObserver(align)
    observer.observe(root.value)
    for (const type of ['pointerover', 'focusin', 'click']) root.value.addEventListener(type, preview)
    document.fonts.ready.then(() => nextTick(align))
  })
  onUpdated(align)
  onBeforeUnmount(() => {
    observer?.disconnect()
    for (const type of ['pointerover', 'focusin', 'click']) root.value?.removeEventListener(type, preview)
    target = selected = null
  })
  const selectionStyle = computed(() => ({ width: `${selection.value.width}px`, height: `${selection.value.height}px`, transform: `translate(${selection.value.x}px, ${selection.value.y}px)` }))
  return { selection, selectionStyle }
}
