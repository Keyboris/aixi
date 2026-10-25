import multiprocessing
import os
import random
import matplotlib.pyplot as plt
import numpy as np

from collections import Counter
from universal_turing_machine import UniversalTuringMachine
from turing_machine import TuringMachine
from TMEnumerator import TMEnumerator
from encoder import Encoder
 
def _simulate(program_string: str, utm: UniversalTuringMachine, max_steps: int, max_bits: int):
    """Returns (output, status) or None if the program cannot be decoded/run.
    status is "halted", "stalled" (ran out of steps) or "capped" (still emitting at max_bits).
    All three keep their output: update() eliminates a program once the data runs past it."""
    try:
        utm.decode(program_string)
        utm.run_on_input("", max_steps, max_bits)
    except Exception:
        return None
 
    return utm.tm.output, utm.tm.status
 
 
_worker_utm = None
_worker_max_steps = None
_worker_max_bits = None
 
 
def _worker_init(max_steps: int, max_bits: int):
    global _worker_utm, _worker_max_steps, _worker_max_bits
    _worker_utm = UniversalTuringMachine()
    _worker_max_steps = max_steps
    _worker_max_bits = max_bits
 
 
def _worker_simulate(program_string: str):
    return _simulate(program_string, _worker_utm, _worker_max_steps, _worker_max_bits)
 
 
class _CandidateProgram:
    __slots__ = ("string", "output", "status")
 
    def __init__(self, string: str, output: list, status: str = None):
        self.string = string
        self.output = output
        self.status = status
 
    def __repr__(self):
        return f"_CandidateProgram({self.string!r}, o={self.output!r}, {self.status})"
 
 
class SolomonoffPredictor:
 
    def __init__(self, utm: UniversalTuringMachine,
                 max_program_length: int,
                 max_number_of_steps: int,
                 samples: int = 10000,
                 enumerator: TMEnumerator = None,
                 processes: int | None = None,
                 chunksize: int = 64,
                 verbose: bool = False,
                 max_number_of_bits: int = 100):
        if max_program_length < 0:
            raise ValueError("max_program_length must be non-negative")
        if max_number_of_steps is None or max_number_of_steps <= 0:
            raise ValueError("max_number_of_steps must be a positive integer")
        if max_number_of_bits is None or max_number_of_bits <= 0:
            raise ValueError("max_number_of_bits must be a positive integer")
 
        self.encoder = Encoder()
        self.utm = utm if utm is not None else UniversalTuringMachine()
        self.max_program_length = max_program_length
        #max_number_of_steps is a budget PER EMITTED BIT; max_number_of_bits caps how many bits a
        #program may emit, so it is also the longest observation sequence the pool can follow
        self.max_number_of_steps = max_number_of_steps
        self.max_number_of_bits = max_number_of_bits
        self.enumerator = (enumerator if enumerator is not None
                           else TMEnumerator(self.max_program_length, samples))
 
        self.observations = []
        self.candidate_programs = []
        self.status_counts = Counter()
 
        program_strings = self._sample_program_strings()
 
        if verbose:
            print(self.enumerator.length_report([len(s) for s in program_strings]))
 
        results = self._simulate_all(program_strings, processes, chunksize)
        for string, result in zip(program_strings, results):
            if result is None:
                self.status_counts["undecodable"] += 1
                continue
            output, status = result
            self.status_counts[status] += 1
            if not output:
                continue
            self.candidate_programs.append(_CandidateProgram(string, output, status))
 
        if verbose:
            print(f"{len(self.candidate_programs)} of {len(program_strings)} sampled programs "
                  f"emitted at least one bit within the step budget")
            print(f"run outcomes over all samples: {dict(self.status_counts)}")
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
            results = [_simulate(s, utm, self.max_number_of_steps, self.max_number_of_bits)
                       for s in unique]
        else:
            with multiprocessing.Pool(processes,
                                      initializer=_worker_init,
                                      initargs=(self.max_number_of_steps, self.max_number_of_bits)) as pool:
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
