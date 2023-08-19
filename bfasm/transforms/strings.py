import re
from .capture import *
from .utils import *


@bfasm_transform(TPass.strings)
@transform_once
@match_nodes("STRING")
def process_import(ast: ASTNode):
    full_string = ast.literals[0].value[1:-1]

    string_values = []
    i = 0
    while i < len(full_string):
        ch = full_string[i]
        if ch == "\\":
            i += 1
            if i >= len(full_string):
                raise RuntimeError("Unexpected end of string")
            ch = full_string[i]
            if ch in "nt\\\"":
                string_values.append(ord(eval(f"'\\{ch}'")))
            else:
                raise RuntimeError("Unknown escape sequence: \\" + ch)
        else:
            string_values.append(ord(ch))
        i += 1
    
    root = ast.root
    if not hasattr(root, "strings"):
        root.strings = {}
    
    key = tuple(string_values)
    if key not in root.strings:
        lbl_name = re.sub(r"[^a-zA-Z0-9_]", "", full_string.lower())[:10]
        lbl = create_unique_ids(ast, f"string_{lbl_name}")[0]
        root.strings[key] = (lbl, string_values)
    else:
        lbl = root.strings[key][0]
    
    return util_parse(ast, lbl, syntax="REF", forward=False)


