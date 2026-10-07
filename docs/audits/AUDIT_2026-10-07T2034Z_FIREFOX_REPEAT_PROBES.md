# Firefox repeat-probe audit — 2026-10-07T2034Z

## Finding

The repeated Firefox restart/continuity archaeology is larger than the seven-operation OP177–OP178 cluster.

A strict scan of the old r29 engineering log for repeated assertions such as:
- no Firefox restart/reload occurred;
- Firefox PID remained continuous;
- full Firefox exit removes the temporary extension;
- restart remains prohibited;

found 25 matching log lines across 18 distinct PCE9 operation ordinals:
`43, 44, 47, 49, 50, 64, 65, 68, 74, 75, 91, 101, 102, 106, 107, 113, 114, 121`.

The later OP177, OP177A, OP177B, OP177C1, OP177C2, OP177C3, and OP178 sequence repeated the continuity/restart-safety check again, adding seven more operation ordinals.

Conservative lower bound: **25 PCE9-era operations** carried this same Firefox continuity/restart/no-reload proof theme. This is not a claim that every one was useless: some accompanied legitimate activation/reload work. It is proof that the invariant was repeatedly re-established instead of being reused as durable knowledge.

Project-lifetime repetition is higher because earlier Action/PCE7 history also contains legitimate and repeated Firefox reload/restart investigations; those older naming systems are not normalized into this lower-bound count.

## Established reusable fact

The development add-on is temporary. A full Firefox exit removes it. Full Firefox restart acceptance is blocked until the signed persistent-XPI/policy path exists.

That fact should be read from established facts/indexes and not rediscovered after source-only, documentation-only, Git-only, or unrelated runtime work.

## Re-probe gate

Repeat Firefox lifecycle proof only when:
1. Firefox/add-on/profile state actually changed;
2. contradictory evidence appeared; or
3. a named acceptance test explicitly requires the proof.

Otherwise cite/reuse the latest established proof.
