from .capture import *
from .control import *
from .functions import *
from .expr import *
from .optimize import *
from .collection import *
from .imports import *
from .strings import *
from .classes import *
from parser.main import *

def full_transform(ast: ASTNode, save_to_file: bool = False):
    passes = flatten([[(tr, tpi) for tr, tpass_ in TRANSFORMS if tpass_ == tpass] for tpi, tpass in enumerate(TPass)])
    best_pass = 0
    transforming = True
    while transforming:
        for tr, tpi in passes:
            ast, transformed = ASTNode.transform(ast, tr)
            if transformed:
                break
            
            if tpi > best_pass:
                if save_to_file:
                    pass_name = str(list(TPass)[best_pass]).partition(".")[2]
                    with open(f"bin/passes/code-{best_pass}-{pass_name}.bfun", "w") as f:
                        f.write(ast.to_string())
                best_pass = tpi
        else:
            transforming = False

    if save_to_file:
        pass_name = str(list(TPass)[best_pass]).partition(".")[2]
        with open(f"bin/passes/code-{best_pass}-{pass_name}.bfun", "w") as f:
            f.write(ast.to_string())
    
    return ast
