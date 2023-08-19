from ..capture import *
from ..utils import *
from .addsub import *
from ...registers import *


@bfasm_ins(1, "even")
def even_0():
    return route_get_data(compute.data1, "even_1")
@bfasm_ins(0)
def even_1():
    code = COMPUTE.bf_move(query_data.data[query_data.data.size - 1], query_data.instruction)
    code += COMPUTE.bf_mod2(query_data.instruction, query_data.instruction, query_data.data1, query_data.data2)
    code += COMPUTE.bf_move(query_data.instruction, query_data.data[query_data.data.size - 1])
    code += COMPUTE.bf_not(query_data.data[query_data.data.size - 1], query_data.instruction)
    code += COMPUTE.bf_set(query.id, get_reg_id("cr"))
    code += route_to_ins("set_unit")
    return code


# odd A -> (even, 0) (odd, 1)
@bfasm_ins(1, "odd")
def odd_0():
    return route_get_data(compute.data1, "odd_1")
@bfasm_ins(0)
def odd_1():
    code = COMPUTE.bf_move(query_data.data[query_data.data.size - 1], query_data.instruction)
    code += COMPUTE.bf_mod2(query_data.instruction, query_data.instruction, query_data.data1, query_data.data2)
    code += COMPUTE.bf_move(query_data.instruction, query_data.data[query_data.data.size - 1])
    code += COMPUTE.bf_set(query.id, get_reg_id("cr"))
    code += route_to_ins("set_unit")
    return code


# lshift A B -> A <<= (B % 256)
@bfasm_ins(2, "lshift", priority=Priority.MEDIUM)
def lshift_0():
    return route_get_data(compute.data2, "lshift_1", compute.data1)
@bfasm_ins(0, priority=Priority.MEDIUM)
def lshift_1():
    code = COMPUTE.bf_move(query_data.data[query_data.data.size - 1], compute_extra.empty[0])
    code += route_get_data(compute.data1, "lshift_2", compute.data1)
    return code
@bfasm_ins(0, priority=Priority.MEDIUM)
def lshift_2():
    shift_code = COMPUTE.bf_shiftl_bytes(query_data.data, query_data.marker, query_data.instruction)

    code = COMPUTE.bf_loop_dec(compute_extra.empty[0], shift_code)
    code += COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code


# rshift A B -> A >>= (B % 256)
@bfasm_ins(2, "rshift", priority=Priority.MEDIUM)
def rshift_0():
    return route_get_data(compute.data2, "rshift_1", compute.data1)
@bfasm_ins(0, priority=Priority.MEDIUM)
def rshift_1():
    code = COMPUTE.bf_move(query_data.data[query_data.data.size - 1], compute_extra.empty[0])
    code += route_get_data(compute.data1, "rshift_2", compute.data1)
    return code
@bfasm_ins(0, priority=Priority.MEDIUM)
def rshift_2():
    shift_code = COMPUTE.bf_shiftr_bytes(query_data.data, compute_extra.marker, compute_extra.empty[0:2], compute_extra.empty[2:4])
    
    code = COMPUTE.bf_move(compute_extra.empty[0], compute.instruction)
    code += COMPUTE.bf_loop_dec(compute.instruction, shift_code)
    code += COMPUTE.bf_move(compute.data1, query.id) 
    code += route_to_ins("set_unit")
    return code
