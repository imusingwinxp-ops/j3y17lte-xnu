/*
 * J3XNU097 host-side Midgard T720 copy-kernel generator.
 * Builds a 1D compute shader: dst[i] = src[i], one 32-bit word per invocation.
 * This runs only on the CI host and emits bytes/metadata for the XNU port.
 */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "compiler/glsl_types.h"
#include "compiler/nir/nir_builder.h"
#include "panfrost/compiler/pan_compiler.h"
#include "util/u_dynarray.h"

static int write_binary(const char *path, const void *data, size_t size)
{
   FILE *f = fopen(path, "wb");
   if (!f)
      return -1;
   size_t n = fwrite(data, 1, size, f);
   fclose(f);
   return n == size ? 0 : -1;
}

int main(int argc, char **argv)
{
   if (argc != 3) {
      fprintf(stderr, "usage: %s OUT.bin OUT.txt\n", argv[0]);
      return 2;
   }

   const uint64_t gpu_id = 0x720;
   const unsigned arch = 4;

   glsl_type_singleton_init_or_ref();

   const nir_shader_compiler_options *opts =
      pan_get_nir_shader_compiler_options(arch, false);

   nir_builder b =
      nir_builder_init_simple_shader(MESA_SHADER_COMPUTE, opts,
                                     "j3_t720_present_copy");

   b.shader->info.workgroup_size[0] = 64;
   b.shader->info.workgroup_size[1] = 1;
   b.shader->info.workgroup_size[2] = 1;
   b.shader->info.num_ubos = 1;
   b.shader->info.first_ubo_is_default_ubo = true;

   nir_def *zero = nir_imm_int(&b, 0);
   nir_def *args = nir_load_ubo(&b, 4, 32, zero, zero,
                                .align_mul = 16,
                                .align_offset = 0,
                                .range_base = 0,
                                .range = 16);

   nir_def *src =
      nir_pack_64_2x32(&b, nir_channels(&b, args, 0x3));
   nir_def *dst =
      nir_pack_64_2x32(&b, nir_channels(&b, args, 0xc));

   nir_def *gid =
      nir_channel(&b, nir_load_global_invocation_id(&b, 32), 0);
   nir_def *byte_off =
      nir_u2u64(&b, nir_imul_imm(&b, gid, 4));

   nir_def *value =
      nir_load_global(&b, 1, 32, nir_iadd(&b, src, byte_off),
                      .align_mul = 4, .align_offset = 0);
   nir_store_global(&b, value, nir_iadd(&b, dst, byte_off),
                    .align_mul = 4, .align_offset = 0);

   nir_shader_gather_info(b.shader, nir_shader_get_entrypoint(b.shader));
   nir_validate_shader(b.shader, "J3 T720 copy kernel before Panfrost lowering");

   struct pan_compile_inputs inputs = {
      .gpu_id = gpu_id,
      .gpu_variant = 0,
   };

   pan_preprocess_nir(b.shader, inputs.gpu_id);

   struct pan_shader_info info = {0};
   pan_postprocess_nir(b.shader, &inputs, &info);

   /* Exactly UBO0 is CPU-visible and eligible for Midgard register promotion. */
   inputs.pushable_ubos = 1u;

   struct util_dynarray binary = UTIL_DYNARRAY_INIT;
   pan_shader_compile(b.shader, &inputs, &binary, &info);

   if (!binary.size) {
      fprintf(stderr, "Midgard compiler returned empty binary\n");
      return 3;
   }

   if (write_binary(argv[1], binary.data, binary.size)) {
      fprintf(stderr, "failed writing %s\n", argv[1]);
      return 4;
   }

   FILE *meta = fopen(argv[2], "w");
   if (!meta) {
      fprintf(stderr, "failed opening %s\n", argv[2]);
      return 5;
   }

   fprintf(meta, "J3XNU097_T720_COPY_KERNEL\n");
   fprintf(meta, "GPU_ID=0x%llx\n", (unsigned long long)gpu_id);
   fprintf(meta, "ARCH=%u\n", arch);
   fprintf(meta, "LOCAL_SIZE=64,1,1\n");
   fprintf(meta, "FRAME_WORDS=921600\n");
   fprintf(meta, "WORKGROUPS=14400,1,1\n");
   fprintf(meta, "BINARY_SIZE=%zu\n", binary.size);
   fprintf(meta, "FIRST_TAG=%u\n", info.midgard.first_tag);
   fprintf(meta, "WORK_REG_COUNT=%u\n", info.work_reg_count);
   fprintf(meta, "TLS_SIZE=%u\n", info.tls_size);
   fprintf(meta, "WLS_SIZE=%u\n", info.wls_size);
   fprintf(meta, "PUSH_COUNT=%u\n", info.push.count);
   fprintf(meta, "UBO_COUNT=%u\n", info.ubo_count);
   fprintf(meta, "WRITES_GLOBAL=%u\n", info.writes_global ? 1 : 0);
   fprintf(meta, "CONTAINS_BARRIER=%u\n", info.contains_barrier ? 1 : 0);
   for (unsigned i = 0; i < info.push.count; ++i) {
      fprintf(meta, "PUSH_%u=ubo:%u,offset:%u\n", i,
              info.push.words[i].ubo, info.push.words[i].offset);
   }

   fprintf(meta, "\n=== MIDGARD DISASSEMBLY ===\n");
   pan_disassemble(meta, binary.data, binary.size, gpu_id, true);
   fclose(meta);

   util_dynarray_fini(&binary);
   glsl_type_singleton_decref();

   return 0;
}
