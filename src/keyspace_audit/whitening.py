"""XOR whitening against a *fixed* keystream adds no entropy — proof and check.

This is the mathematical core of the case study that motivated the toolkit, and
it is worth stating precisely, because the loose version of it is false.

FALSE (do not believe this): "two non-cryptographic generators XORed together
give one generator's worth of unpredictability." Two *independent, seed-varying*
streams XORed together generally give MORE distinct outputs, not fewer.

TRUE (what actually happened, and what this module demonstrates): if the second
operand is a **fixed** keystream ``W`` — the same sequence for every seed,
because it is generated from hardcoded constants — then whitening adds exactly
zero entropy. For each output position ``i`` the map ``x -> x XOR W[i]`` is a
bijection on the word space, so the whole map ``A(seed) -> A(seed) XOR W`` is a
bijection on streams. A bijection cannot change how many distinct streams exist:

    |{ A(seed) XOR W : seed in S }|  ==  |{ A(seed) : seed in S }|   for any S.

The realized keyspace is identical before and after whitening. All the fixed
XOR does is scramble the *appearance* of the output so it no longer visibly
resembles the underlying weak stream. ``whitened_keyspace_is_unchanged`` checks
this empirically for a caller-supplied stream and keystream.
"""
from .entropy import realized_keyspace


def fixed_keystream(word_stream_fn, length):
    """Materialise the first ``length`` words of a fixed keystream. ``word_stream_fn``
    is a zero-argument callable returning an iterator/list of ints (e.g. a
    Yasmarang seeded at constants). The result is the SAME for every call, which
    is exactly what makes the XOR entropy-free."""
    it = iter(word_stream_fn())
    return [next(it) for _ in range(length)]


def whiten_words(words, keystream, mask=0xFFFFFFFF):
    """XOR a list of output words against a fixed keystream, position by
    position. ``len(keystream)`` must be >= ``len(words)``."""
    return [(w ^ keystream[i]) & mask for i, w in enumerate(words)]


def whitened_keyspace_is_unchanged(gen, seeds, keystream_bytes, nbytes=16):
    """Empirical check of the theorem above.

    ``gen(seed) -> bytes`` is the (weak) stream generator. ``keystream_bytes`` is
    a FIXED byte sequence at least ``nbytes`` long. Returns a dict comparing the
    realized keyspace of the raw stream against the whitened stream over the same
    ``seeds``; ``equal`` must be True.
    """
    ks = bytes(keystream_bytes[:nbytes])
    seeds = list(seeds)  # materialise: used twice

    def whitened(seed):
        raw = bytes(gen(seed)[:nbytes])
        return bytes(a ^ b for a, b in zip(raw, ks))

    raw_stats = realized_keyspace(gen, seeds, nbytes=nbytes)
    wht_stats = realized_keyspace(whitened, seeds, nbytes=nbytes)
    return {
        "raw_distinct": raw_stats["distinct"],
        "whitened_distinct": wht_stats["distinct"],
        "raw_realized_bits": raw_stats["realized_bits"],
        "whitened_realized_bits": wht_stats["realized_bits"],
        "equal": raw_stats["distinct"] == wht_stats["distinct"],
    }
