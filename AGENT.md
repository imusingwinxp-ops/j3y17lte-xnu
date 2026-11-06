# J3Y17LTE XNU port — handoff for the next ChatGPT coding agent

**Read this entire file before changing anything.** This is a status handoff for the user's active Samsung Galaxy J3 (2017) / Exynos 7570 XNU bring-up. It is not proof that iOS boots. The user calls the phone "J3", refers to the project as "J3XNU", and prefers short, accurate, test-backed steps. The user has repeatedly incurred unnecessary CircleCI credits from failed patch preflights and is particularly concerned about avoiding another failed CI run.

**As of 2026-11-06 at the end of the session:** J3XNU024 **successfully compiled and packaged on CircleCI pipeline #10**. The user's physical-phone photo for J3XNU024 **has NOT arrived yet**; they said they will send it the following morning. **Wait for that photo and the packaging result before designing J3XNU025.** Do not infer further runtime progress from CI success alone.

## Canonical places and versions

- GitHub repo: <https://github.com/imusingwinxp-ops/j3y17lte-xnu> (branch `main`).
- Last verified **code** commit: `1b0ba05f45d851d486a6cdcee62cb4fd5e8a2f25` ("J3XNU024: trace Mach IPC callback logging and return checkpoints").
- Passing CI pipeline for that code: <https://circleci.com/gh/imusingwinxp-ops/j3y17lte-xnu/10> (green / success, about four minutes). Artifact in its **Artifacts** tab: `j3y17lte-xnu-kernel.tgz`, containing `kernel.development.j3y17lte` and `SHA256SUMS`. CircleCI artifacts can retain identical filenames across runs, so validate their contents.
- Latest patch: `xnu/patches/0130-j3y17lte-trace-mach-ipc-startup.patch`.
- CI config: `.circleci/config.yml`. GitHub Actions was blocked by GitHub billing/spend-limit restrictions; use CircleCI instead.
- Donor heritage: `orhunnx/ios-a5xelte`, itself related to `ios-sweet`; the user is adapting an Exynos/Samsung-oriented XNU port to **Exynos 7570**, not making a working iOS 16 port from scratch.
- XNU base: Apple `apple-oss-distributions/xnu`, tag/branch `rel/xnu-8796` (XNU 8796, iOS 16-era).
- CircleCI pins `blacktop/darwin-xnu-build` to `663906528d1cd5ea8fde7de6f16de73db9511549`, with `MACHINE_CONFIG=J3Y17LTE`, `KERNEL_CONFIG=DEVELOPMENT`, Xcode 16.4 macOS executor.
- The user's own WSL development checkout is `~/ios-j330fn`; CI repository subdirectory `~/ios-j330fn/xnu-j3/ci-repo`. The ChatGPT agent's filesystem is not automatically the user's WSL filesystem.

## Verified physical progress, in order

1. Earlier J3XNU versions brought up an XNU Mach-O ARM64 kernel far enough to paint coloured diagnostic blocks through the J3's physical framebuffer while its unchanged Samsung Galaxy J3 boot splash remains visible. These colours do **not** mean iOS userland or UI is booting.
2. J3XNU021 added scheduler checkpoints stages 111–120. The phone reached stage 111 but stopped at an early scheduler `kprintf`.
3. J3XNU022 bypassed J3-only informational scheduler logging and reached stages 111–117 but not 118. This pointed toward `SCHED(init)` / timeshare initialisation.
4. J3XNU023 patch `0129-j3y17lte-trace-timeshare-init.patch` traced `sched_timeshare_init()` and bypassed two informational `printf` calls **only for J3**. Its phone photo showed stages **121–128 all reached** and also stages **107** (`sched_init` returned) and **108** (MAC policy phase passed), but **no 109** (`kernel_startup_initialize_upto(STARTUP_SUB_MACH_IPC)` returned). This is the crucial last physical observation.
5. J3XNU024 patch `0130` adds three marker rows around **each** MACH_IPC startup callback (up to 20 callbacks). It compiles and has a green pipeline #10, but has not yet been confirmed to execute on physical hardware. **The next task is interpreting the new phone photo**, not guessing more fixes.

Past J3XNU023 photo is in the prior ChatGPT conversation and may need to be reattached. Do not pretend you can see it in the GitHub repository.

## Exact colour-marker encoding (critical!)

The early framebuffer is 32-bit colour with physical base `0x67000000`, stride `2880 bytes = 720 pixels`, marker width `24 pixels`, and marker horizontal spacing `32 pixels`. Each stage draws a brightly coloured short rectangle. **Column position, not colour, is authoritative.** A marker in the first position represents the first stage of that row (except the oldest 1–20 row, where stage number itself is used as horizontal index).

The framebuffer code is `osfmk/arm64/sweet_early.c`, patched in order. Diagnostic rows are at these **framebuffer scanline y coordinates** (lower y is physically higher on-screen):

| Stage ID | Screen y | Purpose |
|---|---:|---|
| 1–20 | 680 | Early original checkpoints |
| 21–40 | 696 | Second generation |
| 41–60 | 708 | Third generation |
| 61–80 | 720 | Fourth generation (80 is panic marker) |
| 81–100 | 668 | Firehose/OSLog |
| 101–120 | 656 | Bootstrap/scheduler; 107 and 108 reached, 109 absent on J3XNU023 |
| 121–140 | 644 | Timeshare 121–128 filled on J3XNU023; 129–140 unassigned by J3XNU024 |
| 141–160 | 632 | **J3XNU024 callback entered**, index 0–19 |
| 161–180 | 620 | **J3XNU024 startup logging returned**, index 0–19 |
| 181–200 | 608 | **J3XNU024 callback function returned**, index 0–19 |

**IMPORTANT CORRECTION TO A PREVIOUS CHAT MESSAGE:** The new rows in a photo appear from **top to bottom** as **181–200 returned**, then **161–180 logging returned**, then **141–160 entered**. The previous assistant's chat table accidentally inverted top/bottom. Always use the precise y coordinates and the new patch, not that old table.

In `kernel_startup_initialize_upto()`, a local zero-based `j3_mach_ipc_callback_index` increments only after each `STARTUP_SUB_MACH_IPC` callback returns. For callback `i` (0 to 19):

- Stage `141+i` is drawn at the **top of the startup loop before even verbose startup logging**.
- Stage `161+i` is drawn after `kernel_startup_log(cur->subsystem)` and immediately before `cur->func(cur->arg)`.
- Stage `181+i` is drawn immediately after `cur->func(cur->arg)` returns.

Interpretation for the same **column**:

| Entered | Logging returned | Callback returned | Implication |
|---|---|---|---|
| Yes | No | No | Hung in verbose logging, startup phase/switch, or `kernel_startup_log` before callback. Inspect that path. |
| Yes | Yes | No | The actual callback function did not return. Identify which callback first. |
| Yes | Yes | Yes | That callback returned; look at the next column. |
| No | No | No | Not reached that callback yet; if even the first column is blank, investigate what happened before the MACH_IPC subsystem / startup loop. |

There may be other startup subsystems executed before MACH_IPC, even in the same `kernel_startup_initialize_upto()` call, so **do not assume zero new markers necessarily means a MACH_IPC callback failed**. If all observed MACH_IPC callbacks return yet stage 109 remains absent, inspect end-of-loop `kernel_startup_log(upto)`, final verbose logging, and function exit.

Do not assume callback index `i` maps to a specific C function merely by filesystem/source search order: XNU startup entries are sorted by subsystem and rank, and same-rank order may be linker-dependent. Inspect `STARTUP(MACH_IPC, ...)` registrations, linker order, or add carefully scoped identifying marks after the photo shows the failing index.

## Next session procedure

1. Ask for or inspect the **J3XNU024 phone photo**, and, if available, the WSL terminal packaging output. Confirm the photo corresponds to J3XNU024, not an earlier image.
2. Decode the **three newly added rows**, counting block **columns** from the left, and relate the first missing stage in each row to the same callback index.
3. Give the user a brief, evidence-backed conclusion before editing. State any uncertainty from camera perspective or overlapping colours. Use image pixel sampling/cropping when helpful.
4. Read latest GitHub main and **all relevant existing patches**, especially `0118`, `0120`, `0121`, `0124`, `0125`, `0127`–`0130`, plus `.circleci/config.yml`, **before** planning a new patch.
5. Diagnose the actual specific failing function/logging path. Prefer targeted diagnostics or narrow J3-only fixes. **Do not bypass core IPC, scheduler, VM, or security initialisation blindly.** Do not claim boot progress past what the phone displays.
6. Only when the diagnosis warrants it, create **one** well-tested new patch (likely `0131-....patch`), with a single remote commit and the correct CI assertions. Let CircleCI run exactly once if possible.
7. Upon green CI, instruct user to download the new artifact, verify `SHA256SUMS`, verify Mach-O arm64 and **version-specific embedded strings**, then package a **newly versioned recovery image** using their established scripts. Avoid overwriting earlier packages.

## Stop wasting CI credits: required edit/preflight discipline

- CircleCI runs on **pushes to `main`**, costs free-plan credits, and has previously failed due mismatching patch context and a version-pinned `grep` assertion. Do not push untested patch guesses.
- CircleCI's preflight step clones `rel/xnu-8796`, runs shell scripts from `xnu/patches/*.sh`, and **sequentially** runs `git apply --check` then `git apply` for every `xnu/patches/*.patch` in lexical order. Any new patch must apply **after** all earlier patches. A hunk matching unpatched Apple source can fail after preceding modifications.
- Before pushing: reconstruct (or fetch) the source as modified by prior relevant patches, dry-run the new patch with `git apply --check`, apply it locally, run `git diff --check` or equivalent whitespace check, inspect affected declarations/macros, and if possible compile/syntax-check the changed C code. Do not assume patch syntax correctness from visual inspection. Validate hunk line counts.
- Check the **entire** `.circleci/config.yml` for version-specific assertions: past problem was a `grep` requiring `stage > 120` even after expanding the stage cap. That grep was fixed in a later commit to accept changing limits. Current CI still checks stage 121 and 128 in `sched_prim.c` and `marker_stage = stage - 121;` in `sweet_early.c`. If intentionally changing those, update checks in the **same atomic code commit**.
- The XNU compilation succeeds using CircleCI macOS with its pinned dependency/toolchain. A successful local patch check alone is **not** proof of a successful ARM64 compile; check CircleCI status and uploaded `kernel.development.j3y17lte` + archive.
- A GitHub documentation-only commit should use **`[ci skip]`** in the commit message to avoid unnecessary builds. CircleCI officially documents this feature: <https://circleci.com/docs/guides/orchestrate/skip-build/>. Do not tag a genuine code-change commit `[ci skip]` when the user actually needs a compiled artifact.
- Do not make repeated commits to `main` one file at a time when one atomic commit could handle the patch plus config change.
- Use GitHub connector tools if configured; do not use expensive CI to validate whether a patch applies.
- Never force-push or rewrite the user's history to resolve an incidental issue.

## User-side artifact, packaging and Odin workflow

At handoff, the user downloaded J3XNU024's `j3y17lte-xnu-kernel.tgz` from CircleCI. Their Windows browser named it **`j3y17lte-xnu-kernel (1).tgz`**. A full Bash packaging command was provided in the previous conversation using:

```bash
cd ~/ios-j330fn
ARCHIVE="/mnt/c/Users/BalJai/Downloads/j3y17lte-xnu-kernel (1).tgz"
ART="$HOME/ios-j330fn/xnu-j3/artifacts/j3xnu024-circleci"
```

It then:

1. Checks archive exists; refuses to reuse an existing versioned artifact directory; extracts the archive into `$ART`.
2. Runs `sha256sum -c SHA256SUMS`, validates `file` reports **Mach-O 64-bit arm64**, and `strings` contains `J3XNU024 Mach IPC callback entered` and `J3XNU024 Mach IPC initializer returned`. This protects against inadvertently using a prior archive.
3. Runs `python3 tools/j3y17lte/mkpayload_j3.py "$K24" tools/j3y17lte/j3y17lte-entry.adt tools/j3y17lte/j3xnu024.payload --cmdline 'debug=0xc cpus=1 keepsyms=1'`.
4. Runs `python3 tools/repack-j3-xnu-recovery.py research/j3-recovery-work/recovery-apple.img loader/j3y17lte/outxnu/Image tools/j3y17lte/j3xnu024.payload recovery-j3xnu024.img`.
5. Validates the final 16 bytes are exactly `SEANDROIDENFORCE`.
6. Copies the generated recovery to `out/j3xnu024/recovery.img`; creates an Odin tar with the member **`recovery.img`**; validates `tar -tf` and SHA256; copies to Windows Downloads as **`recovery-j3xnu024-odin.tar`**.

**Packaging success has not yet been confirmed by the user**. A pipeline-success icon is not a flash-success icon. These are experimental recovery-partition images, and Odin flashing risks a device boot loop, lost recovery, or worse. Confirm the exact handset variant and bootloader state, keep original recovery and a recovery route, and avoid flashing any primary bootloader/partition outside the tested scope. Do not ask the user to flash if validation failed. There is no complete iOS 16 userland boot yet.

Previous J3XNU022 packaging was successful with Mach-O SHA256 `ebeb0062732244c1cb5d82621c0f5f26d6c7184d8a87ff914fa9ba2c3de99b45`; do **not** reuse it. Previous J3XNU021 SHA256 was `2fd00177578a4d06f86fcd995403d8eab2adbb4a5c2e7d41ab4a17af0ba211e3`. Neither is the new J3XNU024.

## What not to do

- Do **not** equate colourful squares under a Samsung splash with an iOS boot or functioning display driver. The framebuffer markers are a temporary early diagnostic.
- Do **not** start another CircleCI build before the new phone screenshot provides a decision point.
- Do **not** assume the A5 project boot success transfers directly to J3; Exynos 7570, platform memory map, interrupts, framebuffer, storage, touch, CPU initialization and userspace integration differ.
- Do **not** silently overwrite older firmware artifacts or user modifications.
- Do **not** claim zero risk, guarantee next-step success, or guess the current screen from the previous photo.

## Immediate handoff sentence

**We have a green J3XNU024 kernel on CircleCI (#10), with its Odin recovery package being prepared locally. Await Düd's morning J3XNU024 phone photo, decode stages 141–200 in the correct top-to-bottom row order (returns / logging / entry), identify the first failing Mach IPC callback or preceding stage, then make one carefully preflighted, targeted patch—not another speculative CI build.**
