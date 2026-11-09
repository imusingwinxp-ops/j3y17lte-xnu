# J3XNU048 — Verified Stable Branch

This branch preserves the last physically verified stable J3Y17LTE XNU state before SMP work.

Verified on Samsung Galaxy J3 2017 (SM-J330FN):

- iOS 16-era XNU boots into iOS userland
- Apple logo renders
- lock screen renders
- TD4100 touch input works
- GPIO button support is included
- single-core CPU configuration
- no experimental SMP patch

The public source patch stack ends at:

`xnu/patches/0152-j3y17lte-input.patch`

The later experimental SMP work is intentionally not part of this branch.

This repository contains source patches only. Compiled kernels, recovery images, build artifacts, private CI configuration, and internal development notes are not distributed here.
