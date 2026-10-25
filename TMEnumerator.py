from turing_machine import TuringMachine
from bisect import bisect_right
from collections import Counter
import math
import random


class TMEnumerator:

    def __init__(self, max_l: int, samples: int = 10000, rng: random.Random = None):
        if samples < 0:
            raise ValueError("samples must be non-negative")

        self.max_l = max_l
        self.samples = samples
        self.rng = rng if rng is not None else random.Random()

        self.classes = self._feasible_classes(max_l)

        self.class_masses = [self._class_size(n, k) << (max_l - self._encoding_length(n, k))
                             for n, k in self.classes]

        self._cumulative_mass = []
        running = 0
        for mass in self.class_masses:
            running += mass
            self._cumulative_mass.append(running)
        self.total_mass = running

        self.min_encoding_length = min((self._encoding_length(n, k) for n, k in self.classes),
                                       default=None)

    def __iter__(self):
        return self._sample_stream()

    def __len__(self):
        return self.samples if self.classes else 0

    # ---------------------------------------------------------------- sampling

    def _sample_stream(self):
        if not self.classes:
            return
        for _ in range(self.samples):
            yield self.sample()

    def sample(self) -> TuringMachine:
        if not self.classes:
            raise ValueError(f"no turing machine fits in {self.max_l} bits "
                             f"(the smallest is {self._encoding_length(2, 2)} bits)")
        n, k = self._pick_class()
        return self._random_tm(n, k)

    def _pick_class(self) -> tuple:
        #randrange over exact integer cumulative mass; no float conversion of huge ints
        target = self.rng.randrange(self.total_mass)
        return self.classes[bisect_right(self._cumulative_mass, target)]

    def _random_tm(self, n: int, k: int) -> TuringMachine:
        rng = self.rng

        blank = rng.randrange(k)

        halt = rng.randrange(n)
        start = rng.randrange(n - 1)  #draw from the n-1 states that are not the halt state, then shift
        if start >= halt:
            start += 1

        # each entry is (new_state, new_symbol, direction, emit)
        table = tuple((rng.randrange(n), rng.randrange(k), rng.randrange(2), rng.randrange(2))
                      for _ in range(n * k))

        return TuringMachine(tuple(range(n)), k, blank, table, start, halt)

    # ----------------------------------------------------------------- weights

    def weight(self, length: int) -> float:
        if self.min_encoding_length is None:
            return 0.0
        return math.ldexp(1.0, self.min_encoding_length - length)

    # ------------------------------------------------------------------ classes

    def class_probabilities(self) -> dict:
        if not self.total_mass:
            return {}
        return {pair: mass / self.total_mass
                for pair, mass in zip(self.classes, self.class_masses)}

    def length_distribution(self) -> dict:
        if not self.total_mass:
            return {}
        by_length = {}
        for (n, k), mass in zip(self.classes, self.class_masses):
            length = self._encoding_length(n, k)
            by_length[length] = by_length.get(length, 0) + mass
        return {length: mass / self.total_mass
                for length, mass in sorted(by_length.items())}

    def length_report(self, lengths) -> str:
        counts = Counter(lengths)
        total = sum(counts.values())
        expected = self.length_distribution()
        classes_by_length = {}
        for n, k in self.classes:
            classes_by_length.setdefault(self._encoding_length(n, k), []).append((n, k))

        lines = [f"{total} programs sampled, {len(counts)} distinct lengths",
                 f"{'len':>5} {'(n,k)':>22} {'sampled':>9} {'observed':>10} {'expected':>10} {'cumulative':>9}"]
        cumulative = 0.0
        for length in sorted(set(counts) | set(expected)):
            share = counts.get(length, 0) / total if total else 0.0
            cumulative += share
            pairs = ",".join(f"{n}x{k}" for n, k in classes_by_length.get(length, []))
            lines.append(f"{length:>5} {pairs[:22]:>22} {counts.get(length, 0):>9} "
                         f"{share:>10.6f} {expected.get(length, 0.0):>10.6f} {cumulative:>9.6f}")
        return "\n".join(lines)

    def _feasible_classes(self, max_l: int) -> list:
        classes = []
        n = 2
        while self._encoding_length(n, 2) <= max_l:
            k = 2
            while self._encoding_length(n, k) <= max_l:
                classes.append((n, k))
                k += 1
            n += 1
        return classes

    def _class_size(self, n: int, k: int) -> int:
        entry_choices = n * k * 2 * 2  
        return k * (n * (n - 1)) * entry_choices ** (n * k)

    def _encoding_length(self, n: int, k: int):
        if n < 1 or k < 2:
            return float('inf')
        sb = math.ceil(math.log2(n)) if n > 1 else 1
        yb = math.ceil(math.log2(k)) if k > 1 else 1
        header = (n + 1) + (k + 1)
        special = 2 * sb
        transition = n * k * (sb + yb + 2)
        blank = yb
        return header + special + transition + blank


def main():
    from encoder import Encoder

    e = TMEnumerator(max_l=102, samples=50000, rng=random.Random(0))
    encoder = Encoder()
    print(f"shortest program: {e.min_encoding_length} bits, {len(e.classes)} classes")
    print(e.length_report([len(encoder.encode(tm)) for tm in e]))


if __name__ == "__main__":
    main()
