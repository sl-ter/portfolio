// Scroll polish:
//  1. Damped (smooth) page scrolling site-wide via Lenis. Sidebars, search results and code
//     blocks keep native scrolling. Off when the visitor prefers reduced motion.
//  2. Hero parallax fallback for browsers without CSS scroll-driven animations
//     (extra.css handles the rest on the compositor).
//  3. Smooth in-page jumps: table-of-contents links, footnotes, back-to-top.
const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches
const cssParallax = CSS.supports("animation-timeline: view()")

const NATIVE_SCROLL = ".md-sidebar__scrollwrap, .md-search__scrollwrap, .md-typeset__scrollwrap, pre"
const lenis = window.Lenis && !reducedMotion()
  ? new Lenis({
      autoRaf: true,
      lerp: 0.1,
      stopInertiaOnNavigate: true,
      prevent: node => Boolean(node.matches && node.matches(NATIVE_SCROLL)),
    })
  : null

let teardown = () => {}

document$.subscribe(() => {
  // navigation.instant swapped the page: let Lenis re-measure it
  if (lenis) lenis.resize()

  teardown()
  teardown = () => {}

  const hero = document.querySelector(".pf-hero")
  if (!hero || cssParallax || reducedMotion()) return

  const layers = [...hero.querySelectorAll("[data-depth]")]
  let queued = false
  const update = () => {
    const y = Math.min(window.scrollY, hero.offsetHeight)
    for (const el of layers)
      el.style.transform = `translate3d(0, ${(y * el.dataset.depth).toFixed(1)}px, 0)`
    queued = false
  }
  const onScroll = () => {
    if (!queued) requestAnimationFrame(update)
    queued = true
  }
  window.addEventListener("scroll", onScroll, { passive: true })
  update()
  teardown = () => window.removeEventListener("scroll", onScroll)
})

const smoothScrollTo = (target, offset = 0) => {
  if (lenis) lenis.scrollTo(target, { offset })
  else if (typeof target === "number") window.scrollTo({ top: target, behavior: "smooth" })
  else target.scrollIntoView({ behavior: "smooth" })
}

// Capture phase, so this runs before Material's own handlers.
document.addEventListener("click", ev => {
  if (reducedMotion() || ev.defaultPrevented || ev.button !== 0) return
  if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return

  if (ev.target.closest(".md-top")) {
    ev.preventDefault()
    ev.stopPropagation()
    smoothScrollTo(0)
    return
  }

  // Same-page anchors only. navigation.instant rewrites hrefs to absolute URLs, so compare
  // the resolved URL rather than looking for a leading "#".
  const link = ev.target.closest("a[href]")
  if (!link || link.target || !link.hash) return
  const url = new URL(link.href)
  if (url.origin !== location.origin || url.pathname !== location.pathname) return
  const id = decodeURIComponent(url.hash.slice(1))
  const target = document.getElementById(id)
  if (!target) return
  ev.preventDefault()
  ev.stopPropagation()
  const header = document.querySelector(".md-header")
  smoothScrollTo(target, -((header ? header.offsetHeight : 0) + 16))
  history.replaceState(history.state, "", `#${encodeURIComponent(id)}`)
}, true)
