from parser.main import *
from .capture import *
from .utils import *



@bfasm_transform(TPass.statement)
@match_nodes("if_else_statement")
def transpile_if_else_statement(ast: ASTNode):
    else_lbl, end_lbl = create_unique_ids(ast, "else_action", "if_end")
    
    code = [mimic_ws_ast(ast, ast.get("expression"), "  ")]
    code += util_parse(ast, f"pop e0; jpz {else_lbl} e0")
    code += ast.get("statement").children
    code += util_parse(ast, f"jp {end_lbl}; {else_lbl}:")
    code += ast.get("statement", 1).children
    code += util_parse(ast, f"{end_lbl}:")
    return code


@bfasm_transform(TPass.statement)
@match_nodes("if_statement")
def transpile_if_statement(ast: ASTNode):
    end_lbl = create_unique_ids(ast, "if_end")[0]

    code = [mimic_ws_ast(ast, ast.get("expression"), "  ")]
    code += util_parse(ast, f"pop e0; jpz {end_lbl} e0")
    code += ast.get("statement").children
    code += util_parse(ast, f"{end_lbl}:")
    return code

def find_loop_control_statements(ast: ASTNode) -> List[ASTNode]:
    stmts = []
    st = list(ast.children)
    while st:
        child = st.pop()
        match child.name:
            case "if_else_statement":
                st.append(child.get("if_statement"))
                st.extend(child.get("statement").children)
            case "if_statement":
                st.extend(child.get("statement").children)
            case "statement":
                st.extend(child.children)
            case "continue_statement" | "break_statement":
                stmts.append(child)
    return stmts

@bfasm_transform(TPass.statement)
@match_nodes("while_statement")
def transpile_while_statement(ast: ASTNode):
    start_lbl, end_lbl = create_unique_ids(ast, "while_start", "while_end")

    stmt = ast.get("statement")
    control_stmts = find_loop_control_statements(stmt)
    for control_stmt in control_stmts:
        control_stmt.loop_start_lbl = start_lbl
        control_stmt.loop_end_lbl = end_lbl

    code = util_parse(ast, f"{start_lbl}:")
    code += [mimic_ws_ast(ast, ast.get("expression"), "  ")]
    code += util_parse(ast, f"pop e0; jpz {end_lbl} e0")
    code += stmt.children
    code += util_parse(ast, f"jp {start_lbl}; {end_lbl}:")
    return code

@bfasm_transform(TPass.expression)
@match_nodes("continue_statement")
def transpile_continue_statement(ast: ASTNode):
    if not hasattr(ast, "loop_start_lbl"):
        raise Exception("continue statement outside of loop")
    return util_parse(ast, f"jp {ast.loop_start_lbl}")

@bfasm_transform(TPass.expression)
@match_nodes("break_statement")
def transpile_break_statement(ast: ASTNode):
    if not hasattr(ast, "loop_end_lbl"):
        raise Exception("break statement outside of loop")
    return util_parse(ast, f"jp {ast.loop_end_lbl}")


@bfasm_transform(TPass.statement)
@match_nodes("return_statement")
def transpile_return_statement(ast: ASTNode):
    code = [mimic_ws_ast(ast, ast.get("expression"), "  ")]
    
    func = find_parent(ast, "function")
    assert(func is not None)
    code += util_parse(ast, f"pop e0; jp {func.__return_lbl__}")
    return code
