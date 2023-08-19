from parser.main import *
from .capture import *
from .utils import *


@bfasm_transform(TPass.classes)
@match_nodes("class_def")
def transpile_class_defs(ast: ASTNode):
    class_name = ast.literals[1].value
    fields = ast.get_all("class_field")
    funcs = ast.get_all("function")

    num_attrs = len(fields) + len(funcs)

    class_func = f"\nfunc {class_name}() {{\n"
    class_func += f"\tattrs = malloc({num_attrs + 1})\n"
    for i, field in enumerate(fields):
        class_func += f"\tattrs[{i}] = \"{field.literals[0].value}\"\n"
    for i, func in enumerate(funcs, len(fields)):
        class_func += f"\tattrs[{i}] = \"{func.literals[1].value}\"\n"
    class_func += f"\tattrs[{num_attrs}] = 0\n\n"

    for func in funcs:
        new_func_name = class_name + "_" +  func.literals[1].value
        new_func_name = create_unique_ids(ast, new_func_name)[0]
        func.literals[1].value = new_func_name

    class_func += f"\tobj = malloc(2 + {num_attrs})\n"
    class_func += "\tset obj attrs\n"
    class_func += "\tinc obj\n"
    class_func += f"\tset obj {class_name}\n"
    class_func += "\tinc obj\n"
    for i, field in enumerate(fields):
        class_func += f"\tobj[{i}] = {field.get('expression').to_string()}\n"
    for i, func in enumerate(funcs, len(fields)):
        class_func += f"\tobj[{i}] = __make_caller__(obj, {func.literals[1].value})\n"
    class_func += "\treturn obj\n}\n"

    code = util_parse(ast, class_func, syntax="function", forward=False)
    for func in funcs:
        code += [func]

    return code

@bfasm_transform(TPass.classes)
@match_nodes(("e_unit", "e_assign"))
def transpile_e_unit_dot(ast: ASTNode):
    e_dot_index = next((i for i, e_piece in enumerate(ast.children) if e_piece.get_all("e_dot")), -1)
    if e_dot_index == -1:
        return

    base = "".join(x.to_string() for x in ast.children[:e_dot_index]).strip()
    attr = ast.children[e_dot_index].literals[1].value
    rest = "".join(x.to_string() for x in ast.children[e_dot_index+1:]).strip()

    new_code = f"__get_ref__({base}, \"{attr}\")[0]{rest}"

    return util_parse(ast, new_code, ast.name, False)



