from keyspace_audit.yasmarang import Yasmarang
from keyspace_audit.yasmarang_vec import kat, stream_vec


def test_scalar_is_deterministic():
    assert Yasmarang().words(8) == Yasmarang().words(8)


def test_vector_matches_scalar_kat():
    result = kat(N=128, K=8)
    assert result["kat_pass"] is True


def test_vector_matches_scalar_explicit():
    # An independent spot-check outside kat()'s own harness.
    states = [(1, 69, 233, 0), (123456789, 12345, 42, 7), (0, 1, 1, 0)]
    for pad, n, d, dat in states:
        ref = Yasmarang(pad, n, d, dat).words(6)
        vec = stream_vec([pad], [n], [d], [dat], 6)[0]
        assert ref == [int(x) for x in vec]


def test_bytes_length_and_prefix():
    b = Yasmarang().bytes(20)
    assert len(b) == 20
    # first word little-endian equals first 4 bytes
    w0 = Yasmarang().next_word()
    assert b[:4] == w0.to_bytes(4, "little")
