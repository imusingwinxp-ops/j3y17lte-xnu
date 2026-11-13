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
