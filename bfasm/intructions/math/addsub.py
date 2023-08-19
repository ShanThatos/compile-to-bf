
from ..capture import *
from ..utils import *


A, B = query_data.data, compute_extra.empty


# inc A -> A += 1
@bfasm_ins(1, "inc")
def inc_0():
    return route_get_data(compute.data1, "inc_1", compute.data1)
@bfasm_ins(0)
def inc_1():
    code = COMPUTE.bf_inc_bytes(query_data.data, query_data.instruction, query.copy)
    code += COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code


# dec A -> A -= 1
@bfasm_ins(1, "dec")
def dec_0():
    return route_get_data(compute.data1, "dec_1", compute.data1)
@bfasm_ins(0)
def dec_1():
    code = COMPUTE.bf_dec_bytes(query_data.data, query_data.instruction, query.copy)
    code += COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code


# neg A -> A = -A
@bfasm_ins(1, "neg")
def neg_0():
    return route_get_data(compute.data1, "neg_1", compute.data1)
@bfasm_ins(0)
def neg_1():
    code = ""
    for i in range(query_data.data.size):
        code += COMPUTE.bf_set(query.copy, [255])
        code += COMPUTE.bf_loop_dec(query_data.data[i], COMPUTE.bf_dec(query.copy))
        code += COMPUTE.bf_move(query.copy, query_data.data[i])
    code += route_to_ins("inc_1")
    return code


# add A B -> A += B
@bfasm_ins(2, "add", Priority.MEDIUM)
def add_0():
    return route_get_data(compute.data2, "add_1", compute.data1)
@bfasm_ins(0, priority=Priority.MEDIUM)
def add_1():
    code = COMPUTE.bf_move(query_data.data, compute_extra.empty)
    code += route_get_data(compute.data1, "add_2", compute.data1)
    return code
@bfasm_ins(0, priority=Priority.MEDIUM)
def add_2():
    A, B = query_data.data, compute_extra.empty
    code = ""
    for i in range(B.size - 1, -1, -1):
        code += COMPUTE.bf_loop_dec(B[i], COMPUTE.bf_inc_bytes(A[:i+1], query.copy, compute_extra.copy))
    code += COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code


# sub A B -> A -= B
@bfasm_ins(2, "sub", Priority.MEDIUM)
def sub_0():
    return route_get_data(compute.data2, "sub_1", compute.data1)
@bfasm_ins(0, priority=Priority.MEDIUM)
def sub_1():
    code = COMPUTE.bf_move(query_data.data, compute_extra.empty)
    code += route_get_data(compute.data1, "sub_2", compute.data1)
    return code
@bfasm_ins(0, priority=Priority.MEDIUM)
def sub_2():
    return route_to_ins("sub_3", "sub_4", compute.data1)
@bfasm_ins(0, priority=Priority.MEDIUM)
@bfasm_callback
def sub_3():
    A, B = query_data.data, compute_extra.empty
    code = ""
    for i in range(B.size - 1, -1, -1):
        code += COMPUTE.bf_loop_dec(B[i], COMPUTE.bf_dec_bytes(A[:i+1], query.copy, compute_extra.copy))
    return code
@bfasm_ins(0, priority=Priority.MEDIUM)
def sub_4():
    code = COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code

