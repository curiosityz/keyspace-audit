/* ============================================================================
 * yasmarang.cl  --  Generic Yasmarang keystream kernel + bit-exactness selftest.
 *
 * This is deliberately ONLY the generator and a self-test. It generates the
 * first K output words of a Yasmarang stream for each initial state, so a host
 * can prove the GPU implementation is bit-for-bit identical to a CPU reference,
 * and can benchmark raw stream throughput.
 *
 * It does NOT contain — by design — any of the following, which are what would
 * turn a PRNG kernel into a wallet-recovery weapon and are documented in
 * SECURITY.md as out of scope for this project:
 *   - any device/product-specific boot or seeding model,
 *   - any BIP32/BIP39/BIP84 or other key-derivation path,
 *   - any hashing-to-address or hash160 membership test against a target set.
 *
 * The methodological point this file makes is the one worth keeping: an
 * optimised kernel is only trustworthy once selftest() proves it matches a
 * simple reference. Numbers from an unverified kernel are worthless.
 * ==========================================================================*/

typedef struct { uint pad, n, d, dat; } yas_t;   /* dat held in uint, masked 0xFF */

static uint yas_step(yas_t *s) {
  uint pad = s->pad, n = s->n, d = s->d, dat = s->dat;
  pad = pad + dat + (d * n);                 /* uint wraps mod 2^32 */
  pad = (pad << 3) + (pad >> 29);
  n   = pad | 2u;
  d   = d ^ ((pad << 31) + (pad >> 1));
  dat = (dat ^ (pad & 0xFFu) ^ ((d >> 8) & 0xFFu) ^ 1u) & 0xFFu;
  s->pad = pad; s->n = n; s->d = d; s->dat = dat;
  return pad ^ (d << 5) ^ (pad >> 18) ^ (dat << 1);
}

/* Emit the first K output words for each initial state (pad0,n0,d0,dat0).
 * out is laid out row-major: out[gid*K + j] is word j of stream gid.
 * The host compares this, element for element, against its CPU reference. */
__kernel void selftest(const uint K,
                       __global const uint *pad0,
                       __global const uint *n0,
                       __global const uint *d0,
                       __global const uint *dat0,
                       __global uint *out) {
  int gid = get_global_id(0);
  yas_t s;
  s.pad = pad0[gid];
  s.n   = n0[gid];
  s.d   = d0[gid];
  s.dat = dat0[gid] & 0xFFu;
  for (uint j = 0; j < K; j++) out[gid * K + j] = yas_step(&s);
}

/* Throughput benchmark: advance each lane `iters` steps and XOR-fold the output
 * into a sink so the compiler cannot elide the work. Measures generator
 * words/second only.
 *
 * Lanes are seeded OFF the device's seeding manifold. Yasmarang's output is a
 * function of the whole (pad,n,d,dat) tuple, so what makes these lanes useless
 * for wallet recovery is that (n,d,dat) are pinned to NON-stock values: streams
 * from non-default (n,d) correspond to no reachable device state. The per-lane
 * pad decorrelation is only to stop the compiler collapsing identical work — it
 * is an invertible hash and is NOT itself a safety barrier. Together this keeps
 * the kernel a pure throughput test and specifically NOT a contiguous pad-sweep
 * pinned to stock defaults, which is the enumeration axis a wallet attack uses.
 * Throughput is seed-independent, so nothing is lost by refusing to lay it down.
 * The three hex constants below are arbitrary nothing-up-my-sleeve decorrelation
 * values (golden ratio; two generic xorshift-family words), not device secrets. */
__kernel void benchmark(const uint iters,
                        const uint salt,
                        __global uint *sink) {
  int gid = get_global_id(0);
  yas_t s;
  s.pad = salt ^ ((uint)gid * 0x9E3779B9u);   /* decorrelate lanes (invertible) */
  s.n = 0x51ED270Bu;                           /* non-stock: off the seed manifold */
  s.d = 0x2545F491u;                           /* non-stock: off the seed manifold */
  s.dat = (uint)(gid & 0xFFu);
  uint acc = 0u;
  for (uint i = 0; i < iters; i++) acc ^= yas_step(&s);
  sink[gid] = acc;
}
