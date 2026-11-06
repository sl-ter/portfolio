// Scroll polish:
//  1. Damped (smooth) page scrolling site-wide via Lenis. Sidebars, search results and code
//     blocks keep native scrolling. Off when the visitor prefers reduced motion.
//  2. Hero parallax fallback for browsers without CSS scroll-driven animations
//     (extra.css handles the rest on the compositor).
//  3. Smooth in-page jumps: table-of-contents links, footnotes, back-to-top.
//  4. The header logo turns with the scroll.
//  5. Hero network: signal routes loop across the mesh after it builds itself.
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

// Logo: the mitsudomoe turns with the scroll position (clockwise, heads leading)
const SPIN_DEG_PER_PX = 0.2
const spinLogo = y => {
  const logo = document.querySelector(".md-header__button.md-logo svg")
  if (logo) logo.style.setProperty("--pf-spin", `${(y * SPIN_DEG_PER_PX).toFixed(1)}deg`)
}
if (!reducedMotion()) {
  if (lenis) lenis.on("scroll", ({ scroll }) => spinLogo(scroll))
  else window.addEventListener("scroll", () => spinLogo(window.scrollY), { passive: true })
}

// Per-page setup; everything registered here is torn down when instant navigation swaps pages
let teardowns = []

document$.subscribe(() => {
  // navigation.instant swapped the page: let Lenis re-measure it, re-sync the logo
  if (lenis) lenis.resize()
  if (!reducedMotion()) spinLogo(window.scrollY)

  teardowns.forEach(fn => fn())
  teardowns = []

  const hero = document.querySelector(".pf-hero")
  if (!hero || reducedMotion()) return
  const network = hero.querySelector(".pf-hero__drawing[data-intro]")
  if (network) teardowns.push(startSignals(hero, network))
  if (!cssParallax) teardowns.push(parallaxFallback(hero))
})

function parallaxFallback(hero) {
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
  return () => window.removeEventListener("scroll", onScroll)
}

// Hero network: once the mesh has built itself, signals keep routing across it. A random path
// lights up node by node and link by link, holds, then dies out one piece at a time from its
// start, and the next route begins as the previous one starts to fade. Pauses while the hero is
// off-screen or the tab is hidden.
const SVG_NS = "http://www.w3.org/2000/svg"
const HOP_MS = 240      // between successive hops lighting up
const HOLD_MS = 450     // fully lit before it starts dying out
const FADE_MS = 140     // between successive pieces dying out
const VISIBLE_Y = 620   // keep routes above the hero's bottom fade (viewBox units)

function startSignals(hero, svg) {
  const nodes = [...svg.querySelectorAll(".node")].map(c => ({
    x: +c.getAttribute("cx"), y: +c.getAttribute("cy"), r: +c.getAttribute("r"),
  }))
  const adj = nodes.map(() => [])
  for (const link of svg.querySelectorAll(".link")) {
    const a = +link.dataset.a, b = +link.dataset.b
    adj[a].push(b)
    adj[b].push(a)
  }
  const linkLayer = svg.querySelector(".net-signal")
  const hopLayer = svg.querySelector(".net-hops")

  const timers = new Set()
  const later = (fn, ms) => {
    const t = setTimeout(() => { timers.delete(t); fn() }, ms)
    timers.add(t)
  }

  // Random route: breadth-first search from a random source with neighbours shuffled, so the
  // path is a shortest one but a different one each time; target 4–7 hops away
  const pickRoute = () => {
    const visible = nodes.flatMap((n, i) => (n.y < VISIBLE_Y ? [i] : []))
    for (let tries = 0; tries < 20; tries++) {
      const src = visible[Math.floor(Math.random() * visible.length)]
      const prev = new Map([[src, -1]])
      const depth = new Map([[src, 0]])
      const queue = [src]
      while (queue.length) {
        const u = queue.shift()
        for (const v of [...adj[u]].sort(() => Math.random() - 0.5)) {
          if (prev.has(v)) continue
          prev.set(v, u)
          depth.set(v, depth.get(u) + 1)
          queue.push(v)
        }
      }
      const targets = [...depth].filter(([i, d]) => d >= 4 && d <= 7 && nodes[i].y < VISIBLE_Y)
      if (!targets.length) continue
      let v = targets[Math.floor(Math.random() * targets.length)][0]
      const route = [v]
      while (prev.get(v) !== -1) route.push((v = prev.get(v)))
      return route.reverse()
    }
    return null
  }

  const lightNode = (i, pieces) => {
    const n = nodes[i]
    const dot = document.createElementNS(SVG_NS, "circle")
    dot.setAttribute("class", "hop")
    dot.setAttribute("cx", n.x)
    dot.setAttribute("cy", n.y)
    dot.setAttribute("r", n.r + 1.5)
    hopLayer.append(dot)
    dot.animate([{ transform: "scale(0)" }, { transform: "scale(1)" }],
      { duration: 280, easing: "cubic-bezier(0.34, 1.56, 0.64, 1)" })
    pieces.push(dot)
  }

  const lightLink = (i, j, pieces) => {
    const a = nodes[i], b = nodes[j]
    const line = document.createElementNS(SVG_NS, "path")
    line.setAttribute("class", "signal")
    line.setAttribute("pathLength", "1")
    line.setAttribute("d", `M${a.x},${a.y}L${b.x},${b.y}`)
    linkLayer.append(line)
    line.animate([{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }],
      { duration: HOP_MS * 0.85, easing: "ease-out", fill: "forwards" })
    pieces.push(line)
  }

  let paused = false, idle = false
  const send = () => {
    if (paused) { idle = true; return }
    const route = pickRoute()
    if (!route) return
    const pieces = []
    lightNode(route[0], pieces)
    for (let k = 1; k < route.length; k++) {
      later(() => lightLink(route[k - 1], route[k], pieces), HOP_MS * (k - 1) + 60)
      later(() => lightNode(route[k], pieces), HOP_MS * k)
    }
    const lit = HOP_MS * (route.length - 1) + HOLD_MS
    later(() => {
      pieces.forEach((el, k) => later(() => {
        el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 320, fill: "forwards" })
          .finished.then(() => el.remove(), () => el.remove())
      }, FADE_MS * k))
      later(send, 260) // next route starts as this one begins to fade
    }, lit)
  }

  const resume = () => {
    paused = document.hidden || !onScreen
    if (!paused && idle) { idle = false; send() }
  }
  let onScreen = true
  const observer = new IntersectionObserver(([entry]) => { onScreen = entry.isIntersecting; resume() })
  observer.observe(hero)
  document.addEventListener("visibilitychange", resume)
  later(send, parseFloat(svg.dataset.intro) * 1000 + 300)

  return () => {
    timers.forEach(clearTimeout)
    timers.clear()
    observer.disconnect()
    document.removeEventListener("visibilitychange", resume)
    linkLayer.replaceChildren()
    hopLayer.replaceChildren()
  }
}

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
