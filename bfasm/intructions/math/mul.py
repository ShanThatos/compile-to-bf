
from ..capture import *
from ..utils import *


# mul A B -> A *= B
@bfasm_ins(2, "mul", Priority.MEDIUM)
def mul_0():
    return route_get_data(compute.data2, "mul_1", compute.data1)
@bfasm_ins(0, priority=Priority.MEDIUM)
def mul_1():
    code = COMPUTE.bf_move(query_data.data, compute_extra.empty)
    code += route_get_data(compute.data1, "mul_2", compute.data1)
    return code
@bfasm_ins(0, priority=Priority.MEDIUM)
def mul_2():
    A, B, C = query_data.data, compute_extra.empty, compute.data
    looping = query.marker
    is_odd = query.marker

    code = COMPUTE.bf_move(compute.data1, query.id)
    code += COMPUTE.bf_clear(C)

    calc_looping = COMPUTE.bf_clear(looping)
    for i in range(B.size):
        calc_looping += COMPUTE.bf_copy(B[i], query.empty[0], query.copy)
        calc_looping += COMPUTE.bf_or(looping, query.empty[0])

    calc_is_odd = COMPUTE.bf_copy(B[B.size - 1], query.copy, is_odd)
    calc_is_odd += COMPUTE.bf_mod2(query.copy, is_odd, ins_router.data1, ins_router.data2)

    add_a_to_c = ""
    for i in range(A.size - 1, -1, -1):
        add_a_to_c += COMPUTE.bf_copy(A[i], compute.instruction, query.copy)
        add_a_to_c += COMPUTE.bf_loop_dec(compute.instruction, COMPUTE.bf_inc_bytes(C[:i+1], query.empty[0], query.empty[1]))

    loop_code = calc_is_odd
    loop_code += COMPUTE.bf_if(is_odd, add_a_to_c)
    loop_code += COMPUTE.bf_shiftl_bytes(A, query_data.marker, query_data.instruction)
    loop_code += COMPUTE.bf_shiftr_bytes(B, compute_extra.copy, ins_router.data1, ins_router.data2)
    loop_code += COMPUTE.bf_set(looping, [1])

    full_loop_code = calc_looping
    full_loop_code += COMPUTE.bf_move(looping, query.copy)
    full_loop_code += COMPUTE.bf_if(query.copy, loop_code)

    code += COMPUTE.bf_set(looping, [1])
    code += COMPUTE.bf_loop(looping, full_loop_code)

    code += COMPUTE.bf_move(C, query_data.data)
    code += route_to_ins("set_unit")
    return code
