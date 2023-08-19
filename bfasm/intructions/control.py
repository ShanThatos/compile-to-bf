from .capture import *
from .utils import *
from ..registers import *

@bfasm_ins()
def dbg():
    return "@"

@bfasm_ins()
def noop():
    return ""

@bfasm_ins()
def end():
    return "[-]"


@bfasm_ins(1, "jp", priority=Priority.MEDIUM)
def jp_0():
    return route_get_data(compute.data1, "jp_1")
@bfasm_ins(0, priority=Priority.MEDIUM)
def jp_1():
    ip_index = USIZE + get_reg_idx("ip") * USIZE
    ip_start_index = ip_index + register.data2.i0
    ip_end_index = ip_start_index + register.data2.size
    ip_data = memrange(list(range(ip_start_index, ip_end_index)), unit=COMPUTE.units[-1])

    code = COMPUTE.bf_move(query_data.data2, ip_data)
    return code


# jpif A B - jump to A if B != 0
@bfasm_ins(2, "jpif")
def jpif_0():
    return route_get_data(compute.data2, callback="jpif_1", cb_data1=compute.data1)
@bfasm_ins(0)
def jpif_1():
    B = query_data.data
    code = "".join(COMPUTE.bf_or(B[0], B[i]) for i in range(1, B.size))
    code += COMPUTE.bf_if(B[0], route_to_ins("jp"))
    return code


# jpz A B - jump to A if B == 0
@bfasm_ins(2, "jpz")
def jpz_0():
    return route_get_data(compute.data2, callback="jpz_1", cb_data1=compute.data1)
@bfasm_ins(0)
def jpz_1():
    B = query_data.data
    code = "".join(COMPUTE.bf_or(B[0], B[i]) for i in range(1, B.size))
    code += COMPUTE.bf_not(B[0], B[1])
    code += COMPUTE.bf_if(B[0], route_to_ins("jp"))
    return code


@bfasm_ins(0, "next_ins", Priority.HIGH)
def next_ins_0():
    ip_index = USIZE + get_reg_idx("ip") * USIZE
    ip_copy_index = ip_index + register.copy.i0
    ip_start_index = ip_index + register.data2.i0
    ip_end_index = ip_start_index + register.data2.size
    ip_mr = memrange([ip_index], unit=COMPUTE.units[-1])
    ip_data = memrange(list(range(ip_start_index, ip_end_index)), unit=COMPUTE.units[-1])
    ip_copy = memrange([ip_copy_index], unit=COMPUTE.units[-1])
    
    code = COMPUTE.bf_tf(ip_mr, REGISTER.bf_inc_bytes(register.data2, register.data1[0], register.data1[1]))
    code += COMPUTE.bf_copy(ip_data, query.id, ip_copy)
    code += route_to_ins("get_unit", "next_ins_1")
    return code
@bfasm_ins(0, priority=Priority.HIGH)
def next_ins_1():
    return COMPUTE.bf_move(query_data.idata, compute.idata)
