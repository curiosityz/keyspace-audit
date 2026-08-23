from keyspace_audit.yasmarang import Yasmarang, stream_bytes
from keyspace_audit.whitening import whitened_keyspace_is_unchanged, whiten_words


def test_fixed_whitening_preserves_keyspace():
    seeds = range(1 << 12)
    ks = Yasmarang(pad=0x0A8CE26F).bytes(16)
    r = whitened_keyspace_is_unchanged(lambda s: stream_bytes(s, count=16), seeds, ks)
    assert r["equal"]
    assert r["raw_distinct"] == r["whitened_distinct"]


def test_whiten_words_is_involutive():
    words = [1, 2, 3, 4]
    ks = [10, 20, 30, 40]
    once = whiten_words(words, ks)
    twice = whiten_words(once, ks)
    assert twice == words  # XOR twice by the same keystream is identity


def test_whitening_changes_appearance():
    # It must scramble the bytes even though it preserves the count.
    seeds = range(64)
    ks = Yasmarang(pad=0x0A8CE26F).bytes(16)
    raw = [stream_bytes(s, count=16) for s in seeds]
    wht = [bytes(a ^ b for a, b in zip(r, ks)) for r in raw]
    assert raw != wht
