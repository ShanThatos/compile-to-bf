from bf.simp import *
from typing import List

class memrange(list):
    def __init__(self, *args, unit=None):
        super().__init__(*args)
        self.unit = unit

    @property
    def i0(self):
        return super().__getitem__(0)
    
    @property
    def il(self):
        return super().__getitem__(self.size - 1)

    @property
    def size(self):
        return len(self)

    @property
    def reversed(self):
        return memrange(reversed(self), unit=self.unit)

    def copy(self, unit=None):
        return memrange(self, unit=unit or self.unit)

    def split(self):
        return [memrange([i], unit=self.unit) for i in self]

    def __getitem__(self, key):
        if isinstance(key, int):
            key = slice(key, key+1)
        return memrange(super().__getitem__(key), unit=self.unit)

    def __add__(self, other: "memrange"):
        assert(self.unit == other.unit)
        return memrange(super().__add__(other), unit=self.unit)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, memrange) and super().__eq__(other) and self.unit == other.unit

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def clean(self):
        indices = sorted(set(self))
        self.clear()
        self.extend(indices)

def setup_unit(cls):
    all_ranges = memrange(unit=cls)
    for attr in dir(cls):
        if isinstance(mr := getattr(cls, attr), memrange):
            mrc = mr.copy(unit=cls)
            setattr(cls, attr, mrc)
            all_ranges += mrc
    all_ranges.clean()
    setattr(cls, "all", all_ranges)
    return cls


r = lambda x,y: memrange(range(x,x+y))
s = lambda x: r(x,1)

N = 2
N2 = 2*N
USIZE = 2*N+2

class base:
    marker = s(0)
    all: memrange = None

@setup_unit
class unit(base):
    instruction = s(1)
    data        = r(2,N2)
    data1       = r(2,N)
    data2       = r(2+N,N)
    idata       = r(1, N2+1)

@setup_unit
class shifter1(base):
    shifting    = unit.instruction
    data1       = unit.data1
    data2       = unit.data2

@setup_unit
class shifter2(base):
    copy        = unit.instruction
    data1       = unit.data1
    data2       = unit.data2

@setup_unit
class query_data(base):
    instruction = unit.instruction
    data        = unit.data
    data1       = unit.data1
    data2       = unit.data2
    idata       = unit.idata

@setup_unit
class query(base):
    copy        = unit.instruction
    id          = unit.data1
    empty       = unit.data2

@setup_unit
class compute(base):
    running     = unit.marker
    instruction = unit.instruction
    data        = unit.data
    data1       = unit.data1
    data2       = unit.data2
    idata       = unit.idata

@setup_unit
class compute_extra(base):
    copy        = unit.instruction
    empty       = unit.data

@setup_unit
class ins_router(base):
    instruction = unit.instruction
    data        = unit.data
    data1       = unit.data1
    data2       = unit.data2
    idata       = unit.idata

@setup_unit
class register(base):
    copy        = unit.instruction
    data        = unit.data
    data1       = unit.data1
    data2       = unit.data2


class Workspace:
    def __init__(self, units: List[base], ref: memrange = None):
        assert(len(units))
        self.units = units
        self.ref_index = self.get_index(ref or units[0].marker)

    def set_ref(self, ref: memrange):
        self.ref_index = self.get_index(ref)
    
    def get_index(self, loc: memrange) -> int:
        for i, unit in enumerate(self.units):
            if loc.unit == unit:
                return i * USIZE + loc.i0
        raise Exception("Invalid location")

    def get_distance(self, loc: memrange):
        return self.get_index(loc) - self.ref_index

    @simplify
    def bf_to(self, loc: memrange):
        return bf_f(self.get_distance(loc))
    
    @simplify
    def bf_from(self, loc: memrange):
        return bf_b(self.get_distance(loc))
    
    @simplify
    def bf_tf(self, loc: memrange, code: str):
        return self.bf_to(loc) + code + self.bf_from(loc)
    
    @simplify
    def bf_ft(self, loc: memrange, code: str):
        return self.bf_from(loc) + code + self.bf_to(loc)
    
    @simplify
    def bf_loop(self, loc: memrange, code: str):
        assert(len(loc) == 1)
        return self.bf_tf(loc, "[" + self.bf_ft(loc, code) + "]")

    @simplify
    def bf_loop_dec(self, loc: memrange, code: str):
        assert(len(loc) == 1)
        return self.bf_tf(loc, "[-" + self.bf_ft(loc, code) + "]")
    
    @simplify
    def bf_if(self, loc: memrange, code: str):
        assert(len(loc) == 1)
        return self.bf_tf(loc, "[[-]" + self.bf_ft(loc, code) + "]")

    @simplify
    def bf_foreach(self, loc: memrange, code: str):
        return "".join(self.bf_tf(l, code) for l in loc.split())

    # bf ops
    @simplify
    def bf_dec(self, loc: memrange):
        return self.bf_tf(loc, "-")

    @simplify
    def bf_inc(self, loc: memrange):
        return self.bf_tf(loc, "+")

    @simplify
    def bf_out(self, loc: memrange):
        return self.bf_tf(loc, ".")
    
    @simplify
    def bf_in(self, loc: memrange):
        return self.bf_tf(loc, ",")

    @simplify
    def bf_clear(self, loc: memrange):
        return self.bf_foreach(loc, "[-]")

    @simplify
    def bf_set(self, loc: memrange, values: List[int]):
        assert(len(loc) == len(values))
        return "".join(self.bf_tf(l, bf_set(v)) for l,v in zip(loc.split(), values))

    @simplify
    def bf_move(self, src: memrange, dest: memrange):
        assert(len(src) == len(dest))
        # code = self.bf_clear(dest)
        code = ""
        for s, d in zip(src.split(), dest.split()):
            code += self.bf_clear(d) + self.bf_loop_dec(s, self.bf_inc(d))
        return code
    
    @simplify
    def bf_copy(self, src: memrange, dest: memrange, empty: memrange):
        assert(len(src) == len(dest))
        assert(len(empty) == 1)
        code = self.bf_clear(dest) + self.bf_clear(empty)
        for s, d in zip(src.split(), dest.split()):
            code += self.bf_loop_dec(s, self.bf_inc(d) + self.bf_inc(empty))
            code += self.bf_loop_dec(empty, self.bf_inc(s))
        return code


    # mathy stuff
    @simplify
    def bf_not(self, loc: memrange, empty: memrange):
        assert(len(loc) == 1)
        assert(len(empty) == 1)
        code = self.bf_clear(empty) + self.bf_inc(empty)
        code += self.bf_if(loc, self.bf_dec(empty))
        code += self.bf_move(empty, loc)
        return code
    
    @simplify
    def bf_eq(self, loc1: memrange, loc2: memrange):
        assert(len(loc1) == 1)
        assert(len(loc2) == 1)
        code = self.bf_loop_dec(loc2, self.bf_dec(loc1))
        code += self.bf_not(loc1, loc2)
        return code

    @simplify
    def bf_or(self, loc1: memrange, loc2: memrange):
        assert(len(loc1) == 1)
        assert(len(loc2) == 1)
        code = self.bf_if(loc1, self.bf_clear(loc2) + self.bf_inc(loc2))
        code += self.bf_if(loc2, self.bf_inc(loc1))
        return code

    @simplify
    def bf_leq(self, loc1: memrange, loc2: memrange, empty1: memrange, empty2: memrange):
        assert(loc1.size == 1)
        assert(loc2.size == 1)
        assert(empty1.size == 1)
        assert(empty2.size == 1)

        code = self.bf_clear(empty1) + self.bf_clear(empty2)
        check_l1_zero = self.bf_copy(loc1, empty1, empty2)
        check_l1_zero += self.bf_not(empty1, empty2)
        check_l1_zero += self.bf_if(empty1, self.bf_inc(empty2) + self.bf_clear(loc2))

        code += check_l1_zero
        code += self.bf_loop_dec(loc2, self.bf_dec(loc1) + check_l1_zero)
        code += self.bf_move(empty2, loc1)
        return code

    @simplify
    def bf_gt(self, loc1: memrange, loc2: memrange, empty1: memrange, empty2: memrange):
        code = self.bf_leq(loc1, loc2, empty1, empty2)
        code += self.bf_not(loc1, loc2)
        return code

    @simplify
    def bf_geq(self, loc1: memrange, loc2: memrange, empty1: memrange, empty2: memrange):
        code = self.bf_leq(loc2, loc1, empty1, empty2)
        code += self.bf_move(loc2, loc1)
        return code

    @simplify
    def bf_inc_bytes(self, loc: memrange, empty1: memrange, empty2: memrange):
        assert(empty1.size == 1)
        assert(empty2.size == 1)
        if loc.size == 0: return ""
        l = loc[loc.size - 1]
        if loc.size == 1: return self.bf_inc(l)
        code = self.bf_inc(l) + self.bf_copy(l, empty1, empty2)
        code += self.bf_not(empty1, empty2)
        code += self.bf_if(empty1, self.bf_inc_bytes(loc[:loc.size - 1], empty1, empty2))
        return code

    @simplify
    def bf_dec_bytes(self, loc: memrange, empty1: memrange, empty2: memrange):
        assert(empty1.size == 1)
        assert(empty2.size == 1)
        if loc.size == 0: return ""
        l = loc[loc.size - 1]
        if loc.size == 1: return self.bf_dec(l)
        code = self.bf_copy(l, empty1, empty2)
        code += self.bf_dec(l)
        code += self.bf_not(empty1, empty2)
        code += self.bf_if(empty1, self.bf_dec_bytes(loc[:loc.size - 1], empty1, empty2))
        return code
    
    @simplify
    def bf_shiftl_bytes(self, loc: memrange, empty1: memrange, empty2: memrange):
        assert(empty1.size == 1)
        assert(empty2.size == 1)
        code = self.bf_clear(empty1) + self.bf_clear(empty2)
        for i in range(loc.size):
            code += self.bf_loop_dec(loc[i], self.bf_inc(empty2) * 2 + self.bf_inc(empty1))
            code += self.bf_loop(empty2, self.bf_dec(empty2) * 2 + self.bf_inc(loc[i]) * 2 + self.bf_dec(empty1))
            code += self.bf_if(empty1, self.bf_inc(loc[i - 1]) if i > 0 else "")
        return code

    @simplify
    def bf_shiftr_bytes(self, loc: memrange, empty1: memrange, empty2: memrange, empty3: memrange):
        assert(empty1.size == 1)
        empty2 = empty2[:2]
        empty3 = empty3[:2]
        assert(empty2.size == 2)
        assert(empty3.size == 2)
        code = self.bf_clear(empty1) + self.bf_clear(empty2) + self.bf_clear(empty3)
        for i in range(loc.size - 1, -1, -1):
            code += self.bf_div2(loc[i], empty1, empty2, empty3)
            if i != loc.size - 1:
                code += self.bf_if(empty1, self.bf_inc(loc[i + 1]) * 128)
        code += self.bf_clear(empty1)
        return code

    @simplify
    def bf_divn(self, loc: memrange, empty: memrange, n: int):
        assert(loc.size == 1)
        assert(empty.size == 1)
        assert(0 < n <= 256)
        code = self.bf_clear(empty)
        div_code = ""
        for _ in range(256 // n + 1):
            div_code = self.bf_inc(empty) + div_code
            for _ in range(n):
                div_code = self.bf_loop_dec(loc, div_code)
        code += div_code + self.bf_move(empty, loc)
        return code

    @simplify
    def bf_divn_rem(self, loc: memrange, rem: memrange, empty: memrange, n: int):
        assert(loc.size == 1)
        assert(rem.size == 1)
        assert(empty.size == 1)
        assert(0 < n <= 256)
        code = self.bf_clear(rem) + self.bf_clear(empty)
        div_code = ""
        for _ in range(256 // n + 1):
            div_code = self.bf_clear(rem) + self.bf_inc(empty) + div_code
            for _ in range(n):
                div_code = self.bf_loop_dec(loc, self.bf_inc(rem) + div_code)
        code += div_code + self.bf_move(empty, loc)
        return code

    @simplify
    def bf_divmod(self, n: memrange, divisor: int, q: memrange, r: memrange, empty1: memrange, empty2: memrange, empty3: memrange):
        d = empty3
        assert(n.size == 1)
        assert(d.size == 1)
        assert(q.size == 1)
        assert(r.size == 1)
        assert(empty1.size == 1)
        assert(empty2.size == 1)
        assert(0 < divisor < 256)

        code = self.bf_clear(d) + self.bf_clear(q) + self.bf_clear(r)
        code += self.bf_clear(empty1) + self.bf_clear(empty2)
        code += self.bf_set(d, [divisor])
        
        loop_code = self.bf_dec(n) + self.bf_dec(d)
        loop_code += self.bf_inc(r)
        loop_code += self.bf_copy(d, empty1, empty2)
        loop_code += self.bf_not(empty1, empty2)
        
        reset_d_code = self.bf_inc(q) + self.bf_clear(r)
        reset_d_code += self.bf_set(d, [divisor])
        loop_code += self.bf_if(empty1, reset_d_code)

        code += self.bf_loop(n, loop_code)
        return code

    @simplify
    def bf_mod2(self, n: memrange, r: memrange, empty1: memrange, empty2: memrange):
        assert(n.size == 1)
        assert(r.size == 1)
        empty1 = empty1[:2]
        empty2 = empty2[:2]
        assert(empty1.size == 2)
        assert(empty2.size == 2)

        code = self.bf_clear(empty1) + self.bf_clear(empty2)
        code += self.bf_inc(empty1[0]) + self.bf_move(n, empty2[0])
        code += self.bf_tf(empty2, "[-[-<]>]")
        code += self.bf_tf(empty1, "[->]<")
        code += self.bf_move(empty1[0], r)
        return code

    @simplify
    def bf_div2(self, n: memrange, r: memrange, empty1: memrange, empty2: memrange):
        assert(n.size == 1)
        assert(r.size == 1)
        assert(empty1.size == 2)
        assert(empty2.size == 2)

        code = self.bf_clear(empty1) + self.bf_clear(empty2)
        code += self.bf_inc(empty1[0]) + self.bf_move(n, empty2[0])
        code += self.bf_tf(empty2, "[-[-" + self.bf_ft(empty2, self.bf_inc(n)) + "<]>]")
        code += self.bf_tf(empty1, "[->]<")
        code += self.bf_move(empty1[0], r)
        return code
