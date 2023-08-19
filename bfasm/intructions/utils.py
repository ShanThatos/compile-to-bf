from ..workspaces import *
from .capture import *

from functools import wraps


def bfasm_callback(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        code = func(*args, **kwargs)
        code += COMPUTE.bf_move(ins_router.idata, compute.idata)
        return code
    return wrapper

@simplify
def route_to_ins(ins_name: str, callback: str = None, cb_data1: memrange = None, cb_data2: memrange = None):
    ins = get_instruction(ins_name)
    code = COMPUTE.bf_set(compute.instruction, [ins.id])
    if cb_data1 is not None:
        code += COMPUTE.bf_move(cb_data1, ins_router.data1)
    if cb_data2 is not None:
        code += COMPUTE.bf_move(cb_data2, ins_router.data2)
    if callback is None:
        code += COMPUTE.bf_clear(ins_router.idata)
    else:
        code += COMPUTE.bf_set(ins_router.instruction, [get_instruction(callback).id])
    return code

@simplify
def route_get_data(data_loc: memrange, callback: str, cb_data1: memrange = None, cb_data2: memrange = None):
    code = COMPUTE.bf_move(data_loc, query.id)
    if data_loc == cb_data1 or data_loc == cb_data2:
        code = COMPUTE.bf_copy(data_loc, query.id, query.copy)
    if data_loc == query.id:
        code = ""
    code += route_to_ins("get_unit", callback, cb_data1, cb_data2)
    return code


