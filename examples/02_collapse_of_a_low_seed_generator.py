"""Example 2 — measuring keyspace collapse on a synthetic generator.

A generator can *advertise* a wide seed but *realize* a narrow one when its
seeding path throws information away. Here we build a deliberately synthetic
generator whose 24-bit seed is folded down to ~12 effective bits before it
reaches the stream, and we let the auditor catch it — exactly and by sampling.

Nothing in this example is product-specific: it is a made-up collapse, used to
show what the auditor's numbers look like when a space is much smaller than it
claims to be.

Run:  python examples/02_collapse_of_a_low_seed_generator.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import random

from keyspace_audit.yasmarang import stream_bytes
from keyspace_audit.entropy import realized_keyspace, sampled_realized_bits

NOMINAL_BITS = 20
EFFECTIVE_BITS = 10  # the seeding path secretly keeps only this many


def collapsing_gen(seed):
    # A 24-bit seed, but only its low 12 bits ever reach the generator: the
    # top 12 bits are silently discarded by the "seeding" step.
    effective = seed & ((1 << EFFECTIVE_BITS) - 1)
    return stream_bytes(effective, count=16)


def main():
    # Exact: enumerate the whole 2^24 nominal space.
    exact = realized_keyspace(collapsing_gen, range(1 << NOMINAL_BITS), nbytes=16)
    print("== exact enumeration of the full nominal space ==")
    print(f"nominal   : {exact['nominal_count']:>10,}  ({exact['nominal_bits']:.1f} bits)")
    print(f"realized  : {exact['distinct']:>10,}  ({exact['realized_bits']:.1f} bits)")
    print(f"collapse  : {exact['collapse_factor']:.1f}x  "
          f"({exact['lost_bits']:.1f} bits lost)")

    # Sampled: the birthday estimator recovers the same order of magnitude
    # without enumerating the whole space.
    rnd = random.Random(20260823)
    est = sampled_realized_bits(
        collapsing_gen, lambda: rnd.getrandbits(NOMINAL_BITS),
        n_samples=20000, nbytes=16,
    )
    print("\n== occupancy/collision estimate (20k samples) ==")
    print(f"collisions: {est['collisions']}")
    print(f"estimated : ~{est['estimated_keyspace']:.0f}  ({est['estimated_bits']:.1f} bits)")

    assert exact["realized_bits"] < NOMINAL_BITS - 6, "collapse should be obvious"
    print(f"\nOK: the auditor flags a ~{EFFECTIVE_BITS}-bit space "
          f"behind a {NOMINAL_BITS}-bit seed.")


if __name__ == "__main__":
    main()
