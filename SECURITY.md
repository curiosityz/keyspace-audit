# Security & responsible-use notice

This repository is a **defensive** entropy-audit toolkit. It exists so that
people who build or review seed generators can measure how much unpredictability
those generators actually keep, and so that the analysis behind a specific
real-world weakness (a hardware-wallet PRNG that collapsed to a tiny keyspace)
can be reproduced and checked by others rather than taken on faith.

## What this repository deliberately does NOT contain

The weakness that motivated this work was exploitable end to end because three
things existed together: a device-specific seeding model, a full key-derivation
path, and a way to match derived keys against real funded addresses. This
repository ships **none of those three**, on purpose:

- **No device/product boot or seeding model.** There is no code that reconstructs
  a specific device's PRNG state from serial numbers, timers, boot sequences, or
  any other hardware input.
- **No key derivation.** There is no BIP32/BIP39/BIP84 (or any other) path from a
  generator output to a private key, mnemonic, or address.
- **No target matching.** There is no address/hash160 set, no membership search,
  and no wallet-scanning harness.

What remains is the *science*: the published PRNG, a proof that fixed-keystream
whitening adds zero entropy, a black-box tool that measures realized keyspace,
and a GPU self-test that proves an optimised generator matches a reference. None
of these, alone or together, recovers anyone's funds. Rebuilding an attack from
this repository would require independently re-deriving all three withheld
pieces — which is exactly the line this project draws.

## Coordinated disclosure

The underlying vulnerability was handled through responsible disclosure, and all
reproduction/validation in the associated research was performed **only against
addresses that had already been emptied, with zero residual balance**. No live
funds were ever touched and no transaction was ever constructed or broadcast.

## Reporting

If you believe a change to this repository would make it materially easier to
attack live systems, please open a private report to the maintainers before
filing a public issue. Contributions that add device models, derivation paths,
or target-matching will be declined.

## Intended users

Wallet and firmware developers auditing their own RNG; security researchers
reproducing the published analysis; educators teaching entropy accounting. If you
are trying to recover keys you do not own, this repository will not help you, and
that is by design.
