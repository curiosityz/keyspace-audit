"""Yasmarang PRNG (Ilya Levin) — scalar reference implementation.

Yasmarang is a small, fast, **non-cryptographic** 32-bit generator. Its whole
state is four words ``(pad, n, d, dat)`` and one step is:

    pad += dat + d*n
    pad  = (pad << 3) + (pad >> 29)        # rotate-left-3 (shifted bits disjoint)
    n    = pad | 2
    d   ^= (pad << 31) + (pad >> 1)        # rotate-right-1 (disjoint)
    dat ^= (char)pad ^ (d >> 8) ^ 1
    return pad ^ (d << 5) ^ (pad >> 18) ^ (dat << 1)

It is included here as the worked example for the rest of the toolkit: a
generator whose *nominal* period is enormous but whose *realized* keyspace, once
it is seeded from a low-entropy value, can be far smaller. Nothing in this file
is specific to any product — it is the published algorithm and a set of
self-consistency checks.

This module is the SCALAR reference. ``yasmarang_vec`` holds a vectorised
(numpy) twin; the two are cross-checked against each other as a self-test, which
is the pattern the whole toolkit is built on: never trust a count from an
optimised implementation you have not proven bit-exact against a simple one.
"""

M32 = 0xFFFFFFFF


class Yasmarang:
    """Scalar Yasmarang. Defaults are the generator's stock seed values."""

    def __init__(self, pad=0xEDA4BABA, n=69, d=233, dat=0):
        self.pad = pad & M32
        self.n = n & M32
        self.d = d & M32
        self.dat = dat & 0xFF

    def next_word(self):
        pad, n, d, dat = self.pad, self.n, self.d, self.dat
        pad = (pad + dat + (d * n & M32)) & M32
        pad = ((pad << 3) + (pad >> 29)) & M32
        n = pad | 2
        d = (d ^ (((pad << 31) + (pad >> 1)) & M32)) & M32
        dat = (dat ^ (pad & 0xFF) ^ ((d >> 8) & 0xFF) ^ 1) & 0xFF
        out = (pad ^ ((d << 5) & M32) ^ (pad >> 18) ^ ((dat << 1) & M32)) & M32
        self.pad, self.n, self.d, self.dat = pad, n, d, dat
        return out

    def words(self, k):
        """First ``k`` output words as a list of ints."""
        return [self.next_word() for _ in range(k)]

    def bytes(self, count):
        """First ``count`` output bytes, little-endian per word."""
        out = bytearray()
        while len(out) < count:
            out += (self.next_word()).to_bytes(4, "little")
        return bytes(out[:count])


def stream_bytes(pad, n=69, d=233, dat=0, count=16):
    """Convenience: first ``count`` output bytes of a Yasmarang seeded at
    ``(pad, n, d, dat)``. Used as the black-box generator handed to the
    keyspace auditor in the examples."""
    return Yasmarang(pad, n, d, dat).bytes(count)


if __name__ == "__main__":
    a = Yasmarang().words(6)
    b = Yasmarang().words(6)
    assert a == b, "a deterministic generator must repeat under the same seed"
    print("stock default [:6] =", [hex(x) for x in a])
    print("OK: scalar Yasmarang reference self-consistent")
