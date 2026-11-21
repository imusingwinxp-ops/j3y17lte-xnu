#!/usr/bin/env python3
from pathlib import Path

path = Path("iokit/Kernel/arm/SweetFramebuffer.cpp")
text = path.read_text()

RECT_SHADER_HEX = "5510204830000000300000000000000095a840200138c002800a080880032800990082080060007f58025550a503a20401d80a40000055550000000000000000a900080200e01880bc240010f0020000200c0000000000000000000000000000aa0022004063188014822a0020039d020000a00c000000000000000000000000feff7f4f0000000000000000000000009a00820000601a0358025550a503460401d800000000000000000000000000000000000000000000000000000000000099008200006000035847f7eace0f40140158000000000000000000000000000089008200000000005847a2e8cef0581409d80000000000000000000000000000980088000000000446040dd8a3240d1899008a000060387c180046827fa0aa037b3401d8c1040dd8000000000000000099008a0000e0387c180040822a10a0037b3401d8c1040558000000000000000089008a0000e0007c180040822a10a003a3240dd8c104055800000000000000005800800000005814099800000000000095a8000100380002801a821c800318005900a8000060010300034604091840020000a00340340198000000000000000055a8000100384002801a821c80031c0095a8412001384001801a0808800310009900aa00016000000080380040020050a503403405586e020020a003580409d85900aa00206000e40068386b58822a50a5036e24201840827f00a0034004015855ac9a8900380000300000000000000055ac7b280138800080a803401400000015c8e00148030000300000000000000000000000000000000000000000000000"
FULL_SHADER_HEX = "85a820c801380001000104120300000088008008007ca21401d80a08000055555800800018687b04051800000000000055ac9a8900380000300000000000000055ac7b280138800080a805401408000015c8e0ab48810000300000000000000000000000000000000000000000000000"
JOB_G1_HEX = "00000000000000000000000000000000090101000000000000000000000000003f000000c61886610000002400000000000000000000000000000000000000000700000000000000000000000000000000000000000000000080674500000000000000000000000000000000000000000000000000000000006045230000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000705634000000000000000000000000"

def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"J3XNU099 {label}: expected exactly 1 match, found {count}")
    text = text.replace(old, new, 1)

def replace_span(start, end, replacement, label):
    global text
    i = text.find(start)
    if i < 0:
        raise SystemExit(f"J3XNU099 {label}: start anchor not found")
    j = text.find(end, i + len(start))
    if j < 0:
        raise SystemExit(f"J3XNU099 {label}: end anchor not found")
    if text.find(start, i + 1) >= 0:
        raise SystemExit(f"J3XNU099 {label}: start anchor is not unique")
    text = text[:i] + replacement + text[j:]

def c_array(name, expected, hex_string):
    data = bytes.fromhex(hex_string)
    if len(data) != expected:
        raise SystemExit(f"J3XNU099 {name}: byte count {len(data)} != {expected}")
    rows = []
    for i in range(0, len(data), 16):
        rows.append("\t" + ",".join(f"0x{b:02x}" for b in data[i:i+16]))
    return f"static const uint8_t {name}[{expected}] = {{\n" + ",\n".join(rows) + "\n};\n"

full_array = c_array("j3_mali_copy_shader", 112, FULL_SHADER_HEX)
rect_array = c_array("j3_mali_rect_shader", 592, RECT_SHADER_HEX)

definitions = """#define J3_MALI_COPY_BYTES               0x384000ULL
#define J3_MALI_COPY_WORDS               921600u
#define J3_MALI_FB_WIDTH                 720u
#define J3_MALI_FB_HEIGHT                1280u
#define J3_MALI_FB_STRIDE                2880u
#define J3_MALI_COPY_SRC_VA              0x10000000ULL
#define J3_MALI_COPY_SRC_STRIDE          0x00800000ULL
#define J3_MALI_COPY_SRC_MAX_BYTES       0x00400000ULL
#define J3_MALI_SOURCE_SLOTS             3u
#define J3_MALI_PRESENT_FAIL             0
#define J3_MALI_PRESENT_SUBMITTED        1
#define J3_MALI_PRESENT_BUSY             2
#define J3_MALI_COPY_DST_VA              0x10400000ULL
#define J3_MALI_COPY_RES_VA              0x107f0000ULL
#define J3_MALI_FULL_SHADER_OFF          0x000u
#define J3_MALI_FULL_RSD_OFF             0x080u
#define J3_MALI_RECT_SHADER_OFF          0x100u
#define J3_MALI_RECT_RSD_OFF             0x380u
#define J3_MALI_COPY_TLS_OFF             0x3c0u
#define J3_MALI_COPY_UBO_DESC_OFF        0x400u
#define J3_MALI_COPY_UBO_DATA_OFF        0x420u
#define J3_MALI_COPY_JOB_OFF             0x480u
#define J3_MALI_JOB_INVOCATION_OFF       32u
#define J3_MALI_RECT_UBO_BYTES           48u

""" + full_array + "\n" + rect_array + "\n"

replace_span(
    "#define J3_MALI_COPY_BYTES               0x384000ULL\n",
    "static uint32_t\nj3_gpu_read(vm_offset_t base, uint32_t offset)\n",
    definitions,
    "definitions/shaders",
)

new_ctx = """struct j3_mali_compute_ctx {
\tstruct j3_mali_pt pt;
\tvoid *resourcePage;
\tuint64_t resourcePA;
\tIOMemoryDescriptor *sourceMemory[J3_MALI_SOURCE_SLOTS];
\tuint32_t sourceOffset[J3_MALI_SOURCE_SLOTS];
\tuint64_t sourceBytes[J3_MALI_SOURCE_SLOTS];
\tunsigned nextSourceSlot;
\tbool initialized;
\tbool disabled;
\tbool inFlight;
\tuint64_t submittedFrames;
\tuint64_t completedFrames;
\tuint64_t busyFrames;
\tuint64_t sourceHits;
\tuint64_t sourceRemaps;
\tuint64_t gpuRect;
\tuint64_t gpuFull;
\tuint64_t cleanBytes;
\tuint64_t gpuBytes;
};

static struct j3_mali_compute_ctx j3_mali_compute;
static uint64_t j3_mali_cpu_fallbacks;
static uint64_t j3_mali_swap_count;
"""
replace_span(
    "struct j3_mali_compute_ctx {\n",
    "static uint64_t j3_mali_cpu_fallbacks;\n",
    new_ctx,
    "compute context",
)
replace_once(
    "static uint64_t j3_mali_swap_count;\nstatic uint64_t j3_mali_cpu_fallbacks;\n",
    "static uint64_t j3_mali_swap_count;\n",
    "context old-global cleanup",
)

