// Hero parallax: each [data-depth] layer drifts at its own rate as the page scrolls.
// Re-bound on every page load, since navigation.instant swaps pages without a reload.
let onScroll = null

document$.subscribe(() => {
  if (onScroll) window.removeEventListener("scroll", onScroll)
  onScroll = null

  const hero = document.querySelector(".pf-hero")
  if (!hero || matchMedia("(prefers-reduced-motion: reduce)").matches) return

  const layers = [...hero.querySelectorAll("[data-depth]")]
  let queued = false
  const update = () => {
    const y = Math.min(window.scrollY, hero.offsetHeight)
    for (const el of layers)
      el.style.transform = `translate3d(0, ${(y * el.dataset.depth).toFixed(1)}px, 0)`
    queued = false
  }
  onScroll = () => {
    if (!queued) requestAnimationFrame(update)
    queued = true
  }
  window.addEventListener("scroll", onScroll, { passive: true })
  update()
})
