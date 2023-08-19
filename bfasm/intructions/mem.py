from .capture import *
from .utils import *


@bfasm_ins(2, "mov", Priority.MEDIUM)
def mov_0():
    return route_get_data(compute.data2, callback="mov_1", cb_data1=compute.data1)
@bfasm_ins(0, priority=Priority.MEDIUM)
def mov_1():
    code = COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code


@bfasm_ins(2, "movl")
def movl_0():
    return route_get_data(compute.data2, callback="movl_1", cb_data1=compute.data1)
@bfasm_ins(0)
def movl_1():
    return route_get_data(compute.data1, callback="movl_2", cb_data1=compute.data1, cb_data2=query_data.data2)
@bfasm_ins(0)
def movl_2():
    code = COMPUTE.bf_move(compute.data2, query_data.data2)
    code += COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code


@bfasm_ins(2, "movh")
def movh_0():
    return route_get_data(compute.data2, callback="movh_1", cb_data1=compute.data1)
@bfasm_ins(0)
def movh_1():
    return route_get_data(compute.data1, callback="movh_2", cb_data1=compute.data1, cb_data2=query_data.data2)
@bfasm_ins(0)
def movh_2():
    code = COMPUTE.bf_move(compute.data2, query_data.data1)
    code += COMPUTE.bf_move(compute.data1, query.id)
    code += route_to_ins("set_unit")
    return code


# get A B -> A = B*
@bfasm_ins(2, "get")
def get_0():
    return route_get_data(compute.data2, callback="get_1", cb_data1=compute.data1)
@bfasm_ins(0)
def get_1():
    return route_get_data(query_data.data2, callback="mov_1", cb_data1=compute.data1)


# set A B -> A* = B
@bfasm_ins(2, "set")
def set_0():
    return route_get_data(compute.data1, callback="set_1", cb_data2=compute.data2)
@bfasm_ins(0)
def set_1():
    code = COMPUTE.bf_move(query_data.data2, compute.data1)
    code += COMPUTE.bf_set(compute.instruction, [get_instruction("mov").id])
    return code

@bfasm_ins(0, "mark_reg", Priority.HIGH)
def mark_reg():
    gfm = bf_glide_f(254, USIZE)
    gb = bf_glide_b(255, USIZE)
    first_reg_marker = memrange([USIZE], unit=COMPUTE.units[-1])
    code = COMPUTE.bf_set(first_reg_marker, [254])
    code += COMPUTE.bf_loop_dec(query.id[query.id.size - 1], gfm + "[-]" + bf_f(USIZE) + REGISTER.bf_set(register.marker, [254]) + gb)
    code += COMPUTE.bf_clear(query.id)
    
    code += COMPUTE.bf_copy(query.marker, query.id[0], query.copy)
    code += COMPUTE.bf_not(query.id[0], query.copy)
    code += COMPUTE.bf_if(query.marker, COMPUTE.bf_set(compute.instruction, [get_instruction("get_reg").id]))
    code += COMPUTE.bf_if(query.id[0], COMPUTE.bf_set(compute.instruction, [get_instruction("set_reg").id]))
    return code


@bfasm_ins(0, "mark_mem", Priority.HIGH)
def mark_mem():
    gb = bf_glide_b(253, USIZE) # glide back to shifter
    gf = bf_glide_f(255, USIZE) # glide to compute
    gfm = bf_glide_f(254, USIZE) # glide to the marker

    # move the id back to the shifter
    code = ""
    for i in range(len(query.id)):
        code += COMPUTE.bf_loop_dec(query.id[i], gb + SHIFTER.bf_inc(shifter1.data1[i]) + gf)
    code += gb

    # set the first marker
    code += SHIFTER.bf_set(memrange([USIZE], unit=SHIFTER.units[-1]), [254])

    calc_shifting = SHIFTER.bf_clear(shifter2.marker)
    for i in range(shifter1.data1.size):
        calc_shifting += SHIFTER.bf_copy(shifter1.data1[i], shifter1.data2[1], shifter1.data2[0])
        calc_shifting += SHIFTER.bf_or(shifter2.marker, shifter1.data2[1])
    calc_shifting += SHIFTER.bf_copy(shifter2.marker, shifter1.shifting, shifter2.copy)

    last_byte = shifter1.data1[shifter1.data1.size - 1]

    zero_case_shift = SHIFTER.bf_dec_bytes(shifter1.data1[:-1], shifter1.data2[0], shifter1.data2[1])
    zero_case_shift += SHIFTER.bf_clear(last_byte)
    zero_case_shift += gfm + "[-]" + bf_f(256 * USIZE) + UNIT.bf_set(unit.marker, [254]) + gb

    nonzero_case_shift = SHIFTER.bf_loop_dec(last_byte, gfm + "[-]" + bf_f(USIZE) + UNIT.bf_set(unit.marker, [254]) + gb)

    shift_code = SHIFTER.bf_copy(last_byte, shifter1.data2[0], shifter1.data2[1])
    shift_code += SHIFTER.bf_not(shifter1.data2[0], shifter1.data2[1])
    shift_code += SHIFTER.bf_if(shifter1.data2[0], zero_case_shift)
    shift_code += SHIFTER.bf_copy(last_byte, shifter1.data2[0], shifter1.data2[1])
    shift_code += SHIFTER.bf_if(shifter1.data2[0], nonzero_case_shift)

    code += SHIFTER.bf_set(shifter1.shifting, [1])
    code += SHIFTER.bf_loop(shifter1.shifting, calc_shifting + SHIFTER.bf_if(shifter2.marker, shift_code))
    code += gf
    
    code += COMPUTE.bf_copy(query.marker, query.id[0], query.copy)
    code += COMPUTE.bf_not(query.id[0], query.copy)
    code += COMPUTE.bf_if(query.marker, COMPUTE.bf_set(compute.instruction, [get_instruction("get_mem").id]))
    code += COMPUTE.bf_if(query.id[0], COMPUTE.bf_set(compute.instruction, [get_instruction("set_mem").id]))

    return code


@bfasm_ins(0, "get_set_unit", Priority.HIGH)
def get_set_unit():
    # check if it's in registers or memory
    is_reg, is_mem = query.empty[0], query.empty[1]
    code = COMPUTE.bf_clear(is_reg + is_mem)
    code += COMPUTE.bf_copy(query.id[0], is_reg, query.copy)
    code += COMPUTE.bf_inc(is_reg)
    code += COMPUTE.bf_copy(is_reg, is_mem, query.copy)
    code += COMPUTE.bf_not(is_reg,  query.copy)

    code += COMPUTE.bf_if(is_reg, COMPUTE.bf_set(compute.instruction, [get_instruction("mark_reg").id]))
    code += COMPUTE.bf_if(is_mem, COMPUTE.bf_set(compute.instruction, [get_instruction("mark_mem").id]))

    return code


@bfasm_ins(0, "set_unit", Priority.MEDIUM)
def set_unit():
    code = COMPUTE.bf_clear(query.marker) 
    code += COMPUTE.bf_set(compute.instruction, [get_instruction("get_set_unit").id])
    return code

@bfasm_ins(0, "set_reg", Priority.MEDIUM)
@bfasm_callback
def set_reg():
    gf, gb = bf_glide_f(254, USIZE), bf_glide_b(255, USIZE)
    code = gf + REGISTER.bf_clear(register.data) + gb
    for i in range(query_data.data.size):
        code += COMPUTE.bf_loop_dec(query_data.data[i], gf + REGISTER.bf_inc(register.data[i]) + gb)
    code += gf + REGISTER.bf_clear(register.marker) + gb
    return code


@bfasm_ins(0, "set_mem", Priority.MEDIUM)
@bfasm_callback
def set_mem():
    gb, gf = bf_glide_b(254, USIZE), bf_glide_f(255, USIZE)
    code = gb + UNIT.bf_clear(unit.idata) + gf
    for i in range(unit.idata.size):
        code += COMPUTE.bf_loop_dec(query_data.idata[i], gb + UNIT.bf_inc(unit.idata[i]) + gf)
    code += gb + UNIT.bf_clear(unit.marker) + gf
    return code




@bfasm_ins(0, "get_unit", Priority.HIGH)
def get_unit():
    code = COMPUTE.bf_set(query.marker, [1])
    code += COMPUTE.bf_set(compute.instruction, [get_instruction("get_set_unit").id])
    return code

@bfasm_ins(0, "get_reg", Priority.HIGH)
@bfasm_callback
def get_reg():
    gf, gb = bf_glide_f(254, USIZE), bf_glide_b(255, USIZE)
    code = COMPUTE.bf_clear(query_data.idata)
    code += gf

    for i in range(register.data.size):
        inc = REGISTER.bf_inc(register.copy) + gb + COMPUTE.bf_inc(query_data.data[i]) + gf
        code += REGISTER.bf_loop_dec(register.data[i], inc)
        code += REGISTER.bf_move(register.copy, register.data[i])
    
    code += REGISTER.bf_clear(register.marker)
    code += gb
    return code

@bfasm_ins(0, "get_mem", Priority.HIGH)
@bfasm_callback
def get_mem():
    gb, gf = bf_glide_b(254, USIZE), bf_glide_f(255, USIZE)

    prev_marker = memrange([-USIZE], unit=unit)
    code = COMPUTE.bf_clear(query_data.idata) + gb
    for i in range(unit.idata.size):
        inc = UNIT.bf_inc(prev_marker) + gf + COMPUTE.bf_inc(query_data.idata[i]) + gb
        code += UNIT.bf_loop_dec(unit.idata[i], inc)
        code += UNIT.bf_move(prev_marker, unit.idata[i])
    code += UNIT.bf_clear(unit.marker) + gf

    return code
