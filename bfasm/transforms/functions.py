from parser.main import *
from .capture import *
from .utils import *
from ..registers import *


@bfasm_transform(TPass.function)
@match_nodes("function")
def transpile_function(ast: ASTNode):
    func_type = ast.literals[0].value
    if func_type == "func":
        return transpile_normal_function(ast)
    elif func_type == "varfunc":
        return transpile_variadic_function(ast)
    raise RuntimeError(f"Unknown function type: {func_type}")

def transpile_normal_function(ast: ASTNode):
    name = ast.literals[1].value
    start, end, caller_start, caller = create_unique_ids(ast, f"{name}_start", f"{name}_end", f"{name}_caller_start", f"{name}_caller")
    ret = ast.__return_lbl__

    ast.literals[0].whitespace = "\n" + get_last_whitespace_line(ast)
    code = util_parse(ast, f"mov {name} {caller_start}")
    ast.literals[0].whitespace = get_last_whitespace_line(ast)
    code += util_parse(ast, f"jp {end}")

    vars = getattr(ast, "vars", {})
    params = getattr(ast, "params", [])
    
    for _, _, lbl2 in reversed(params):
        code += util_parse(ast, f"{lbl2}: 0", tab="  ")
    for _, var_lbl in vars.items():
        code += util_parse(ast, f"{var_lbl}: 0", tab="  ")

    code += util_parse(ast, f"{caller_start}:")
    code += util_parse(ast, f"{caller}: 0")
    code += util_parse(ast, f"{start}:")

    code += util_parse(ast, f"pop __junk__", tab="  ")
    for _, _, lbl2 in reversed(params):
        code += util_parse(ast, f"pop {lbl2}", tab="  ")
    for _, var_lbl in vars.items():
        code += util_parse(ast, f"push {var_lbl}", tab="  ")
    for var_name, var_lbl in vars.items():
        value_lbl = next((x[2] for x in params if x[0] == var_name), "0")
        code += util_parse(ast, f"mov {var_lbl} {value_lbl}", tab="  ")

    code += ast.get("function_body").children

    code += util_parse(ast, f"mov e0 0; {ret}:")
    for _, var_lbl in reversed(vars.items()):
        code += util_parse(ast, f"pop {var_lbl}", tab="  ")

    code += util_parse(ast, f"pop ip", tab="  ")
    code += util_parse(ast, f"{end}:")
    return code

def transpile_variadic_function(ast: ASTNode):
    MAX_ARGS = 10

    name = ast.literals[1].value
    start, end, caller_start, caller = create_unique_ids(ast, f"{name}_start", f"{name}_end", f"{name}_caller_start", f"{name}_caller")
    args, num_args = create_unique_ids(ast, f"{name}_args", f"{name}_num_args")
    all_args = create_unique_ids(ast, *[f"{name}_arg_{i}" for i in range(MAX_ARGS)])
    ret = ast.__return_lbl__

    ast.literals[0].whitespace = "\n" + get_last_whitespace_line(ast)
    code = util_parse(ast, f"mov {name} {caller_start}")
    code += util_parse(ast, f"add {args} TWO")
    ast.literals[0].whitespace = get_last_whitespace_line(ast)
    code += util_parse(ast, f"jp {end}")

    vars = getattr(ast, "vars", {})
    params = getattr(ast, "params", [])
    if len(params) != 1:
        raise RuntimeError("Variadic functions must have exactly one parameter")
    param_name = params[0][0]
    param_lbl = params[0][2]
    
    code += util_parse(ast, f"{param_lbl}: 0", tab="  ")
    for _, var_lbl in vars.items():
        code += util_parse(ast, f"{var_lbl}: 0", tab="  ")

    code += util_parse(ast, f"{args}:; {num_args}: 0")
    for arg_lbl in all_args:
        code += util_parse(ast, f"{arg_lbl}: 0")

    code += util_parse(ast, f"{caller_start}:")
    code += util_parse(ast, f"{caller}: 0")
    code += util_parse(ast, f"{start}:")

    code += util_parse(ast, f"pop e0; mov {num_args} e0; neg e0; add e0 10; add ip e0", tab="  ")
    for arg_lbl in reversed(all_args):
        code += util_parse(ast, f"pop {arg_lbl}", tab="  ")
    code += util_parse(ast, f"mov {param_lbl} {args}")

    for _, var_lbl in vars.items():
        code += util_parse(ast, f"push {var_lbl}", tab="  ")
    for var_name, var_lbl in vars.items():
        value_lbl = param_lbl if var_name == param_name else "0"
        code += util_parse(ast, f"mov {var_lbl} {value_lbl}", tab="  ")

    code += ast.get("function_body").children

    code += util_parse(ast, f"mov e0 0; {ret}:")
    for _, var_lbl in reversed(vars.items()):
        code += util_parse(ast, f"pop {var_lbl}", tab="  ")

    code += util_parse(ast, f"pop ip", tab="  ")
    code += util_parse(ast, f"{end}:")
    return code


@match_nodes("NUMBER")
def transpile_number_to_ref(ast: ASTNode):
    if find_parent(ast, "instruction") is None:
        return
    root = ast.root
    num = ast.literals[0].value
    if num not in root.constants:
        root.constants[num] = create_unique_ids(root, f"const_{num}")[0]
    return util_parse(ast, root.constants[num], syntax="REF", forward=False)

@bfasm_transform(TPass.program)
@transform_once
@match_nodes("program")
def transpile_program(ast: ASTNode):
    ast.literals[0].whitespace = get_last_whitespace_line(ast)

    start_lbl = create_unique_ids(ast, "program_start")[0]

    ast.constants = CONSTANT_REGISTERS.copy()
    ast.inner_transform(transpile_number_to_ref)
    const_lbls = []
    for num, lbl in ast.constants.items():
        if num not in CONSTANT_REGISTERS:
            const_lbls += util_parse(ast, f"{lbl}: {num}")
    const_lbls += util_parse(ast, f"{start_lbl}:")
    ast.children = const_lbls + ast.children
    ast.index_children()

    var_lbls = util_parse(ast, f"jp {start_lbl}")
    for _, var_lbl in getattr(ast, "vars", {}).items():
        var_lbls += util_parse(ast, f"{var_lbl}: 0")
    ast.children = var_lbls + ast.children
    ast.index_children()


