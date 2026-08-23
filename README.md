# keyspace-audit

**Measure the *realized* entropy of a seed generator — and catch keyspace
collapse before an attacker does.**

A seed generator's *nominal* keyspace is how many seeds you could feed it. Its
*realized* keyspace is how many distinct outputs those seeds actually produce.
When a seeding path quietly funnels a wide input into a narrow effective state,
the two diverge — and it is the realized keyspace, not the advertised one, that
gets searched. This toolkit measures the gap.

It is built around one real, worked example: a hardware-wallet PRNG whose seed
space collapsed from a nominal 32 bits to roughly 2²³ reachable seeds. This
repository ships the **reusable, defensive** parts of that analysis — the PRNG
reference, the whitening proof, the black-box keyspace auditor, and a
generator-only GPU self-test. It deliberately omits the three pieces that would
turn those into a wallet attack: the device boot/seeding model, the key-
derivation path, and the address-matching step. See [`SECURITY.md`](SECURITY.md).

## What's here

| Piece | What it does |
|---|---|
| `keyspace_audit.yasmarang` | Reference implementation of the Yasmarang PRNG (a published non-cryptographic generator), used as the worked example. |
| `keyspace_audit.yasmarang_vec` | A vectorised (numpy) twin, cross-checked bit-for-bit against the reference. The self-test *is* the point. |
| `keyspace_audit.entropy` | The auditor: exact realized-keyspace counting over a seed set, plus an occupancy/collision estimator for spaces too large to enumerate. Treats any generator as a black box `gen(seed) -> bytes`. |
| `keyspace_audit.whitening` | Proof and empirical check that XORing a **fixed** keystream into a stream adds exactly zero entropy. |
| `opencl/` | A generic Yasmarang keystream kernel with a GPU↔CPU bit-exactness self-test and a throughput benchmark. No boot model, no derivation, no matching. |

## Install

```bash
pip install -e .            # numpy only
pip install -e ".[gpu]"     # + pyopencl, for the OpenCL self-test/benchmark
pip install -e ".[dev]"     # + pytest
```

## Use it

```bash
keyspace-audit kat          # prove the vectorised generator bit-exact
keyspace-audit whitening    # show fixed-keystream XOR adds zero entropy
keyspace-audit collapse --nominal-bits 20 --effective-bits 10
```

As a library, on your own generator:

```python
from keyspace_audit import realized_keyspace

def my_gen(seed: int) -> bytes:
    ...  # seed your RNG, return >= 16 output bytes

stats = realized_keyspace(my_gen, range(1 << 20))
print(stats["realized_bits"], "effective bits out of", stats["nominal_bits"])
print(stats["collapse_factor"], "x collapse")
```

The [`examples/`](examples) directory has two runnable scripts: the zero-entropy
whitening demonstration, and a synthetic generator whose 20-bit seed collapses to
10 effective bits, caught both exactly and by sampling.

## The two ideas worth taking away

1. **Whitening is not entropy.** A second generator seeded from *fixed public
   constants* and XORed over a weak first generator scrambles the output's
   appearance and adds nothing an attacker must search — the fixed XOR is a
   bijection on streams. (The looser claim, that *any* two non-crypto generators
   XORed give one generator's worth of unpredictability, is false; `whitening.py`
   is careful about which statement is which.)

2. **Never trust an unverified fast path.** Every optimised implementation here —
   numpy twin, OpenCL kernel — is gated behind a self-test that proves it matches
   a trivial reference on random inputs. A keyspace count from an unverified
   kernel is worthless; a one-bit shift error runs fast and is wrong on every
   input.

## Background & citation

This toolkit is the general-purpose distillate of a specific responsible-
disclosure investigation into a weak hardware-wallet seed generator. The public
write-ups of that investigation (mechanism, keyspace-collapse analysis,
reproduction methodology, and on-chain forensics) are the place to read the full
story; this repository is the part meant to be reused on other generators. See
[`CITATION.cff`](CITATION.cff) to cite the software.

## License

MIT — see [`LICENSE`](LICENSE).
