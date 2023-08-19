import json
import os.path

from parser.ast import *
from parser.main import ProceduralParser
from .registers import *
from .units import *
from .utils import *
from .intructions.all import *
from .transforms.all import full_transform
from .program import *


class BFunCompiler:
    def __init__(self, script_path: str, spec_path: str, heap_size: int = 100):
        self.script_path = script_path
        self.spec_path = spec_path
        self.heap_size = heap_size

    def compile_to_bfasm(self, save_to_file: bool = False):
        spec = json.load(open(self.spec_path))
        parser = ProceduralParser(spec, "program")
        code = open(self.script_path, "r").read()
        ast = parser.parse(code, self.script_path)
        ast.imports = [os.path.normpath(os.path.abspath(self.script_path))]
        ast = full_transform(ast, save_to_file)
        if save_to_file:
            self.__save("bin/code.bfasm", ast.to_string())
        return ast
    
    def compile_bfasm_to_bytes(self, ast: ASTNode) -> List[int]:
        return self.instructions_to_bytes(self.collect_instructions(ast))
    
    def compile_ast_to_bf(self, ast: ASTNode, save_to_file: bool = False):
        bf_code = generate_program(self.compile_bfasm_to_bytes(ast))
        if save_to_file:
            self.__save("bin/code.bf", bf_code)
        return bf_code

    def compile_to_bf(self, save_to_file: bool = False):
        ast = self.compile_to_bfasm(save_to_file)
        bf_code = self.compile_ast_to_bf(ast, save_to_file)
        return bf_code
    
    def collect_instructions(self, ast: ASTNode) -> List[List[str]]:
        if not hasattr(ast, "strings"):
            ast.strings = {}
        data_map = {}
        lines = [["label", "__junk__"], ["instruction", "inc", ["__heap_start__"]]]

        for lbl, string_values in ast.strings.values():
            lines.append(["instruction", "add", [lbl, "TWO"]])
        
        lines.append(["instruction", "jp", ["~~start~~"]])

        for lbl, string_values in ast.strings.values():
            lines += [["label", lbl], ["label", None, len(string_values)]]
            string_values = string_values + [0]
            for i, v in enumerate(string_values):
                lines.append(["label", None, v])
        
        lines += [["label", "__heap_size__", self.heap_size], ["label", "__heap_start__"]]
        lines.append(["label", None, -self.heap_size])
        for i in range(1, self.heap_size + 1):
            lines.append(["label", None, 0])
        
        lines += [["label", "~~start~~"], ]

        children = ast.children
        for i in range(len(children)):
            child = children[i]
            literals = child.literals
            if child.name == "label":
                if get_reg_idx(child.name) != -1:
                    raise Exception(f"Label '{child.name}' already exists as a register name")
                if child.name in data_map:
                    raise Exception(f"Label '{child.name}' defined more than once")
                line = ["label", literals[0].value]
                if len(literals) == 3:
                    line.append(int(literals[2].value))
                lines.append(line)
            elif child.name == "instruction":
                args = [x.value for x in literals[1:]]
                lines.append(["instruction", literals[0].value, args])
        lines.append(["instruction", "end", []])
        lines.append(["instruction", "end", []])
        return lines

    def instructions_to_bytes(self, lines: List[List[str]]) -> List[int]:
        labels = {reg: get_reg_id(reg) for reg, _ in REGISTERS}

        for i, line in enumerate(lines):
            if line[0] == "label" and line[1]:
                if line[1] in labels:
                    raise Exception(f"{line[1]} label is defined twice")
                labels[line[1]] = b256(i, query.id.size)

        program = []
        for i, line in enumerate(lines):
            if line[0] == "label":
                val = b256(i if len(line) == 2 else line[2], unit.data.size)
                program += [0] + [get_instruction("ref").id] + val
            elif line[0] == "instruction":
                program += [0] + [get_instruction(line[1]).id]
                for j in range(2):
                    if j < len(line[2]):
                        if line[2][j] not in labels:
                            raise Exception(f"Reference '{line[2][j]}' not found")
                        program += labels[line[2][j]]
                    else:
                        program += [0] * query.id.size
        
        return program

    def __save(self, path: str, contents: str):
        with open(path, "w") as f:
            f.write(contents)
        