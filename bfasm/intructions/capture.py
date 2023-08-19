from typing import List, Callable
from bf.simp import *
from enum import Enum

class Priority(Enum):
    REF = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3

INSTRUCTIONS: List["Instruction"] = []

class Instruction:
    __ID_COUNTER = 0
    def __init__(self, name: str, num_args: int, func: Callable, priority: Priority):
        self.id = Instruction.__ID_COUNTER
        Instruction.__ID_COUNTER += 1
        self.name = name
        self.num_args = num_args
        self.func = func
        self.priority = priority
    
    @property
    def code(self):
        if hasattr(self, "__code"):
            return self.__code
        self.__code = simp(self.func())
        return self.__code

INSTRUCTIONS.append(Instruction("ref", 0, lambda: "", Priority.REF))

def clean_instructions():
    INSTRUCTIONS.sort(key= lambda x: x.priority.value)
    for i, ins in enumerate(INSTRUCTIONS):
        ins.id = i

def bfasm_ins(num_args: int = 0, ins_name: str = None, priority: Priority = Priority.LOW):
    def bf_ins_capture(func):
        INSTRUCTIONS.append(Instruction(ins_name or func.__name__, num_args, func, priority))
        clean_instructions()
        return func
    return bf_ins_capture

def get_instruction(name: str) -> Instruction:
    for ins in INSTRUCTIONS:
        if ins.name == name:
            return ins
    raise Exception("Invalid instruction name")

