---
title: Tullomer in Drone Applications
duration: Jul – Aug 2026
role: Solo R&D at Z Polymers
skills:
  - Design
  - FFF 3D Printing
  - Electronics integration and troubleshooting
  - Firmware management
  - Betaflight (software) configuration
  - Power-system management
  - Design of experiments
tagline: A flight-tested drone platform for finding out whether a printable superpolymer can earn its place in a drone frame.
hero: img/quad-assembled.jpg
deep_dives: []
---

!!! abstract "TL;DR"
    Designed, built and flight-tested a modular 5-inch quadcopter with a Tullomer frame, then wrote
    a comprehensive report detailing my work and a future three-part material testing plan (RF
    transparency, structural efficiency, vibration behavior) for benchmarking Tullomer against
    incumbents like carbon-fiber reinforced nylon and polycarbonate.

## Challenge

Tullomer is [Z Polymers'](https://z-polymers.com/){ .pf-external } proprietary crystalline polymer,
printable on ordinary desktop 3D printers. In Z Polymers' words, it is "one-sixth the weight of
steel yet up to six times stronger", and with extensive resistance to environmental factors it
rivals traditional high-performance polymers like PEEK, PEKK, PAEK, and Ultem, which require
expensive, specialized industrial printers. On paper it is radio frequency-transparent (dielectric
constant ≈ 3), light (1.4 g/cm³), and stiff, which makes it a natural fit for drone frames;
especially where carbon fiber's conductivity forces pilots to route antennas around it. At roughly
$500/kg however against $30–80/kg for carbon-fiber reinforced nylon, it has to exhibit a measurable
advantage before anyone will build with it.

Demonstrating its effectiveness in drone applications first required a drone that flew reliably and
could swap frame element materials without changing geometry. The original plan was to develop the
drone then do material testing, however the process of learning and configuring the entire system
along with troubleshooting unfamiliar hardware proved to absorb the whole of the project's duration.
A drone had in part been developed previously at the company, but nothing final ever flew and no
documentation was written to explain previous work or many of the faulty electronic components
in-house (worn motors, a freezing transmitter, a faulty flight controller, etc.).

## Media

<div class="pf-media" markdown>

<figure>
<video src="img/flight-test.mp4" poster="img/flight-test.jpg" width="1080" height="1920" controls preload="none" playsinline></video>
<figcaption>Flight test, August 2026</figcaption>
</figure>

<div markdown>

<figure markdown="span">
  ![The quad from above with its top plate off: flight controller stack, wiring, battery and the printed Tullomer arms](img/quad-electronics.jpg)
  <figcaption>Top plate off: the SpeedyBee F405 stack, wiring and threaded inserts in the Tullomer arms</figcaption>
</figure>

<figure>
<model-viewer src="cad/frame.glb" poster="img/frame-render.png" alt="3D model of the drone frame: four arms, a perforated center plate, camera mount and antenna mounts" camera-orbit="30deg 65deg 90%" environment-image="neutral" tone-mapping="neutral" exposure="0.7" shadow-intensity="1.2" camera-controls disable-zoom></model-viewer>
<figcaption>Frame assembly from Onshape: drag to orbit</figcaption>
</figure>

</div>

</div>

## Labor & Results

- **Design:** Adopted an open-source 5-inch modular frame (see [report](files/developing-tullomer-in-drone-applications.pdf) BOM for source) so that
  arms and center plates all bolt apart, allowing any piece to be reprinted in a different material
  and swapped in. Built editable
  [Onshape models of drone arms](https://cad.onshape.com/documents/8715dbd739085dd50a309c9a/w/8b3b11719ed05ccb2a306301/e/e5ca05f8a3461390b5089c11){ .pf-external }
  to allow future geometry modifications. Maintained the 5-inch propeller class size to be small
  enough to fly in tight spaces but large enough for material tests against commercial and defense
  FPV platforms.
- **FFF 3D Printing:** Printed the entire frame in Tullomer, as well as several other candidate parts
  of the same geometry across PLA, PETG and nylon. No parts for incumbent-material testing were
  printed yet, as finalizing standardization of print parameters had not been completed by the end
  of my time with the company. (see [report](files/developing-tullomer-in-drone-applications.pdf))
- **Electronics integration and troubleshooting:** Wired and soldered the full stack: a SpeedyBee
  F405 flight controller and coupled 35 A SpeedyBee electronic speed controller, ExpressLRS receiver,
  XT30 power lead with a 470 µF input capacitor, as well as motors and connectors. Faulty components
  were the scourge of this project. I tracked a faulty radio link to its source, replaced burnt
  motors, soldered new connectors, replaced undersized motors with stronger motors, retired a flight
  controller with a broken receiver pad, and bypassed a burnt ground pin by soldering straight to the
  board. Ultimately this project served as an excellent head first dive into learning about
  electronics and their integration.
- **Firmware management:** Matched ExpressLRS firmware at 3.3.1 on both receiver and transmitter
  sides of the RF link, configured the EdgeTX transmitter (stick calibration, ADC filter off to stop
  stepped commands and motor jitter), and documented the binding procedure for whoever picks the
  project up next.
- **Betaflight (software) configuration:** Set up CRSF serial receiver input, motor protocol, motor
  stop, arm and flight-mode switch ranges, as well as appropriate props-out motor spin direction to
  keep debris off the camera area and improve crash recovery maneuvers.
- **Power-system management:** After moving up to Surpass Hobby S2207 2550 KV motors, checked every
  current path against its rating. The 15 A motor connectors and 30 A battery connector had been
  sized for the old, smaller motors, well under the new motors' ~35 A rating. At full throttle on
  5×4.8 props each motor pulls 46 A, beyond the ESC's 35 A continuous / 45 A burst rating. The
  850 mAh 95C battery pack tops out around 81 A, while the quad can ask for more than 100 A. The
  result was a tiered upgrade plan: a 75% output cap now, MR60/XT60 connectors and 1300 mAh packs
  next, and a 30×30 stack long-term. (see [report](files/developing-tullomer-in-drone-applications.pdf) for more)
- **Design of experiments:** Wrote the methods for all three tests, each with its own metrics:
    - **RF transparency:** three experiment options based on threshold for equipment investment,
      from free link-quality tests on the drone's own radio up to NanoVNA insertion-loss and
      antenna-detuning measurements.
    - **Structural efficiency:** drop tests reported against impact energy (m·g·h) rather than drop
      height, so a heavier arm isn't mistaken for a stronger one. Additionally recommended crash
      tests for more robust real world performance testing.
    - **Vibration behavior:** Blackbox accelerometer and gyro logs analyzed with FFTs and
      spectrograms.
- **Results:** A flight-validated platform and a 13-page handoff report and final presentation for
  Z Polymers. Material testing was not run during the internship; the report sets the hardware
  baseline and the order of work for whoever takes it next.

## Reflection

Most of the summer went to getting a reliable drone in the air rather than testing the material.
Part of that was the faulty inherited hardware, and part of it was completely learning drone
engineering from the ground up, as well as all my basics in soldering, electronics and
configuration. If I had more time I'd buy the bench RF equipment (a ~$200 NanoVNA) and proceed with
material testing Tullomer; RF transparency is Tullomer's clearest advantage, and an
instrument-grade insertion-loss number for Tullomer against carbon-fiber nylon could be measured in
a week, an insight I wish I'd had sooner.

## Deep Dive Resources

- [*Developing Tullomer in Drone Applications*](files/developing-tullomer-in-drone-applications.pdf): Comprehensive final report for Z Polymers
- [Drone arm Onshape models](https://cad.onshape.com/documents/8715dbd739085dd50a309c9a/w/8b3b11719ed05ccb2a306301/e/e5ca05f8a3461390b5089c11){ .pf-external }
- [Leopard FPV Drone](https://www.printables.com/model/1517629-leopard-fpv-drone){ .pf-external }:
  Base frame credit for open-source geometry
