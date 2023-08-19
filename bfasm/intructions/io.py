from .capture import *
from .utils import *


@bfasm_ins(1, "out")
def out_0():
    return route_get_data(compute.data1, callback="out_1")
@bfasm_ins(0)
def out_1():
    return COMPUTE.bf_out(query_data.data[query_data.data.size - 1])


@bfasm_ins(1, "in")
def in_():
    code = COMPUTE.bf_clear(query_data.data)
    code += COMPUTE.bf_in(query_data.data[query_data.data.size - 1])
    code += COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code

