from parser.main import *

from functools import wraps
from typing import List


def check_match(ast: ASTNode, *names: List[str | Tuple[str]]):
    cast = ast
    for i, nm in enumerate(names):
        if isinstance(nm, Tuple):
            if cast.name not in nm:
                return False
        elif cast.name != nm:
            return False
        if i < len(names) - 1:
            if len(cast.children) != 1:
                return False
            cast = cast.children[0]
    return True

def match_nodes(*names: List[str | Tuple[str]]):
    def match_nodes_capture(func):
        @wraps(func)
        def match_nodes_wrapper(ast: ASTNode):
            if check_match(ast, *names):
                return func(ast)
        return match_nodes_wrapper
    return match_nodes_capture

def transform_once(func):
    @wraps(func)
    def once_wrapper(ast: ASTNode):
        attr_name = f"__{func.__name__}_has_run"
        if not getattr(ast, attr_name, False):
            setattr(ast, attr_name, True)
            return func(ast)
    return once_wrapper

def find_parent(ast: ASTNode, name: str):
    while ast and ast.name != name:
        ast = ast.parent
    return ast

def create_unique_ids(ast: ASTNode, *bases: List[str]):
    if not hasattr(ast.root, "ids"):
        ast.root.ids = set(x.value for x in ast.root.literals if x.name == "REF")
    used_ids = ast.root.ids
    ids = []
    i = 0
    while len(ids) < len(bases):
        if i == 0:
            value = bases[len(ids)]
        else:
            value = bases[len(ids)] + "_" + str(i)
        i += 1
        if value not in used_ids:
            ids.append(value)
            i = 0
            used_ids.add(value)
    return ids

def get_last_whitespace_line(ast: ASTNode):
    fws = ast.literals[0].whitespace
    return fws[fws.rindex("\n"):] if "\n" in fws else "\n" + fws

def mimic_ws_code(ast: ASTNode, code: str | List[str], tab: str = ""):
    fws = ast.literals[0].whitespace
    if isinstance(code, str):
        return f"{fws}{tab}{code}"
    ws = get_last_whitespace_line(ast)
    return [f"{fws}{tab}{code[0]}"] + [f"{ws}{tab}{x}" for x in code[1:]]

def mimic_ws_ast(orig_ast: ASTNode, ast: ASTNode, tab: str = ""):
    ast.literals[0].whitespace = orig_ast.literals[0].whitespace + tab
    return ast

def util_parse(ast: ASTNode, code: str | List[str], syntax="asm", forward=True, tab: str = ""):
    if isinstance(code, str):
        code = [x.strip() for x in code.split(";") if x.strip()]
    if forward: 
        syntax = ["FORWARD", syntax]
    return ast.parser.with_syntax(syntax).multiparse(mimic_ws_code(ast, code, tab=tab))

