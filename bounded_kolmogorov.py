from universal_turing_machine import UniversalTuringMachine, Enumerator

def bounded_kolmogorov(target_output: str, max_program_length: int, max_steps: int, utm: UniversalTuringMachine) -> int:
    enumerator = Enumerator()

    while True:
        program = enumerator.generate_next()

        #programs are enumerated shortest-first, so once we exceed the bound
        #every remaining candidate is also too long: no shorter match exists.
        if len(program) > max_program_length:
            return max_program_length + 1

        try:
            utm.decode(program)
            halted = utm.run_on_input("", max_steps)
        except (ValueError, IndexError):
            continue

        if halted is None:
            continue

        blank = str(utm.tm.blank_index)
        output = utm.tm.get_tape_as_string().strip(blank)

        if output == target_output:
            return len(program)
