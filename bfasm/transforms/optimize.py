from parser.main import *
from .capture import *
from .utils import *

def match_siblings(*siblings_names: List[List[str | Tuple[str]]]):
    def match_siblings_capture(func):
        @wraps(func)
        def wrapper(ast: ASTNode):
            cast = ast
            for sibling_names in siblings_names:
                cast = cast.next_sibling
                if cast is None or not check_match(cast, *sibling_names):
                    return None
            return func(ast)
        return wrapper
    return match_siblings_capture

@bfasm_transform(TPass.optimize)
@match_siblings(["instruction", "pop_ins"])
@match_nodes("instruction", "push_ins")
def optimize_push_pop(ast: ASTNode):
    sibling = ast.next_sibling
    sibling.remove_self()
    new_code = f"mov {sibling.literals[1].value} {ast.literals[1].value}"
    return util_parse(ast, new_code)

@bfasm_transform(TPass.optimize)
@match_siblings(["instruction", "mov_ins"], ["instruction", "pop_ins"])
@match_nodes("instruction", "push_ins")
def optimize_push_move_pop(ast: ASTNode):
    """
        push a
        mov b c
        pop d

        mov b c
        mov d a
    """
    s1 = ast.next_sibling
    s2 = s1.next_sibling
    if ast.literals[1].value == s1.literals[1].value:
        return None
    
    s1.remove_self()
    s2.remove_self()
    new_code = util_parse(ast, s1.to_string())
    new_code += util_parse(ast, f"mov {s2.literals[1].value} {ast.literals[1].value}")
    return new_code


@bfasm_transform(TPass.optimize)
@match_nodes("instruction", "mov_ins")
def optimize_mov_to_self(ast: ASTNode):
    if ast.literals[1].value == ast.literals[2].value:
        return []
    return None

@bfasm_transform(TPass.optimize)
@match_siblings(["instruction", "push_ins"], ["instruction", ("mov_ins", "pop_ins", "add_ins", "sub_ins")])
@match_nodes("instruction", "mov_ins")
def optimize_mov_push_write(ast: ASTNode):
    ref = ast.literals[1].value
    s1 = ast.next_sibling
    s2 = s1.next_sibling
    if s1.literals[1].value != ref:
        return None
    if s2.literals[1].value != ref:
        return None
    if len(s2.literals) == 3 and s2.literals[2].value == ref:
        return None
    s1.remove_self()
    new_code = f"push {ast.literals[2].value}"
    return util_parse(ast, new_code)

@bfasm_transform(TPass.optimize)
@match_siblings(["instruction", "mov_ins"], ["instruction", ("mov_ins", "pop_ins")])
@match_nodes("instruction", "mov_ins")
def optimize_mov_mov_write(ast: ASTNode):
    """
        mov a b
        mov c a
        mov a d

        mov c b
        mov a d
    """
    ref = ast.literals[1].value
    s1 = ast.next_sibling
    s2 = s1.next_sibling
    if s1.literals[2].value != ref:
        return None
    if s2.literals[1].value != ref:
        return None
    if len(s2.literals) == 3 and s2.literals[2].value == ref:
        return None
    s1.remove_self()
    new_code = f"mov {s1.literals[1].value} {ast.literals[2].value}"
    return util_parse(ast, new_code)

@bfasm_transform(TPass.optimize)
@match_siblings(["instruction", ("mov_ins", "pop_ins")])
@match_nodes("instruction", "mov_ins")
def optimize_mov_write(ast: ASTNode):
    """
        mov a b
        mov a c

        mov a c
    """
    ref = ast.literals[1].value
    s1 = ast.next_sibling
    if s1.literals[1].value != ref:
        return None
    if len(s1.literals) == 3 and s1.literals[2].value == ref:
        return None
    return []

@bfasm_transform(TPass.optimize)
@match_siblings(["instruction", "push_ins"], ["instruction", "push_ins"], ["instruction", ("mov_ins", "pop_ins")])
@match_nodes("instruction", "mov_ins")
def optimize_mov_push_push_write(ast: ASTNode):
    """
        mov cp func_out_num
        push cp
        push call_return_17
        mov cp func_mul

        push func_out_num
        push call_return_17
        mov cp func_mul
    """

    ref = ast.literals[1].value
    s1 = ast.next_sibling
    s2 = s1.next_sibling
    s3 = s2.next_sibling
    if s1.literals[1].value != ref:
        return None
    if s2.literals[1].value == ref:
        return None
    if s3.literals[1].value != ref:
        return None
    if len(s3.literals) == 3 and s3.literals[2].value == ref:
        return None
    s1.remove_self()
    new_code = f"push {ast.literals[2].value}"
    return util_parse(ast, new_code)

@bfasm_transform(TPass.optimize)
@match_nodes("instruction", ("add_ins", "sub_ins"))
def optimize_add_sub_zero(ast: ASTNode):
    if ast.literals[2].value in ("ZERO", "0"):
        return []

@bfasm_transform(TPass.optimize)
@match_nodes("instruction", ("add_ins", "sub_ins"))
def optimize_add_sub_one(ast: ASTNode):
    ins, ref, diff = ast.literals
    if diff not in ("ONE", "1"):
        return
    new_code = "inc" if ins == "add" else "dec" + " " + ref
    return util_parse(ast, new_code)

@bfasm_transform(TPass.optimize)
@match_nodes("instruction", "mov_ins")
def optimize_mov_junk(ast: ASTNode):
    """ mov a __junk__ """
    if ast.literals[1].value == "__junk__" or ast.literals[2].value == "__junk__":
        return []
