import os.path
from parser.main import *
from .capture import *
from .utils import *
from ..registers import *



@bfasm_transform(TPass.imports)
@match_nodes("IMPORT")
def process_import(ast: ASTNode):
    import_path = ast.literals[0].value[:-1].partition("\"")[2]
    if import_path.startswith("./"):
        import_path = os.path.join(os.path.dirname(ast.parser.script_path), import_path)
    else:
        import_path = os.path.join(os.path.dirname(ast.root.parser.script_path), import_path)
    import_path = os.path.normpath(os.path.abspath(import_path))
    if import_path in ast.root.imports:
        return []
    ast.root.imports.append(import_path)

    parser = ProceduralParser(ast.root.parser.original_syntax, "program")
    code = open(import_path).read()
    ast = parser.parse(code, import_path)
    return ast.children

