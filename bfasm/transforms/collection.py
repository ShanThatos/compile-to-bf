from parser.main import *
from .capture import *
from .utils import *
from ..registers import *


@bfasm_transform(TPass.pre_collection)
@transform_once
@match_nodes(("program", "function"))
def setup_container_nodes(ast: ASTNode):
    ast.vars = {}
    if ast.name == "function":
        ast.params = []

@bfasm_transform(TPass.collection)
@transform_once
@match_nodes("function")
def collect_function_params(ast: ASTNode):
    func_name = ast.literals[1].value
    lbl = create_unique_ids(ast, f"func_{func_name}")[0]
    if func_name in ast.root.vars:
        raise Exception(f"{func_name} has already been defined???")
    ast.root.vars[func_name] = lbl
    
    ast.__return_lbl__ = create_unique_ids(ast, f"func_{func_name}_return")[0]

    for param in ast.get("function_params").get_all("REF"):
        param_name = param.literals[0].value
        lbl1, lbl2 = create_unique_ids(ast, f"var_local_{param_name}", f"var_param_{param_name}")
        ast.vars[param_name] = lbl1
        ast.params.append((param_name, lbl1, lbl2))

@bfasm_transform(TPass.collection)
@transform_once
@match_nodes("e_assign")
def collect_variables(ast: ASTNode):
    container = find_parent(ast, "function") or ast.root
    is_global = container == ast.root

    var_name = ast.literals[0].value
    if len(ast.get_all("e_ref")) or get_reg_idx(var_name) != -1:
        return
    if var_name not in container.vars:
        lbl_base = "var_global_" if is_global else "var_local_"
        lbl = create_unique_ids(ast, f"{lbl_base}{var_name}")[0]
        container.vars[var_name] = lbl

@bfasm_transform(TPass.collection)
@match_nodes("global_statement")
def fix_global_references(ast: ASTNode):
    container = find_parent(ast, "function")
    if container is None:
        raise Exception("global statement outside of function???")

    var_name_asts = ast.get_all("REF")
    for var_name_ast in var_name_asts:
        var_name = var_name_ast.literals[0].value
        container.vars.pop(var_name, None)
        if any(x == var_name for x, *_ in container.params):
            raise Exception(f"global statement cannot include function parameter: {var_name}")
        if var_name not in ast.root.vars:
            raise Exception(f"global statement undefined variable: {var_name}")
    return []

@bfasm_transform(TPass.statement)
@match_nodes("REF")
def transpile_variable_reference(ast: ASTNode):
    container = find_parent(ast, "function") or ast.root
    var_name = ast.literals[0].value
    var_lbl = container.vars.get(var_name, ast.root.vars.get(var_name, None))
    if var_lbl is None:
        return
    return util_parse(ast, var_lbl, syntax="REF", forward=False)
