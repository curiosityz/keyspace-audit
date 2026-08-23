"""Vectorised (numpy) Yasmarang twin, cross-checked against the scalar reference.

The point of this module is not speed for its own sake. It is the *method*: an
optimised implementation (here, numpy over uint64 lanes; on a GPU, an OpenCL
kernel) is only trustworthy once it has been proven to produce the same bits as
a dead-simple reference on random inputs. A single wrong shift silently corrupts
every downstream count, and a keyspace measurement you cannot trust is worse
than none. ``kat()`` is that proof; run it before you believe any number this
module produces.
"""
import numpy as np

from .yasmarang import Yasmarang

M32 = np.uint64(0xFFFFFFFF)
_3, _29, _31, _1, _5, _18 = (np.uint64(x) for x in (3, 29, 31, 1, 5, 18))
_2 = np.uint64(2)
_8 = np.uint64(8)
_255 = np.uint64(0xFF)
_ONE = np.uint64(1)
_32 = np.uint64(32)


def step_vec(pad, n, d, dat):
    """One vectorised Yasmarang step over uint64 arrays holding 32-/8-bit
    values. Returns ``(pad, n, d, dat, out)``, all masked. Mirrors the scalar
    reference exactly."""
    pad = (pad + dat + ((d * n) & M32)) & M32
    pad = ((pad << _3) + (pad >> _29)) & M32
    n = pad | _2
    d = (d ^ (((pad << _31) + (pad >> _1)) & M32)) & M32
    dat = (dat ^ (pad & _255) ^ ((d >> _8) & _255) ^ _ONE) & _255
    out = (pad ^ ((d << _5) & M32) ^ (pad >> _18) ^ ((dat << _ONE) & M32)) & M32
    return pad, n, d, dat, out


def stream_vec(pad0, n0, d0, dat0, k):
    """First ``k`` output words for a batch of initial states -> ``(N, k)``
    uint64 array."""
    pad, n, d, dat = (np.asarray(a, np.uint64).copy() for a in (pad0, n0, d0, dat0))
    cols = np.empty((pad.shape[0], k), dtype=np.uint64)
    for j in range(k):
        pad, n, d, dat, out = step_vec(pad, n, d, dat)
        cols[:, j] = out
    return cols


def fingerprint_vec(pad0, n0, d0, dat0):
    """Pack the first four output words (128 bits) of each initial state into an
    ``(N, 2)`` uint64 array. 128 bits makes accidental fingerprint collisions
    negligible up to ~1e18 states, so distinct fingerprints == distinct streams
    for realistic sample sizes, at low peak memory."""
    pad, n, d, dat = (np.asarray(a, np.uint64).copy() for a in (pad0, n0, d0, dat0))
    pad, n, d, dat, w0 = step_vec(pad, n, d, dat)
    pad, n, d, dat, w1 = step_vec(pad, n, d, dat)
    pad, n, d, dat, w2 = step_vec(pad, n, d, dat)
    pad, n, d, dat, w3 = step_vec(pad, n, d, dat)
    hi = (w0 << _32) | w1
    lo = (w2 << _32) | w3
    return np.stack([hi, lo], axis=1)


def distinct_fingerprints_chunked(pad0, n0, d0, dat0, chunk=1_000_000):
    """Exact count of distinct 128-bit stream fingerprints over a batch,
    processed in chunks to bound memory and ``unique()``-d once at the end."""
    N = np.asarray(pad0).shape[0]
    pad0 = np.asarray(pad0, np.uint64)
    n0 = np.asarray(n0, np.uint64)
    d0 = np.asarray(d0, np.uint64)
    dat0 = np.asarray(dat0, np.uint64)
    buf = np.empty((N, 2), dtype=np.uint64)
    for s in range(0, N, chunk):
        e = min(s + chunk, N)
        buf[s:e] = fingerprint_vec(pad0[s:e], n0[s:e], d0[s:e], dat0[s:e])
    return int(np.unique(buf, axis=0).shape[0])


def kat(seed=20260821, N=256, K=8):
    """Cross-check the vectorised twin against the scalar reference on random
    initial states. Returns a dict; raises AssertionError on any mismatch."""
    rng = np.random.default_rng(seed)
    pad0 = rng.integers(0, 1 << 32, N, dtype=np.uint64)
    n0 = rng.integers(0, 1 << 32, N, dtype=np.uint64)
    d0 = rng.integers(0, 1 << 32, N, dtype=np.uint64)
    dat0 = rng.integers(0, 1 << 8, N, dtype=np.uint64)
    vec = stream_vec(pad0, n0, d0, dat0, K)
    for i in range(N):
        ref = Yasmarang(int(pad0[i]), int(n0[i]), int(d0[i]), int(dat0[i])).words(K)
        assert ref == [int(x) for x in vec[i]], f"KAT mismatch at row {i}"
    return {"kat_rows": N, "kat_words": K, "kat_pass": True}


if __name__ == "__main__":
    print("KAT:", kat())
    print("OK: vectorised twin is bit-exact with the scalar reference")
