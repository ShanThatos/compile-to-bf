
from bf.simp import *
from .units import *
from .registers import *
from .intructions.all import *
from .workspaces import *
from .utils import *



@simplify
def generate_program(program: List[int]):
    code = setup(program)
    code += program_loop()
    return code


@simplify
def setup(program: List[int]):
    assert(len(program) % USIZE == 0)

    code = SHIFTER.bf_set(shifter1.marker, [253])
    code += ">" * USIZE * len(SHIFTER.units)
    code += "".join((bf_set(v) if v != 0 else "") + ">" for v in program)
    code += ">" * USIZE * len(COMPUTE.units)

    # setting up all registers
    for _reg, v in REGISTERS:
        if v: code += REGISTER.bf_set(register.data, b256(v, register.data.size))
        code += ">" * USIZE * len(REGISTER.units)
    code += "<" * USIZE * len(REGISTER.units) * len(REGISTERS)

    # move to compute.running
    code += "<" * USIZE * len(COMPUTE.units) + ">" * COMPUTE.get_index(compute.running)
    code += COMPUTE.bf_set(compute.running, [255])
    return code

@simplify
def program_loop():
    code = COMPUTE.bf_set(compute.instruction, [get_instruction("next_ins").id])
    lookup_and_execute = ""
    for ins in INSTRUCTIONS:
        check_match_and_run = COMPUTE.bf_copy(compute.instruction, query.empty[0], query.copy)
        check_match_and_run += COMPUTE.bf_dec(query.empty[0]) * ins.id
        check_match_and_run += COMPUTE.bf_not(query.empty[0], query.copy)
        run_ins = COMPUTE.bf_clear(compute.instruction) + ins.code
        check_match_and_run += COMPUTE.bf_if(query.empty[0], run_ins)
        lookup_and_execute += check_match_and_run
    
    code += COMPUTE.bf_loop(compute.instruction, lookup_and_execute)
    return COMPUTE.bf_loop(compute.running, code)

