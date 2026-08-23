"""OpenCL host for yasmarang.cl: prove the kernel bit-exact, then benchmark it.

Run this on a machine with an OpenCL platform (CPU or GPU) and pyopencl:

    python opencl/host.py

It does two things, in the order that matters:

  1. selftest — generate the first K words for many random initial states on the
     device and assert every word equals the CPU reference in
     ``keyspace_audit.yasmarang``. If this fails, STOP: nothing the device
     produces can be trusted until it matches the reference.

  2. benchmark — advance millions of independent lanes from scrambled, non-stock
     states and report words/second: raw generator throughput on your hardware.

If pyopencl or an OpenCL platform is unavailable, the script prints a clear
message and exits 0 (the CPU reference and the rest of the toolkit do not need a
GPU). Nothing here derives keys or matches addresses — see SECURITY.md.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
from keyspace_audit.yasmarang import Yasmarang

KERNEL = os.path.join(os.path.dirname(__file__), "yasmarang.cl")


def _load_cl():
    try:
        import pyopencl as cl  # noqa: F401
    except Exception as e:  # pragma: no cover - environment dependent
        print(f"[skip] pyopencl not available ({e}). The CPU reference still works.")
        return None
    try:
        import pyopencl as cl
        platforms = cl.get_platforms()
        if not platforms:
            print("[skip] no OpenCL platform found. The CPU reference still works.")
            return None
        return cl
    except Exception as e:  # pragma: no cover
        print(f"[skip] could not initialise OpenCL ({e}). The CPU reference still works.")
        return None


def run_selftest(cl, ctx, queue, prog, N=4096, K=8, seed=20260821):
    rng = np.random.default_rng(seed)
    pad0 = rng.integers(0, 1 << 32, N, dtype=np.uint32)
    n0 = rng.integers(0, 1 << 32, N, dtype=np.uint32)
    d0 = rng.integers(0, 1 << 32, N, dtype=np.uint32)
    dat0 = rng.integers(0, 1 << 8, N, dtype=np.uint32)
    out = np.empty(N * K, dtype=np.uint32)

    mf = cl.mem_flags
    bufs = [cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a)
            for a in (pad0, n0, d0, dat0)]
    out_buf = cl.Buffer(ctx, mf.WRITE_ONLY, out.nbytes)
    prog.selftest(queue, (N,), None, np.uint32(K), *bufs, out_buf)
    cl.enqueue_copy(queue, out, out_buf)
    queue.finish()

    gpu = out.reshape(N, K)
    for i in range(N):
        ref = Yasmarang(int(pad0[i]), int(n0[i]), int(d0[i]), int(dat0[i])).words(K)
        if ref != [int(x) for x in gpu[i]]:
            raise AssertionError(f"GPU/CPU mismatch at row {i}")
    print(f"[ok] selftest passed: {N} states x {K} words, GPU bit-exact with CPU reference")


def run_benchmark(cl, ctx, queue, prog, lanes=1 << 20, iters=1024):
    sink = np.empty(lanes, dtype=np.uint32)
    mf = cl.mem_flags
    sink_buf = cl.Buffer(ctx, mf.WRITE_ONLY, sink.nbytes)
    # warm-up
    prog.benchmark(queue, (lanes,), None, np.uint32(iters), np.uint32(0), sink_buf)
    queue.finish()
    t0 = time.perf_counter()
    prog.benchmark(queue, (lanes,), None, np.uint32(iters), np.uint32(0), sink_buf)
    queue.finish()
    dt = time.perf_counter() - t0
    words = lanes * iters
    print(f"[bench] {words/1e9:.2f} G words in {dt*1e3:.1f} ms "
          f"= {words/dt/1e9:.2f} G words/s")


def main():
    cl = _load_cl()
    if cl is None:
        return 0
    ctx = cl.create_some_context(interactive=False)
    queue = cl.CommandQueue(ctx)
    with open(KERNEL) as f:
        prog = cl.Program(ctx, f.read()).build()
    run_selftest(cl, ctx, queue, prog)
    run_benchmark(cl, ctx, queue, prog)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
