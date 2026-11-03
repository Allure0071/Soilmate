// Native scrolling is preserved. Only the marked content gets a small visual offset.
const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)')

export function revealOnScroll(root) {
  const media = reducedMotion()
  if (media.matches) return () => {}
  const animations = new Set()
  const elements = [...root.querySelectorAll('[data-reveal]')]
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue
      const element = entry.target
      observer.unobserve(element)
      element.style.opacity = ''
      if (media.matches) continue
      const animation = element.animate([
        { opacity: 0, transform: 'translate3d(0, 20px, 0)', offset: 0, easing: 'cubic-bezier(.16,.85,.24,1)' },
        { opacity: 1, transform: 'translate3d(0, -2px, 0)', offset: .74, easing: 'cubic-bezier(.3,0,.25,1)' },
        { opacity: 1, transform: 'translate3d(0, 0, 0)', offset: 1 },
      ], { duration: 620, delay: Number(element.dataset.reveal || 0), fill: 'backwards', easing: 'cubic-bezier(0,0,1,1)' })
      animations.add(animation)
      animation.onfinish = animation.oncancel = () => animations.delete(animation)
    }
  }, { threshold: .12 })
  for (const element of elements) {
    element.style.opacity = '0'
    observer.observe(element)
  }
  const finish = () => {
    if (!media.matches) return
    observer.disconnect()
    for (const element of elements) element.style.opacity = ''
    for (const animation of animations) animation.finish()
  }
  media.addEventListener('change', finish)
  return () => {
    observer.disconnect()
    media.removeEventListener('change', finish)
    for (const animation of animations) animation.cancel()
    for (const element of elements) element.style.opacity = ''
  }
}

export function attachScrollResponse(scroller, content) {
  const media = reducedMotion()
  let frame = 0, previousTime = 0, lastScrollTime = 0
  let lastTop = scroller.scrollTop, offset = 0, velocity = 0, target = 0
  const reset = () => {
    cancelAnimationFrame(frame)
    frame = 0
    offset = velocity = target = 0
    lastTop = scroller.scrollTop
    content.style.removeProperty('--scroll-drift')
  }
  const tick = now => {
    if (media.matches || document.hidden) { reset(); return }
    const dt = Math.min((now - previousTime) / 1000, .032)
    previousTime = now
    if (now - lastScrollTime > 65) target = 0
    // A damped spring follows at most 8px of scroll response, then settles at zero.
    velocity += (180 * (target - offset) - 18 * velocity) * dt
    offset += velocity * dt
    content.style.setProperty('--scroll-drift', `${offset.toFixed(3)}px`)
    if (target === 0 && Math.abs(offset) < .025 && Math.abs(velocity) < .04) { reset(); return }
    frame = requestAnimationFrame(tick)
  }
  const onScroll = () => {
    const delta = scroller.scrollTop - lastTop
    lastTop = scroller.scrollTop
    if (media.matches) return
    target = Math.max(-8, Math.min(8, -delta * .12))
    lastScrollTime = performance.now()
    if (!frame) { previousTime = lastScrollTime; frame = requestAnimationFrame(tick) }
  }
  scroller.addEventListener('scroll', onScroll, { passive: true })
  media.addEventListener('change', reset)
  document.addEventListener('visibilitychange', reset)
  return () => {
    reset()
    scroller.removeEventListener('scroll', onScroll)
    media.removeEventListener('change', reset)
    document.removeEventListener('visibilitychange', reset)
  }
}
