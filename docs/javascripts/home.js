// Hero parallax: each [data-depth] layer drifts at its own rate as the page scrolls.
// Damped: every frame the offset closes a fraction of the gap to the scroll position,
// so layers glide and settle rather than tracking the scrollbar 1:1.
// Re-bound on every page load, since navigation.instant swaps pages without a reload.
const DAMPING = 0.08 // fraction of the remaining distance covered per frame

let teardown = () => {}

document$.subscribe(() => {
  teardown()
  teardown = () => {}

  const hero = document.querySelector(".pf-hero")
  if (!hero || matchMedia("(prefers-reduced-motion: reduce)").matches) return

  const layers = [...hero.querySelectorAll("[data-depth]")]
  const target = () => Math.min(window.scrollY, hero.offsetHeight)
  let current = target()
  let frame = 0

  const apply = () => {
    for (const el of layers)
      el.style.transform = `translate3d(0, ${(current * el.dataset.depth).toFixed(2)}px, 0)`
  }
  const step = () => {
    const goal = target()
    current += (goal - current) * DAMPING
    if (Math.abs(goal - current) < 0.1) current = goal
    apply()
    frame = current === goal ? 0 : requestAnimationFrame(step)
  }
  const onScroll = () => {
    if (!frame) frame = requestAnimationFrame(step)
  }

  window.addEventListener("scroll", onScroll, { passive: true })
  apply()
  teardown = () => {
    window.removeEventListener("scroll", onScroll)
    cancelAnimationFrame(frame)
  }
})
