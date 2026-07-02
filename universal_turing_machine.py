from turing_machine import TuringMachine
from encoder import Encoder
import math

class UniversalTuringMachine:
    def decode(self, encoding: str):
        number_of_states = encoding.find("0")
        encoding = encoding[number_of_states+1:]
        alphabet_length = encoding.find("0")
        encoding = encoding[alphabet_length+1:]

        state_bits = math.ceil(math.log2(number_of_states)) if number_of_states > 1 else 1
        symbol_bits = math.ceil(math.log2(alphabet_length)) if alphabet_length > 1 else 1

        start_state = int(encoding[:state_bits], 2)
        encoding = encoding[state_bits:]

        accept_state = int(encoding[:state_bits], 2)
        encoding = encoding[state_bits:]


        reject_state = int(encoding[:state_bits], 2)
        encoding = encoding[state_bits:]

        transition_function = list()

        for _ in range(number_of_states * alphabet_length):
            new_state = int(encoding[:state_bits], 2)
            encoding = encoding[state_bits:]
            new_symbol = int(encoding[:symbol_bits], 2)
            encoding = encoding[symbol_bits:]
            direction = int(encoding[:1], 2)
            encoding = encoding[1:]

            transition_function.append((new_state, new_symbol, direction))

        blank_index = int(encoding[:symbol_bits], 2)

        self.tm = TuringMachine(tuple(range(number_of_states)), alphabet_length, blank_index, transition_function, start_state, accept_state, reject_state)

    def run_on_input(self, input_string: str, number_of_steps: int):

        try:
            self.tm.reset(input_string)
        except ValueError:
            raise ValueError("max steps must be a number")
        
        halt = self.tm.run(number_of_steps)
        if halt is not None:
            return halt

class Enumerator:
    def __init__(self):
        self.generator = self._generate_string()

    def _generate_string(self):
        yield ""
        i = 1
        while True:
            for j in range(1 << i):
                yield f"{j:0{i}b}"
            i += 1
    
    def generate_next(self):
        return next(self.generator)
        

def main():
    utm = UniversalTuringMachine()
    utm.decode("11110111001101101001010111110100001000111010110101101011010110101101011010110")

    tm = utm.tm

    print(utm.run_on_input("", 10000))

    enumerator = Enumerator()
    print(enumerator.generate_next())
    print(enumerator.generate_next())
    print(enumerator.generate_next())
    print(enumerator.generate_next())
    print(enumerator.generate_next())
    print(enumerator.generate_next())
    print(enumerator.generate_next())
    print(enumerator.generate_next())
    print(enumerator.generate_next())
    
    
    #print(f"states: {tm.states}, \nalphabet: {tm.alphabet}, \n blank index: {tm.blank_index}, \ntransition: {tm.transition}, \nstart: {tm.start}, \naccept: {tm.accept}, \nreject: {tm.reject}")



if __name__ == "__main__":
    main()
