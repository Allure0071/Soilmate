export function trapWorkspaceFocus(event, enabled) {
  if (!enabled) return
  const controls = [...event.currentTarget.querySelectorAll('button:not(:disabled), a[href], input, select, textarea, [tabindex="0"]')]
    .filter(element => element.getClientRects().length && !element.closest('[inert]'))
  const first = controls[0], last = controls.at(-1)
  if (!first) return
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
}
