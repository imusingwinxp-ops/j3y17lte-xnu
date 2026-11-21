#!/usr/bin/env python3
from pathlib import Path
import re

FB = Path("iokit/Kernel/arm/SweetFramebuffer.cpp")
SH = Path("iokit/Kernel/arm/SweetSurface.h")
SC = Path("iokit/Kernel/arm/SweetSurface.cpp")

fb = FB.read_text()
sh = SH.read_text()
sc = SC.read_text()

UPSCALE_SHADER_HEX = "5510204830000000300000000000000095a840200138c002800a080880032800990082080060007f58025550a503a20401d80a50000055550000000000000000a900080200e01880bc240010f0020000200c0000000000000000000000000000aa0022004063188014822a0020039d020000a00c000000000000000000000000feff7f4f0000000000000000000000009a00820000601a0358025550a503460401d800000000000000000000000000000000000000000000000000000000000099008200006000035847f7eace0f40140158000000000000000000000000000089008200000000005847a2e8cef0581409d80000000000000000000000000000980088000000000446040dd8a3240d1899008a000060387c180046827fa0aa037b3401d8c1040dd8000000000000000099008a0000e0387c180040822a10a0037b3401d8c1040558000000000000000059008a0000e0007c180040822a10a003a3240dd8c1040558000000000000000095a8000100384002801a821c800318005900a20000600003000058822aa0aa0346020000a00340340598000000000000a5a8000100384001801a0412800320005a00aa00016000e45803190440822a00a0036e2410186e020000a03058040d580300000000000000000000000000000095a8818000380001801a100080031c009900a8000100010001004014099840020000a0034034055800000000000000005900aa00206000e4386b186858822aa0aa036e04201840020000a0037b04095855ac9a8900380000300000000000000055ac7b280138800080a803401400000085c8e0014803000030000000000000005800800000e84024405800000000000085c8e001480300003000000000000000580088000000186840240d187b04015885c8e0014803000030000000000000005800800000e84004405800000000000015c8e00148030000300000000000000000000000000000000000000000000000"

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"J3XNU100 {label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)

def c_array(name, expected, hex_string):
    data = bytes.fromhex(hex_string)
    if len(data) != expected:
        raise SystemExit(f"J3XNU100 {name}: byte count {len(data)} != {expected}")
    rows = []
    for i in range(0, len(data), 16):
        rows.append("\t" + ",".join(f"0x{b:02x}" for b in data[i:i+16]))
    return f"static const uint8_t {name}[{expected}] = {{\n" + ",\n".join(rows) + "\n};\n"

# -------------------------------------------------------------------------
# IOSurface: create a real low-resolution default render target.
# -------------------------------------------------------------------------
decl = """SweetSurface *sweet_surface_create_physical(uint64_t phys, uint32_t width,
    uint32_t height, uint32_t bytesPerRow, uint32_t pixelFormat);
"""
decl_new = decl + """
/* J3XNU100: kernel-owned CPU-render target, published like a normal IOSurface. */
SweetSurface *sweet_surface_create_buffer(uint32_t width, uint32_t height,
    uint32_t bytesPerRow, uint32_t pixelFormat);
"""
sh = replace_once(sh, decl, decl_new, "buffer-surface header declaration")

port_marker = """mach_port_name_t
sweet_surface_port_in_task(SweetSurface *s, task_t task)
"""
if port_marker not in sc:
    raise SystemExit("J3XNU100 buffer-surface insertion anchor not found")

buffer_fn = r"""SweetSurface *
sweet_surface_create_buffer(uint32_t width, uint32_t height,
    uint32_t bytesPerRow, uint32_t pixelFormat)
{
	if (width == 0 || height == 0 || bytesPerRow < width * 4u) {
		return NULL;
	}
	uint64_t bytes64 = (uint64_t)bytesPerRow * height;
	if (bytes64 == 0 || bytes64 > SWEET_SURFACE_MAX_ALLOC) {
		return NULL;
	}

	SweetSurface *s = sweet_surface_alloc();
	if (s == NULL) {
		return NULL;
	}
	s->width = width;
	s->height = height;
	s->bytesPerRow = bytesPerRow;
	s->bytesPerElement = 4;
	s->elementWidth = s->elementHeight = 1;
	s->pixelFormat = pixelFormat;
	s->allocSize = (uint32_t)round_page(bytes64);

	uint64_t old = (uint64_t)OSAddAtomic64(s->allocSize,
	    (volatile SInt64 *)&sweet_surface_wired);
	if (old + s->allocSize > SWEET_SURFACE_WIRED_MAX) {
		OSAddAtomic64(-(SInt64)s->allocSize,
		    (volatile SInt64 *)&sweet_surface_wired);
		s->release();
		return NULL;
	}

	IOBufferMemoryDescriptor *mem = IOBufferMemoryDescriptor::inTaskWithOptions(
	    kernel_task, kIODirectionInOut | kIOMemoryKernelUserShared,
	    s->allocSize, page_size);
	if (mem == NULL) {
		OSAddAtomic64(-(SInt64)s->allocSize,
		    (volatile SInt64 *)&sweet_surface_wired);
		s->release();
		return NULL;
	}

	bzero(mem->getBytesNoCopy(), s->allocSize);
	s->memory = mem;
	s->mapCache = kIOMapDefaultCache;
	if (!sweet_surface_publish(s)) {
		s->release();
		return NULL;
	}
	return s;
}

"""
sc = sc.replace(port_marker, buffer_fn + port_marker, 1)

# -------------------------------------------------------------------------
# Exact compiler-produced Midgard-v4 2x shader from the free capture.
# -------------------------------------------------------------------------
m = re.search(
    r"static const uint8_t j3_mali_rect_shader\[592\] = \{.*?\n\};\n",
    fb, re.S)
if not m:
    raise SystemExit("J3XNU100 captured shader replacement anchor not found")
fb = fb[:m.start()] + c_array("j3_mali_rect_shader", 720, UPSCALE_SHADER_HEX) + fb[m.end():]

# The 720-byte program runs from 0x100..0x3cf. Move following resources.
offsets = {
    "#define J3_MALI_RECT_RSD_OFF             0x380u":
        "#define J3_MALI_RECT_RSD_OFF             0x400u",
    "#define J3_MALI_COPY_TLS_OFF             0x3c0u":
        "#define J3_MALI_COPY_TLS_OFF             0x440u",
    "#define J3_MALI_COPY_UBO_DESC_OFF        0x400u":
        "#define J3_MALI_COPY_UBO_DESC_OFF        0x460u",
    "#define J3_MALI_COPY_UBO_DATA_OFF        0x420u":
        "#define J3_MALI_COPY_UBO_DATA_OFF        0x480u",
    "#define J3_MALI_COPY_JOB_OFF             0x480u":
        "#define J3_MALI_COPY_JOB_OFF             0x4c0u",
}
for old, new in offsets.items():
    fb = replace_once(fb, old, new, "resource-layout " + old.split()[-1])

fb = replace_once(
    fb,
    "#define J3_MALI_FB_STRIDE                2880u\n",
    """#define J3_MALI_FB_STRIDE                2880u
#define J3_MALI_RENDER_WIDTH             360u
#define J3_MALI_RENDER_HEIGHT            640u
#define J3_MALI_RENDER_STRIDE            1472u
#define J3_MALI_RENDER_PIXELS            230400u
#define J3_MALI_UPSCALE_GROUPS           3600u
""",
    "render constants",
)

fb = replace_once(
    fb,
    "J3 GPU: dual compute ARMED JS1 full=112B rect=592B slots=%u ptpages=%u\\n",
    "J3 GPU: upscale2x ARMED JS1 shader=720B render=360x640 slots=%u ptpages=%u\\n",
    "armed log",
)

# Never select the old 720x1280 linear copy shader in half-resolution mode.
full_re = re.compile(
    r"\tbool fullLinear = sx == 0u && sy == 0u && dx == 0u && dy == 0u &&\n"
    r"\t    w == J3_MALI_FB_WIDTH && h == J3_MALI_FB_HEIGHT &&\n"
    r"\t    s->bytesPerRow == J3_MALI_FB_STRIDE;")
fb, n = full_re.subn(
    "\tbool fullLinear = false; /* J3XNU100: every J3 present uses the 2x shader. */",
    fb, count=1)
if n != 1:
    raise SystemExit(f"J3XNU100 fullLinear anchor: expected 1, found {n}")

fb = fb.replace("groups > 14400u", "groups > J3_MALI_UPSCALE_GROUPS")
fb = replace_once(
    fb,
    "if (!pixels64 || pixels64 > J3_MALI_COPY_WORDS) {",
    "if (!pixels64 || pixels64 > J3_MALI_RENDER_PIXELS) {",
    "render pixel cap",
)

# -------------------------------------------------------------------------
# AppleCLCD: keep physical scanout 720x1280, expose/render 360x640.
# -------------------------------------------------------------------------
surface_field = "SweetSurface *fSurface;         /* the panel memory as an IOSurface */"
if surface_field not in fb:
    # 0061 and later may have only preserved spacing/comment text.
    m = re.search(r"\tSweetSurface \*fSurface;[^\n]*", fb)
    if not m:
        raise SystemExit("J3XNU100 fSurface field anchor not found")
    fb = fb[:m.start()] + (
        "\tSweetSurface *fSurface;         /* default render IOSurface */\n"
        "#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)\n"
        "\tSweetSurface *fScanoutSurface;  /* physical 720x1280 DECON memory */\n"
        "#endif"
    ) + fb[m.end():]
else:
    fb = replace_once(
        fb, surface_field,
        """SweetSurface *fSurface;         /* default render IOSurface */
#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
	SweetSurface *fScanoutSurface;  /* physical 720x1280 DECON memory */
#endif""",
        "scanout surface field",
    )

logical_old = """	fLogicalW = fWidth;
	fLogicalH = fHeight;
#if !defined(ARM64_BOARD_CONFIG_J3Y17LTE)
	if (!native && fWidth <= SWEET_FB_LOGICAL_W && fHeight <= SWEET_FB_LOGICAL_H) {
		fLogicalW = SWEET_FB_LOGICAL_W;
		fLogicalH = SWEET_FB_LOGICAL_H;
	}
#endif
	fOffX = (int32_t)(fLogicalW - fWidth) / 2;
	fOffY = (int32_t)(fLogicalH - fHeight) / 2;
"""
logical_new = """#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
	/* Same 360x640 point layout as 720x1280 @2x, but only 1/4 the raster work. */
	fLogicalW = 360;
	fLogicalH = 640;
	fOffX = 0;
	fOffY = 0;
#else
	fLogicalW = fWidth;
	fLogicalH = fHeight;
	if (!native && fWidth <= SWEET_FB_LOGICAL_W && fHeight <= SWEET_FB_LOGICAL_H) {
		fLogicalW = SWEET_FB_LOGICAL_W;
		fLogicalH = SWEET_FB_LOGICAL_H;
	}
	fOffX = (int32_t)(fLogicalW - fWidth) / 2;
	fOffY = (int32_t)(fLogicalH - fHeight) / 2;
#endif
"""
fb = replace_once(fb, logical_old, logical_new, "logical render size")

create_old = """	fSurface = sweet_surface_create_physical(fPhys, fWidth, fHeight, fRowBytes, SWEET_FB_FORMAT_BGRA);
	fPixels = fSurface != NULL ? fSurface->kernelAddress() : 0;
"""
create_new = """#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
	fScanoutSurface = sweet_surface_create_physical(
	    fPhys, fWidth, fHeight, fRowBytes, SWEET_FB_FORMAT_BGRA);
	fSurface = sweet_surface_create_buffer(
	    J3_MALI_RENDER_WIDTH, J3_MALI_RENDER_HEIGHT,
	    J3_MALI_RENDER_STRIDE, SWEET_FB_FORMAT_BGRA);
	fPixels = fScanoutSurface != NULL ? fScanoutSurface->kernelAddress() : 0;
#else
	fSurface = sweet_surface_create_physical(fPhys, fWidth, fHeight, fRowBytes, SWEET_FB_FORMAT_BGRA);
	fPixels = fSurface != NULL ? fSurface->kernelAddress() : 0;
#endif
"""
fb = replace_once(fb, create_old, create_new, "default/render surface creation")

fb = replace_once(
    fb,
    "if (fLock == NULL || fClients == NULL || fPixels == 0 || fWorkLoop == NULL) {",
    "if (fLock == NULL || fClients == NULL || fSurface == NULL || fPixels == 0 || fWorkLoop == NULL) {",
    "setup validation",
)

cleanup = "		OSSafeReleaseNULL(fSurface);    /* stays published: also held by the table */\n"
cleanup_new = cleanup + """#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
		OSSafeReleaseNULL(fScanoutSurface);
#endif
"""
fb = replace_once(fb, cleanup, cleanup_new, "scanout cleanup")

# The J3 default surface is now the low-res render target, so it MUST be presented.
skip_old = """		if (s == NULL || s == fSurface) {
			OSSafeReleaseNULL(s);
			continue;
		}
"""
skip_new = """#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
		if (s == NULL) {
#else
		if (s == NULL || s == fSurface) {
#endif
			OSSafeReleaseNULL(s);
			continue;
		}
"""
fb = replace_once(fb, skip_old, skip_new, "default-surface present")

clip_old = """		if (w > (int32_t)fWidth - dx) {
			w = (int32_t)fWidth - dx;
		}
		if (h > (int32_t)fHeight - dy) {
			h = (int32_t)fHeight - dy;
		}
"""
clip_new = """#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
		if (w > (int32_t)fLogicalW - dx) {
			w = (int32_t)fLogicalW - dx;
		}
		if (h > (int32_t)fLogicalH - dy) {
			h = (int32_t)fLogicalH - dy;
		}
#else
		if (w > (int32_t)fWidth - dx) {
			w = (int32_t)fWidth - dx;
		}
		if (h > (int32_t)fHeight - dy) {
			h = (int32_t)fHeight - dy;
		}
#endif
"""
fb = replace_once(fb, clip_old, clip_new, "logical destination clipping")

# CPU fallback remains correct if Mali faults: nearest-neighbour 2x in software.
cpu_old = """				j3_mali_cpu_fallbacks++;
				for (int32_t y = 0; y < h; y++) {
					memcpy((void *)(fPixels + (uint64_t)(dy + y) * fRowBytes + (uint64_t)dx * 4),
					    (const void *)(src + s->offset + (uint64_t)(sy + y) * s->bytesPerRow + (uint64_t)sx * 4),
					    (size_t)w * 4);
				}
"""
cpu_new = """				j3_mali_cpu_fallbacks++;
				for (int32_t y = 0; y < h; y++) {
					const uint32_t *sp = (const uint32_t *)(src + s->offset +
					    (uint64_t)(sy + y) * s->bytesPerRow + (uint64_t)sx * 4);
					uint32_t *d0 = (uint32_t *)(fPixels +
					    (uint64_t)((dy + y) * 2) * fRowBytes + (uint64_t)(dx * 2) * 4);
					uint32_t *d1 = (uint32_t *)((uintptr_t)d0 + fRowBytes);
					for (int32_t x = 0; x < w; x++) {
						uint32_t p = sp[x];
						d0[x * 2] = p;
						d0[x * 2 + 1] = p;
						d1[x * 2] = p;
						d1[x * 2 + 1] = p;
					}
				}
"""
fb = replace_once(fb, cpu_old, cpu_new, "2x CPU fallback")

# Strong device-visible identity for the one paid shot.
# Do not exact-match C's "\\n" inside a normal Python string: that escape
# becomes a real newline at runtime. Locate the unique AppleCLCD startup log
# structurally and insert immediately after its terminating semicolon.
startup_prefix = '\tIOLog("SWEET FB: AppleCLCD '
startup_i = fb.find(startup_prefix)
if startup_i < 0:
    raise SystemExit("J3XNU100 halfres startup log: AppleCLCD IOLog not found")
if fb.find(startup_prefix, startup_i + 1) >= 0:
    raise SystemExit("J3XNU100 halfres startup log: AppleCLCD IOLog not unique")
startup_end = fb.find(";\n", startup_i)
if startup_end < 0:
    raise SystemExit("J3XNU100 halfres startup log: terminator not found")
startup_end += 2
startup_insert = r"""#if defined(ARM64_BOARD_CONFIG_J3Y17LTE)
	IOLog("J3 FB: HALFRES 360x640 scale1 -> Mali 2x -> 720x1280 scanout, default surface %u\n",
	    fSurface->id);
#endif
"""
fb = fb[:startup_end] + startup_insert + fb[startup_end:]

required = [
    "static const uint8_t j3_mali_rect_shader[720]",
    "#define J3_MALI_RENDER_WIDTH             360u",
    "#define J3_MALI_RENDER_HEIGHT            640u",
    "#define J3_MALI_UPSCALE_GROUPS           3600u",
    "SweetSurface *fScanoutSurface;",
    "sweet_surface_create_buffer(",
    "fLogicalW = 360;",
    "fLogicalH = 640;",
    "bool fullLinear = false;",
    "J3 GPU: upscale2x ARMED JS1 shader=720B render=360x640",
    "J3 FB: HALFRES 360x640 scale1 -> Mali 2x -> 720x1280 scanout",
]
for marker in required:
    if marker not in fb + sh + sc:
        raise SystemExit(f"J3XNU100 required marker missing: {marker}")

FB.write_text(fb)
SH.write_text(sh)
SC.write_text(sc)
print("J3XNU100 half-resolution + Mali 2x upscale transform: PASS")
