"""Command-line entry point for keyspace-audit.

    keyspace-audit kat           run the bit-exact self-test of the vectorised twin
    keyspace-audit whitening     show that fixed-keystream XOR adds zero entropy
    keyspace-audit collapse      measure keyspace collapse on a synthetic generator

These mirror the scripts in examples/ but are runnable straight from an install.
"""
import argparse

from .yasmarang import Yasmarang, stream_bytes
from .yasmarang_vec import kat as run_kat
from .entropy import realized_keyspace, sampled_realized_bits
from .whitening import whitened_keyspace_is_unchanged


def cmd_kat(args):
    print(run_kat())
    print("OK: vectorised twin is bit-exact with the scalar reference")


def cmd_whitening(args):
    bits = args.seed_bits
    seeds = range(1 << bits)
    ks = Yasmarang(pad=0x0A8CE26F).bytes(16)
    r = whitened_keyspace_is_unchanged(
        lambda s: stream_bytes(s, count=16), seeds, ks, nbytes=16
    )
    print(f"raw realized keyspace      : {r['raw_distinct']} ({r['raw_realized_bits']:.2f} bits)")
    print(f"whitened realized keyspace : {r['whitened_distinct']} ({r['whitened_realized_bits']:.2f} bits)")
    print(f"whitening added nothing    : {r['equal']}")


def cmd_collapse(args):
    nominal, effective = args.nominal_bits, args.effective_bits
    gen = lambda s: stream_bytes(s & ((1 << effective) - 1), count=16)
    stats = realized_keyspace(gen, range(1 << nominal), nbytes=16)
    print(f"nominal  : {stats['nominal_count']:,} ({stats['nominal_bits']:.1f} bits)")
    print(f"realized : {stats['distinct']:,} ({stats['realized_bits']:.1f} bits)")
    print(f"collapse : {stats['collapse_factor']:.1f}x ({stats['lost_bits']:.1f} bits lost)")


def build_parser():
    p = argparse.ArgumentParser(prog="keyspace-audit", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    k = sub.add_parser("kat", help="bit-exact self-test of the vectorised twin")
    k.set_defaults(func=cmd_kat)

    w = sub.add_parser("whitening", help="fixed-keystream XOR adds zero entropy")
    w.add_argument("--seed-bits", type=int, default=14, help="nominal seed width (default 14)")
    w.set_defaults(func=cmd_whitening)

    c = sub.add_parser("collapse", help="measure collapse on a synthetic generator")
    c.add_argument("--nominal-bits", type=int, default=20, help="advertised seed width")
    c.add_argument("--effective-bits", type=int, default=10, help="bits the path actually keeps")
    c.set_defaults(func=cmd_collapse)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
