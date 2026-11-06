// "Portfolio as a PDF": visitors tick the sections they want and get one PDF.
// CI prints every page to its own PDF beforehand (scripts/build_pdfs.py writes them and
// pdf/manifest.json). Here the ticked ones are merged with pdf-lib behind the cover, with a
// contents page (linked), page numbers and bookmarks, all in the browser. pdf-lib, fontkit and
// the IBM Plex fonts load only on this page.
const PDF_LIBS = [
  "https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/dist/pdf-lib.min.js",
  "https://cdn.jsdelivr.net/npm/@pdf-lib/fontkit@1.1.1/dist/fontkit.umd.min.js",
]
const PLEX = "https://cdn.jsdelivr.net/npm/@ibm/plex-sans@1.1.0/fonts/complete/woff/IBMPlexSans-"

// Letter, in points; matches the margins in print.css
const PAGE_W = 612, PAGE_H = 792, MARGIN = 54
const ROWS_PER_CONTENTS_PAGE = 24

document$.subscribe(() => {
  const root = document.getElementById("pf-pdf-builder")
  if (root) initBuilder(root)
})

const loadScript = src => new Promise((resolve, reject) => {
  if (document.querySelector(`script[src="${src}"]`)) return resolve()
  const s = document.createElement("script")
  s.src = src
  s.onload = resolve
  s.onerror = () => reject(new Error(`Couldn't load ${src}`))
  document.head.append(s)
})
let libs = null
const loadLibs = () => (libs ??= Promise.all(PDF_LIBS.map(loadScript)))

const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag)
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v
    else if (k in node && typeof v !== "string") node[k] = v
    else node.setAttribute(k, v)
  }
  node.append(...children.filter(c => c != null))
  return node
}

async function initBuilder(root) {
  const manifestUrl = new URL(root.dataset.manifest, location.href)
  let manifest
  try {
    const res = await fetch(manifestUrl, { cache: "no-cache" })
    if (!res.ok) throw new Error(res.status)
    manifest = await res.json()
  } catch {
    root.replaceChildren(el("p", { class: "pf-builder__empty" },
      "The section PDFs are generated when the site is published, so the builder only works on ",
      el("a", { href: "https://sl-ter.github.io/portfolio/pdf-builder/" }, "the live site"), "."))
    return
  }
  loadLibs().catch(() => {}) // warm up while the visitor picks; errors resurface on download

  // One row per section: checkbox, title, duration, page count, and Summary/Full when it has deep dives
  const rows = []
  const groups = manifest.groups.map(group => {
    const items = group.items.map(item => {
      const box = el("input", { type: "checkbox", checked: true })
      const pages = el("span", { class: "pf-builder__pages" })
      const variant = el("span", { class: "pf-builder__variant" })
      const radios = item.variants.full ? ["summary", "full"].map(v => el("input", {
        type: "radio", name: `pf-variant-${item.id}`, value: v, checked: v === "summary",
      })) : []
      radios.forEach(r => variant.append(el("label", {}, r, r.value === "full" ? "Full" : "Summary")))
      const row = { item, box, radios, pages }
      row.variant = () => radios.find(r => r.checked)?.value ?? "summary"
      rows.push(row)
      return el("li", { class: "pf-builder__item" },
        el("label", { class: "pf-builder__pick" }, box,
          el("span", { class: "pf-builder__title" }, item.title),
          item.duration ? el("span", { class: "pf-builder__meta" }, item.duration) : null),
        radios.length ? variant : null, pages)
    })
    const set = on => () => {
      for (const r of rows) if (group.items.includes(r.item)) r.box.checked = on
      update()
    }
    return el("fieldset", { class: "pf-builder__group" },
      el("legend", {}, el("span", {}, group.title),
        group.items.length > 1 ? el("span", { class: "pf-builder__bulk" },
          el("button", { type: "button", onclick: set(true) }, "All"),
          el("button", { type: "button", onclick: set(false) }, "None")) : null),
      el("ul", {}, ...items))
  })

  const frontMatter = el("input", { type: "checkbox", checked: true })
  const total = el("span", { class: "pf-builder__total" })
  const status = el("p", { class: "pf-builder__status", role: "status" })
  const download = el("button", { type: "submit", class: "md-button md-button--primary" }, "Download PDF")
  const form = el("form", { class: "pf-builder" }, ...groups,
    el("div", { class: "pf-builder__bar" },
      el("label", { class: "pf-builder__pick" }, frontMatter, "Cover and contents page"),
      total, download),
    status)

  const chosen = () => rows.filter(r => r.box.checked)
  function update() {
    for (const r of rows) {
      const n = r.item.variants[r.variant()].pages
      r.pages.textContent = `${n} ${n === 1 ? "page" : "pages"}`
    }
    const picks = chosen()
    let pages = picks.reduce((sum, r) => sum + r.item.variants[r.variant()].pages, 0)
    if (frontMatter.checked && picks.length) pages += manifest.cover.pages + contentsPages(picks.length)
    total.textContent = picks.length
      ? `${picks.length} ${picks.length === 1 ? "section" : "sections"} · ${pages} pages` : "Nothing selected"
    download.disabled = !picks.length
  }
  form.addEventListener("change", update)
  form.addEventListener("submit", async ev => {
    ev.preventDefault()
    download.disabled = true
    status.textContent = "Assembling your PDF…"
    try {
      const bytes = await assemble(manifest, manifestUrl, chosen(), frontMatter.checked)
      save(bytes, `${manifest.author.replace(/\s+/g, "_")}_Portfolio.pdf`)
      status.textContent = "Done. Your download should have started."
    } catch (err) {
      console.error(err)
      status.textContent = "Something went wrong building the PDF. Please try again in a moment."
    }
    download.disabled = false
  })
  root.replaceChildren(form)
  update()
}

const contentsPages = n => Math.ceil(n / ROWS_PER_CONTENTS_PAGE)

function save(bytes, name) {
  const url = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }))
  const a = el("a", { href: url, download: name })
  document.body.append(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

async function assemble(manifest, base, picks, frontMatter) {
  await loadLibs()
  const { PDFDocument, PDFHexString, PDFName, rgb } = PDFLib
  const fetchBytes = async url => {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`${res.status} ${url}`)
    return res.arrayBuffer()
  }
  const files = picks.map(r => r.item.variants[r.variant()].files.map(f => new URL(f, base)))
  const [sections, cover, regular, semibold] = await Promise.all([
    Promise.all(files.map(urls => Promise.all(urls.map(fetchBytes)))),
    frontMatter ? fetchBytes(new URL(manifest.cover.file, base)) : null,
    fetchBytes(`${PLEX}Regular.woff`),
    fetchBytes(`${PLEX}SemiBold.woff`),
  ])

  const doc = await PDFDocument.create()
  doc.registerFontkit(fontkit)
  const font = await doc.embedFont(regular, { subset: true })
  const bold = await doc.embedFont(semibold, { subset: true })
  const ink = rgb(0.114, 0.125, 0.149), muted = rgb(0.42, 0.44, 0.475)
  const rule = rgb(0.835, 0.847, 0.867), orange = rgb(1, 0.31, 0)

  const append = async bytes => {
    const src = await PDFDocument.load(bytes)
    const pages = await doc.copyPages(src, src.getPageIndices())
    pages.forEach(p => doc.addPage(p))
    return pages
  }
  if (cover) await append(cover)
  const contents = frontMatter
    ? Array.from({ length: contentsPages(picks.length) }, () => doc.addPage([PAGE_W, PAGE_H])) : []

  // Sections, remembering where each starts
  const entries = []
  for (const [k, r] of picks.entries()) {
    let first = null
    for (const bytes of sections[k]) {
      const added = await append(bytes)
      first ??= added[0]
    }
    const group = manifest.groups.find(g => g.items.includes(r.item)).title
    const full = r.variant() === "full" ? " (full)" : ""
    entries.push({ group, title: r.item.title + full, meta: r.item.duration, page: first })
  }
  const pages = doc.getPages()
  const numberOf = page => pages.indexOf(page) + 1

  // Contents: grouped rows, each linking to its section
  const link = (page, [x0, y0, x1, y1], target) => page.node.addAnnot(doc.context.register(doc.context.obj({
    Type: "Annot", Subtype: "Link", Rect: [x0, y0, x1, y1], Border: [0, 0, 0],
    Dest: [target.ref, "XYZ", null, null, null],
  })))
  let row = 0, y = 0, lastGroup = null
  for (const e of entries) {
    const page = contents[Math.floor(row / ROWS_PER_CONTENTS_PAGE)]
    if (row % ROWS_PER_CONTENTS_PAGE === 0) {
      y = PAGE_H - MARGIN - 26
      page.drawText(row ? "Contents (continued)" : "Contents", { x: MARGIN, y, size: 26, font: bold, color: ink })
      y -= 20
      page.drawText(`${manifest.author} · ${manifest.title} · ${manifest.site_url.replace(/^https:\/\//, "")}`,
        { x: MARGIN, y, size: 9, font, color: muted })
      y -= 22
      page.drawLine({ start: { x: MARGIN, y }, end: { x: PAGE_W - MARGIN, y }, thickness: 0.75, color: rule })
      y -= 16
      lastGroup = null
    }
    if (e.group !== lastGroup) {
      y -= lastGroup === null ? 14 : 36
      page.drawText(e.group.toUpperCase(), { x: MARGIN, y, size: 8.5, font: bold, color: orange })
      y -= 2
      lastGroup = e.group
    }
    y -= 22
    const num = String(numberOf(e.page))
    const numW = bold.widthOfTextAtSize(num, 11)
    const titleW = font.widthOfTextAtSize(e.title, 11)
    page.drawText(e.title, { x: MARGIN, y, size: 11, font, color: ink })
    let leaderX = MARGIN + titleW + 8
    if (e.meta) {
      page.drawText(e.meta, { x: leaderX, y: y + 0.5, size: 8.5, font, color: muted })
      leaderX += font.widthOfTextAtSize(e.meta, 8.5) + 8
    }
    page.drawLine({ start: { x: leaderX, y: y + 2 }, end: { x: PAGE_W - MARGIN - numW - 8, y: y + 2 },
      thickness: 0.6, color: rule, dashArray: [0.6, 3], lineCap: 1 })
    page.drawText(num, { x: PAGE_W - MARGIN - numW, y, size: 11, font: bold, color: ink })
    link(page, [MARGIN - 4, y - 6, PAGE_W - MARGIN + 4, y + 14], e.page)
    row++
  }

  // Page numbers on everything after the cover
  pages.forEach((page, i) => {
    if (cover && i === 0) return
    const { width } = page.getSize()
    const label = `${i + 1} / ${pages.length}`
    page.drawText(`${manifest.author} · ${manifest.title}`, { x: MARGIN, y: 28, size: 8, font, color: muted })
    page.drawText(label, { x: width - MARGIN - font.widthOfTextAtSize(label, 8), y: 28, size: 8, font, color: muted })
  })

  // Bookmarks: Contents, then one per section
  const marks = [...(contents.length ? [{ title: "Contents", page: contents[0] }] : []), ...entries]
  const ctx = doc.context
  const outline = ctx.nextRef()
  const refs = marks.map(() => ctx.nextRef())
  marks.forEach((m, i) => ctx.assign(refs[i], ctx.obj({
    Title: PDFHexString.fromText(m.title), Parent: outline,
    ...(i > 0 ? { Prev: refs[i - 1] } : {}), ...(i < marks.length - 1 ? { Next: refs[i + 1] } : {}),
    Dest: [m.page.ref, "XYZ", null, null, null],
  })))
  ctx.assign(outline, ctx.obj({ Type: "Outlines", First: refs[0], Last: refs[refs.length - 1], Count: marks.length }))
  doc.catalog.set(PDFName.of("Outlines"), outline)
  doc.catalog.set(PDFName.of("PageMode"), PDFName.of("UseOutlines"))

  doc.setTitle(`${manifest.author} · ${manifest.title}`)
  doc.setAuthor(manifest.author)
  doc.setSubject(entries.map(e => e.title).join(", "))
  doc.setCreator(manifest.site_url)
  return doc.save()
}
