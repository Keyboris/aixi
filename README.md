# AIXI

A from-scratch implementation of the machinery behind **AIXI** — Hutter's universal
artificial intelligence agent — built bottom-up in pure Python with no dependencies.

AIXI is uncomputable: evaluating its universal mixture means simulating every program,
including the ones that never halt. This repo builds **AIXI*tl***, the tractable
approximation that bounds programs to length `l` and runs each for at most `t` steps,
starting from the Turing machine and working up:

```
TuringMachine  ->  Encoder  ->  UniversalTuringMachine  ->  SolomonoffPredictor
                                       |
                                       +-->  bounded_kolmogorov
```

The Solomonoff sequence predictor is working. The expectimax planner that turns the
predictor into a full agent is not implemented yet.

## Contents

| File | What it does |
| --- | --- |
| `turing_machine.py` | Single-tape deterministic TM over a flattened transition table. Emits an output bit stream alongside the tape. |
| `encoder.py` | Serialises a `TuringMachine` to a binary string — the "program" the UTM runs. |
| `universal_turing_machine.py` | Decodes a binary string back into a machine and runs it. Also holds a shortest-first enumerator over all bit strings. |
| `bounded_kolmogorov.py` | Computes `K_{l,t}(x)`: the length of the shortest program under `l` bits that outputs `x` within `t` steps. |
| `TMEnumerator.py` | Stratified Monte Carlo sampler over the hypothesis space, with exact integer mass arithmetic and diagnostics. |
| `solomonoff_predictor.py` | The universal predictor: samples programs, simulates them in parallel, filters by consistency with observations, predicts the next bit. |
| `docs/report.tex` | Full technical report — derivations, design rationale, worked encoding example, empirical results. |

Every module has a `main()`, so each stage runs standalone:

```bash
python turing_machine.py          # two toy machines: alternating bits, single bit
python encoder.py                 # encode a machine to its bit string
python universal_turing_machine.py # round-trip encode -> decode -> run
python TMEnumerator.py            # sampler diagnostics: observed vs expected length distribution
python solomonoff_predictor.py    # predict a periodic sequence
```

Requires Python 3.10+. Standard library only.

## Design decisions

**One halt state, not accept/reject.** The textbook 7-tuple needs
`q_accept != q_reject`, which makes every 2-state machine halt after a single symbol —
computationally inert. Since 2-state machines have the shortest encodings and therefore
carry the most prior mass, that would render the most heavily weighted class of the
hypothesis space useless. Merging the halt states costs one `state_bits` field per
program and buys back the entire class.

**An explicit emit bit.** Each transition carries a flag for whether it emits. Output is
the stream of emitted symbols mod 2, so the output stays binary whatever the tape
alphabet size is, and a machine can compute silently before producing anything.

**Encoding layout.** `states (unary) | alphabet (unary) | start | halt | transitions | blank`.
The two unary headers are self-delimiting, which fixes `state_bits` and `symbol_bits`
for everything that follows, so the decoder never needs separators.

**Stratified sampling instead of enumeration.** Exhaustive enumeration over programs of
length `l` is `2^l` — hopeless past trivial bounds. `TMEnumerator` instead partitions the
space into `(n, k)` classes (n states, k symbols), computes each class's exact prior mass
as `|class| * 2^(l - encoding_length)` in Python big integers with no float conversion,
and samples classes proportionally before drawing a uniform machine within the chosen
class. `length_report()` cross-checks the sampled length distribution against the
analytic one.

**`K(x)` is an analysis tool, `2^-|p|` is the implementation.** Kolmogorov complexity is
incomputable, so nothing in the predictor calls `bounded_kolmogorov`. Program weights are
`2^(min_length - |p|)`, anchored at the shortest feasible program to keep the ratios in
float range.

## Results

On the repeating sequence `1,0,0,0,1,1,0,0,0,1,1,...`, `P(next=1)` moves
`0.495, 0.076, 0.498, 0.753, 0.047, 0.996, 0.0, 0.998, 0.0, 1.0, 0.0, 1.0, ...` over eight
observations, and stays locked on from there. The survivor pool falls from roughly a
million candidates to a stable handful without collapsing to zero — mass concentrating on
the many weight-equivalent period-2 hypotheses, which is what the convergence argument
predicts.

Two failure modes, both structural rather than a matter of sample budget:

- **Sequences needing a counter.** A doubling-block sequence (runs of length
  1,1,2,2,4,4,8,8,...) empties the survivor pool after ~15 observations and
  `predict_next` falls back to 0.5. Counting needs enough states and transitions to
  implement a counter, and those classes are exactly the ones the prior starves. The
  theory guarantees convergence only when the true program lies inside the sampled
  space.
- **Stochastic sources.** A biased coin cannot be modelled at all. Every candidate runs
  on an empty tape and produces one fixed output string, so enough Bernoulli bits
  eliminate every hypothesis in turn. The fix is in Hutter's original formulation: a
  second read-only random input tape, so `M` becomes a weighted sum over program
  *behaviours* rather than a consistency filter over program *outputs*.

## Roadmap

- Random input tape, so stochastic environments are representable
- Expectimax planner over the mixture — the step from predictor to agent
- A toy environment to run the agent in

See `docs/report.tex` for the full derivations and the development retrospective.

## Licence

MIT.
