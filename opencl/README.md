# OpenCL: prove the generator, then measure it

Two kernels in `yasmarang.cl`, driven by `host.py`:

- **`selftest`** — generates the first *K* output words of a Yasmarang stream for
  many initial states and hands them back so the host can assert every word is
  bit-for-bit identical to the CPU reference in `keyspace_audit.yasmarang`.
- **`benchmark`** — advances a million-plus independent lanes, seeded from
  scrambled non-stock states, and reports raw generator throughput (words/second)
  for your hardware. The lanes are deliberately *not* a contiguous pad sweep — it
  measures speed, not a keyspace.

```
pip install pyopencl numpy
python opencl/host.py
```

On a machine without an OpenCL platform or without `pyopencl`, `host.py` prints a
skip notice and exits cleanly — the rest of the toolkit is pure-Python/numpy and
needs no GPU.

## Why bit-exactness comes first

The single most important discipline this repository is trying to transmit: **a
count from an optimised kernel is worthless until the kernel is proven to match a
trivial reference.** A one-bit error in a shift or a mask produces a kernel that
runs fast, looks plausible, and is wrong on every input. `selftest` is the gate.
Run it, see it pass, *then* trust the throughput number.

## What this kernel deliberately is not

This is a **reference generator plus a self-test**, nothing more. It contains no
device- or product-specific boot/seeding model, no BIP32/39/84 key derivation,
and no address/hash160 matching against any target set. Those three pieces are
what turn a PRNG kernel into a wallet-recovery tool, and they are intentionally
absent here — see [`../SECURITY.md`](../SECURITY.md) for the rationale and the
responsible-disclosure background.
