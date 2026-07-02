from turing_machine import TuringMachine
import math

class Encoder:
    def encode(self, tm: TuringMachine) -> str:
        number_of_states = "".join('1' for state in range(len(tm.states))) + "0"
        alphabet_length = "".join('1' for state in range(len(tm.alphabet))) + "0"

        state_bits = math.ceil(math.log2(len(tm.states))) if len(tm.states) > 1 else 1
        symbol_bits = math.ceil(math.log2(len(tm.alphabet))) if len(tm.alphabet) > 1 else 1

        start_state_index = f"{tm.start:0{state_bits}b}"
        accept_state_index = f"{tm.accept:0{state_bits}b}"
        reject_state_index = f"{tm.reject:0{state_bits}b}"

        transition_function = ""

        for new_state, new_symbol, direction in tm.transition:
            transition_function += f"{new_state:0{state_bits}b}"
            transition_function += f"{new_symbol:0{symbol_bits}b}"
            transition_function += str(direction)

        blank_index = f"{tm.blank_index:0{symbol_bits}b}"

        encoding = number_of_states + alphabet_length + start_state_index + accept_state_index + reject_state_index + transition_function + blank_index
        return encoding

def main():

    t = TuringMachine((0,1), 2, 0, ((1,1,1), (0,0,0), (1,0,1), (0,1,0)), 0, 1, 0)
    
    #(0,1,2), ('0','1','_'), '_', ((1, '1', 1), (1, '0', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1), (2, '_', 1)), 0, 1, 2

    e = Encoder()
    print(e.encode(t))

if __name__ == "__main__":
    main()