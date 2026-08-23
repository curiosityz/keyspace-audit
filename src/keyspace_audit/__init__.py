"""keyspace-audit — measure the *realized* entropy of a seed generator.

A small, dependency-light toolkit for detecting keyspace collapse: the class of
weakness where a generator with a large nominal seed space produces far fewer
distinct outputs than its inputs suggest. Built around a worked example (the
Yasmarang PRNG and fixed-keystream whitening), but the auditor treats any
generator as a black box ``gen(seed) -> bytes``.

Public API:
    Yasmarang, stream_bytes            — the example generator
    realized_keyspace                  — exact realized keyspace over a seed set
    sampled_realized_bits              — birthday/collision estimator for large spaces
    whitened_keyspace_is_unchanged     — fixed-XOR-whitening adds zero entropy (proof/check)
    kat                                — bit-exact self-test of the vectorised twin
"""
from .yasmarang import Yasmarang, stream_bytes
from .yasmarang_vec import kat
from .entropy import realized_keyspace, sampled_realized_bits, stream_fingerprint
from .whitening import whitened_keyspace_is_unchanged, fixed_keystream, whiten_words

__version__ = "0.1.0"

__all__ = [
    "Yasmarang",
    "stream_bytes",
    "kat",
    "realized_keyspace",
    "sampled_realized_bits",
    "stream_fingerprint",
    "whitened_keyspace_is_unchanged",
    "fixed_keystream",
    "whiten_words",
]
