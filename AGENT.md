# J3Y17LTE XNU port — handoff for the next ChatGPT coding agent

**Read this entire file before changing anything.** This is a status handoff for the user's active Samsung Galaxy J3 (2017) / Exynos 7570 XNU bring-up. It is not proof that iOS boots. The user calls the phone "J3", refers to the project as "J3XNU", and prefers short, accurate, test-backed steps. The user has repeatedly incurred unnecessary CircleCI credits from failed patch preflights and is particularly concerned about avoiding another failed CI run.

**As of 2026-11-08:** the physical SM-J330FN now boots XNU from RECOVERY, mounts the verified iOS 16.7.16 HFSX USERDATA root, executes real PID 1, passes the iOS 16 KiB dyld shared-cache registration blocker, and reaches launchd's boot-task phase. J3XNU043 physically printed `Darwin Bootstrapper Version 7.0.0`, spawned `fsck`, and then hit the expected next blocker when `mount_hfs` tried to reopen/remount `/dev/emmcroot0` writable while the J3 eMMC driver was still read-only. J3XNU044 is the current physically tested code candidate: a tightly gated USERDATA-only CMD24 write path adapted from the device-proven A5XELTE patch0108. Its first supplied phone photo (2026-11-08, 22:01 UK) shows sustained launchd service-spawn authorization messages for xpcproxy, bluetoothd and mobileactivationd, plus HFS hardlink-bit messages. No kernel panic or successful iOS UI frame is visible in that photo. It is evidence of progression beyond the previous mount failure, not proof that every service survived or that a sector write was verified. SpringBoard has still not been observed and no real iOS UI frame has been rendered.

## J3XNU045 display bridge — 2026-11-08 (latest source handoff; BUILD/DEVICE TEST PENDING)

- Current purpose: move beyond J3XNU044's repeated `xpcproxy` / `bluetoothd` / `mobileactivationd` launchd service authorizations by making the real DECON scanout discoverable through the already-existing software IOSurface / IOMobileFramebuffer class. Repeated spawn authorizations alone do not prove that a service crashed or that graphics was rendered. This patch is **not** a fix for a proven service exit reason.
- New code patch: `xnu/patches/0149-j3y17lte-decon-iosurface-bridge.patch`. It adapts donor A5XELTE patch0109 **to J3** and does not copy the donor's 1080x1920 dimensions or its ADT compatible string.
- Exact J3 display geometry proven by J3XNU037's physical framebuffer console (`0141`): physical `0x67000000`, **720x1280 XRGB8888**, stride **2880** bytes; estimated panel density ~294 ppi. No Apple GPU acceleration is claimed; this is a software framebuffer bridge.
- `iokit/KernelConfigTables.cpp`: enables only `AppleCLCD` for J3, with `IONameMatch='samsung,j3y17lte-display'`; the SWEET-only HID/touch/battery service entries stay excluded from J3.
- `iokit/Kernel/arm/SweetFramebuffer.cpp`: widens only the existing SWEET implementation compile guard to J3, supplies the J3 DECON physical address/geometry when `boot_args.Video` is empty, presents **native 720x1280** instead of the donor's 1125x2436 logical canvas, and offers opt-in `j3fb_noconsole=1` muting at the first actual GUI swap.
- `osfmk/console/serial_console.c`: defines the console-mute bridge on J3, prevents the J3XNU037 text mirror from drawing over a presented frame only when muted, and preserves panic diagnostics. Unlike SWEET, J3 does **not** yet have persistent console logging; do not claim otherwise.
- **Required WSL ADT change BEFORE any physical J3XNU045 test:** user's source is `~/ios-j330fn/tools/j3y17lte/mkadt_j3y17lte.py`, NOT tracked in this CI repo. It calls `mkadt.build(..., qemu=True, donor_product=False)`, sets `arm_io.children=[]`, then appends exactly one GIC. Append another child `mkadt.node("disp0", [("device_type", mkadt.cstr("display-subsystem")), ("compatible", mkadt.cstr("samsung,j3y17lte-display")), ("canvas-width", mkadt.u32(720)), ("canvas-height", mkadt.u32(1280))])` after the GIC; also set `chosen.display-scale` to `mkadt.u32(2)`. Re-run the generator to replace `tools/j3y17lte/j3y17lte-entry.adt`; verify the parsed tree contains one matching `/arm-io/disp0`. The previous physical artifact's ADT had `arm-io` but **no `disp0`**. A donor-schema serialization/parse test of the proposed J3 node and scale was run locally and passed; the user's actual WSL generator has not yet been modified by this agent.
- **Local full-chain preflight performed:** cloned pinned Apple `rel/xnu-8796` SHA `1b191cb58250d0705d8a51287127505aa4bc0789`; staged pinned libpthread, BearSSL and HFS (the Linux preflight substituted a local `TargetConditionals.h` placeholder only for SDK copy); applied all **145** pre-existing kernel patches through `0148` successfully in lexical order. The new 0149 diff was generated from actual before/after text across exactly 3 files; reversed cleanly to byte-for-byte identical pre-0149 files, then passed `git apply --check --whitespace=error`, actual reapply, reverse-check and targeted `git diff --check`. Existing donor whitespace warnings during old patches were unrelated.
- **J3XNU045 artifact/package VERIFIED on 2026-11-08:** user downloaded the successful CircleCI artifact as `j3y17lte-xnu-kernel (22).tgz`. `SHA256SUMS` passed and `file` reports Mach-O 64-bit arm64. Embedded checks found `samsung,j3y17lte-display`, `j3fb_noconsole`, the AMFI bridge string, and the writable J3 eMMC ready string. Old Cortex-A53-incompatible LDADD byte pattern `28 01 28 f8` count remains **0**.
  - kernel SHA256: **`1e58529845ad652d2209818a9abc27d00fd1d789215604b52bc4ff6f6e74a32c`**
  - rebuilt ADT: **3740 bytes**, parsed/verified with `display-scale=2`, `/arm-io/disp0`, compatible `samsung,j3y17lte-display`, canvas **720x1280**
  - payload Mach-O size: **16527024 bytes**; entry `0xfffffff007413488`
  - repacked recovery: **16906256 bytes**, Samsung `SEANDROIDENFORCE` trailer preserved
  - recovery image SHA256: **`effd959d2241027cbfac37bd5cfe3698d49b73a80f466f75a91c79c1a23de52f`**
  - Odin TAR SHA256: **`2e671b134bfed07921bbbea5eaedfa4151277e98dfec2945d6227a49f654b12a`**
  - Windows package: **`C:\\Users\\BalJai\\Downloads\\recovery-j3xnu045-odin.tar`**
  - TAR contains exactly `recovery.img`.
- **J3XNU045 physical test VERIFIED, 2026-11-08 ~22:32–22:33 UK:** the supplied photo sequence shows the new display bridge running on the real J3:
  - `SWEET SURF: IOCoreSurfaceRoot registered`.
  - `SWEET FB: AppleCLCD 720x1280 stride 2880 at 0x67000000` with default surface 1 created/published. This proves AppleCLCD/IOSurface registration and the exact J3 scanout geometry; the default surface is not itself proof of a SpringBoard-rendered frame.
  - launchd progresses through many boot tasks and prints **`Early boot complete. Continuing system boot.`**
  - launchd authorizes a real **SpringBoard** spawn: `Allowing spawn of iOS binary SpringBoard ...`.
  - many later services are also attempted, including xpcproxy, bluetoothd, identityservicesd, imagent, ReportCrash, fseventsd, DumpPanic, nfcd, mobiletimerd, AppleCredentialManagerDaemon, timed, thermalmonitord, tccd, nehelper and MobileGestaltHelper.
  - framebuffer userspace interaction is now device-proven: `SWEET FB: MobileGestaltHelper sel 8 ... -> 0x0` and `sel 28 ... -> 0x0`. In the existing SweetFramebuffer ABI, selector 8 is GetDisplaySize and selector 28 is GetDotPitch. So iOS userspace successfully opens the IOMobileFramebuffer client and queries J3 display properties.
  - the same sequence also contains non-fatal/secondary messages including BindFS lookup failures, unsupported Data Protection on `/private/var/`, and a `GetMasterBlock: Error 16 opening /dev/emmcroot0` during one mount task; launchd continues beyond all of these into full system boot.
  - **No submitted J3XNU045 capture contains the existing `SWEET FB: swap ...` log from `AppleCLCD::swap()`, and no real iOS UI frame is visible.** Do not treat the default surface, SpringBoard spawn authorization, or Samsung splash as a successful GUI frame.
- **Current J3XNU045 status:** kernel, ADT and package are verified; physical display-service registration, system-boot completion and SpringBoard spawn authorization are verified. Actual SpringBoard/backboardd survival and a GUI swap remain unproven.
- **Best zero-CI next diagnostic:** repackage the same J3XNU045 kernel with only `j3fb_noconsole=1`. The console-mute flag is checked on the first actual framebuffer SwapEnd path, so if the console never mutes then no swap reached AppleCLCD; if it mutes, the swap path ran and the resulting visible frame/black/garbled output becomes the next evidence. Panics retain the existing J3 diagnostics. Do not build J3XNU046 merely for this test.
- **J3XNU045 no-console repack VERIFIED:** same kernel and ADT, boot args additionally include only `j3fb_noconsole=1`.
## J3XNU049 — Exynos7570 4-core SMP performance bring-up

- **Goal:** remove the dominant J3XNU048 performance wall by bringing all four Cortex-A53 cores online while preserving the proven iOS GUI/touch path.
- **Patch:** `0153-j3y17lte-smp4.patch`.
- **Samsung hardware source confirms:** Exynos7570 exposes four Cortex-A53 CPUs with MPIDRs 0,1,2,3 and `enable-method = "psci"`; PSCI uses SMC and CPU_ON function ID `0xC4000003`. This matches the donor XNU PSCI secondary-entry mechanism already compiled into the J3 kernel.
- **Board limit:** `SWEET_SMP_MAX_CPUS` raised from 1 to 4; existing board `MAX_CPUS` was already 4.
- **Topology:** J3 uses MPIDR Aff0 for core IDs, unlike SWEET's Aff1 layout. J3 now derives `cluster_core_id` from `phys_id & 0xff`.
- **GICv2 SMP:** replaces self-only SGI with targetable GICD_SGIR delivery for CPU0-3 and adds per-CPU initialization of banked SGI/PPI group/priority/enable registers plus GICC PMR/BPR/CTLR before each core's self-IPI validation.
- **Secondary entry:** J3 skips donor `ICC_SRE_EL2` accesses in the EL2 fallback because Exynos7570 is GICv2; the rest of the PSCI secondary reset path is retained.
- **SweetCPU:** J3 topology now accepts coherent CPU0-3, calls per-CPU GIC init from `initCPU`, and routes scheduler IPIs to arbitrary selected J3 CPUs.
- **Display/GPU:** no Mali driver is attempted in this build. Current AppleCLCD presentation remains CPU-copy based and defaults to `sweetfb_hz=10`; after SMP proof, test `sweetfb_hz=20` then 30 via boot args with no additional kernel build.
- **ADT requirement:** current J3 payload ADT is local-only and presently describes CPU0. After a successful kernel artifact, add CPU1-3 locally with logical IDs/regs 1,2,3 and package with `cpus=4`; this costs no CircleCI build.
- **Preflight:** all 9 patch hunks have validated old/new line counts. Reconstructed SweetCPU/header/topology contexts were checked while preparing the patch; no branch update occurred until the final diff metadata passed.
- **CircleCI #48:** SUCCESS.
- **Verified J3XNU049 artifact:**
  - kernel SHA256: `4ed5a52709bdd375dd2479cf69ba70b0e1a8b6ffc7234ca30c46c233bb183881`
  - kernel size: 16547136
  - entry: `0xfffffff007414488`
  - old Cortex-A53-incompatible LDADD byte-pattern count: 0
  - SMP strings present for requested/selected CPUs, PSCI CPU_ON, per-CPU alive+SGI, and all-CPU initialized.
- **Local SMP4 ADT:** CPU0 cloned to CPU1-3 with regs/MPIDRs 0,1,2,3.
  - original ADT bytes: 3740
  - SMP4 ADT bytes: 6128
  - SMP4 ADT SHA256: `3b83ba35b939368c73604de1dcd762048ce423ab861e6f7053e3e5efb1eeb7be`
- **SMP4 + 20Hz quiet package:**
  - boot args include `cpus=4 sweetfb_hz=20` plus the proven quiet J3 args.
  - recovery SHA256: `976f7a44e863ef34c5f63923203f07469ec03b64d889f835b742e5c2f0078f68`
  - Odin TAR SHA256: `3286fc76fb5c55599315615da26dce82c5b52ffb5209b01139b96097ce32b22c`
  - Windows package: `C:\\Users\\BalJai\\Downloads\\recovery-j3xnu049-smp4-fast-odin.tar`
  - Samsung `SEANDROIDENFORCE` trailer preserved.
- **First physical SMP4 test FAILED before GUI/console.**
  - Photo shows the early panic/assertion barcode over the stale Samsung splash; this is not iOS rendering.
  - Assertion barcode decoded from the supplied photo:
    - source prefix: `machine_routines`
    - source line barcode: `0x0000045e` = **1118**
    - expression prefix: `topology_info.bo`
  - Failure occurs in CPU topology parsing, before useful evidence of PSCI secondary CPU_ON/GIC bring-up.
  - Strong root-cause candidate: the local SMP4 ADT was produced by deep-cloning CPU0. XNU's `ml_is_boot_cpu()` treats a CPU node as the boot CPU iff its `state` property equals `running`. If CPU0's proven node has `state=running`, CPU1-3 inherited that state, causing multiple CPUs to be identified as boot CPUs and an assertion on `topology_info.boot_cpu == NULL`.
  - **Do not spend the final CircleCI build yet.** First make a zero-CI ADT-only repair: preserve CPU0 `state=running`, set CPU1-3 to a non-running state, reuse the verified J3XNU049 kernel, and test at the default 10 Hz display rate to isolate SMP.
- **Zero-CI ADT repair CONFIRMED the root cause:**
  - Before repair: CPU0/1/2/3 all had `state='running'`.
  - After repair: CPU0=`running`; CPU1/2/3=`halted`.
  - This confirms the original SMP4 ADT incorrectly marked every cloned CPU as the boot CPU, matching the topology assertion seen physically.
  - repaired SMP4 ADT SHA256: `cb751629f74719e825da8e4e3d39578e68137ca61db96f6ebbf9417393ba252b`
- **J3XNU049 2-core state-fixed control package:**
  - recovery SHA256: `7942fe0e5dec52b2e006d8ac3e490ac1b04b065a19fe4155e4ee10b42defcc2a`
  - Odin TAR SHA256: `99e94b82743f5e0d43faf5b408007bcd31b8b24de787052c1a5bda1f92ebb5ee`
  - Windows: `C:\\Users\\BalJai\\Downloads\\recovery-j3xnu049-smp2-statefix-odin.tar`
- **J3XNU049 4-core state-fixed package (hold until 2-core result):**
  - recovery SHA256: `37108c5ad05f188314f9b26152a8023f0d0276dc86e8321e29de5a270e13edcd`
  - Odin TAR SHA256: `e749e77c349371432651cf5f438654f58ce0f42144ec8c80a9263561e74d79d6`
  - Windows: `C:\\Users\\BalJai\\Downloads\\recovery-j3xnu049-smp4-statefix-odin.tar`
- **Status:** repaired ADT and both zero-CI packages verified. Next physical test is **2 cores first at 10 Hz**. Do not spend the final CircleCI build yet.




## J3XNU048 — physical touch + GPIO keys

- **Goal:** make the proven J3XNU047 iOS lock screen physically usable in one build: real Synaptics touch plus direct J3 hardware keys.
- **Patch:** `0152-j3y17lte-input.patch`.
- **HID services:** enables the existing `SweetHIDButtons` and `SweetHIDTouch` personalities on J3 while keeping `SweetBattery` excluded. `SweetHIDTouch` gets J3-native 720x1280 geometry, zero offset, ~62x110 mm surface size and a 24-pixel edge threshold; SWEET behavior remains under the non-J3 branch.
- **Direct keys from Samsung source:** Exynos7570 ALIVE GPIO base `0x139f0000`; Volume Up = GPA0.7, Home = GPA0.4, Volume Down = GPA2.3. They are polled read-only with debounce and feed `sweet_hid_key()`. The side power key is PMIC-interrupt-backed and is intentionally not guessed in this one-build attempt.
- **Touch from Samsung source:** Synaptics RMI4 TD4100 at address `0x4b`, 720x1280, on GPC3.0/1 under TOUCH GPIO base `0x139d0000`. The driver uses open-drain GPIO bit-banged I2C, tries both SDA/SCL conventions by ACK, scans the RMI4 PDT at runtime for F01/F12, configures the production type+XY+Wx/Wy report, caps to five contacts and polls at 50 Hz.
- **Failure isolation:** touch setup/read failure is non-fatal and retried; `j3touch=0`, `j3keys=0`, or `j3input=0` can disable pieces without another kernel build. No PMIC writes, touch firmware/NVM writes, eMMC/HFS changes, or display changes.
- **Full lexical audit:** all existing patches were scanned for `bsd/conf/files`, `iokit/bsddev/IOKitBSDInit.cpp`, `iokit/KernelConfigTables.cpp`, and `iokit/Kernel/arm/hid/SweetHID.cpp`. Relevant later overlaps were reconstructed: patch0142 J3 eMMC in files/IOKitBSDInit and patch0149 J3 AppleCLCD in KernelConfigTables; patches0150/0151 do not overlap.
- **Strict preflight:** the final patch blob was applied exactly (no fuzz) to reconstructed post-chain `IOKitBSDInit.cpp`, `KernelConfigTables.cpp`, and `SweetHID.cpp`; `bsd/conf/files` had already passed the same strict apply before unrelated hunk-header corrections. New driver header count matches all 647 added source lines and source trailing-whitespace count is zero.
- **Expected physical test:** package with the proven J3XNU047 boot args including `j3fb_noconsole=1`. Home/volume should emit native consumer-control HID events; TD4100 tap/swipe should emit digitizer events and make the lock screen interactive.
- **CI correction:** the first J3XNU048 attempt failed before compilation because the SweetHID hunk at patch line 70 declared +24 lines but contained +27. Header-only repair: +24→+27; downstream new-start coordinates 474→477 and 488→491. All patch hunk counts validate after repair; SweetHID strict-apply passes.
- **Build status:** corrected J3XNU048 commit `51f24e0c5404e9900d0cd307094d7c74a2a52569` passed CircleCI #47.
- **J3XNU048 quiet-performance physical result:** Apple logo appeared substantially sooner than the normal J3XNU048 package and, for the first time, visibly faded out (still laggy). A loading spinner then appeared, followed by a long powered-black interval; **the lock screen eventually did appear** without any further repack or reboot.
  - Therefore the post-spinner black interval was not a terminal stall. The quiet package reaches SpringBoard/lock screen successfully.
  - Removing `debug=0xc`, `keepsyms=1`, `-v`, and `-enable_kprintf_spam` materially improves boot/render timing on the single Cortex-A53.
  - Touch remains functional, but gestures are still extremely slow/unusable. The remaining dominant bottleneck is the single-core J3 topology plus the ~50 Hz GPIO bit-banged TD4100 polling path, not a boot failure.
  - Do **not** replace this package with the proposed `fastv` diagnostic unless new evidence requires it; the quiet package already proved stable to lock screen.
  - This proves removing `debug=0xc`, `keepsyms=1`, `-v`, and `-enable_kprintf_spam` materially improves boot/render timing on the single Cortex-A53.
  - The post-spinner black screen is not yet classified: it may be the known display-off path or a later userspace stall. Use a zero-CI diagnostic repack of the same J3XNU048 kernel with lightweight console visibility to distinguish them before spending any remaining build budget.
- **J3XNU048 quiet-performance repack (same kernel, no CI):**
  - removed boot args: `debug=0xc`, `keepsyms=1`, `-v`, `-enable_kprintf_spam`
  - retained: `cpus=1 -noprogress rd=emmcroot0 emmcroot=USERDATA launchdsuffix=release unentitled_ios_sim_launch=1 ignition_level=1 launchd_unsecure_cache=1 wdt_test=no_user_checkin wdt=-1 cs_enforcement_disable=1 emmcwrite=1 j3fb_noconsole=1`
  - recovery SHA256: **`133adbdc14a15cd60adf5d62917d7b9bf9244809d45d4b0f57dfc2d3a18a5f2e`**
  - Odin TAR SHA256: **`645779313d5ea4a694f294c09e5a194e58f21beb4414dd88a735074f0c1e4cea`**
  - Windows package: **`C:\\Users\\BalJai\\Downloads\\recovery-j3xnu048-fast-odin.tar`**
  - Status: **PACKAGED, NOT YET FLASHED** at time of this update.
- **J3XNU048 PHYSICAL RESULT — TOUCH WORKS, PERFORMANCE UNUSABLE, 2026-11-09 ~00:02 UK:** user-supplied video proves real TD4100 touch input is reaching iOS and causing correct UI transitions. The lock screen responds to gestures and transitions into other SpringBoard UI, so coordinate mapping/HID delivery are functionally working. However, response is multi-second/slideshow-like and practically unusable.
  - This is not primarily a touch-coordinate failure: gestures eventually produce the intended UI changes.
  - Current J3 topology remains intentionally single-core: patch0101 hard-requires `topology->num_cpus == 1` and disables donor secondary-CPU support on J3. Merely changing the `cpus=` boot arg cannot expose more cores in the current build.
  - J3XNU048 touch also polls the TD4100 at ~50 Hz using GPIO bit-banged I2C on that same single Cortex-A53, which adds measurable CPU overhead on top of iOS 16 userspace.
  - No further CI build budget remains in this session. Future performance work should prioritize real Exynos7570 SMP bring-up and/or hardware-I2C/IRQ-driven touch instead of framebuffer/UI work.
  - Hardware button functionality was not conclusively established by the supplied video; touch functionality was.
- **J3XNU048 artifact/package VERIFIED:**
  - kernel SHA256: **`1c920a362a49557177090dd6b54a1d5d39dbe84cd476129a6da6e23d0fe27065`**
  - payload Mach-O size: **16528320 bytes**, entry `0xfffffff007414488`
  - recovery size: **16908304 bytes**, Samsung `SEANDROIDENFORCE` trailer preserved
  - recovery SHA256: **`498d9eed276395c2a0ecb95d9a4c607651f9e2abcbe7b679a2b6aa9cb3db0c27`**
  - Odin TAR SHA256: **`14092e50595c8ff38509d25800832b9b753d0aa462cb29e65f5d04e112c51e69`**
  - Windows package: **`C:\\Users\\BalJai\\Downloads\\recovery-j3xnu048-touch-buttons-odin.tar`**
  - embedded J3 input strings verified: keys online/change logging, TD4100 ACK, TD4100 RMI ready/retry, SweetHID touch/buttons registration.
  - prior boot features verified: AMFI bridge, writable J3 eMMC root string, J3 AppleCLCD personality, `j3fb_noconsole`; old LDADD byte-pattern count remains **0**.
  - Status: **PACKAGED, NOT YET FLASHED** at time of this update.

## J3XNU047 — HFS atomic RENAME_SWAP compatibility (Apple-logo attempt)

- **Purpose:** use the final available build on the exact donor change that moved A5XELTE from the same post-SpringBoard/no-swap stage to its first photographed white Apple logo and recorded framebuffer swaps.
- **Patch:** `0151-j3y17lte-hfs-rename-swap.patch`.
- **Change:** widen the existing SWEET-only guard around the already-present HFS `VFS_RENAME_SWAP` fallback in `bsd/vfs/kpi_vfs.c` to include `ARM64_BOARD_CONFIG_J3Y17LTE`. The fallback itself is unchanged: only when `VNOP_RENAME` returns `ENOTSUP`, the request is exactly `VFS_RENAME_SWAP`, both vnodes are regular files, and both are on the same mount, use `VNOP_EXCHANGE(*fvpp, *tvpp, 0, ctx)`.
- **Why this build:** donor A5XELTE observed `usermanagerd` atomic persona/session writes failing with ENOTSUP, then enabled the same pre-existing SWEET fallback in patch0117. The next physical run produced the first white Apple logo; its recovered log later showed `exec SpringBoard`, `exec backboardd`, display-on and five BGRA swaps. This is precedent, not a guarantee that J3 will behave identically.
- **J3XNU046 evidence:** J3 reaches `Early boot complete`, `exec SpringBoard`, heavy xpcproxy/service churn, and bounded crash diagnostics. The supplied captures show a `driverkitd` SIGKILL, but no captured SpringBoard/backboardd crash reason and still no framebuffer SwapEnd.
- **Lexical audit / preflight:** among HFS/VFS-related project patches, only patch0052 touches `bsd/vfs/kpi_vfs.c`; patch0026/0041 do not. Later J3 root/HFS/write/display/crash patches 0143/0144/0145/0148/0149/0150 do not touch this file. Pinned Apple `rel/xnu-8796` `kpi_vfs.c` was reconstructed by applying patch0052; the proposed J3 guard replacement matched exactly once and preserved the existing ENOTSUP/VFS_RENAME_SWAP/VNOP_EXCHANGE safety conditions.
- **No other behavior changes:** no framebuffer geometry, eMMC bounds, AMFI, dyld, root image, or crash-diagnostic logic changes.
- **Expected best-case physical result:** first AppleCLCD SwapEnd(s) and a visible white Apple logo. Package the same kernel with `j3fb_noconsole=1` for the physical trial so console muting itself proves the first swap occurred.
- **Build status:** CircleCI #45 passed for commit `57a664e430bfd78f44f2868a56b9c969d01a5ee8`.
- **J3XNU047 PHYSICAL MILESTONE — FIRST WHITE APPLE LOGO, 2026-11-08 ~23:13 UK:** user-supplied photo sequence proves the first real post-console iOS framebuffer presentation on the J3.

- **J3XNU047 MAJOR MILESTONE — FULL GUI BOOT TO iOS LOCK SCREEN, 2026-11-08 ~23:19 UK:** after the white Apple logo and a temporary black/display-off interval, the device rendered a real iOS lock screen with date/time, home indicator, and a red top diagnostic banner (`rdar:45025638`). A subsequent frame shows the centered iOS loading spinner, then the lock screen returned. This proves SpringBoard/backboardd progressed beyond the boot logo into the lock-screen UI and that the framebuffer presentation path continues to update after first boot.
  - The earlier post-logo black screen was **not a kernel hang**; userspace remained alive and later rendered the lock screen.
  - Touch and hardware buttons do nothing in this build because J3XNU045 intentionally excludes the inherited `SweetHIDButtons` and `SweetHIDTouch` registrations under the `J3Y17LTE` board guard, and no J3 GPIO/touch controller bridge has been added yet.
  - Therefore the next major bring-up target is **J3 HID/input**, not display or boot. Reuse the donor A5XELTE patch0118 approach only as a template: J3 needs its own Exynos7570 GPIO-key addresses/pins and its own touchscreen controller/I2C/power sequencing; do not blindly reuse A5 physical addresses.
  - This milestone supersedes all earlier states that only proved Apple logo or framebuffer SwapEnd.

- **Immediate follow-up observation:** after remaining on the white Apple logo for a while, the J3 display transitions to black while the panel/device remains powered. Treat this as **likely display-off**, not a proven hang: donor A5XELTE patch0117 showed the same Apple-logo-to-black sequence, and its recovered log later contained `SWEET FB: display off` after real swaps. J3XNU047 currently has no J3 equivalent of the donor's later `a5fb_keep_on=1` override, so an iOS power-state request can still blank the framebuffer. Verify with the same J3XNU047 kernel repackaged without `j3fb_noconsole=1` before changing kernel code.
  - Before the transition the console shows continued iOS userland startup, including `exec backboardd`, `exec bluetoothd`, `exec identityservicesd`, `exec mobiletimerd`, `exec imagent`, `exec MobileGestaltHelper`, `exec ReportCrash`, `exec tccd`, and many other services.
  - The package was booted with `j3fb_noconsole=1`. The console subsequently disappears and the display becomes black with a centered **white Apple logo**. Because J3's console mute is only armed on the AppleCLCD SwapEnd path, this is device proof that a real framebuffer swap occurred.
  - This supersedes all earlier “no SwapEnd” states from J3XNU045/046.
  - The photo proves a rendered Apple-logo frame and working presentation path; it does **not** yet prove that SpringBoard reaches an interactive lock/home screen or that the system is not stalled after that frame.
  - No additional CI build is required to distinguish “stuck” from “slow”: repackage the same verified J3XNU047 kernel without `j3fb_noconsole=1` and observe post-logo console activity, or leave the Apple-logo build running and test later visible transition. Do not modify USERDATA/eMMC bounds for this diagnostic.
- **J3XNU047 artifact/package VERIFIED:**
  - kernel SHA256: **`b7cc84351d8c81d011aef05d638b3c10edffa21183ed0265957e385d51ceb68a`**
  - payload Mach-O size: **16527408 bytes**, entry `0xfffffff007414488`
  - recovery size: **16908304 bytes**, Samsung `SEANDROIDENFORCE` trailer preserved
  - recovery SHA256: **`0ca2bb10e49901c85b9d058397700e80c96bb9f8dac135c3001b8f62e871ed16`**
  - Odin TAR SHA256: **`bd3ccc22d5e760098b10b1a4e93bcf193299eafecbbf8e08b01d3a7c54ec3b21`**
  - Windows package: **`C:\\Users\\BalJai\\Downloads\\recovery-j3xnu047-applelogo-odin.tar`**
  - required features verified: crash diagnostics, short exec logging, AMFI bridge, J3 writable eMMC root string, J3 display match, `j3fb_noconsole`; old LDADD byte-pattern count **0**.
  - ADT verified at **720x1280**, display-scale **2**.
  - packaged with **`j3fb_noconsole=1`** so the first real AppleCLCD SwapEnd should mute the console.
  - Status: **PACKAGED, NOT YET FLASHED** at time of this update.

## J3XNU046 — bounded userland crash diagnostics

- **Purpose:** spend one build only to identify the concrete process failure preventing the first IOMobileFramebuffer SwapEnd. J3XNU045 already proves AppleCLCD registration, MobileGestalt framebuffer queries, SpringBoard spawn authorization and full-system launchd progress, but the no-console trial proves no observed SwapEnd.
- **Patch:** `0150-j3y17lte-crash-diagnostics.patch`.
- **Minimal adaptation of donor A5XELTE patch 0111:** enable the already-existing SWEET crash/exit diagnostics for J3Y17LTE; use the existing short `exec %s` line for permitted iOS execs; keep heap-string scanning bounded to the first four matching J3 crashes. No framebuffer geometry, eMMC, HFS, AMFI, dyld or USERDATA behavior changes.
- **Targeted lexical audit:** the inherited diagnostic implementation is introduced/touched by J3 patches 0042, 0043, 0044, 0051, 0053 and 0066. Every patch 0067 through 0149 was inspected for `bsd/kern/kern_exit.c`, `osfmk/kern/exception.c` and `bsd/kern/kern_exec.c`; none touches those files.
- **Preflight:** pinned Apple `rel/xnu-8796` versions of the three files were reconstructed by applying J3 patches 0042/0043/0044/0051/0053/0066 in order. The functional 0150 hunks then applied exactly to that reconstructed state. A stale cosmetic closing-comment hunk was intentionally removed after preflight rejected its shifted context; no guessed line-count fix was used.
- **Expected device evidence:** short `exec SpringBoard` / `exec backboardd` records plus, on a real terminating process, `CRASH <name>...`, exit-reason text, register/backtrace data, fault-region data for SIGSEGV/SIGBUS, and bounded heap strings for SIGABRT/SIGTRAP. Do not assume the A5 backboardd container-path crash unless J3 prints its own evidence.
- **Build status:** CircleCI #44 passed for commit `8082483ace7016cc13259d3d1592ab86e5db30b2`.
- **J3XNU046 artifact/package VERIFIED:**
  - kernel SHA256: **`5e891e8dd788e4238e4ff0fa1765ed64f830edda08348e41cc6106f42aac3d5e`**
  - payload Mach-O size: **16527408 bytes**, entry `0xfffffff007414488`
  - recovery size: **16908304 bytes**, Samsung `SEANDROIDENFORCE` trailer preserved
  - recovery SHA256: **`5870ac9511442fd40299f755bbcda2230b5112959ebcca3594911a113cd04ae1`**
  - Odin TAR SHA256: **`382cd5f0127f2b38ab173fdd1b602d422b000813d664a8849e8ba51977095cc8`**
  - Windows package: **`C:\\Users\\BalJai\\Downloads\\recovery-j3xnu046-crashdiag-odin.tar`**
  - embedded diagnostics verified: `CRASH %s[%d] sig`, `CRASH %s reason ns`, `STR scan of %s heap`, `exec %s`.
  - required prior features verified: AMFI bridge, writable J3 eMMC root string, `samsung,j3y17lte-display`, `j3fb_noconsole`; old LDADD byte-pattern count remains **0**.
  - Status: **PACKAGED, NOT YET FLASHED** at time of this update.

- **J3XNU045 no-console PHYSICAL RESULT (2026-11-08 ~22:40 UK):** console text continues to scroll after the display bridge and after `MobileGestaltHelper sel 8/28 -> 0x0`. Therefore `j3fb_noconsole=1` did **not** activate and the existing `AppleCLCD::swap()` / SwapEnd path is not device-proven on J3. The submitted frames contain no `SWEET FB: swap ...` line and no iOS-rendered GUI frame.
  - New visible activity includes containermanagerd selectors, mediaserverd selectors, `ansaccountsd`, `remoted`, `cloud`, repeated `xpcproxy`, many HFS hardlink updates, and a network-thread scheduling warning. None of those lines alone proves a fatal blocker.
  - This narrows the display problem: AppleCLCD registration and framebuffer property queries work, but the compositor has not reached a successful SwapEnd presentation in the observed boot.
  - Strong donor precedent: A5XELTE reached the same post-0109 state (AppleCLCD + SpringBoard/launchd activity but no swap), then enabled bounded process-exit/crash diagnostics in patch0111. That later exposed backboardd crashes; do **not** assume J3 has the same crash until J3 records its own exit reason.
  - Evidence-driven next kernel work should be a minimal J3 adaptation of donor0111 crash/exec diagnostics (guards only, bounded output), validated against the full cumulative patch chain before one CI build. Do not alter framebuffer geometry, USERDATA, or eMMC write bounds based on this no-console result.
  - recovery SHA256: **`5d01c897cba746897ed8f5ef2965e48378bda0b960273d62d702eed2e2d101cb`**
  - Odin TAR SHA256: **`15c23debd82ffc62350a2b0b611b26bd13a24da6bfdb2c560724fce82fd5c304`**
  - Windows package: **`C:\\Users\\BalJai\\Downloads\\recovery-j3xnu045-noconsole-odin.tar`**
  - recovery size: **16906256 bytes**, Samsung `SEANDROIDENFORCE` trailer preserved, TAR contains exactly `recovery.img`.
  - Status: **NOT YET FLASHED** at time of this update.
- **First boot:** retain proven J3XNU044 args including `rd=emmcroot0 emmcroot=USERDATA emmcwrite=1 cs_enforcement_disable=1 -noprogress`, keep `rootrw` absent, and retain verbose console (no `j3fb_noconsole=1` on first trial). If AppleCLCD is confirmed but text overwrites a UI frame, repackage the same kernel with `j3fb_noconsole=1` without another CI build.
- No USERDATA image rewrite, Android boot, BL/CP/CSC/PIT flash, partition resizing or broader eMMC write permission is required for this patch. SpringBoard and rendered UI remain unproven on J3.

## J3XNU044 active handoff — 2026-11-08 (supersedes all earlier active handoffs)

### Physical storage / iOS root state — VERIFIED

- Device: Samsung Galaxy J3 (2017) SM-J330FN / `j3y17lte`, Exynos7570, Cortex-A53.
- TWRP positively identified `USERDATA -> /dev/block/mmcblk0p25`.
- USERDATA geometry is independently identical in TWRP and XNU:
  - start LBA: **6713344**
  - sectors: **24051712**
  - bytes: **12314476544**
- J3 XNU eMMC host base is `0x13540000`; J3XNU038 proved real CMD17 reads and GPT parsing on hardware.
- Installed root is a reduced **genuine iPhone X iOS 16.7.16 (20H392)** HFSX image built from `iPhone10,3,iPhone10,6_16.7.16_20H392_Restore.ipsw`.
- Final root image:
  - path on user's WSL: `~/ios-j330fn/rootbuild/20H392/ios16-j3-reduced-20H392.img`
  - bytes: **11811160064** (11 GiB)
  - SHA256: **6e462e69ae145358d72cb19aa9f03346ad23c35c282d8c72dda3cfc2b4243e0c**
  - leaves **480 MiB** unused at the end of USERDATA.
- The image was written from TWRP with root ADB and then the **entire 11 GiB region was read back and SHA256-hashed on-device**. Device hash exactly matched the host hash above. Treat the installed USERDATA root as byte-for-byte verified.
- Critical files were verified before install: `/sbin/launchd`, SpringBoard, dyld shared cache, SystemOS cryptex cache and AppOS cryptex.
- The root was fsck-repaired/verified clean before install. Donor first-boot tweaks were applied. No mobileactivationd data ark existed in this reduced image; this may matter later, but is not the current blocker.
- **Do not boot Android.** Android/TWRP may regard the HFSX USERDATA as foreign. TWRP may be flashed to the separate RECOVERY partition, but do not mount/format/repair/resize `/data`/USERDATA.

### J3XNU038 → J3XNU041 physical progression

- **J3XNU038** (`0142-j3y17lte-readonly-emmc-root.patch`) added a deliberately read-only direct BSD eMMC root device. Hardware printed:
  - `J3Y17LTE eMMC: GPT USERDATA first=6713344 sectors=24051712 read-only`
  - then the old Apple_HFS wait remained because no `rd=emmcroot0` was yet used.
  - kernel SHA256: `33aeb440379f222dcef9a4489c717f34781e16e67ccd79f5705e5e2f67cdec76`.
- **J3XNU039** added `0143-j3y17lte-unsealed-hfs-root.patch` (commit `e7d861fb500aead5b2dbc8758929dceb66ac2311`). First real `rd=emmcroot0 emmcroot=USERDATA` boot selected USERDATA, then panicked in `IOService::setRootMedia()` because J3's direct BSD device has no `IOBlockStorageDriver` / `IOMedia` provider chain.
  - J3XNU039 kernel SHA256: `459997e6a4800e537f6c6bd35eeb206765bb74095700d6d8f51fe1e3a4442d62`.
- **J3XNU040** added `0144-j3y17lte-direct-bsd-root-media.patch`, reusing the donor's existing direct-root handling for J3. Physical result: the IOService assertion was passed. HFS then repeatedly failed during late journal init because the journal code tried to write its header and the intentionally read-only eMMC strategy returned `EROFS` (`0x1e`).
- **J3XNU041** added `0145-j3y17lte-readonly-hfs-journal.patch`, skipping write-requiring late journal initialization only for a J3 read-only root, allowing Apple's existing read-only journaled-volume path to run.
- **J3XNU041 physical proof:** the phone displayed:
  - `J3Y17LTE eMMC: GPT USERDATA first=6713344 sectors=24051712 read-only`
  - `J3Y17LTE eMMC: /dev/emmcroot0 ready, GPT USERDATA read-only`
  - `BSD root: emmcroot0, major 1, minor 0`
  - **`hfs: mounted iosRoot on device b(1, 0)`**
  - `SWEET: root volume is not authenticated (error 25); continuing unsealed`
  - `load_init_program: attempting to load /sbin/launchd`
- This is the current strongest milestone: **the physical J3 mounts the installed genuine iOS HFSX root and reaches process-1 exec.**

### J3XNU041 userspace-args trial and new panic

- J3XNU041 was repackaged without a kernel rebuild using:
  `debug=0xc cpus=1 keepsyms=1 -noprogress -v -enable_kprintf_spam rd=emmcroot0 emmcroot=USERDATA launchdsuffix=release unentitled_ios_sim_launch=1 ignition_level=1 launchd_unsecure_cache=1 wdt_test=no_user_checkin wdt=-1`
- Still **no `rootrw`**, no `emmcwrite=1`, and no eMMC write implementation. Keep root read-only until a specific later milestone requires writes.
- Physical boot still mounted `iosRoot` and went directly to `/sbin/launchd`; about 30 seconds later a new panic appeared.
- The framebuffer panic-format barcode decodes to the prefix **`%s at pc 0x%016l`**, matching XNU's generic ARM64 saved-state panic path in `sleh.c`. The photo did not expose a readable PC/LR/ESR/FAR.
- Comparison with the device-proven A5XELTE port found an extremely close precedent: its first populated iOS USERDATA boot reached launchd and then took a kernel data abort in `accelerate_entitlement_queries` because the donor AMFI interface registration was guarded for SWEET only.

### J3XNU042 physical result — VERIFIED

- J3XNU042 kernel/package from artifact `j3y17lte-xnu-kernel (19).tgz` was physically flashed/tested through the established RECOVERY-only Odin AP workflow.
- Kernel SHA256: `dd6e4ae55531adac34472a730151a6ac85cacf48683e1f05cc83feb42f7633d9`.
- Recovery image SHA256: `2578482adb43d188ae8f12efce988ed1307c1746d02a81f31d96e0152f7e3d81`.
- Odin TAR SHA256: `3f1864d6149f1287fce5faab7d32fc2d2aecd0076f3f29b1ca5cef90ec1d44de`.
- The AMFI bridge worked: the previous launchd-stage generic ARM64 panic moved forward into dyld/shared-cache handling.
- Physical console evidence now shows the exact next blocker:
  - `disallowing unsupported code signature page shift: 14`
  - `unable to create a validated cs_blob object: 85`
  - dyld reports code-signature registration for the shared cache failed
  - `Library not loaded: /usr/lib/libSystem.B.dylib`
  - PID 1 (`/sbin/launchd`) exits because the dyld shared cache could not be registered.
- This matches the A5XELTE port's previously device-verified 4 KiB-kernel vs 16 KiB iOS shared-cache CodeDirectory failure nearly exactly. Therefore the AMFI-null-pointer hypothesis for J3XNU041 was correct enough to move execution into real dyld processing.
- The second J3XNU042 photo is a panic/terminal state after PID1 exits; the useful root cause is already printed in plain text above it. No further panic-barcode decoding is needed for this revision.
- Root mount remains verified read-only and unchanged. The coredump path also fails with error 30 (`EROFS`), which is expected with the current read-only root and is not the immediate blocker.

### J3XNU043 physical result — VERIFIED

- Corrected J3XNU043 source commit: **`bf218d33d4ffc0787670c0047615c04a370e22dc`**.
- CircleCI build **#41 succeeded**.
- User downloaded the successful artifact as **`j3y17lte-xnu-kernel (20).tgz`**.
- Artifact/package verification supplied by the user:
  - `SHA256SUMS`: OK
  - Mach-O 64-bit arm64
  - kernel SHA256: **`5edbe10317a96b62ee8ba2bd50eae7056e5447a906fb8f4f3a14bd6d7d740d86`**
  - old LSE `28 01 28 f8` occurrence count: **0**
  - recovery SHA256: **`1bff0b74327e847be8f65af296ba910e2ce0834d94d3d65abefdc09db4759673`**
  - Odin TAR SHA256: **`2030196e37a45a434e153ac31b68282ee45c086656fdf7cd7179e168e4f65581`**
  - package: `C:\Users\BalJai\Downloads\recovery-j3xnu043-userland-ro-odin.tar`
  - boot args included `cs_enforcement_disable=1`; eMMC writes were still disabled.
- Four physical photos from one J3XNU043 boot, taken moments apart, establish the sequence:
  1. normal J3 XNU/platform bring-up;
  2. HFS metadata/hardlink activity on `iOSRoot`;
  3. real launchd execution with **`Darwin Bootstrapper Version 7.0.0`**, the expected J3XNU043 boot args, `Doing boot task`, and launchd authorizing `fsck`;
  4. the mount task fails with:
     - `GetMasterBlock: Error 16 opening /dev/emmcroot0`
     - `mount_hfs: error on mount(): error = -1`
     - **`mount_hfs: Read-only file system`**
     - `mount: / failed with 1`
     - then `mount[3] exited` / coredump handling.
- Therefore the J3XNU042 shared-cache error (`page shift: 14`, no dyld cache, missing libSystem) is **passed**. This is genuine PID1/launchd boot-task progress, not merely a colourful framebuffer milestone.
- The coredump `error 30` remains expected while the root is read-only and is secondary to the mount failure.
- The visible BindFS lookup failure under `/private/preboot/.../usr/standalone/firmware` occurs after the mount failure and is not the first blocker to solve.

### J3XNU044 — gated writable USERDATA trial

- New patch: **`xnu/patches/0148-j3y17lte-userdata-write.patch`**.
- Runtime evidence now proves writes are required: launchd's mount phase explicitly fails because `/dev/emmcroot0` is read-only. This satisfies the earlier rule not to enable writes prematurely.
- Device-proven donor precedent is A5XELTE **`0108-a5xelte-userdata-write.patch`**, which immediately followed its identical `Bootstrapped Version 7.0.0` / `mount_hfs: Read-only file system` milestone.
- J3-specific hardware assumptions were independently checked against Samsung's exact J3Y17LTE kernel source before adapting the donor:
  - `dwmmc0@13540000` has **`fifo-depth = <0x40>`** (64 entries);
  - `exynos7570-j3y17lte_defconfig` has **`CONFIG_MMC_DW_FORCE_32BIT_SFR_RW=y`**;
  - these match the donor's CMD24 PIO/FIFO assumptions and the J3's already-proven CMD17 paired-32-bit read path.
- J3XNU044 adds:
  1. polled single-sector eMMC **CMD24** writes;
  2. paired 32-bit FIFO writes for the J3's 64-bit FIFO unit;
  3. existing mutex serialization plus read-modify-write for partial 512-byte sectors;
  4. writable BSD-device reporting only when the write gate is active.
- J3 adds stricter safety gates than the donor:
  - `emmcwrite=1` is mandatory;
  - selected GPT partition must be exactly `USERDATA`;
  - verified J3 USERDATA geometry must exactly match **first LBA 6713344, sectors 24051712**;
  - the strategy path still bounds every request to the selected partition;
  - `emmc_write_sector()` independently rejects any absolute LBA outside the selected USERDATA range;
  - default `SYSTEM` selection remains read-only.
- Patch-chain audit:
  - `0142` created `bsd/dev/j3y17lte_emmc.c`;
  - `0143` through `0147` were inspected and do not modify that file;
  - therefore the exact pre-0148 state is the 487-line file introduced by 0142.
- Mechanical pre-push validation:
  - reconstructed those exact 487 source lines from the cumulative patch chain;
  - generated the 0148 contextual diff from actual before/after text;
  - 13 contextual hunks;
  - independent apply/check simulation: **PASS**;
  - generated after-state exactly matches the intended 619-line target;
  - added-line whitespace / `git diff --check` equivalent: **PASS**;
  - USERDATA-name, exact-geometry, write-bootarg, CMD24, FIFO-depth, paired-32-bit and per-LBA bounds invariants: **PASS**.
- First J3XNU044 package should keep the successful J3XNU043 args and add only **`emmcwrite=1`**:
  `debug=0xc cpus=1 keepsyms=1 -noprogress -v -enable_kprintf_spam rd=emmcroot0 emmcroot=USERDATA launchdsuffix=release unentitled_ios_sim_launch=1 ignition_level=1 launchd_unsecure_cache=1 wdt_test=no_user_checkin wdt=-1 cs_enforcement_disable=1 emmcwrite=1`
- **Do not add `rootrw` on the first J3XNU044 test.** The proven failure is the block device refusing writable open during launchd's mount task; A5's patch0108 milestone was solved by enabling the device write path. If J3 then proves a separate root-mount flag blocker, the same kernel can be repackaged with `rootrw=1` without another CI build.
- This is the first J3 XNU candidate intentionally capable of mutating the iOS USERDATA root. The verified host image `~/ios-j330fn/rootbuild/20H392/ios16-j3-reduced-20H392.img` remains the restore source; do not write any partition outside the GPT-bounded USERDATA path.
- Expected next physical evidence:
  - early eMMC line should say `GPT USERDATA ... writable`;
  - no `mount_hfs: Read-only file system`;
  - either launchd advances into broader service startup (A5 precedent) or a new concrete CMD24/HFS/userspace error becomes the next blocker.

### J3XNU044 physical test — 2026-11-08 (newer than the packaging handoff)

- User supplied a 2016×1512 JPEG photo named `WhatsApp Image 2026-11-08 at 22.01.15.jpeg` and reports that the screen continuously scrolls messages. This follows the J3XNU044 `(21).tgz` packaging step; no new kernel SHA256 or recovered full boot log was supplied with the photo.
- Visible repeated lines include `Allowing spawn of iOS binary xpcproxy`, `bluetoothd`, `mobileactivationd`, and `hfs: set hardlink bit on vol=iOSRoot cnid=...`. The authorization comes from the permissive `unentitled_ios_sim_launch=1` path. It is **not** an error by itself and does not establish that the spawned process stays alive.
- No `mount_hfs: Read-only file system` or terminal kernel panic is visible in this specific captured frame. The continuation into multiple service spawns is strong evidence that the previous launchd mount-phase hard stop was passed. It does **not** independently verify CMD24 persistence, HFS consistency, SpringBoard execution or actual rendered iOS graphics.
- Exact donor parallel: A5XELTE progress after its patch0108 recorded the same repetitive `xpcproxy` and `bluetoothd` spawn-authorization lines during sustained userland startup. It next prepared patch0109 (DECON / IOSurface / AppleCLCD bridge) and patch0110 (persistent boot logging). Its progress log specifically warns that repeated authorizations can be service restarts but the exit reason must not be guessed.
- J3's physical scanout geometry is **720×1280, stride 2880**, framebuffer physical **0x67000000** (the working `0141` J3 framebuffer console). Do **not** copy A5's 1080×1920, stride 4320 or its `samsung,a5xelte-display` ADT node. Before a J3 display patch, reconstruct the full cumulative state of `iokit/KernelConfigTables.cpp`, `iokit/Kernel/arm/SweetFramebuffer.cpp` and `osfmk/console/serial_console.c` (especially J3 0088 and 0141, donor 0109), and verify the actual J3 entry ADT source/path on the user's WSL. Existing `0141` diagnostic-console writes would need a proven way to stop overwriting presented UI frames.
- **Next step:** capture a fuller runtime/exit reason if possible, or carefully preflight the J3-specific display bridge. No J3XNU045 kernel code is yet committed; do not spend CI on an unvalidated patch, and do not rewrite USERDATA or widen the eMMC write gate.
- The J3XNU044 physical result supersedes the earlier “not yet physically tested” expectation above.

### CI / patch discipline — CURRENT USER REQUIREMENT

- The user reports CircleCI budget is tight and explicitly said **stop burning credits/tokens**.
- **Do not push speculative code to main.**
- **Do not invoke/re-run CircleCI for documentation.**
- This AGENT.md update itself must be docs-only with **`[ci skip]`**.
- New kernel patches must be validated against the **full cumulative lexical patch chain**, not upstream source alone. The recent failures were:
  - malformed hunk count in 0138/0144-style manual diffs;
  - stale context copied from donor A5 patches;
  - assuming a donor patch's line numbers/guards still matched J3's cumulative tree.
- For any next patch: inspect all earlier patches touching the same target file; reconstruct the post-chain text; generate the diff rather than hand-counting hunk sizes; run `git apply --check`, apply it, and run `git diff --check` before a code push.
- Do **not** rewrite USERDATA or rebuild the iOS root for the current AMFI/dyld issues. The installed root is already full-readback verified.
- J3XNU043 has now provided the concrete userspace proof that writable USERDATA is required at launchd mount-phase. J3XNU044 therefore enables only the separately bounded, opt-in USERDATA write path above. Do not broaden writes beyond those gates or add `rootrw` until runtime evidence requires it.
- TWRP can be restored to RECOVERY without touching the iOS root, but never format/mount/repair Android `/data`.
- Never flash BL/CP/CSC/PIT or repartition. The established experiment is RECOVERY-only plus the already-completed USERDATA root install.



## J3XNU032 active handoff — 2026-11-07 (supersedes earlier handoffs)

- **J3XNU031 physical test decoded from photo `WhatsApp Image 2026-11-07 at 17.37.54.jpeg`:** the retained J3XNU030 barcode still decodes to `Undefined kernel`. The new J3XNU031 PC grid decodes cleanly to **`0xfffffff00725470c`** and the instruction grid to **`0xf8280128`**. Colour confidence is high for all bits because the same affine mapping also round-trips the known 16-byte panic barcode exactly.
- **Exact failing instruction:** `0xf8280128` decodes as **`LDADD X8, X8, [X9]`**, a 64-bit FEAT_LSE atomic add. This follows directly from the Arm encoding: size=11, A=0, R=0, Rs=8, Rn=9, Rt=8. FEAT_LSE instructions decode as UNDEFINED on implementations without LSE. Cortex-A53 is an Armv8.0-A core; LSE is mandatory only from Armv8.1-A and is not part of the Cortex-A53 baseline.
- **Root-cause class:** the immediate blocker is therefore **LSE code generation on an Armv8.0 Cortex-A53**, not the earlier IOKit duplicate-registration hypothesis. Do not bypass IOKit checks. The faulting PC is only `0x70c` bytes into `__TEXT_EXEC` (segment start `0xfffffff007254000` from the J3XNU031 packaging output), consistent with an early kernel code path.
- **Build-flag investigation:** current cumulative J3 patch0094 sets `MACHINE_FLAGS_ARM64_J3Y17LTE = ... -mcpu=cortex-a53 -march=armv8-a`. A local Clang 17 Darwin-target reproduction showed `-mcpu=cortex-a53` emits LL/SC (`ldxr/stxr`), while `-march=armv8-a` alone emits LSE `ldadd` due Darwin/Apple target defaults. Another active non-Apple XNU ARMv8.0 port uses only `-mcpu=cortex-a53` specifically to avoid Apple-M1/LSE defaults.
- **J3XNU032 patch:** `xnu/patches/0138-j3y17lte-force-cortex-a53-no-lse.patch` removes the trailing `-march=armv8-a` from J3Y17LTE machine flags, leaving **`-mcpu=cortex-a53`** as the explicit codegen target. No exception path, panic, atomic operation, or kernel logic is bypassed. Existing J3XNU030/031 diagnostics stay compiled in so the next blocker remains visible.
- **Related PAN state:** J3 patch0095 already changes `__ARM_PAN_AVAILABLE__` from1 to0, so the known Armv8.1 PAN incompatibility was already handled separately; do not duplicate that change.
- **Git/CI discipline:** J3XNU032 **code-only** commit is `9c79d914f5770757f88bceb8962242075da98718`; this is the commit intended to trigger the single CircleCI build. This AGENT.md handoff is intentionally a separate `[ci skip]` commit, per user instruction.
- **Next:** after CircleCI succeeds, verify the exact J3XNU032 ARM64 artifact, package recovery under versioned names, and physically test. If the same undefined-instruction barcode reappears, decode the new PC/opcode before making another logic change. If execution moves past this point, use the existing cumulative callback and panic markers to identify the next blocker. Do not present a drawn Apple logo as evidence of userland boot.

## Historical J3XNU031 handoff — 2026-11-07

## J3XNU031 active handoff — 2026-11-07 (supersedes earlier handoffs)

- **J3XNU030 artifact and physical test:** User downloaded CircleCI artifact as `j3y17lte-xnu-kernel (7).tgz`, verified `SHA256SUMS: OK`, ARM64 Mach-O, and confirmed the binary differs from J3XNU029. Raw kernel SHA256 `14d0e7fb8164181965b9b338a463381062b369c5d2d888eaab503b8d517f30ab`; recovery image SHA256 `7a83d8a3a815fd21ba0b9554cd4647cb4c6539439aac337035f2d7fbfa03e838`; Odin tar SHA256 `6003a053d386f68b35121ce71f37997951715c539efb3472069b1524c00f47ff`. The physical test photograph `WhatsApp Image 2026-11-07 at 17.24.03.jpeg` clearly shows the new 16x8 red/cyan panic-format barcode, proving J3XNU030 executed on hardware and `sweet_early_panic()` reached the barcode path.
- **Decoded panic prefix:** Sampling the 16 barcode columns top-to-bottom gives bytes `55 6e 64 65 66 69 6e 65 64 20 6b 65 72 6e 65 6c`, ASCII **`Undefined kernel`**. This matches XNU ARM64 `handle_uncategorized()` in `osfmk/arm64/sleh.c`, which panics with `Undefined kernel instruction: pc=%p instr=%x` for a kernel-mode uncategorized/undefined-instruction exception. The earlier IOKIT callback hypothesis is therefore superseded as the immediate failure mechanism; do not bypass IOKIT duplicate checks based on the old marker interpretation.
- **J3XNU031 patch:** `xnu/patches/0137-j3y17lte-decode-undefined-instruction.patch` modifies only the J3 early panic diagnostic. It first matches the exact prefix `Undefined kernel instruction`, then `va_copy`s the panic arguments and reads the existing `%p` faulting PC and `%x` 32-bit instruction word. It does not suppress or alter the exception/panic.
- **J3XNU031 display format:** PC is shown as 16 hexadecimal nibbles at framebuffer x96..599, y250..285; instruction is 8 hexadecimal nibbles at x96..343, y300..335. Each nibble is four vertical bits, MSB first; cyan=1, red=0. Stages363 and364 mark argument capture and completed painting. The existing J3XNU030 panic-format barcode remains visible below.
- **Validation before push:** Patch was generated from the exact J3XNU030 panic-hook context, passed `git apply --check --whitespace=error` on a reconstructed current snippet, applied cleanly, and `git diff --check` passed. A host C varargs sanity test confirmed the `%p` then `%x` extraction order and round-tripped representative 64-bit PC / 32-bit instruction values through the nibble encoding.
- **Git/CI discipline:** J3XNU031 **code-only** commit is `7c3581781d725580c7042259cd62f7ec28a10ef6`; this is the commit that should trigger the single CircleCI build. This AGENT.md update is intentionally a separate `[ci skip]` docs-only commit, per user request, so documentation does not trigger another CI job.
- **Next physical decision point:** Verify the J3XNU031 CircleCI artifact and package it under versioned names. On hardware, photograph the full screen. Decode the upper PC grid and instruction grid. Resolve the PC against the exact J3XNU031 Mach-O and decode the 32-bit ARM64 instruction before changing execution logic. A current unrelated non-Apple ARM XNU port has also reported the same undefined-instruction panic class around Apple-specific system-register handling, but that is only an analogy; do not assume the J3 instruction is Apple IMPDEF until the J3XNU031 opcode proves it.

## Historical J3XNU030 handoff — 2026-11-07

## J3XNU030 active handoff — 2026-11-07 (supersedes earlier handoffs)

- **J3XNU029 packaging:** User verified the CircleCI artifact downloaded as `j3y17lte-xnu-kernel (6).tgz`, `SHA256SUMS: OK`, ARM64 Mach-O, and all nine J3XNU029 embedded diagnostic strings. Raw Mach-O SHA256 `2c464321adcb4e7d661023eadef51693d525f9e369f711e0e44a380350928db2`; recovery image SHA256 `7abb367989afefcc3bdb128b3d7403b04b5c91dc34bc9774da8ebe7e4ced50cc`; Odin recovery tar SHA256 `44c0f69e0af1ff4585e459f2ed8744fb2344814dea7ec7df800415262657e420`. File in Windows Downloads: `recovery-j3xnu029-odin.tar`. Trailer `SEANDROIDENFORCE` preserved; tar contains only `recovery.img`.
- **J3XNU029 physical report:** User states it displays **no additional visible colours** compared with J3XNU028. No new J3XNU029 photograph was attached; this is user-reported screen identity, not an independently pixel-verified comparison. The nine stage341–349 markers are not established on hardware. Treat the user's established recovery-only Odin procedure as working unless specific evidence contradicts it; do not repeatedly ask about Download Mode or Odin basics.
- **Rechecked J3XNU028 physical photo:** Sampling the highly sloped y560 callback return row around x≈1216,y≈1198 finds purple consistent with stage278 (`#ae76b6`) at callback37's column; stage326 light-blue panic marker was independently visible around x≈563,y≈1090. Yet stage321 and J3XNU029's stage341 are reported/observed absent in clear left-side areas. This creates a **real diagnostic inconsistency** if all markers belong to the same currently executing binary; possibilities include stage-display visibility/overwrite, asynchronous panic during marker writes, incorrect read of the previous return marker, or stale runtime image despite a correct artifact. Do not resolve the contradiction by guessing.
- **J3XNU030 approach:** Print the first sixteen literal bytes of the **actual panic format string** directly to the early framebuffer as a binary barcode, independent of callback index and without a normal console. This is more informative than another handful of callback-index lights, and it makes the new build visually unmistakable if it executes. It does **not** replace panic handling, bypass duplicate checks, draw a fake iOS boot, or launch userland.
- **Patch:** `xnu/patches/0136-j3y17lte-encode-early-panic-format.patch` changes only `osfmk/arm64/sweet_early.c`. Marker cap360→380; new stages361–380 mapped at framebuffer y500–507 (only361 and362 currently used). Within `sweet_early_panic`, the existing stage326 panic marker still comes first. If `fmt` is non-null, stage361 marks entry to barcode generation; for up to 16 bytes of `fmt` before NUL, eight bits per character are painted top-to-bottom (bit7 to bit0), **cyan=1, red=0**, into x=96+32*i..+23, y=360+10*bit..+5. The grid spans x96..599 and y360..435. Stage362 follows a `dsb sy` after the grid, then the existing stage80 panic marker remains. Source is read-only and uses no dynamic allocation/printf/locks; writes remain inside the existing 2MiB framebuffer alias.
- **Interpreting next photo:** Look for a distinct 16-column×8-row red/cyan grid high above `SAMSUNG Galaxy J3`. A camera image of the entire unannotated screen is best. Decode each column top-to-bottom as eight bits, convert each byte to ASCII to recover the *literal panic format prefix*. It may contain `%d` placeholders because this uses `fmt`, not expanded arguments. Stage361/362 are ancillary proofs. If neither appears, investigate why the latest kernel path or panic reporter is not running before spending another build.
- **Local preflight:** Starting from Apple XNU `rel/xnu-8796` at `1b191cb58250d0705d8a51287127505aa4bc0789`, prior pinned staging sources and the complete cumulative patch chain through0135 were already applied successfully. Patch0136 passes `git apply --check --whitespace=error` against that cumulative tree, reverses/reapplies cleanly, and all existing CircleCI source grep assertions pass. The bitmap ranges and 2MiB aperture bounds were statically verified, including round-trip bit decoding. No local macOS/Xcode compiler; CircleCI must establish build success.
- **Next:** One atomic source+AGENT.md GitHub commit on main, exactly one CircleCI build, verify physical binary and package under J3XNU030 names; then inspect the first actual panic string before changing XNU logic. Docs-only edits use `[ci skip]`. Apple-logo goal remains a visual milestone, not evidence of iOS boot.

## Historical J3XNU029 handoff — 2026-11-07 (supersedes older handoffs)

- **J3XNU028 physical evidence:** User successfully built and packaged J3XNU028 from CircleCI archive `j3y17lte-xnu-kernel (5).tgz`; verified ARM64 Mach-O and `SHA256SUMS: OK`. Raw kernel SHA256 `757849ec5c3fc7da1c7eaf90155f6e23768d71095c74b3856045c9c3f48cc792`; recovery image SHA256 `6fd5a55e27ff3ec9e225d60bfb8c6c5b407ecdb2f137147d89125b6142d87788`; Odin tar SHA256 `c792c30681d4af912931c280447ce5ca8a34b3ddb930d458296500b441db46e9`. Recovery package `C:\\Users\\BalJai\\Downloads\\recovery-j3xnu028-odin.tar`, only member `recovery.img`, `SEANDROIDENFORCE` preserved. User physically tested it and supplied `WhatsApp Image 2026-11-07 at 12.54.41.jpeg` (1512×2016), annotating the only visible change with a green circle at the 'G' in Samsung Galaxy J3.
- **Critical visual finding:** The new isolated pale-blue bar beneath the annotation near photo x≈550, y≈1090 matches stage326 colour `#7ea6e6` and column5 (zero-based) in framebuffer row y524. That is `sweet_early_panic` entry. Stage321–324 columns0–3 at the same scanline appear black; stage325's dark colour would be partly obscured by the annotation and should not be asserted conclusively absent. The photo thus establishes an early panic and no visible progress through post-callback37 marker321. **Do not assume callback37 successfully returned or that callback38 itself is defective.** The previous stage278 identification may have conflated adjacent stacked rows, photographic perspective or marker colour; it remains tentative. The exact panic text is not available on this framebuffer.
- **Target callback reasoning:** The previously decoded J3XNU026 Mach-O startup table mapped zero-based index37 to `ipc_kobject_register_startup` with `IKOT_IOKIT_OBJECT` (enum30), and index38 to `IKOT_IOKIT_CONNECT` (enum29). A new build can potentially alter same-rank startup order; the index37 dispatcher and type30 body are traced separately to avoid silently assuming exact linker order. Registration checks in `osfmk/kern/ipc_kobject.c` include a duplicate-type panic and a struct copy; neither is bypassed.
- **J3XNU029 patch:** `xnu/patches/0135-j3y17lte-trace-iokit-object-callback37.patch`, modifying only `osfmk/arm64/sweet_early.c`, `osfmk/kern/startup.c`, and `osfmk/kern/ipc_kobject.c`. Adds new stage341–360 row at framebuffer scanlines y512–519 (32-pixel horizontal spacing, 8-pixel height; no overlap with J3XNU028 row y524–531). Stage cap increases from340 to360. Nine assigned marks, **341–349**:
  - 341: dispatcher sees MACH_IPC callback index37 before verbose logging.
  - 342: callback37 verbose logging passed.
  - 343: callback37 phase log passed; function call imminent.
  - 344: callback37 function body returned, *before* older stage278 mark.
  - 345: `ipc_kobject_register_startup` entered for `IKOT_IOKIT_OBJECT` (type30).
  - 346: type30 duplicate check passed.
  - 347: type30 operations struct copy completed.
  - 348: type30 registration function about to return.
  - 349: type30 duplicate detected immediately before the **unchanged original** `panic`.
- **Local preflight:** On a clone of Apple `rel/xnu-8796` commit `1b191cb58250d0705d8a51287127505aa4bc0789`, pinned libpthread/BearSSL/HFS stage scripts ran successfully, all earlier **131** patches (through J3XNU028 0134) were applied in CircleCI lexical order. Patch0135 was independently generated from the cumulative tree and verified using `git apply --check --whitespace=error`, reverse-check, and exact reapplication. Current CircleCI grep assertions passed, `IKOT_IOKIT_OBJECT = 30` confirmed in XNU header, stage341–349 calls present, framebuffer mapping within first 2MiB and rows nonoverlapping. Existing donor whitespace warnings are unrelated; no local macOS/Xcode toolchain to prove compile.
- **Next:** Atomic GitHub code+AGENT.md commit on `main` after strict preflight, one CircleCI macOS build only, then checksum-verify actual ARM64 artifact before recovery packaging and physical test. No speculative bypasses or new CI retries without evidence. User wants 5–10 meaningful diagnostic markers per iteration and is aiming for a visible Apple-logo-style milestone by Monday, but a cosmetic logo must never be presented as proof of an iOS userland boot.

## Historical J3XNU028 handoff — 2026-11-07 (supersedes historical pending notes)

- **New physical evidence:** User confirms the uploaded annotated Samsung Galaxy J3 photograph is from the J3XNU027 recovery-only physical test, and Download Mode remains accessible. They report the display appears unchanged from J3XNU026. Per user instruction, assume the correct J3XNU027 Odin image ran unless contradictory evidence appears. No further Odin reconfirmation is required for this investigation. Original recovery/firmware should still be preserved for future tests.
- **Photo assessment and limitation:** The stage261–280 callback-return row is visible, apparently through stage278 (zero-based callback37). The diagnostic row at framebuffer y536 (stage301–320) would appear about 16 photo pixels above the stage261 row, and its first six positions are in the black left-of-logo region; no stage301 marker is discernible there. The photo is only 579×735 and includes annotations over parts of the splash; treat absence of 301 as **strong visual evidence, not irrefutable proof**. Stage279, stages281–287, and stages311–315 are not established. Coloured markers are not iOS boot.
- **Exact code gap:** `startup.c` calls callback37, paints stage278 with `sweet_early_mark(261+37)`, increments `j3_mach_ipc_callback_index` from37 to38, advances global cursor via `startup_entry_cur = ++cur`, then evaluates `while (cur < startup_entries_end && cur->subsystem <= upto)`. Only once inside the next iteration does the J3XNU027 check `cur->subsystem == STARTUP_SUB_MACH_IPC && index == 38` paint stage301. There is **no explicit panic** between those points; a fault, failed loop guard, different next subsystem, delayed framebuffer write or stage278's barrier remaining stuck are the hypotheses. This does **not** prove the IOKIT_CONNECT registration body itself is defective.
- **J3XNU028 patch prepared for next diagnostic:** `xnu/patches/0134-j3y17lte-trace-callback37-transition.patch` modifies only `osfmk/kern/startup.c` and `osfmk/arm64/sweet_early.c`. It adds six *noninvasive* checkpoints. No duplicate check or panic path is bypassed; no startup loop logic is rewritten.
  - 321: after the existing callback37 return marker **returns** (detect possible stall in stage278 marker/DSB).
  - 322: callback counter incremented to38.
  - 323: `startup_entry_cur = ++cur` completed.
  - 324: next `while` iteration entered with counter38, before testing `cur->subsystem == STARTUP_SUB_MACH_IPC`.
  - 325: startup loop exited with counter still38 (rather than dispatching callback38).
  - 326: `sweet_early_panic` entered (additional independent marker alongside stage80).
  - Mapping: stages321–340 occupy framebuffer scanlines y524–531, column `stage - 321` at 32-pixel horizontal steps; only321–326 assigned. Stage cap becomes340. This row is disjoint from y536–543 and stays under the first 2MiB mapped framebuffer aperture.
- **Local preflight performed:** Cloned Apple `rel/xnu-8796` at commit `1b191cb58250d0705d8a51287127505aa4bc0789`; staged pinned libpthread `a6c70ca...`, BearSSL `7bea48e...` and HFS `31d5ec...`; applied all 130 existing `.patch` files in lexical CircleCI order successfully; then validated patch0134 using `git apply --check --whitespace=error` against the cumulative J3XNU027 tree, applied and reverse-checked it. Existing donor patches have unrelated trailing-whitespace warnings (e.g. `IOUserClient.cpp:2602`), but the *new patch* passes strict whitespace. All current CircleCI grep assertions pass; stages321–326 and framebuffer bounds were statically checked. Linux preflight used a temporary placeholder `TargetConditionals.h` solely to let staging scripts copy a file; this is **not** a macOS/ARM64 compilation. No local Xcode/iig compiler is available, so only the real CircleCI macOS build can establish compiled success.
- **Next step:** Atomically commit patch0134 **and this AGENT.md update** to `main` only after all local checks. Let exactly one CircleCI run compile J3XNU028; then verify the arm64 Mach-O and SHA256SUMS before repacking/physical testing. Do not assume CI success or iOS userland boot in advance. Avoid unrelated changes and additional CI pushes.

## Canonical places and versions

- GitHub repo: <https://github.com/imusingwinxp-ops/j3y17lte-xnu> (branch `main`).
- Last physically tested **code** commit (user-reported result): `d9d9238772b06511494eb392344c5117a4e19319` (J3XNU029; no visible change). J3XNU028 commit `73979e89...` has a documented photograph.
- Passing CI pipeline for that code: <https://circleci.com/gh/imusingwinxp-ops/j3y17lte-xnu/13> (**green / success on first attempt**). Its `j3y17lte-xnu-kernel.tgz` artifact contains `kernel.development.j3y17lte` and `SHA256SUMS`. **User downloaded as `j3y17lte-xnu-kernel (4).tgz`, verified `SHA256SUMS: OK`, ARM64 Mach-O and marker strings, and packaged `recovery-j3xnu027-odin.tar` successfully**. See exact user-reported hashes below. Historical J3XNU026 #12 artifact was downloaded as `(3).tgz` and packaged successfully.
- Latest source patch (J3XNU030, locally preflight-verified; macOS CI pending): `xnu/patches/0136-j3y17lte-encode-early-panic-format.patch`. J3XNU029 source commit `d9d9238772b06511494eb392344c5117a4e19319` produced the checksum-verified user-packaged artifact.
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
8. J3XNU026 (committed patch `0132`) adds **two rows only** for completed callbacks 20–39 (stages261–280, framebuffer y560) and callbacks40–42 (stages281–283, y548). Stages284–287 mark the end of callback loop, final `kernel_startup_log(upto)`, final verbose `kprintf`, and function return. `sweet_early_mark` stage cap increases to 300. Patch was locally applied on an XNU preflight tree already including 0131, regenerated via `git diff --no-index`, and validated by `git apply --check --verbose --whitespace=error` on the pristine preflight copy. **CI pipeline #12 passed** with code commit `c52a3551f4ba491bf377e76def9f987bc0a52ea0` (one attempt only). Archive verification, packaging and physical photo were subsequently completed; see steps 9–10.
9. J3XNU026 **physical photo received**: `WhatsApp Image 2026-11-07 at 11.50.51.jpeg` (1512×2016), colour markers extending under/over the "Galaxy J3" text. Examined a high-resolution crop and original photo pixel samples. At marker column17 (image x≈1200), two distinguishable rectangles: green around y1183–1199 (J3XNU025 stage258) and purple around y1204–1219 (J3XNU026 **stage278**, callback index37 returned). At column18 (x≈1254), rectangles appear red around y1182–1199 (stage259, MIG finish), then yellow-green around y1203–1219 (stage239, MIG entered); **no peach-coloured stage279** (callback index38 returned). At column19 (x≈1310), there are no top-row stage280 return markers. Stage281–287 (callbacks40–42 and loop exit) also appear absent. Screen framebuffer mapping and photo perspective make the on-screen order of individual row colours nontrivial; identify markers using **stage-specific RGB colours and column**, not a rigid horizontal scan. Thus last proven completion is likely **callback index37**, and first nonreturning is **index38**. The precise J3XNU026 archive and startup callback table **were subsequently received and analysed** (step10); old requests in earlier chat for that archive are satisfied.
10. **J3XNU026 archive now attached and decoded.** `/workspace/scratch/efd2accecee5/upload/j3y17lte-xnu-kernel (3).tgz`: tar contains raw Mach-O and SHA256SUMS, `sha256sum -c` **OK**. Copied exact Apple XNU qsort reference helper and analyzer into scratch `j3xnu026_binary`; the Mach-O contains 4069 startup entries, **43** MACH_IPC callbacks with the same qsort order as J3XNU024. Relevant exact mappings: index37 -> `_ipc_kobject_register_startup`, arg `0xfffffff007c559b0` = `_ipc_kobject_ops_IKOT_IOKIT_OBJECT` (type30); index38 -> `_ipc_kobject_register_startup` at `0xfffffff007a480e0`, arg `0xfffffff007c559d0` = `_ipc_kobject_ops_IKOT_IOKIT_CONNECT` (type29); index39 -> same function, arg `0xfffffff007c559f0` = `_ipc_kobject_ops_IKOT_UEXT_OBJECT` (type41). **The callback identity is confirmed, not inferred.** The function in `osfmk/kern/ipc_kobject.c` performs a duplicate-type check then a struct copy to `ipc_kobject_ops_array` and returns; its body is too simple to assume the precise failure without targeted markers. Could hang in preceding verbose startup logging, phase log, duplicate check/panic, or memory copy. Do not bypass checks blindly.
11. **J3XNU027 patch built and packaged successfully:** `xnu/patches/0133-j3y17lte-trace-iokit-connect-startup.patch`. `sweet_early.c` cap 320 with **stage301–320 at framebuffer y536** (x=0..19, 8px high). `startup.c` marks stage301 dispatch idx38 entered, 302 verbose kprintf returned, 303 phase log returned, 304 imminent callback call, 305 callback body returned, and 306 cursor committed. `ipc_kobject.c` ONLY for `ops->iko_op_type == IKOT_IOKIT_CONNECT`: 311 entry, 312 duplicate check passed, 313 struct copy completed, 314 returning, **315 duplicate detected before original `panic`**. No core logic bypass. Patch was generated by editing the correctly previously-patched local XNU tree and using `git diff --no-index`, then verified with **`git apply --check --verbose --whitespace=error`** against untouched baseline copy. Three target files: `osfmk/arm64/sweet_early.c`, `osfmk/kern/startup.c`, `osfmk/kern/ipc_kobject.c`. Code + AGENT.md atomically pushed as `cd7908b...`; **CircleCI #13 succeeded** and user has now verified and packaged its artifact. **Next: physical recovery-only test and clear photo after verifying backup/recovery safeguards.** Do not bypass or guess further.

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
| 301–320 | 536 | **J3XNU027 targeted dispatcher/IOKIT_CONNECT markers**: 301–306 around callback idx38, 311–315 inside registration; colour/position authoritative |

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

## Historical next-session procedure (superseded by J3XNU028 active handoff above)

1. J3XNU025 is **complete and physically tested**. Its photo demonstrates all MIG init steps and all 20 tracked MACH_IPC callbacks return. **Do not generate a second J3XNU025 build.**
2. J3XNU026 patch `0132` is **already committed, CircleCI-green on pipeline #12, checksum-verified and Odin-packaged**; **do not rebuild or repack**. The package is in Windows Downloads as `recovery-j3xnu026-odin.tar` with tar hash documented below. Confirm correct J330FN handset, original recovery backup and a working Download Mode/Odin recovery path before any recovery-partition test. Do not write BOOT/BL/CP/CSC.
3. **J3XNU026 photo and exact binary now both received and assessed.** Callback38 conclusively `_ipc_kobject_register_startup` for `IKOT_IOKIT_CONNECT`. **J3XNU027 diagnostic patch `0133` is already committed, CI #13 GREEN, archive checksum VERIFIED, and Odin package CREATED**. Do not rebuild or repackage. The next step is a physical recovery-only test after safeguards below. Request the new phone photo; interpret stages301–306 and 311–315 to locate the precise failure. **Every new code change must include AGENT.md in the same atomic commit.**

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

### J3XNU027 — artifact verification and Odin package COMPLETED (user log, 7 November 2026)

1. The user downloaded the #13 `j3y17lte-xnu-kernel.tgz` artifact. Their Windows browser saved it as **`j3y17lte-xnu-kernel (4).tgz`**. They posted complete WSL terminal output from the guarded packaging block **showing SUCCESS**. We have inspected the output, **not independently read the Windows files**; no physical flash/photo for J3XNU027 has yet been reported.
2. Archive contents were `kernel.development.j3y17lte` and `SHA256SUMS`; `sha256sum -c SHA256SUMS` returned **OK**. `file` identified **Mach-O 64-bit arm64 executable**. `strings` found all three J3XNU027 checks: `callback 38 dispatch entered`, `IOKIT_CONNECT registration entered`, and `IOKIT_CONNECT duplicate registration`. The payload/boot image tool reported entry `0xfffffff00740c488`, `kernel_end=0xfffffff0080a0000`, Mach-O size **16441520** bytes. Recovery repack reported **16822288** bytes, Samsung trailer `SEANDROIDENFORCE` preserved. `tar -tf` listed **only `recovery.img`**. User terminal hashes:

   - Raw ARM64 Mach-O: `f719abb029e5fb78e4d0022c3be8e373635c4ae33909d0c558fdcb2c694c685f`.
   - Repacked `recovery-j3xnu027.img` AND packaged `out/j3xnu027/recovery.img`: `a3e4fc6967ef159df8e355ae94bdc839dceae2478f8b6494393bc2ea940c10f1`.
   - `out/j3xnu027/recovery-j3xnu027-odin.tar`: `32f83ae8fb76c1da05dbba32473429e05f62eb8d2331cfa01dd69c65a7c3ff2e`.
   - Copied Odin package: `C:\Users\BalJai\Downloads\recovery-j3xnu027-odin.tar`.

3. The exact **already executed** command is retained below for history/diagnosis. **Do not rerun** it since the guard tests deliberately refuse existing J3XNU027 files. `strings` proves marker text was **compiled into** the kernel, not that those lines executed on real hardware.

```bash
(
set -euo pipefail
cd ~/ios-j330fn
ARCHIVE="/mnt/c/Users/BalJai/Downloads/j3y17lte-xnu-kernel (4).tgz"
ART="$HOME/ios-j330fn/xnu-j3/artifacts/j3xnu027-circleci"
test -s "$ARCHIVE"
test ! -e "$ART"
mkdir -p "$ART"
tar -tzf "$ARCHIVE"
tar -xzf "$ARCHIVE" -C "$ART"
cd "$ART"
sha256sum -c SHA256SUMS
K27="$ART/kernel.development.j3y17lte"
file "$K27" | grep -Eq 'Mach-O 64-bit.*arm64'
strings "$K27" | grep -F 'J3XNU027 callback 38 dispatch entered'
strings "$K27" | grep -F 'J3XNU027 IOKIT_CONNECT registration entered'
strings "$K27" | grep -F 'J3XNU027 IOKIT_CONNECT duplicate registration'
sha256sum "$K27"
cd ~/ios-j330fn
test ! -e tools/j3y17lte/j3xnu027.payload
test ! -e recovery-j3xnu027.img
test ! -e out/j3xnu027/recovery.img
test ! -e out/j3xnu027/recovery-j3xnu027-odin.tar
test ! -e /mnt/c/Users/BalJai/Downloads/recovery-j3xnu027-odin.tar
python3 tools/j3y17lte/mkpayload_j3.py \
  "$K27" tools/j3y17lte/j3y17lte-entry.adt \
  tools/j3y17lte/j3xnu027.payload \
  --cmdline 'debug=0xc cpus=1 keepsyms=1'
python3 tools/repack-j3-xnu-recovery.py \
  research/j3-recovery-work/recovery-apple.img \
  loader/j3y17lte/outxnu/Image \
  tools/j3y17lte/j3xnu027.payload recovery-j3xnu027.img
test "$(tail -c 16 recovery-j3xnu027.img)" = "SEANDROIDENFORCE"
sha256sum recovery-j3xnu027.img
mkdir -p out/j3xnu027
cp recovery-j3xnu027.img out/j3xnu027/recovery.img
cd out/j3xnu027
tar -cf recovery-j3xnu027-odin.tar recovery.img
tar -tf recovery-j3xnu027-odin.tar
sha256sum recovery.img recovery-j3xnu027-odin.tar
cp recovery-j3xnu027-odin.tar /mnt/c/Users/BalJai/Downloads/
echo 'SUCCESS: J3XNU027 Odin package ready — NOT FLASHED'
)
```

4. **Next: physical test only if user has an exact SM-J330FN device, preserved original recovery/stock firmware, working Download Mode and known recovery route.** Odin **AP** with the versioned recovery-only tar; never change BOOT/BL/CP/CSC in this experiment. No blind flash if safety prerequisites are missing. Ask for a clear photo showing the full screen and, if possible, a short video of the last changing markers. Compare colour positions for stages301–306 and 311–315 and distinguish panic stage315 from a post-copy stall. Stop and inspect physical evidence before creating J3XNU028 or using more CI credits.

### J3XNU026 packaging completed (user terminal log, 7 November 2026)

User downloaded the CircleCI #12 artifact as `C:\Users\BalJai\Downloads\j3y17lte-xnu-kernel (3).tgz` and ran the WSL packaging sequence successfully with `set -euo pipefail`. Archive `SHA256SUMS` reported `kernel.development.j3y17lte: OK`, `file` reported `Mach-O 64-bit arm64 executable`, and `strings` found all three markers (`J3XNU026 Mach IPC callback 20-39 returned`, `J3XNU026 Mach IPC callback 40-42 returned`, `J3XNU026 MACH_IPC initializer returning`). Repacked image preserved `SEANDROIDENFORCE`, and Odin tar contains only `recovery.img`.

- Raw J3XNU026 Mach-O SHA256: `fbe833b23fdd5bcd6efc3645d2a526f99af38289d072f0c784251549c78959c3`.
- Recovery image SHA256: `3701ab13dd270c1b72f21fef91a4896697b782c07bc209ea01c4d78217c8416c`.
- Odin tar SHA256: `bf54693a955ee9a7c3481a31da02abe9765931b80bc4229ea5a01bfbea301d63`.
- User's Odin package: `C:\Users\BalJai\Downloads\recovery-j3xnu026-odin.tar`.
- **Physical J3XNU026 boot/photo was received later** (step9): colourful diagnostics likely show callback37 returned but callback38 did not. J3XNU027 supersedes this test; its **physical photo was subsequently received** (see current J3XNU028 handoff).

### J3XNU025 packaging completed (user terminal log, 7 November 2026)

CircleCI pipeline **#11 succeeded** for J3XNU025 commit `7ee1e8b1361006359b71233924cd4dceb96253fd`. The user downloaded the artifact as `C:\Users\BalJai\Downloads\j3y17lte-xnu-kernel (2).tgz` and successfully performed all validation/packaging steps on Kali WSL:

- Archive `SHA256SUMS`: **OK**. Mach-O: **64-bit arm64 executable**. Embedded `J3XNU025 mig_init entered`, `J3XNU025 mig_init returning`, `J3XNU025 MIG subsystem populated`: all found.
- J3XNU025 raw Mach-O SHA256: `e933fb18ba2c22d9ad9ba7529377a9ea7a70a8965002aa229831a1bcdda9e87b`.
- Repacked recovery image SHA256: `baae21dd80dd3942ff5e811593fe9af0e9f55950822a1fe552fe1e59dc424f1e`.
- Odin tar SHA256: `a70dab8a88512db7de23cab4d4e27b7a055a1a6e0c15eb82ec8d44a0b3d2e353`.
- Odin package path: `C:\Users\BalJai\Downloads\recovery-j3xnu025-odin.tar`. Tar contains precisely `recovery.img`; repacked image maintains `SEANDROIDENFORCE` trailer. Packaging script printed `SUCCESS: J3XNU025 Odin package ready!`.
- **Historical note superseded:** J3XNU025's real-device photo was subsequently supplied (2026-11-07 11:23); see step 7. It demonstrated `_mig_init` returned and callbacks 0–19 completed. The package should not be reflashed just to reproduce evidence that already exists.

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

## Historical J3XNU027 handoff sentence (superseded above)

**J3XNU026 code commit `c52a3551...`, CircleCI #12 GREEN, Odin SHA256 `bf54693a955ee9a7c3481a31da02abe9765931b80bc4229ea5a01bfbea301d63`, physical photo and exact Mach-O attached. Callback index37 returned but index38 probably did not; Mach-O qsort confirms index38=`ipc_kobject_register_startup`, arg `_ipc_kobject_ops_IKOT_IOKIT_CONNECT` type29. J3XNU027 code+AGENT.md atomic commit `cd7908bcd6455fc99d84d16b20ffebab4fe7aabf` adds patch `0133` stages301–306 and311–315 at y536, locally preflight-verified, **CircleCI #13 GREEN on FIRST TRY**. User downloaded as `j3y17lte-xnu-kernel (4).tgz`, verified archive checksum and markers, and successfully packaged `C:\Users\BalJai\Downloads\recovery-j3xnu027-odin.tar` (SHA256 `32f83ae8fb76c1da05dbba32473429e05f62eb8d2331cfa01dd69c65a7c3ff2e`). **Next: validate the exact J330FN and recovery safeguards, then user may run a recovery-only physical test; request a full-screen photo/video.** NO NEW CI/build until real device evidence arrives. Docs-only update: `[ci skip]`.**