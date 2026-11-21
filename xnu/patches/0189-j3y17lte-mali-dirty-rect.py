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

new_init = r"""static bool
j3_mali_compute_init(vm_offset_t mali)
{
	struct j3_mali_compute_ctx *c = &j3_mali_compute;
	if (c->initialized) {
		return !c->disabled;
	}
	bzero(c, sizeof(*c));
	if (j3_mali_pt_alloc(&c->pt) < 0) {
		return false;
	}
	c->resourcePage = IOMallocAligned(4096, 4096);
	if (!c->resourcePage) {
		j3_mali_pt_destroy(&c->pt);
		return false;
	}
	bzero(c->resourcePage, 4096);
	c->resourcePA = (uint64_t)ml_vtophys((vm_offset_t)c->resourcePage);
	if (!c->resourcePA || (c->resourcePA & 0xfffULL)) {
		IOFreeAligned(c->resourcePage, 4096);
		c->resourcePage = NULL;
		j3_mali_pt_destroy(&c->pt);
		return false;
	}

	uint8_t *r = (uint8_t *)c->resourcePage;
	memcpy(r + J3_MALI_FULL_SHADER_OFF, j3_mali_copy_shader,
	    sizeof(j3_mali_copy_shader));
	memcpy(r + J3_MALI_RECT_SHADER_OFF, j3_mali_rect_shader,
	    sizeof(j3_mali_rect_shader));

	static const uint8_t fullRsdTemplate[64] = {
		0x05,0x50,0x34,0x12,0,0,0,0, 0,0,0,0,0,0,0,0,
		0x01,0x00,0x01,0x00,0,0,0,0, 0,0,0,0,0,0,0,0,
		0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,
		0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0
	};
	static const uint8_t rectRsdTemplate[64] = {
		0x05,0x50,0x34,0x12,0,0,0,0, 0,0,0,0,0,0,0,0,
		0x01,0x00,0x02,0x00,0,0,0,0, 0,0,0,0,0,0,0,0,
		0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,
		0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0
	};
	memcpy(r + J3_MALI_FULL_RSD_OFF, fullRsdTemplate, sizeof(fullRsdTemplate));
	memcpy(r + J3_MALI_RECT_RSD_OFF, rectRsdTemplate, sizeof(rectRsdTemplate));
	*(uint64_t *)(r + J3_MALI_FULL_RSD_OFF) =
	    (J3_MALI_COPY_RES_VA + J3_MALI_FULL_SHADER_OFF) | 5ULL;
	*(uint64_t *)(r + J3_MALI_RECT_RSD_OFF) =
	    (J3_MALI_COPY_RES_VA + J3_MALI_RECT_SHADER_OFF) | 5ULL;
	/* Midgard RSD renderer-properties bit 13: shader has global side effects. */
	((uint32_t *)(r + J3_MALI_FULL_RSD_OFF))[4] |= (1u << 13);
	((uint32_t *)(r + J3_MALI_RECT_RSD_OFF))[4] |= (1u << 13);

	static const uint8_t tlsTemplate[32] = {
		0,0,0,0,0x1f,0,0,0, 0,0,0,0,0,0,0,0,
		0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0
	};
	memcpy(r + J3_MALI_COPY_TLS_OFF, tlsTemplate, sizeof(tlsTemplate));

	uint64_t uboDataVA = J3_MALI_COPY_RES_VA + J3_MALI_COPY_UBO_DATA_OFF;
	*(uint64_t *)(r + J3_MALI_COPY_UBO_DESC_OFF) =
	    ((uboDataVA >> 4) << 12) | 2ULL;

	static const uint8_t jobTemplate[192] = {
		0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
		0x09,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
		0x3f,0x00,0x00,0x00,0xc6,0x18,0x86,0x61,0x00,0x00,0x00,0x24,0x00,0x00,0x00,0x00,
		0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
		0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
		0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x80,0x67,0x45,0x00,0x00,0x00,0x00,
		0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
		0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x60,0x45,0x23,0x00,0x00,0x00,0x00,
		0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
		0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
		0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
		0x00,0x70,0x56,0x34,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
	};
	memcpy(r + J3_MALI_COPY_JOB_OFF, jobTemplate, sizeof(jobTemplate));
	*(uint64_t *)(r + J3_MALI_COPY_JOB_OFF + 88) =
	    J3_MALI_COPY_RES_VA + J3_MALI_COPY_UBO_DESC_OFF;
	*(uint64_t *)(r + J3_MALI_COPY_JOB_OFF + 120) =
	    J3_MALI_COPY_RES_VA + J3_MALI_FULL_RSD_OFF;
	*(uint64_t *)(r + J3_MALI_COPY_JOB_OFF + 176) =
	    J3_MALI_COPY_RES_VA + J3_MALI_COPY_TLS_OFF;

	if (!j3_mali_pt_map_page(&c->pt, J3_MALI_COPY_RES_VA,
	    c->resourcePA, j3_mali_live_attr)) {
		return false;
	}
	for (uint64_t off = 0; off < J3_MALI_COPY_BYTES; off += 0x1000ULL) {
		if (!j3_mali_pt_map_page(&c->pt, J3_MALI_COPY_DST_VA + off,
		    J3_MALI_FB_PA + off, j3_mali_live_attr)) {
			return false;
		}
	}
	j3_mali_pt_clean(&c->pt);
	flush_dcache64((addr64_t)(uintptr_t)c->resourcePage, 4096, FALSE);
	if (!j3_mali_compute_program_as0(mali)) {
		return false;
	}
	c->initialized = true;
	IOLog("J3 GPU: dual compute ARMED JS1 full=112B rect=592B slots=%u ptpages=%u\n",
	    J3_MALI_SOURCE_SLOTS, c->pt.count);
	return true;
}

"""
replace_span(
    "static bool\nj3_mali_compute_init(vm_offset_t mali)\n{\n",
    "static int\nj3_mali_compute_poll(vm_offset_t mali, bool wait)\n",
    new_init,
    "compute init",
)

new_present = r"""static int
j3_mali_compute_poll(vm_offset_t mali, bool wait)
{
	struct j3_mali_compute_ctx *c = &j3_mali_compute;
	uint32_t irq = 0;
	uint32_t mmuRaw = 0;
	unsigned limit = wait ? 2000000u : 1u;

	for (unsigned spin = 0; spin < limit; spin++) {
		mmuRaw = j3_gpu_read(mali, J3_MALI_MMU_IRQ_RAWSTAT);
		irq = j3_gpu_read(mali, J3_MALI_JOB_IRQ_RAWSTAT);
		if ((mmuRaw & (J3_MALI_MMU_PAGE_FAULT0 | J3_MALI_MMU_BUS_ERROR0)) ||
		    (irq & J3_MALI_JOB_FAIL1)) {
			IOLog("J3 GPU: rect present FALLBACK irq=%#x mmu=%#x js1=%#x fault=%#x@%#x:%08x\n",
			    irq, mmuRaw, j3_gpu_read(mali, J3_MALI_JS1_STATUS),
			    j3_gpu_read(mali, J3_MALI_AS0_FAULTSTATUS),
			    j3_gpu_read(mali, J3_MALI_AS0_FAULTADDRESS_HI),
			    j3_gpu_read(mali, J3_MALI_AS0_FAULTADDRESS_LO));
			j3_mali_compute_recover(mali, irq, mmuRaw);
			c->inFlight = false;
			c->disabled = true;
			return J3_MALI_PRESENT_FAIL;
		}
		if (irq & J3_MALI_JOB_DONE1) {
			j3_gpu_write(mali, J3_MALI_JOB_IRQ_CLEAR, J3_MALI_JOB_DONE1);
			__asm__ volatile("dsb sy" ::: "memory");
			c->inFlight = false;
			c->completedFrames++;
			j3_mali_present_frames++;
			return J3_MALI_PRESENT_SUBMITTED;
		}
		if (wait) {
			__asm__ volatile("yield");
		}
	}

	if (wait) {
		IOLog("J3 GPU: rect present FALLBACK timeout js1=%#x irq=%#x mmu=%#x\n",
		    j3_gpu_read(mali, J3_MALI_JS1_STATUS), irq, mmuRaw);
		j3_mali_compute_recover(mali, irq, mmuRaw);
		c->inFlight = false;
		c->disabled = true;
		return J3_MALI_PRESENT_FAIL;
	}

	c->busyFrames++;
	return J3_MALI_PRESENT_BUSY;
}

static unsigned
j3_mali_ceil_log2(unsigned value)
{
	if (value <= 1u) {
		return 0u;
	}
	unsigned n = 0u;
	value--;
	while (value) {
		value >>= 1;
		n++;
	}
	return n;
}

/*
 * Exact PAN_ARCH=4 1D workgroup packing captured from Mesa/Panfrost.
 * Locals are fixed at 64x1x1; only group count X changes per rectangle.
 */
static bool
j3_mali_pack_groups(uint8_t *invocation, unsigned groups)
{
	if (!invocation || groups == 0u || groups > 14400u) {
		return false;
	}
	unsigned groupEnd = 6u + j3_mali_ceil_log2(groups);
	uint32_t invocations = 0x3fu | ((groups - 1u) << 6);
	uint32_t shifts = 6u | (6u << 5) | (6u << 10) |
	    (groupEnd << 16) | (groupEnd << 22) | (6u << 28);
	memcpy(invocation + 0, &invocations, sizeof(invocations));
	memcpy(invocation + 4, &shifts, sizeof(shifts));
	return true;
}

static void
j3_mali_clean_source_rect(struct j3_mali_compute_ctx *c, uintptr_t src,
    SweetSurface *s, uint32_t sx, uint32_t sy, uint32_t w, uint32_t h)
{
	uint64_t rowBytes = (uint64_t)w * 4ULL;
	uint64_t base = (uint64_t)src + (uint64_t)s->offset +
	    (uint64_t)sy * s->bytesPerRow + (uint64_t)sx * 4ULL;

	if (sx == 0u && rowBytes == s->bytesPerRow) {
		uint64_t bytes = rowBytes * h;
		flush_dcache64((addr64_t)base, (unsigned)bytes, FALSE);
		c->cleanBytes += bytes;
		return;
	}

	for (uint32_t y = 0; y < h; y++) {
		flush_dcache64((addr64_t)(base + (uint64_t)y * s->bytesPerRow),
		    (unsigned)rowBytes, FALSE);
		c->cleanBytes += rowBytes;
	}
}

static int
j3_mali_present_rect(SweetSurface *s, uintptr_t src,
    int32_t sxIn, int32_t syIn, int32_t dxIn, int32_t dyIn,
    int32_t wIn, int32_t hIn, bool async)
{
	if (!j3_mali_live_ready || !j3_mali_live_base || !s || !s->memory ||
	    j3_mali_compute.disabled || !src ||
	    sxIn < 0 || syIn < 0 || dxIn < 0 || dyIn < 0 ||
	    wIn <= 0 || hIn <= 0 || (s->offset & 3u)) {
		return J3_MALI_PRESENT_FAIL;
	}

	vm_offset_t mali = j3_mali_live_base;
	if (!j3_mali_compute_init(mali)) {
		j3_mali_compute.disabled = true;
		IOLog("J3 GPU: dual compute FALLBACK init failed\n");
		return J3_MALI_PRESENT_FAIL;
	}
	struct j3_mali_compute_ctx *c = &j3_mali_compute;

	/*
	 * 098 could return BUSY from the async path and silently lose a visible
	 * update. 099 never drops one: poll cheaply first, then wait only when
	 * the previous JS1 job really is still running.
	 */
	if (c->inFlight) {
		int state = j3_mali_compute_poll(mali, false);
		if (state == J3_MALI_PRESENT_BUSY) {
			state = j3_mali_compute_poll(mali, true);
		}
		if (state == J3_MALI_PRESENT_FAIL) {
			return state;
		}
	}

	uint32_t sx = (uint32_t)sxIn;
	uint32_t sy = (uint32_t)syIn;
	uint32_t dx = (uint32_t)dxIn;
	uint32_t dy = (uint32_t)dyIn;
	uint32_t w = (uint32_t)wIn;
	uint32_t h = (uint32_t)hIn;
	uint64_t pixels64 = (uint64_t)w * h;
	if (!pixels64 || pixels64 > J3_MALI_COPY_WORDS) {
		return J3_MALI_PRESENT_FAIL;
	}
	unsigned groups = (unsigned)((pixels64 + 63ULL) / 64ULL);
	if (!groups || groups > 14400u) {
		return J3_MALI_PRESENT_FAIL;
	}

	uint32_t mapOffset = s->offset & ~0xfffu;
	uint32_t mapDelta = s->offset - mapOffset;
	uint64_t lastByte = (uint64_t)mapDelta +
	    (uint64_t)sy * s->bytesPerRow + (uint64_t)sx * 4ULL +
	    (uint64_t)(h - 1u) * s->bytesPerRow + (uint64_t)w * 4ULL;
	uint64_t mapBytes = (lastByte + 0xfffULL) & ~0xfffULL;
	if (!mapBytes || mapBytes > J3_MALI_COPY_SRC_MAX_BYTES ||
	    (uint64_t)mapOffset + mapBytes > s->memory->getLength()) {
		return J3_MALI_PRESENT_FAIL;
	}

	unsigned slot = J3_MALI_SOURCE_SLOTS;
	for (unsigned i = 0; i < J3_MALI_SOURCE_SLOTS; i++) {
		if (c->sourceMemory[i] == s->memory &&
		    c->sourceOffset[i] == mapOffset &&
		    c->sourceBytes[i] >= mapBytes) {
			slot = i;
			break;
		}
	}
	if (slot == J3_MALI_SOURCE_SLOTS) {
		slot = c->nextSourceSlot++ % J3_MALI_SOURCE_SLOTS;
		uint64_t sourceVA = J3_MALI_COPY_SRC_VA +
		    (uint64_t)slot * J3_MALI_COPY_SRC_STRIDE;
		if (!j3_mali_map_md_range(&c->pt, s->memory, mapOffset,
		    sourceVA, mapBytes, j3_mali_live_attr)) {
			IOLog("J3 GPU: rect source map fallback id=%u off=%u map=%u bytes=%llu slot=%u\n",
			    s->id, s->offset, mapOffset, mapBytes, slot);
			return J3_MALI_PRESENT_FAIL;
		}
		j3_mali_pt_clean(&c->pt);
		if (!j3_mali_compute_program_as0(mali)) {
			c->disabled = true;
			return J3_MALI_PRESENT_FAIL;
		}
		if (c->sourceMemory[slot]) {
			c->sourceMemory[slot]->release();
		}
		s->memory->retain();
		c->sourceMemory[slot] = s->memory;
		c->sourceOffset[slot] = mapOffset;
		c->sourceBytes[slot] = mapBytes;
		c->sourceRemaps++;
	} else {
		c->sourceHits++;
	}

	uint64_t sourceVA = J3_MALI_COPY_SRC_VA +
	    (uint64_t)slot * J3_MALI_COPY_SRC_STRIDE + mapDelta;
	uint8_t *r = (uint8_t *)c->resourcePage;
	uint8_t *ubo = r + J3_MALI_COPY_UBO_DATA_OFF;
	uint8_t *job = r + J3_MALI_COPY_JOB_OFF;
	bool fullLinear = sx == 0u && sy == 0u && dx == 0u && dy == 0u &&
	    w == J3_MALI_FB_WIDTH && h == J3_MALI_FB_HEIGHT &&
	    s->bytesPerRow == J3_MALI_FB_STRIDE;

	bzero(ubo, J3_MALI_RECT_UBO_BYTES);
	*(uint64_t *)(ubo + 0) = sourceVA;
	*(uint64_t *)(ubo + 8) = J3_MALI_COPY_DST_VA;
	if (fullLinear) {
		*(uint32_t *)(ubo + 16) = J3_MALI_COPY_WORDS;
		*(uint64_t *)(job + 120) =
		    J3_MALI_COPY_RES_VA + J3_MALI_FULL_RSD_OFF;
		groups = 14400u;
	} else {
		*(uint32_t *)(ubo + 16) = s->bytesPerRow;
		*(uint32_t *)(ubo + 20) = J3_MALI_FB_STRIDE;
		*(uint32_t *)(ubo + 24) = sx;
		*(uint32_t *)(ubo + 28) = sy;
		*(uint32_t *)(ubo + 32) = dx;
		*(uint32_t *)(ubo + 36) = dy;
		*(uint32_t *)(ubo + 40) = w;
		*(uint32_t *)(ubo + 44) = h;
		*(uint64_t *)(job + 120) =
		    J3_MALI_COPY_RES_VA + J3_MALI_RECT_RSD_OFF;
	}
	if (!j3_mali_pack_groups(job + J3_MALI_JOB_INVOCATION_OFF, groups)) {
		return J3_MALI_PRESENT_FAIL;
	}

	j3_mali_clean_source_rect(c, src, s, sx, sy, w, h);
	flush_dcache64((addr64_t)(uintptr_t)ubo, J3_MALI_RECT_UBO_BYTES, FALSE);
	/* 32..127 covers dynamic INVOCATION and the RSD pointer at job+120. */
	flush_dcache64((addr64_t)(uintptr_t)(job + J3_MALI_JOB_INVOCATION_OFF),
	    96u, FALSE);
	__asm__ volatile("dsb sy" ::: "memory");

	j3_gpu_write(mali, J3_MALI_JOB_IRQ_CLEAR,
	    J3_MALI_JOB_DONE1 | J3_MALI_JOB_FAIL1);
	j3_gpu_write(mali, J3_MALI_MMU_IRQ_CLEAR,
	    J3_MALI_MMU_PAGE_FAULT0 | J3_MALI_MMU_BUS_ERROR0);
	uint64_t jobVA = J3_MALI_COPY_RES_VA + J3_MALI_COPY_JOB_OFF;
	j3_gpu_write(mali, J3_MALI_JS1_HEAD_NEXT_LO, (uint32_t)jobVA);
	j3_gpu_write(mali, J3_MALI_JS1_HEAD_NEXT_HI, (uint32_t)(jobVA >> 32));
	uint32_t shader = j3_gpu_read(mali, J3_MALI_SHADER_READY);
	j3_gpu_write(mali, J3_MALI_JS1_AFFINITY_NEXT_LO, shader ? shader : 1u);
	j3_gpu_write(mali, J3_MALI_JS1_AFFINITY_NEXT_HI, 0);
	j3_gpu_write(mali, J3_MALI_JS1_CONFIG_NEXT, J3_MALI_JS_CFG);
	j3_gpu_write(mali, J3_MALI_JS1_COMMAND_NEXT, J3_MALI_JS_START);
	c->inFlight = true;
	c->submittedFrames++;
	c->gpuBytes += pixels64 * 4ULL;
	if (fullLinear) {
		c->gpuFull++;
	} else {
		c->gpuRect++;
	}

	if (async) {
		return J3_MALI_PRESENT_SUBMITTED;
	}
	return j3_mali_compute_poll(mali, true);
}

"""
replace_span(
    "static int\nj3_mali_compute_poll(vm_offset_t mali, bool wait)\n",
    "/*\n * Credit-efficient validation ladder.",
    new_present,
    "poll/presenter",
)

replace_once(
    "\tuint32_t mask = get32(rec, 0x104);\n",
    "\tuint32_t mask = get32(rec, 0x104);\n#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)\n\tj3_mali_swap_count++;\n#endif\n",
    "swap counter",
)

swap_block = r"""		if (src != 0 && bpe == 4) {
#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
			bool singleLayer = mask != 0 && (mask & (mask - 1u)) == 0;
			int present = j3_mali_present_rect(s, src,
			    sx, sy, dx, dy, w, h, singleLayer);
			if (present == J3_MALI_PRESENT_FAIL) {
				j3_mali_cpu_fallbacks++;
				for (int32_t y = 0; y < h; y++) {
					memcpy((void *)(fPixels + (uint64_t)(dy + y) * fRowBytes + (uint64_t)dx * 4),
					    (const void *)(src + s->offset + (uint64_t)(sy + y) * s->bytesPerRow + (uint64_t)sx * 4),
					    (size_t)w * 4);
				}
			}
#else
			for (int32_t y = 0; y < h; y++) {
				memcpy((void *)(fPixels + (uint64_t)(dy + y) * fRowBytes + (uint64_t)dx * 4),
				    (const void *)(src + s->offset + (uint64_t)(sy + y) * s->bytesPerRow + (uint64_t)sx * 4),
				    (size_t)w * 4);
			}
#endif
		}"""
pixel_start = "\t\tif (src != 0 && bpe == 4) {\n"
pixel_end = "\n\t\ts->release();"
pixel_i = text.find(pixel_start)
if pixel_i < 0:
    raise SystemExit("J3XNU099 swap pixel path: start anchor not found")
pixel_j = text.find(pixel_end, pixel_i)
if pixel_j < 0:
    raise SystemExit("J3XNU099 swap pixel path: end anchor not found")
if "j3_mali_cpu_fallbacks++;" not in text[pixel_i:pixel_j]:
    raise SystemExit("J3XNU099 swap pixel path: expected J3XNU098 body not found")
text = text[:pixel_i] + swap_block + text[pixel_j:]

swap_end_old = """\t\ts->release();
\t}
}

bool
IOMobileFramebufferUserClient::initWithTask"""
swap_end_new = """\t\ts->release();
\t}
#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
\tif (j3_mali_swap_count <= 8ULL || (j3_mali_swap_count % 120ULL) == 0ULL) {
\t\tstruct j3_mali_compute_ctx *c = &j3_mali_compute;
\t\tIOLog("J3 GPU: rect stats swap=%llu gpu_rect=%llu gpu_full=%llu gpu_busy=%llu cpu_copy=%llu clean_bytes=%llu gpu_bytes=%llu submit=%llu done=%llu hit=%llu remap=%llu\\n",
\t\t    j3_mali_swap_count, c->gpuRect, c->gpuFull, c->busyFrames,
\t\t    j3_mali_cpu_fallbacks, c->cleanBytes, c->gpuBytes,
\t\t    c->submittedFrames, c->completedFrames, c->sourceHits,
\t\t    c->sourceRemaps);
\t}
#endif
}

bool
IOMobileFramebufferUserClient::initWithTask"""
if swap_end_old not in text:
    marker = "\t\ts->release();\n\t}\n"
    pos = text.find(marker)
    if pos < 0:
        raise SystemExit("J3XNU099 swap stats: loop end anchor not found")
    tail = text.find("\nbool\nIOMobileFramebufferUserClient::initWithTask", pos)
    if tail < 0:
        raise SystemExit("J3XNU099 swap stats: user-client anchor not found")
    text = text[:pos] + swap_end_new[:-len("bool\nIOMobileFramebufferUserClient::initWithTask")] + text[tail+1:]
else:
    text = text.replace(swap_end_old, swap_end_new, 1)

replace_once(
    '#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)\n\tuint32_t hz = 60;\n\tPE_parse_boot_argn("j3fb_hz", &hz, sizeof(hz));',
    '#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)\n\tuint32_t hz = 30;\n\tPE_parse_boot_argn("j3fb_hz", &hz, sizeof(hz));',
    "30 Hz default",
)

stale = [
    "j3_mali_present_surface(",
    "full-frame compute ARMED JS1 shader=112B",
    "async present ARMED slots=",
    "present stats submit=",
]
for marker in stale:
    if marker in text:
        raise SystemExit(f"J3XNU099 stale marker remains: {marker}")

required = [
    "static const uint8_t j3_mali_rect_shader[592]",
    "J3 GPU: dual compute ARMED JS1 full=112B rect=592B",
    "j3_mali_pack_groups",
    "j3_mali_clean_source_rect",
    "j3_mali_present_rect",
    "J3 GPU: rect stats swap=%llu gpu_rect=%llu gpu_full=%llu gpu_busy=%llu cpu_copy=%llu clean_bytes=%llu gpu_bytes=%llu",
    "uint32_t hz = 30;",
]
for marker in required:
    if marker not in text:
        raise SystemExit(f"J3XNU099 required marker missing: {marker}")

path.write_text(text)
print("J3XNU099 dirty-rectangle Mali transform: PASS")
