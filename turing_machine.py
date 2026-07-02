from collections import defaultdict

class TuringMachine:
    def __init__(self, states, num_symbols, blank_index, transition, start, accept, reject): #i want transition as hashmap by the current state and symbol as keys
        self.states = states  # i will flatten a 2d array and represent the whole thing as an array. given the key pair (i,c), the correct index in an array
                              # will be i * k + l where K is the size of the alphabet and l is the index of c in the alphabet
        self.alphabet = [x for x in range(0, num_symbols)]
        self.blank_index = blank_index
        self.transition = transition
        self.start = start
        self.accept = accept
        self.reject = reject

    def step(self) -> bool: # one transition; returns False if halted
        transition_index = self.current_state * len(self.alphabet) + self.tape[self.head_pos]
        (next_state, symbol_to_write, direction) = self.transition[transition_index]

        self.tape[self.head_pos] = symbol_to_write
        self.current_state = next_state
        
        if direction == 0:
            self.head_pos -= 1          
        else : self.head_pos += 1

        if next_state == self.reject: return False
        if next_state == self.accept: return True


    def run(self, max_steps): # runs to halt or step limit
        if max_steps is None:
            raise ValueError("max steps must be a number")
        for _ in range(max_steps):
            halt = self.step()
            if (halt is not None):
                return halt

    def get_tape_as_string(self) -> str:  #maybe useful later
        return "".join(f"{val}" for pos, val in sorted(self.tape.items()))

    def reset(self, input_string: str):
        program_dict = defaultdict(lambda: self.alphabet[self.blank_index])
        for pos, c in enumerate(input_string):
            if (int(c) not in self.alphabet):
                raise ValueError(f"character {c} at position {pos} is not in alphabet")
            program_dict[pos] = int(c)

        self.tape = program_dict
        self.head_pos = 0
        self.current_state = self.start
        

def main():
    t = TuringMachine((0,1,2,3), 3, 2, ((1, 0, 1),(1, 1, 1), (3, 2, 1), (0, 0, 1), (0, 1, 1), (2, 2, 1), (2, 2 , 1), (2, 2 , 1), (2, 2 , 1), (2, 2 , 1), (2, 2 , 1), (2, 2 , 1)), 1, 2, 3)

    #program to accept anything non empty: (0,1,2), ('0','1','_'), '_', ((1, '1', 1), (1, '0', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1)), 0, 1, 2
    #program to accept string of even length: (0,1,2,3), ('0','1','_'), '_', ((1,'0',1),(1,'1',1), (3, '_', 1), (0,'0',1), (0,'1',1), (2, '_',1),(2, '_', 1),(2, '_', 1),(2, '_', 1),(2, '_', 1),(2, '_', 1),(2, '_', 1)), 1, 2, 3
    t.reset("2")
    print(t.run(10))


if __name__ == "__main__":
    main()