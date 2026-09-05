from collections import defaultdict

class TuringMachine:
    def __init__(self, states, alphabet_length, blank_index, transition, start, halt):
        self.states = states  # i will flatten a 2d array and represent the whole thing as an array. given the key pair (i,c), the correct index in an array
                              # will be i * k + l where K is the size of the alphabet and l is the index of c in the alphabet
        self.alphabet = [x for x in range(0, alphabet_length)]
        self.blank_index = blank_index
        self.transition = transition  # each entry is (new_state, new_symbol, direction, emit)
        self.start = start
        self.halt = halt

    def step(self) -> bool:
        if self.current_state == self.halt:
            return True

        transition_index = self.current_state * len(self.alphabet) + self.tape[self.head_pos]
        (next_state, symbol_to_write, direction, emit) = self.transition[transition_index]

        self.tape[self.head_pos] = symbol_to_write
        self.current_state = next_state

        if emit:
            #the machine chooses what it writes, so symbol % 2 still lets it emit either bit,
            #and the stream stays binary whatever the alphabet size is
            self.output.append(symbol_to_write % 2)

        if direction == 0:
            self.head_pos -= 1
        else : self.head_pos += 1

        return next_state == self.halt


    def run(self, max_steps) -> bool:
        if max_steps is None:
            raise ValueError("max steps must be a number")
        for _ in range(max_steps):
            if self.step():
                return True
        return False

    def get_tape_as_string(self) -> str:
        return "".join(f"{val}" for pos, val in sorted(self.tape.items()))

    def get_output_as_string(self) -> str:
        return "".join(str(bit) for bit in self.output)

    def reset(self, input_string: str):
        program_dict = defaultdict(lambda: self.alphabet[self.blank_index])
        for pos, c in enumerate(input_string):
            if (int(c) not in self.alphabet):
                raise ValueError(f"character {c} at position {pos} is not in alphabet")
            program_dict[pos] = int(c)

        self.tape = program_dict
        self.head_pos = 0
        self.current_state = self.start
        self.output = []


def main():
    #emits 0,1,0,1,... forever: two working states (0 and 1) ping pong, state 2 is the halt state
    alternating = TuringMachine((0, 1, 2), 2, 0,
                                ((1, 0, 1, 1), (1, 0, 1, 1),
                                 (0, 1, 1, 1), (0, 1, 1, 1),
                                 (2, 0, 1, 0), (2, 0, 1, 0)), 0, 2)
    alternating.reset("")
    print(f"halted={alternating.run(10)} output={alternating.get_output_as_string()}")

    #emits a single 1 and halts
    one_bit = TuringMachine((0, 1), 2, 0,
                            ((1, 1, 1, 1), (1, 1, 1, 1),
                             (1, 0, 1, 0), (1, 0, 1, 0)), 0, 1)
    one_bit.reset("")
    print(f"halted={one_bit.run(10)} output={one_bit.get_output_as_string()}")


if __name__ == "__main__":
    main()