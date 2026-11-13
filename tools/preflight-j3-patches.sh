#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCHDIR="$ROOT/xnu/patches"
WORK="${TMPDIR:-/tmp}/j3-xnu-patch-preflight"

rm -rf "$WORK"
git clone --depth 1 --branch xnu-8796.141.3 \
  https://github.com/apple-oss-distributions/xnu.git "$WORK"

test "$(git -C "$WORK" rev-parse HEAD)" = \
  "1b191cb58250d0705d8a51287127505aa4bc0789"

cd "$WORK"

# Mirror CircleCI's XNU target environment. Without these, the staging scripts
# intentionally no-op and later HFS/libpthread patches fail on missing files.
export MACHINE_CONFIG=J3Y17LTE
export MACOS_VERSION=13.5

# The staging scripts only use xcrun here to locate TargetConditionals.h.
# Linux/WSL has no Apple SDK, and patch preflight does not compile these
# providers, so supply a minimal throwaway SDK path solely for those copies.
PREFLIGHT_SDK="$WORK/.j3-preflight-sdk"
PREFLIGHT_BIN="$WORK/.j3-preflight-bin"
mkdir -p "$PREFLIGHT_SDK/usr/include" "$PREFLIGHT_BIN"
cat > "$PREFLIGHT_SDK/usr/include/TargetConditionals.h" <<'EOF'
#ifndef __TARGETCONDITIONALS__
#define __TARGETCONDITIONALS__
#define TARGET_OS_OSX 1
#define TARGET_OS_MAC 1
#define TARGET_OS_IPHONE 0
#endif
EOF
cat > "$PREFLIGHT_BIN/xcrun" <<EOF
#!/bin/sh
if [ "\$1" = "--sdk" ] && [ "\$2" = "macosx" ] && [ "\$3" = "--show-sdk-path" ]; then
  printf '%s\n' "$PREFLIGHT_SDK"
  exit 0
fi
echo "preflight xcrun stub: unsupported invocation: \$*" >&2
exit 1
EOF
chmod +x "$PREFLIGHT_BIN/xcrun"
export PATH="$PREFLIGHT_BIN:$PATH"

echo "===== STAGING ====="
for s in "$PATCHDIR"/*.sh; do
  echo "RUN: $(basename "$s")"
  bash "$s"
done

echo "===== PATCHES ====="
for p in "$PATCHDIR"/*.patch; do
  echo "CHECK: $(basename "$p")"
  git apply --check "$p"
  git apply "$p"
done

echo "===== J3XNU075 MARKERS ====="
grep -nF 'j3y17lte_send_ipi(i);' iokit/Kernel/arm/SweetCPU.cpp
grep -nF 'if (*delta < step) {' pexpert/arm/pe_init.c
grep -nF 'static bool j3_touch_force_gpio;' bsd/dev/j3y17lte_input.c
grep -nF 'J3 INPUT: HW-I2C RMI setup failed; switching to GPIO transport' bsd/dev/j3y17lte_input.c
grep -nF 'return KERN_NOT_SUPPORTED;' bsd/net/dlil.c

echo
echo "========================================"
echo " FULL J3 PATCH STACK PREFLIGHT: PASS"
echo "========================================"
