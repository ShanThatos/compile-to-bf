from .capture import *
from .utils import *
from ..utils import *
from .math.addsub import *
from ..registers import *


def set_cr(n: int):
    return COMPUTE.bf_set(query_data.data, b256(n, query_data.data.size))

def zcmp_not_zero():
    A = compute_extra.empty
    code = COMPUTE.bf_set(A[1], [127])
    code += COMPUTE.bf_gt(A[0], A[1], A[2], A[3])

    code += COMPUTE.bf_copy(A[0], A[1], compute_extra.copy)
    code += COMPUTE.bf_not(A[1], compute_extra.copy)
    code += COMPUTE.bf_if(A[0], set_cr(0))
    code += COMPUTE.bf_if(A[1], set_cr(2))
    return code

# zcmp A - (A < 0, 0) (A == 0, 1) (A > 0, 2)
@bfasm_ins(1, "zcmp", Priority.HIGH)
def zcmp_0():
    return route_get_data(compute.data1, "zcmp_1")
@bfasm_ins(0, priority=Priority.HIGH)
def zcmp_1():
    A = compute_extra.empty
    is_zero, is_not_zero = compute.data2[0], compute.data2[1]
    code = COMPUTE.bf_move(query_data.data, compute_extra.empty)
    code += COMPUTE.bf_set(is_zero, [1])
    for i in range(A.size):
        code += COMPUTE.bf_copy(A[i], is_not_zero, compute_extra.copy)
        code += COMPUTE.bf_if(is_not_zero, COMPUTE.bf_clear(is_zero))
    code += COMPUTE.bf_copy(is_zero, is_not_zero, compute_extra.copy)
    code += COMPUTE.bf_not(is_not_zero, compute_extra.copy)
    code += COMPUTE.bf_if(is_zero, set_cr(1))
    code += COMPUTE.bf_if(is_not_zero, zcmp_not_zero())
    code += COMPUTE.bf_set(query.id, get_reg_id("cr"))
    code += route_to_ins("set_unit")
    return code


# cmp A B - (A < B, 0) (A == B, 1) (A > B, 2)
@bfasm_ins(2, "cmp", Priority.MEDIUM)
def cmp_0():
    return route_get_data(compute.data2, "cmp_1", compute.data1)
@bfasm_ins(0, priority=Priority.MEDIUM)
def cmp_1():
    code = COMPUTE.bf_move(query_data.data, compute_extra.empty)
    code += route_get_data(compute.data1, "cmp_2")
    return code
@bfasm_ins(0, priority=Priority.MEDIUM)
def cmp_2():
    return route_to_ins("sub_3", "cmp_3")
@bfasm_ins(0, priority=Priority.MEDIUM)
def cmp_3():
    return route_to_ins("zcmp_1")

