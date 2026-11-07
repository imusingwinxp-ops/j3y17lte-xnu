# J3Y17LTE XNU port — handoff for the next ChatGPT coding agent

**Read this entire file before changing anything.** This is a status handoff for the user's active Samsung Galaxy J3 (2017) / Exynos 7570 XNU bring-up. It is not proof that iOS boots. The user calls the phone "J3", refers to the project as "J3XNU", and prefers short, accurate, test-backed steps. The user has repeatedly incurred unnecessary CircleCI credits from failed patch preflights and is particularly concerned about avoiding another failed CI run.

**As of 2026-11-07:** J3XNU025 **successfully compiled in CircleCI pipeline #11**, packaged as a versioned Odin recovery tar (see checksums below), and physically tested. Its photo **proves `_mig_init` finishes and all first 20 Mach IPC callbacks return**. J3XNU026 is **now built successfully in CircleCI pipeline #12**, commit `c52a3551f4ba491bf377e76def9f987bc0a52ea0`; it extends completion tracing to callbacks 20–42 and the startup-phase exit. **J3XNU026 has NOT yet been downloaded, packaged, or physically tested.** The J3XNU025 photo also shows the stage-80 panic marker (likely a later panic) but does **not** show iOS userspace.

## Canonical places and versions

- GitHub repo: <https://github.com/imusingwinxp-ops/j3y17lte-xnu> (branch `main`).
- Last verified **code** commit: `c52a3551f4ba491bf377e76def9f987bc0a52ea0` ("J3XNU026: trace remaining Mach IPC callbacks and phase exit; update AGENT.md").
- Passing CI pipeline for that code: <https://circleci.com/gh/imusingwinxp-ops/j3y17lte-xnu/12> (green / success). Artifact in its **Artifacts** tab: `j3y17lte-xnu-kernel.tgz`, containing `kernel.development.j3y17lte` and `SHA256SUMS`. **Browser-assigned J3XNU026 archive name still unknown.** Prior J3XNU025 was called `j3y17lte-xnu-kernel (2).tgz`.
- Latest committed patch: `xnu/patches/0132-j3y17lte-trace-rest-mach-ipc.patch`.
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
5. J3XNU024 patch `0130` adds three marker rows around **each** MACH_IPC startup callback (up to 20 callbacks). It compiles, has a green pipeline #10, and its real-device photo was supplied on 2026-11-07. **Indices 0 through 14 all entered, logged and returned. Index 15 entered and logged but did not return.** Pixel samples of the photo confirm that row 181–200 at screen photo y≈1318 has 15 occupied columns; row 161–180 at photo y≈1338 has 16; row 141–160 at photo y≈1358 has 16. Thus stages **156 and 176 are present, 196 is missing**. Do not confuse this with callback 15 when using one-based numbering: it is the **16th**.
6. The user attached **J3XNU024 Mach-O archive**. Verified SHA256 `808ba33e1f3655f9772eb6b1fe69395f06226ea4719bb0d76711ab0e71304f23`. Parsed `__BOOTDATA,__init_entry_set` and used the original Apple XNU `qsort` implementation in a local reference shared library to reconstruct the exact sorted startup table: 4069 entries, **43** MACH_IPC entries; callback **index15 is `_mig_init`**. The Apple file is `osfmk/kern/ipc_kobject.c`.
7. J3XNU025 patch `0131` adds per-MIG-subsystem and milestone markers and suppresses two J3-only informational MIG `printf` statements. CI #11 green, packaging hashes below. On the physical photo (2026-11-07 11:23), **201–207 are lit, MIG subsystem 0–18 all entered and completed** (19 subsystems; stage256 is almost black **by design**, not necessarily missing), and **all 20 callbacks 0–19 returned**, including stage200. This was confirmed by sampling the rightmost marker rectangle at image coordinates x≈1125, y≈1039–1052, where stage200's teal appears. **Do not misread a horizontally level sample across the photo**: photographed rows slope a few pixels between left and right. Stage80's orange/pink panic marker appears lit. There is no stage109 evidence yet, suggesting a later MACH_IPC callback or final phase logging still stalls. The supplied MP4 is ~19.7s and shows markers static after early moments.
8. J3XNU026 (committed patch `0132`) adds **two rows only** for completed callbacks 20–39 (stages261–280, framebuffer y560) and callbacks40–42 (stages281–283, y548). Stages284–287 mark the end of callback loop, final `kernel_startup_log(upto)`, final verbose `kprintf`, and function return. `sweet_early_mark` stage cap increases to 300. Patch was locally applied on an XNU preflight tree already including 0131, regenerated via `git diff --no-index`, and validated by `git apply --check --verbose --whitespace=error` on the pristine preflight copy. **CI pipeline #12 passed** with code commit `c52a3551f4ba491bf377e76def9f987bc0a52ea0` (one attempt only). Next: download and verify archive, package J3XNU026 recovery, and request a new phone photo.

Past J3XNU023 and J3XNU024 photos are in the prior ChatGPT conversation and may need to be reattached. Do not pretend you can see them in the GitHub repository.

**Startup mapping is now decoded, not guessed:** Apple XNU 8796's `IPC_KOBJECT_DEFINE` macro expands to multiple `STARTUP_ARG(MACH_IPC, STARTUP_RANK_FIRST, ipc_kobject_register_startup, &ipc_kobject_ops_...)` registrations. On J3XNU024, callback index15 `_mig_init`, indices16–28 are `_ipc_kobject_register_startup` with different arguments; index19 specifically registers `_ipc_kobject_ops_IKOT_TASK_NAME` (first `iko_op_type` dword20); index29 `_waitq_bootstrap`; indices33 `_bank_init`,34 `_ipc_pthread_priority_init`; index41 `_ipc_importance_init`; index42 `_ipc_init`. The local scratch decoder `j3xnu024_binary/analyze_mach_ipc.py` reproduces the exact per-index table using qsort, though scratch files may expire. For definitive J3XNU026 mapping, verify the new Mach-O's startup table rather than assuming linker order remains identical across code builds.

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
| 201–220 | 596 | **J3XNU025 `_mig_init` milestone**, 201–207 currently assigned |
| 221–240 | 584 | **J3XNU025 MIG subsystem entered**, zero-based index 0–19 |
| 241–260 | 572 | **J3XNU025 MIG subsystem finished**, zero-based index 0–19 |
| 261–280 | 560 | **J3XNU026 MACH_IPC callback returned**, zero-based index 20–39 |
| 281–300 | 548 | **J3XNU026 callback indices 40–42 returned** in columns 0–2; stage284 loop finished, 285 final log returned, 286 final verbose log passed, 287 startup initializer returning |

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

1. J3XNU025 is **complete and physically tested**. Its photo demonstrates all MIG init steps and all 20 tracked MACH_IPC callbacks return. **Do not generate a second J3XNU025 build.**
2. J3XNU026 patch `0132` is **already committed and CircleCI-green on pipeline #12**; **do not rebuild**. Ask user to download `j3y17lte-xnu-kernel.tgz`, report browser-assigned filename, and use WSL to verify archive `SHA256SUMS`, Mach-O arm64, embedded unique `J3XNU026` strings. Package via existing scripts to uniquely versioned `tools/j3y17lte/j3xnu026.payload`, `recovery-j3xnu026.img`, and `out/j3xnu026/recovery-j3xnu026-odin.tar`, copying to Windows Downloads. Preserve J3XNU025 files. Confirm secure recovery-flash route before testing.
3. On J3XNU026 photo, count stages 261–280 and 281–283 to find the last returned callback. Stage284–287 indicate whether loop and final logging completed. **Take camera tilt into account** when counting right-hand columns; some marker colours are nearly black by design. Decode the J3XNU026 Mach-O for accurate function/arg mapping before designing another patch. **Every new code change must include AGENT.md in the same atomic commit.**

## Stop wasting CI credits: required edit/preflight discipline

- CircleCI runs on **pushes to `main`**, costs free-plan credits, and has previously failed due mismatching patch context and a version-pinned `grep` assertion. Do not push untested patch guesses.
- CircleCI's preflight step clones `rel/xnu-8796`, runs shell scripts from `xnu/patches/*.sh`, and **sequentially** runs `git apply --check` then `git apply` for every `xnu/patches/*.patch` in lexical order. Any new patch must apply **after** all earlier patches. A hunk matching unpatched Apple source can fail after preceding modifications.
- Before pushing: reconstruct (or fetch) the source as modified by prior relevant patches, dry-run the new patch with `git apply --check`, apply it locally, run `git diff --check` or equivalent whitespace check, inspect affected declarations/macros, and if possible compile/syntax-check the changed C code. Do not assume patch syntax correctness from visual inspection. Validate hunk line counts.
- Check the **entire** `.circleci/config.yml` for version-specific assertions: past problem was a `grep` requiring `stage > 120` even after expanding the stage cap. That grep was fixed in a later commit to accept changing limits. Current CI still checks stage 121 and 128 in `sched_prim.c` and `marker_stage = stage - 121;` in `sweet_early.c`. If intentionally changing those, update checks in the **same atomic code commit**.
- The XNU compilation succeeds using CircleCI macOS with its pinned dependency/toolchain. A successful local patch check alone is **not** proof of a successful ARM64 compile; check CircleCI status and uploaded `kernel.development.j3y17lte` + archive.
- A GitHub documentation-only commit should use **`[ci skip]`** in the commit message to avoid unnecessary builds. CircleCI officially documents this feature: <https://circleci.com/docs/guides/orchestrate/skip-build/>. Do not tag a genuine code-change commit `[ci skip]` when the user actually needs a compiled artifact.
- Do not make repeated commits to `main` one file at a time when one atomic commit could handle the patch plus config change **and the user's newly requested AGENT.md update**. **Every code change must have an up-to-date AGENT.md in the same commit**.
- Use GitHub connector tools if configured; do not use expensive CI to validate whether a patch applies.
- Never force-push or rewrite the user's history to resolve an incidental issue.

## User-side artifact, packaging and Odin workflow

### J3XNU025 packaging completed (user terminal log, 7 November 2026)

CircleCI pipeline **#11 succeeded** for J3XNU025 commit `7ee1e8b1361006359b71233924cd4dceb96253fd`. The user downloaded the artifact as `C:\Users\BalJai\Downloads\j3y17lte-xnu-kernel (2).tgz` and successfully performed all validation/packaging steps on Kali WSL:

- Archive `SHA256SUMS`: **OK**. Mach-O: **64-bit arm64 executable**. Embedded `J3XNU025 mig_init entered`, `J3XNU025 mig_init returning`, `J3XNU025 MIG subsystem populated`: all found.
- J3XNU025 raw Mach-O SHA256: `e933fb18ba2c22d9ad9ba7529377a9ea7a70a8965002aa229831a1bcdda9e87b`.
- Repacked recovery image SHA256: `baae21dd80dd3942ff5e811593fe9af0e9f55950822a1fe552fe1e59dc424f1e`.
- Odin tar SHA256: `a70dab8a88512db7de23cab4d4e27b7a055a1a6e0c15eb82ec8d44a0b3d2e353`.
- Odin package path: `C:\Users\BalJai\Downloads\recovery-j3xnu025-odin.tar`. Tar contains precisely `recovery.img`; repacked image maintains `SEANDROIDENFORCE` trailer. Packaging script printed `SUCCESS: J3XNU025 Odin package ready!`.
- **Device boot/photo NOT YET PROVIDED for J3XNU025.** Next: carefully flash the verified package to the **recovery** partition only using the already tested Odin recovery procedure, if user confirms device identity, backup, and recovery path; request a clear phone photo. Interpret rows y596 (201–220), y584 (221–240), y572 (241–260) and original callback row y608 (181–200) to determine whether `_mig_init` returns. Do not infer the kernel has advanced just from successful packaging.

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

**The packaging terminal output was not separately provided, although the subsequent actual-device J3XNU024 photo shows the firmware did run.** These are experimental recovery-partition images, and Odin flashing risks a device boot loop, lost recovery, or worse. Confirm the exact handset variant and bootloader state, keep original recovery and a recovery route, and avoid flashing any primary bootloader/partition outside the tested scope. Do not ask the user to flash if validation failed. There is no complete iOS 16 userland boot yet.

Previous J3XNU022 packaging was successful with Mach-O SHA256 `ebeb0062732244c1cb5d82621c0f5f26d6c7184d8a87ff914fa9ba2c3de99b45`; do **not** reuse it. Previous J3XNU021 SHA256 was `2fd00177578a4d06f86fcd995403d8eab2adbb4a5c2e7d41ab4a17af0ba211e3`. Neither is the new J3XNU024.

## What not to do

- Do **not** equate colourful squares under a Samsung splash with an iOS boot or functioning display driver. The framebuffer markers are a temporary early diagnostic.
- Do **not** start another CircleCI build before the new phone screenshot provides a decision point.
- Do **not** assume the A5 project boot success transfers directly to J3; Exynos 7570, platform memory map, interrupts, framebuffer, storage, touch, CPU initialization and userspace integration differ.
- Do **not** silently overwrite older firmware artifacts or user modifications.
- Do **not** claim zero risk, guarantee next-step success, or guess the current screen from the previous photo.

## Immediate handoff sentence

**J3XNU025 CircleCI #11 GREEN, SHA-verified and physically tested. It passes `_mig_init` and all first 20 MACH_IPC callbacks, with a stage80 panic marker lit and stage109 apparently absent. J3XNU026 patch `0132` extends callback return marks to indices20–42 and final loop/logging exit; its code commit `c52a3551...` and CircleCI #12 are GREEN. Await user download, J3XNU026 SHA-verified Odin packaging, and next actual-device photo. Every future code-change commit MUST simultaneously update AGENT.md.**
