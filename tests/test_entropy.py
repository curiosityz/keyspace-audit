import math

from keyspace_audit.yasmarang import stream_bytes
from keyspace_audit.entropy import realized_keyspace, sampled_realized_bits


def test_injective_generator_has_no_collapse():
    # Distinct small seeds give distinct Yasmarang streams here.
    stats = realized_keyspace(lambda s: stream_bytes(s, count=16), range(1000))
    assert stats["distinct"] == 1000
    assert abs(stats["collapse_factor"] - 1.0) < 1e-9
    assert stats["lost_bits"] < 1e-9


def test_collapsed_generator_is_detected():
    eff = 8  # only low 8 bits reach the stream
    gen = lambda s: stream_bytes(s & ((1 << eff) - 1), count=16)
    stats = realized_keyspace(gen, range(1 << 14))
    assert stats["distinct"] == (1 << eff)
    assert abs(stats["realized_bits"] - eff) < 1e-9
    assert stats["lost_bits"] > 5


def test_sampled_estimator_order_of_magnitude():
    eff = 10
    gen = lambda s: stream_bytes(s & ((1 << eff) - 1), count=16)
    import random
    rnd = random.Random(1)
    est = sampled_realized_bits(gen, lambda: rnd.getrandbits(20), n_samples=8000)
    # collisions should appear well before 2^10 distinct are exhausted
    assert est["collisions"] > 0
    assert abs(est["estimated_bits"] - eff) < 3.0  # rough estimator, wide bar
