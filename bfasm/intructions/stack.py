from .capture import *
from .utils import *
from .math.addsub import *
from ..registers import *


# push A
@bfasm_ins(1, "push", Priority.HIGH)
def push_0():
    move_forward = UNIT.bf_move(unit.all.reversed, memrange(list(range(USIZE, USIZE * 2)), unit=unit).reversed)

    code = COMPUTE.bf_to(COMPUTE.units[0].marker)
    num_units = len(COMPUTE.units) + len(REGISTERS)
    for i in range(num_units - 1, -1, -1):
        code += bf_fb(USIZE * i, move_forward)
    code += bf_f(USIZE) + COMPUTE.bf_from(COMPUTE.units[0].marker)
    code += route_get_data(compute.data1, "push_1")
    return code
@bfasm_ins(0, priority=Priority.HIGH)
def push_1():
    code = COMPUTE.bf_set(query_data.instruction, [get_instruction("ref").id])
    for i in range(query_data.idata.size):
        code += COMPUTE.bf_tf(query_data.idata[i], "[-" + bf_bf(USIZE, "+") + "]")
    return code


# pop A
@bfasm_ins(1, "pop", priority=Priority.HIGH)
def pop_0():
    move_backward = UNIT.bf_move(unit.all, memrange(list(range(-USIZE, 0)), unit=unit))
    # ignore query_data since it will be filled with the last item on the stack
    code = COMPUTE.bf_to(COMPUTE.units[1].marker)
    num_units = len(COMPUTE.units) + len(REGISTERS) - 1
    for i in range(num_units):
        code += bf_fb(USIZE * i, move_backward)
    code += bf_b(USIZE) + COMPUTE.bf_from(COMPUTE.units[1].marker)

    code += COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code

