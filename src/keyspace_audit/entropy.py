"""Realized-keyspace auditor: measure how much entropy a seed generator *keeps*.

The nominal keyspace of a seed generator is how many distinct seeds you could
feed it (``2**nominal_bits``). The **realized** keyspace is how many distinct
*outputs* those seeds actually produce. When a generator's seeding path funnels
a wide input into a narrow effective state, the two diverge — and it is the
realized keyspace, not the nominal one, that an attacker searches.

This module treats the generator as a black box ``gen(seed) -> bytes`` and
measures the realized keyspace two ways:

* ``realized_keyspace`` — EXACT distinct count over a caller-supplied set of
  seeds. Enumerate the whole seed space and you get the exact realized keyspace;
  enumerate a subset and you get the realized keyspace *of that subset*.
* ``sampled_realized_bits`` — an occupancy/coverage ESTIMATOR for seed spaces too
  large to enumerate. Draw ``m`` random seeds, count how many produce a distinct
  fingerprint ``d``, and invert the occupancy relation
  ``E[d] = K*(1-(1-1/K)**m)`` for the realized keyspace ``K``. This is honest
  across regimes (barely-touched through saturated); when no collision is seen it
  degrades to a birthday-floor heuristic rather than a firm number. Treat it as
  an order-of-magnitude screen, then confirm by exact enumeration where it says
  the space is small enough to.

A stream fingerprint is the first ``nbytes`` (default 16 = 128 bits) of output.
That is wide enough that two distinct fingerprints almost certainly mean two
distinct streams; collisions from truncation are negligible below ~1e18 seeds.
"""
import math


def stream_fingerprint(gen, seed, nbytes=16):
    """First ``nbytes`` of ``gen(seed)`` as a bytes key."""
    return bytes(gen(seed)[:nbytes])


def realized_keyspace(gen, seeds, nbytes=16):
    """Exact realized keyspace over the seeds in ``seeds`` (any iterable).

    Returns a dict:
      * ``nominal_count``   — number of seeds enumerated
      * ``distinct``        — number of distinct output fingerprints
      * ``nominal_bits``    — log2(nominal_count)
      * ``realized_bits``   — log2(distinct)
      * ``collapse_factor`` — nominal_count / distinct  (1.0 == injective)
      * ``lost_bits``       — nominal_bits - realized_bits
    """
    seen = set()
    n = 0
    for s in seeds:
        seen.add(stream_fingerprint(gen, s, nbytes))
        n += 1
    distinct = len(seen)
    nominal_bits = math.log2(n) if n else 0.0
    realized_bits = math.log2(distinct) if distinct else 0.0
    return {
        "nominal_count": n,
        "distinct": distinct,
        "nominal_bits": nominal_bits,
        "realized_bits": realized_bits,
        "collapse_factor": (n / distinct) if distinct else float("inf"),
        "lost_bits": nominal_bits - realized_bits,
    }


def _keyspace_from_occupancy(m, d):
    """Invert the occupancy (coverage) relation E[distinct] = K*(1-(1-1/K)**m)
    for K, given m draws that yielded d distinct fingerprints.

    This estimator is honest across the whole range: near-injective sampling
    (d ~ m), heavy collision (d << m, saturated toward K), and everything
    between. It replaces the pairwise-birthday estimate ~C(m,2)/collisions,
    which is only valid for m << sqrt(K) and badly overestimates once samples
    exceed the keyspace. Returns (K_hat, is_lower_bound).
    """
    if d <= 0:
        return 0.0, True
    if d >= m:
        # No collision observed: K could be anything large. We return the
        # birthday-floor HEURISTIC ~C(m,2) — the keyspace at which m draws would
        # be expected to produce their first collision. It is a rough
        # order-of-magnitude screen ("K is at least around here, draw more"),
        # not a rigorous lower bound. is_lower_bound=True flags it as such.
        return (m * (m - 1) / 2.0 if m > 1 else 1.0), True

    def expected_distinct(K):
        # K*(1-(1-1/K)**m), stable via log1p/exp for large K.
        return K * (1.0 - math.exp(m * math.log1p(-1.0 / K)))

    lo, hi = float(d), float(d)
    # grow hi until expected_distinct(hi) >= d (monotone increasing toward m)
    while expected_distinct(hi) < d and hi < 1e18:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if expected_distinct(mid) < d:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi), False


def sampled_realized_bits(gen, sampler, n_samples, nbytes=16):
    """Estimate the realized keyspace of a large space by sampling.

    ``sampler()`` returns a random seed from the space. Draws ``n_samples`` seeds,
    records how many produce a distinct fingerprint, and inverts the occupancy
    relation ``E[distinct] = K*(1-(1-1/K)**m)`` for the keyspace ``K``. This is
    reliable whether the space is barely touched or saturated; see
    ``_keyspace_from_occupancy`` for why it is preferred over a naive birthday
    estimate.

    Returns a dict with ``samples``, ``distinct``, ``collisions``,
    ``estimated_keyspace``, ``estimated_bits`` and ``is_lower_bound``. When no
    collision is seen the estimate is only a lower bound — draw more samples.
    """
    seen = set()
    collisions = 0
    for _ in range(n_samples):
        fp = stream_fingerprint(gen, sampler(), nbytes)
        if fp in seen:
            collisions += 1
        else:
            seen.add(fp)
    m = n_samples
    d = len(seen)
    k_hat, is_lb = _keyspace_from_occupancy(m, d)
    return {
        "samples": m,
        "distinct": d,
        "collisions": collisions,
        "estimated_keyspace": k_hat,
        "estimated_bits": math.log2(k_hat) if k_hat > 0 else 0.0,
        "is_lower_bound": is_lb,
    }
