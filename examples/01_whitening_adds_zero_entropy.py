"""Example 1 — XORing a fixed keystream into a stream adds zero entropy.

We take a weak stream (Yasmarang seeded from a small integer), whiten it by
XORing against a FIXED second Yasmarang seeded from constants, and show the
realized keyspace is IDENTICAL before and after. The whitening changes how the
output looks; it changes nothing an attacker has to search.

This mirrors the real finding that motivated the toolkit: a second generator,
seeded from hardcoded public constants, was XORed over a weak first generator.
Because the second stream is fixed, the XOR is a per-position bijection and
cannot add entropy.

Run:  python examples/01_whitening_adds_zero_entropy.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from keyspace_audit.yasmarang import Yasmarang, stream_bytes
from keyspace_audit.whitening import whitened_keyspace_is_unchanged

# A weak stream: seeded by a 16-bit integer (nominal 65,536 seeds).
SEEDS = range(1 << 16)


def weak_gen(seed):
    return stream_bytes(seed, count=16)


# A FIXED keystream: the first 16 bytes of a Yasmarang seeded from constants.
# These are the public, hardcoded second-stream constants from the finding that
# motivated the toolkit. The zero-entropy result does not depend on them — any
# fixed seed gives a fixed keystream and the same bijection — but using the real
# public constants keeps this example concrete and reproducible.
fixed_keystream_bytes = Yasmarang(pad=0x0A8CE26F, n=69, d=233, dat=0).bytes(16)


def main():
    result = whitened_keyspace_is_unchanged(
        weak_gen, SEEDS, fixed_keystream_bytes, nbytes=16
    )
    print("raw realized keyspace      :", result["raw_distinct"],
          f"({result['raw_realized_bits']:.2f} bits)")
    print("whitened realized keyspace :", result["whitened_distinct"],
          f"({result['whitened_realized_bits']:.2f} bits)")
    print("equal (whitening added nothing):", result["equal"])
    assert result["equal"], "fixed-keystream whitening must not change the keyspace"
    print("\nOK: the fixed XOR is a bijection — same number of distinct streams.")


if __name__ == "__main__":
    main()
