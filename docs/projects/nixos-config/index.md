---
title: NixOS Config
duration: Apr 2026 – present
role: Personal project
skills:
  - NixOS & Nix flakes
  - Linux systems administration
  - systemd
  - Storage & filesystem design
  - Basic networking
  - Git version control
  - Technical documentation
tagline: My whole operating system as version-controlled code, which I can rebuild, roll back, and share across machines.
hero: img/nixos-logo-diagram.png
deep_dives: []
---

!!! abstract "TL;DR"
    Built my laptop's entire operating system (desktop, services, disk layout, power behavior,
    terminal and shell) from about 650 lines of version-controlled Nix. Any change can be rolled
    back to one of the last 21 system versions, and the setup is published as an open-source,
    MIT-licensed configuration.

## Challenge

Most computers are configured manually, where a package installed here and a settings file edited
there are changed in an imperative way. This is fine until machines have been changed so many times
that they drift from their original purpose, where it may work but perhaps nobody can say exactly
why, reproduce it, or undo last month's change. I wanted my main machine to be engineered like
anything else I build: specified in writing, under version control, and recoverable when something
breaks. NixOS declaratively manages all of that control up front. Every service, driver and setting
has to be declared, in a functional language, with nothing switched on by default for you.

**Why work on your own operating system?** The OS is the tool every other tool runs on. Owning its
configuration means understanding the layers most engineers never see: how the machine boots, how
storage is laid out, which services run and why, and who can log in and how. Those same layers
dictate every element of efficiency, capability, and security at every step of the system, and turn
it from a black box into a project with a design record I can be proud of.

**Why NixOS specifically:**

- **Declarative:** the whole system, from bootloader to terminal colors, is described in plain-text
  files. The files *are* the system: delete a line, rebuild, and that thing is gone, with no
  leftover state.
- **Reproducible:** a lockfile pins the exact version of every input, so the same config builds the
  same system, today or a year from now, on this laptop or a new one.
- **Atomic, with rollback:** each rebuild produces a new, complete system "generation" alongside the
  old ones. If an update breaks something, I pick the previous generation from the boot menu and I'm
  back, with nothing half-installed.
- **Auditable:** because the system is text in git, every change has a diff, a message and a date.
  My OS has a commit history.
- **Modular:** the config is built from modules the way an assembly is built from parts. Each
  machine (its hardware and system services), each person's environment, and each piece of shared
  policy is its own module, and a machine is defined by the list of modules it imports. Adding a
  second computer means writing only what's different about it, and a change to a shared module
  reaches every machine that uses it on its next rebuild. Home Manager applies the same approach to
  user-level settings like the shell, terminal and editor.

## Labor & Results

- **NixOS & Nix flakes:** Moved a hand-configured NixOS install into a git-tracked flake with one
  entry per machine, and split it into three kinds of module: `hosts/` (one machine's hardware and
  system), `users/` (one person's environment, importable by any host) and `modules/` (shared
  policy, such as the garbage-collection rules below), all with space for future room to build. A
  new machine is a short file that lists which modules it needs. The live system config is a
  symlink to the repo, so editing the repo *is* editing the system. I built the desktop on Hyprland
  (a tiling Wayland compositor) with the Noctalia shell, configured through Nix attribute sets that
  render to its TOML config.
- **Linux systems administration:** Diagnosed problems by checking the live system rather than
  trusting the config files. For instance, a first desktop shell (Caelestia) was discarding every
  settings change since its service logs showed it trying to write to a read-only file in the Nix
  store. I replaced it with a shell (Noctalia) that keeps declarative and runtime settings in
  separate files by design.
- **systemd:** Wrote a weekly cleanup service that keeps the newest 21 system generations no matter
  their age, then garbage-collects. An age-based cutoff ("delete anything older than 30 days") would
  eventually delete every rollback point on a machine left alone for months. Set 21 from
  measurement, not a guess: generations share most of their files, so the last 10 together took
  only ~12.8 GiB against a 12.15 GiB running system, about 0.5 GiB per extra generation. Also
  configured lid-close, docking and sleep behavior through systemd-logind, and disabled hibernation
  outright because the machine has no swap to hibernate into.
- **Storage & filesystem design:** Partitioned the drive as a 1 GiB EFI partition, a 175 GiB Btrfs
  partition split into `/`, `/home`, `/nix` and `/var` subvolumes (zstd compression), and ~300 GiB
  of XFS for `/data`. XFS holds databases and AI model weights, workloads that Btrfs's copy-on-write
  slows down. The layout is recorded declaratively with disko.
- **Git version control:** Every change is a commit. Flake updates never apply automatically: a
  custom shell function (`nix-update`) updates the inputs, checks the flake, rebuilds, stops at the
  first failure, and leaves the lockfile diff uncommitted for review.
- **Cross-platform configuration:** Shared one terminal, prompt and keybind setup with a MacBook
  that doesn't run Nix. The shared configs are plain files in the repo, which Home Manager links in
  on NixOS and the Mac symlinks from its own clone, so one edit reaches both machines. Each machine
  gets a small override file for platform-only settings. Window-manager keybinds use the same keys
  on both: the Super layer on Linux mirrors the Ctrl layer on macOS.
- **Technical documentation:** Published a sanitized, MIT-licensed copy of the config on GitHub.
  Personal details are stripped and hardware IDs replaced with placeholders, and the README covers
  the design decisions and how to adapt the config to another machine.
- **Results:** The laptop has run from this repo since September 2026, with dozens of rebuilds, each
  one reversible. The modular structure is now paying off in a second machine, the first step of a
  small homelab: an always-on mini PC whose draft config reuses the laptop's shared modules. Its job
  is to stay up 24/7 as the anchor of an encrypted mesh VPN that links my devices wherever they are,
  and to wake heavier machines over the network (wake-on-LAN) only when they're needed, instead of
  leaving them running.

## Reflection

The most expensive mistake was in process, not code. For ten days I applied changes with
`nixos-rebuild test`, which activates a config only until the next reboot, instead of `switch`,
which makes it the boot default. When the machine finally rebooted, it came back on a ten-day-old
system. The repo still had every change, so nothing was lost, but it taught me to check what the
system is *actually* running rather than what the file says. I also started out planning a
multi-node cluster and scaled back to learning one machine properly first, which was the right
call. Next install, I'd set up full-disk encryption from the start: adding it now means
repartitioning.

## Deep-dive references

- Public config: [github.com/sl-ter/nixos-config](https://github.com/sl-ter/nixos-config){ .pf-external }
  (MIT); the README's "Design choices" section is the long-form write-up
- Credits, as in the repo: lockscreen, fastfetch and blur recipe adapted from
  [Adarsh496/niri-noctalia-dots](https://github.com/Adarsh496/niri-noctalia-dots){ .pf-external };
  prompt based on Starship's Catppuccin preset
- NixOS logo from [NixOS/nixos-artwork](https://github.com/NixOS/nixos-artwork/tree/master/logo){ .pf-external },
  CC BY 4.0
