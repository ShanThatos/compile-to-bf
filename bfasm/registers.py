from .units import *

CONSTANT_REGISTERS = {"0": "ZERO", "1": "ONE", "2": "TWO", "48": "FORTY_EIGHT"}

REGISTERS = [
    ("ip", 0),
    ("cr", 0), # comparison register
    ("e0", 0), # expression registers / return value
    ("e1", 0),
    ("r0", 0), # fast registers
    ("r1", 0),
    ("r2", 0),
    ("cp", 0), # call pointer
    ("this", 0), # this pointer
    ("BASE_SIZE", N2*8)
] + [(v, int(k)) for k, v in CONSTANT_REGISTERS.items()]


def get_reg_idx(name: str) -> int:
    for i, (nm, _) in enumerate(REGISTERS):
        if nm == name:
            return i
    return -1

def get_reg_id(reg: str):
    return [255] + [0] * (query.id.size - 2) + [get_reg_idx(reg)]

