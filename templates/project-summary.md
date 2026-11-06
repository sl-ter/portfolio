---
# Copy to docs/projects/<slug>/index.md. Front matter and sections mirror the vault intake note
# (one per project, named after it). The page header (hero, title, tagline, duration, role,
# skill chips) is rendered from this front matter by overrides/main.html; the body starts at TL;DR.
title: Project Name
duration: July - Sept 2026
role: Your role
skills:
  - Skill A
  - Skill B
tagline: One sentence of impact, ideally with a number.
hero: img/hero.jpg
deep_dives: []
---

!!! abstract "TL;DR"
    One sentence of impact, ideally with a number.

## Challenge

Two or three sentences: the problem and why it was hard.

## Media

<figure markdown="span">
  ![Caption](img/figure-1.jpg)
  <figcaption>Caption</figcaption>
</figure>

<!-- Video and CAD. Make files with scripts/compress_media.sh <slug> <file>..., which prints
     these snippets. In the PDF each one prints as its poster with a link back to the page.
     Keep these figures plain <figure> (no markdown attribute).

<figure>
<video src="img/clip.mp4" poster="img/clip.jpg" controls preload="none" playsinline></video>
<figcaption>Caption</figcaption>
</figure>

Silent loop (compress with --mute):
<video src="img/loop.mp4" poster="img/loop.jpg" autoplay loop muted playsinline></video>

CAD: export GLB (Onshape: right-click the part studio, Export, GLTF/GLB) to cad/part.glb, plus an
iso render to cad/part.png as the poster:
<figure>
<model-viewer src="cad/part.glb" poster="cad/part.png" alt="Part name" camera-controls disable-zoom></model-viewer>
<figcaption>Drag to orbit</figcaption>
</figure>
-->

## Labor & Results

- **Skill A:** what you did with it, and what it produced.
- **Skill B:** ...

<!-- Optional headline numbers:
<div class="grid cards metrics" markdown>

-   **00 %**

    what the number means

</div>
-->

## Reflection

Two or three lines: what you'd do differently next time.

## Deep dives

- [Topic](topic.md)
