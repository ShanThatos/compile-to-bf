from enum import Enum, auto
from typing import List, Callable, Tuple
from parser.ast import *

class TPass(Enum):
    imports = auto()
    strings = auto()
    classes = auto()
    pre_collection = auto()
    collection = auto()
    statement = auto()
    expression = auto()
    function = auto()
    program = auto()
    optimize = auto()
    default = auto()

TRANSFORMS: List[Tuple[Callable[[ASTNode], ASTNode], TPass]] = []

def bfasm_transform(tpass=TPass.default):
    def bfasm_transform_capture(func):
        TRANSFORMS.append((func, tpass))
        return func
    return bfasm_transform_capture

