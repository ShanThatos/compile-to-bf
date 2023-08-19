from parser.main import *
from .capture import *
from .utils import *


def get_expr_sub_units(ast: ASTNode):
    assert(len(ast.children) > 0)
    return [x for x in ast.children if x.name == ast.children[0].name]
def get_expr_ops(ast: ASTNode):
    assert(len(ast.children) > 0)
    return [x for x in ast.children if x.name != ast.children[0].name]


def top_level(func):
    @wraps(func)
    def wrapper(ast: ASTNode):
        if ast.parent != (find_parent(ast, "function_body") or ast.root):
            return
        return func(ast)
    return wrapper


@bfasm_transform(TPass.pre_collection)
@match_nodes("e_assign")
def transpile_e_specialassign(ast: ASTNode):
    op = ast.get("e_assign_op")
    if op.literals[0].value == "=":
        return

    base = "".join(x.to_string() for x in ast.children[:op.index]).strip()
    rest = "".join(x.to_string() for x in ast.children[op.index+1:]).strip()
    new_code = base + " = " + base + " " + op.literals[0].value[:-1] + " " + rest

    return util_parse(ast, new_code, "e_assign", False)


@bfasm_transform(TPass.pre_collection)
@match_nodes("e_mul")
def transpile_div_mod_ops(ast: ASTNode):
    dm_index = next((i for i, child in enumerate(ast.children) if child.name in ("/", "%")), -1)
    if dm_index == -1:
        return
    new_code = "div(" if ast.children[dm_index].name == "/" else "mod("
    new_code += "".join(x.to_string() for x in ast.children[:dm_index]).strip()
    new_code += ", "
    new_code += "".join(x.to_string() for x in ast.children[dm_index+1:]).strip()
    new_code += ")"
    return util_parse(ast, new_code, "e_mul", False)



@bfasm_transform(TPass.expression)
@top_level
@match_nodes("expression_statement")
def transpile_expression(ast: ASTNode):
    assert(len(ast.children) == 1)
    ast.literals[0].whitespace = get_last_whitespace_line(ast)
    return [ast.children[0]] + util_parse(ast, "pop __junk__")

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("expression")
def transpile_expression(ast: ASTNode):
    assert(len(ast.children) == 1)
    ast.literals[0].whitespace = get_last_whitespace_line(ast)
    return [ast.children[0]]

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_rel")
def transpile_rel(ast: ASTNode):
    first_unit, *units = get_expr_sub_units(ast)
    ops = get_expr_ops(ast)
    code = [mimic_ws_ast(ast, first_unit)]
    for i, (unit, op) in enumerate(zip(units, ops)):
        code += [mimic_ws_ast(ast, unit)]
        code += util_parse(ast, "pop e1; pop e0; ")
        lbl = create_unique_ids(ast, f"rel_{i}")[0]
        if op.name == "==":
            code += util_parse(ast, f"sub e1 e0; mov e0 ZERO; jpif {lbl} e1; mov e0 ONE; {lbl}:; push e0")
        elif op.name == "!=":
            code += util_parse(ast, f"sub e1 e0; mov e0 ONE; jpif {lbl} e1; mov e0 ZERO; {lbl}:; push e0")
        elif op.name == "<":
            code += util_parse(ast, f"cmp e0 e1; mov e0 ZERO; jpif {lbl} cr; mov e0 ONE; {lbl}:; push e0")
        elif op.name == ">=":
            code += util_parse(ast, f"cmp e0 e1; mov e0 ZERO; jpz {lbl} cr; mov e0 ONE; {lbl}:; push e0")
        elif op.name == ">":
            code += util_parse(ast, f"cmp e1 e0; mov e0 ZERO; jpif {lbl} cr; mov e0 ONE; {lbl}:; push e0")
        elif op.name == "<=":
            code += util_parse(ast, f"cmp e1 e0; mov e0 ZERO; jpz {lbl} cr; mov e0 ONE; {lbl}:; push e0")
        else:
            raise NotImplementedError(f"Unknown rel operator '{op}'")
    return code

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_add_sub")
def transpile_add(ast: ASTNode):
    first_unit, *units = get_expr_sub_units(ast)
    ops = get_expr_ops(ast)
    code = [mimic_ws_ast(ast, first_unit)]
    for unit, op in zip(units, ops):
        code += [mimic_ws_ast(ast, unit)]
        code += util_parse(ast, "pop e1; pop e0")
        code += util_parse(ast, ("sub", "add")[op.name == "+"] + " e0 e1")
        code += util_parse(ast, "push e0")
    return code

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_mul")
def transpile_mul(ast: ASTNode):
    first_unit, *units = get_expr_sub_units(ast)
    ops = get_expr_ops(ast)
    code = [mimic_ws_ast(ast, first_unit)]
    for unit, op in zip(units, ops):
        if op.name != "*":
            raise NotImplementedError(f"Unknown mul operator '{op.to_string()}'")
        code += [mimic_ws_ast(ast, unit)]
        code += util_parse(ast, "pop e1; pop e0; mul e0 e1; push e0")
    return code

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_neg")
def transpile_neg(ast: ASTNode):
    unit = ast.children[-1]
    code = [mimic_ws_ast(ast, unit)]
    if ast.literals[0].value == "-":
        code += util_parse(ast, "pop e0; neg e0; push e0")
    return code

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_unit")
def transpile_unit(ast: ASTNode):
    name = ast.children[0].name
    code = []
    if name in ("REF", "NUMBER"):
        code += util_parse(ast, f"push {ast.literals[0].value}")
    else:
        code += [mimic_ws_ast(ast, ast.children[0])]

    for i, e_ref in enumerate(ast.get_all("e_ref"), 1):
        code += [mimic_ws_ast(ast, e_ref.children[0], i * "  ")]

    return code

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_par")
def transpile_par(ast: ASTNode):
    return [mimic_ws_ast(ast, ast.get("expression"))]

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_assign")
def transpile_assign(ast: ASTNode):
    code = [mimic_ws_ast(ast, ast.get("expression"), tab="  ")]
    code += util_parse(ast, f"pop e0; push e0")

    base = ast.children[0]
    refs = ast.get_all("e_ref")
    if base.name not in ("REF",) and len(refs) == 0:
        raise Exception("Invalid assignment")
    
    if base.name == "REF" and len(refs) == 0:
        code += util_parse(ast, f"mov {base.literals[0].value} e0")
        return code
    
    if base.name in ("REF",):
        code += util_parse(ast, f"push {ast.literals[0].value}")
    else:
        code += [mimic_ws_ast(ast, base,)]

    for i, e_ref in enumerate(refs[:-1]):
        code += [mimic_ws_ast(ast, e_ref.children[0], i * "  ")]
    
    last_ref = refs[-1].children[0]
    if last_ref.name not in ("e_index",):
        raise Exception("Invalid assignment")
    
    if last_ref.name == "e_index":
        code += [mimic_ws_ast(ast, last_ref.get("expression"), "  ")]
        code += util_parse(ast, "pop e0; pop e1; add e1 e0; pop e0; set e1 e0; push e0")

    return code

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_call")
def transpile_call(ast: ASTNode):
    lbl = create_unique_ids(ast, "call_return")[0]
    code = util_parse(ast, f"pop e0; push cp; push this; mov cp e0; push {lbl}")
    exprs = ast.get_all("expression")
    for expr in exprs:
        code += [mimic_ws_ast(ast, expr, "  ")]
    code += util_parse(ast, f"push {len(exprs)}; inc cp; get this cp; inc cp; get cp cp")
    code += util_parse(ast, f"jp cp; {lbl}:; pop this; pop cp; push e0")

    return code

@bfasm_transform(TPass.expression)
@top_level
@match_nodes("e_index")
def transpile_index(ast: ASTNode):
    expr = ast.get("expression")
    expr_str = expr.to_string().strip()
    
    if expr_str.isdigit():
        return util_parse(ast, f"pop e0; add e0 {expr_str}; get e0 e0; push e0")

    code = [mimic_ws_ast(ast, expr, "  ")]
    code += util_parse(ast, "pop e0; pop e1; add e0 e1; get e0 e0; push e0")
    return code

