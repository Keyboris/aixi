import multiprocessing
import os
import random
import matplotlib.pyplot as plt
import numpy as np

from universal_turing_machine import UniversalTuringMachine
from turing_machine import TuringMachine
from TMEnumerator import TMEnumerator
from encoder import Encoder

def _extract_output(tm: TuringMachine):
    return tm.output


def _simulate(program_string: str, utm: UniversalTuringMachine, max_steps: int):
    try:
        utm.decode(program_string)
        utm.run_on_input("", max_steps)
    except Exception:
        return None

    return _extract_output(utm.tm)


_worker_utm = None
_worker_max_steps = None


def _worker_init(max_steps: int):
    global _worker_utm, _worker_max_steps
    _worker_utm = UniversalTuringMachine()
    _worker_max_steps = max_steps


def _worker_simulate(program_string: str):
    return _simulate(program_string, _worker_utm, _worker_max_steps)


class _CandidateProgram:
    __slots__ = ("string", "output")

    def __init__(self, string: str, output: list):
        self.string = string
        self.output = output 

    def __repr__(self):
        return f"_CandidateProgram({self.string!r}, o={self.output!r})"


class SolomonoffPredictor:

    def __init__(self, utm: UniversalTuringMachine,
                 max_program_length: int,
                 max_number_of_steps: int,
                 samples: int = 10000,
                 enumerator: TMEnumerator = None,
                 processes: int | None = None,
                 chunksize: int = 64,
                 verbose: bool = False):
        if max_program_length < 0:
            raise ValueError("max_program_length must be non-negative")
        if max_number_of_steps is None or max_number_of_steps <= 0:
            raise ValueError("max_number_of_steps must be a positive integer")

        self.encoder = Encoder()
        self.utm = utm if utm is not None else UniversalTuringMachine()
        self.max_program_length = max_program_length
        self.max_number_of_steps = max_number_of_steps
        self.enumerator = (enumerator if enumerator is not None
                           else TMEnumerator(self.max_program_length, samples))

        self.observations = []
        self.candidate_programs = []

        program_strings = self._sample_program_strings()

        if verbose:
            print(self.enumerator.length_report([len(s) for s in program_strings]))

        outputs = self._simulate_all(program_strings, processes, chunksize)
        for string, output in zip(program_strings, outputs):
            if not output:
                continue
            self.candidate_programs.append(_CandidateProgram(string, output))

        if verbose:
            print(f"{len(self.candidate_programs)} of {len(program_strings)} sampled programs "
                  f"halted with a usable bit string")
            print(self.enumerator.length_report([len(p.string) for p in self.candidate_programs]))

    # ---------------------------------------------------------------- setup

    def _sample_program_strings(self) -> list:
        strings = []
        for tm in self.enumerator:
            program = self.encoder.encode(tm)
            if len(program) > self.max_program_length:
                continue
            strings.append(program)
        return strings

    def _simulate_all(self, program_strings: list, processes: int | None, chunksize: int) -> list:
        unique = list(dict.fromkeys(program_strings))

        if processes is None:
            processes = os.cpu_count() or 1

        in_child = multiprocessing.current_process().name != "MainProcess"
        if processes <= 1 or in_child or len(unique) < 2 * chunksize:
            utm = UniversalTuringMachine()
            results = [_simulate(s, utm, self.max_number_of_steps) for s in unique]
        else:
            with multiprocessing.Pool(processes,
                                      initializer=_worker_init,
                                      initargs=(self.max_number_of_steps,)) as pool:
                results = list(pool.map(_worker_simulate, unique, chunksize=chunksize))

        cache = dict(zip(unique, results))
        return [cache[s] for s in program_strings]

    # ------------------------------------------------------------ inference

    def update(self, observed_bit: int) -> None:
        if observed_bit not in (0, 1):
            raise ValueError(f"observed_bit must be 0 or 1, got {observed_bit!r}")

        index = len(self.observations)
        next_index = index + 1
        survivors = []
        for program in self.candidate_programs:
            output = program.output
            if len(output) >= next_index and output[index] == observed_bit:
                survivors.append(program)

        self.candidate_programs = survivors
        self.observations.append(observed_bit)

    def predict_next(self) -> float:
        if len(self.candidate_programs) == 0:
            return 0.5

        index = len(self.observations)


        num_programs_for_1 = 0
        num_live_programs = 0

        for program in self.candidate_programs:
            if len(program.output) <= index:
                continue
            num_live_programs += 1
            if program.output[index] == 1:
                num_programs_for_1 += 1

        if num_live_programs == 0:
            return 0.5

        return num_programs_for_1 / num_live_programs


class Bernoulli:
    def __init__(self, p: float):
        self.p = p

    def get_next(self) -> int:
        n = random.uniform(0,1)
        if n <= self.p:
            return 1
        else:
            return 0

def main():
    utm = UniversalTuringMachine()
    predictor = SolomonoffPredictor(utm,
                                    max_program_length=115,
                                    max_number_of_steps=100,
                                    samples=2000000,
                                    verbose=True)

    print(f"candidate programs: {len(predictor.candidate_programs)}")

    for bit in (1,0,0,0,1,1,0,0,0,1,1,0,0,0,1,1,0,0,0,1):
        print(f"P(next=1) = {predictor.predict_next():.4f}  -> observed {bit}")
        predictor.update(bit)
        print(f"  survivors: {len(predictor.candidate_programs)}")

    print(f"P(next=1) = {predictor.predict_next():.4f}")


if __name__ == "__main__":
    main()
