import re
import copy
from typing import Dict, List, Tuple, Callable, TypeVar

from .token import Token
from .ast import ASTNode, ASTLiteral

T = TypeVar('T')
def flatten(x: List[T] | T) -> List[T]:
    if isinstance(x, list):
        return sum((flatten(e) for e in x), [])
    return [x]

def point_out_index(code: str, index: int, before=None, after=None):
    code = f"\n{code}\n"
    line_start = code.rfind("\n", 0, index)
    line_end = code.find("\n", index)
    before_index = 0 if before is None else line_end - before
    after_index = len(code) if after is None else line_end + after
    first_half = code[before_index:line_end] + "\n"
    pointer_line = " " * (index - line_start) + "^" + "\n"
    second_half = code[line_end:after_index]
    return first_half + pointer_line + second_half

def tab_all_lines(code: str, tab: str) -> str:
    return "\n".join((tab + line for line in code.split("\n")))


class ProceduralLexer:
    def __init__(self, reserved_tokens: List[str], regex_matches: List[Tuple[str, str]] = []) -> None:
        self.res = list(sorted(reserved_tokens, key=lambda x: -len(x)))
        self.rgx = regex_matches
    
    def tokenize(self, code: str) -> List[Token]:
        tokens = []
        current = 0
        while current < len(code):
            whitespace_start = current
            while current < len(code) and code[current].isspace():
                current += 1
            whitespace_end = current
            token_whitespace = code[whitespace_start:whitespace_end]

            if current >= len(code):
                tokens.append(Token("==END==", "", token_whitespace))
                break

            token_name = None
            token_value = None
            for special_token in self.res:
                if special_token.isalpha():
                    if match := re.match(fr"{re.escape(special_token)}\b", code[current:]):
                        token_name = special_token
                        token_value = special_token
                        break
                elif code.startswith(special_token, current):
                    token_name = special_token
                    token_value = special_token
                    break
            else:
                for rgx_type, rgx_match in self.rgx:
                    if match := re.match(rgx_match, code[current:]):
                        token_name = rgx_type
                        token_value = match.group(0)
                        break
            
            if token_name is None:
                raise Exception("Unknown token: \n\n" + point_out_index(code, current, 500, 500))

            tokens.append(Token(token_name, token_value, token_whitespace))
            current += len(token_value)
        return tokens


class ParseError(Exception):
    def __init__(self, message: str, tokens: List[Token], index: int):
        super().__init__()
        self.message = message
        self.tokens = tokens
        self.index = index
    
    def __add__(self, other: "ParseError"):
        return ParseError(self.message + "\n" + tab_all_lines(other.message, "    "), other.tokens, other.index)
    
    def __str__(self) -> str:
        code_first_half = "".join(str(x) for x in self.tokens[:self.index])
        code_second_half = "".join(str(x) for x in self.tokens[self.index:])
        location_message = point_out_index(code_first_half + code_second_half, len(code_first_half), before=100, after=30)
        location_message = tab_all_lines(location_message, "    ")
        return f"{location_message}\n\nParseError: {self.message}"

class ProceduralParser:
    def __init__(self, syntax: Dict[str, List], start_syntax: str | List):
        self.original_syntax = copy.deepcopy(syntax)
        self.syntax = copy.deepcopy(syntax)
        self.start_syntax = start_syntax
        self.directives = {
            "ONE_OF": self.__parse_directive_one_of, 
            "REPEAT": self.__parse_directive_repeat, 
            "OPTIONAL": self.__parse_directive_optional,
            "FORWARD": self.__parse_directive_forward,
            "PASS": self.__parse_directive_pass,
            "DELIMITER": self.__parse_directive_delimiter
        }
        self.find_regex_matches()
        self.find_reserved_tokens()

        self.__subparsers = {}
    
    def with_syntax(self, start_syntax: str | List) -> "ProceduralParser":
        if isinstance(start_syntax, str):
            if start_syntax not in self.__subparsers:
                self.__subparsers[start_syntax] = ProceduralParser(self.original_syntax, start_syntax)
            return self.__subparsers[start_syntax]
        
        return ProceduralParser(self.original_syntax, start_syntax)


    def traverse_syntax_tree(self, callback: Callable[[str | list], bool | None]):
        open_set = [self.start_syntax]
        closed_set = set()
        while open_set:
            current = open_set.pop()
            if isinstance(current, str):
                if current in closed_set or current in self.directives:
                    continue
                closed_set.add(current)
            if callback(current):
                continue
            if isinstance(current, str) and current in self.syntax:
                open_set.append(self.syntax[current])
            elif isinstance(current, list):
                open_set.extend(current)

    def find_regex_matches(self):
        self.regex_matches = []
        regex_matches = []
        def callback(current):
            if isinstance(current, str) and current in self.syntax and not any(current == x[0] for x in regex_matches):
                if len(x := self.syntax[current]) == 2 and x[0] == "REGEX_MATCH":
                    regex_matches.append((current, x[1]))
                    return True
        self.traverse_syntax_tree(callback)
        self.regex_matches = [(x[0], x[1][1]) for x in sorted(regex_matches, key=lambda x: x[1][0])]

        for rgx_type, _ in self.regex_matches:
            self.syntax.pop(rgx_type)

    def find_reserved_tokens(self):
        reserved = []
        def callback(current):
            if isinstance(current, str) and current not in self.syntax and not any(current == x[0] for x in self.regex_matches):
                reserved.append(current)
        self.traverse_syntax_tree(callback)
        self.reserved_tokens = list(sorted(reserved, key=lambda x: -len(x)))


    def parse(self, code: str, script_path: str = None):
        self.script_path = script_path
        lexer = ProceduralLexer(self.reserved_tokens, self.regex_matches)
        tokens = lexer.tokenize(code)

        self.tokens = tokens
        self.index = 0
        ast = self.__parse_all()
        return ast
    
    def multiparse(self, codes: List[str]):
        return flatten([self.parse(code) for code in codes])

    @property
    def current(self) -> Token:
        return self.tokens[self.index] if self.ready else None
    @property
    def ready(self) -> bool:
        return self.index < len(self.tokens) and self.tokens[self.index].name != "==END=="

    def error(self, message: str, index: int = None):
        return ParseError(message, self.tokens, self.index if index is None else index)

    def __parse_all(self) -> ASTNode:
        try:
            ast = self.__parse(self.start_syntax)
            if self.ready:
                raise self.error(f"Expected end of file")
            return ast
        except ParseError as pe:
            raise pe
    
    def __parse(self, syntax: str | List) -> ASTNode:
        if isinstance(syntax, str):
            return self.__parse_str(syntax)
        elif isinstance(syntax, list):
            return self.__parse_list(syntax)
    
    def __parse_str(self, syntax: str) -> ASTNode:
        if syntax in self.syntax:
            try:
                saved_index = self.index
                return ASTNode(syntax, self.__parse_list(self.syntax[syntax]), self)
            except ParseError as pe:
                raise self.error(f"Expected '{syntax}'", saved_index) + pe from None
        token = self.current
        if not self.ready or token.name != syntax:
            raise self.error(f"Expected '{syntax}' found {repr(token)}")
        self.index += 1
        return ASTLiteral(syntax, token, parser=self)

    def __parse_list(self, syntax: List) -> List[ASTNode]:
        index = 0
        children = []
        while index < len(syntax):
            item = syntax[index]
            if isinstance(item, str) and item in self.directives:
                result = self.directives[item](syntax[index := index + 1])
            else:
                result = self.__parse(item)
            children.append(result)
            index += 1
        return flatten(children)

    def __parse_directive_one_of(self, syntax: list) -> ASTNode | List[ASTNode]:
        if not isinstance(syntax, list) or len(syntax) == 0:
            raise self.error(f"ONE_OF: Expected list of options")
        
        saved_index = self.index
        best_index = saved_index
        best_error = None
        for choice in syntax:
            try:
                self.index = saved_index
                return self.__parse(choice)
            except ParseError as pe:
                if pe.index > best_index:
                    best_index = pe.index
                    best_error = pe
        if best_error is None:
            raise self.error(f"ONE_OF: Expected one of {syntax}")
        self.index = best_index
        raise best_error

    def __parse_directive_repeat(self, syntax: str | List) -> ASTNode | List[ASTNode]:
        children = []
        while self.ready:
            try:
                saved_index = self.index
                children.append(self.__parse(syntax))
            except ParseError as pe:
                if self.index == saved_index:
                    break
                raise pe from None
        return flatten(children)

    def __parse_directive_optional(self, syntax: str | List) -> ASTNode | List[ASTNode]:
        saved_index = self.index
        try:
            return self.__parse(syntax)
        except ParseError:
            self.index = saved_index
            return []

    def __parse_directive_forward(self, syntax: str) -> ASTNode | List[ASTNode]:
        if syntax not in self.syntax:
            raise Exception(f"Unknown syntax: {syntax}")
        return self.__parse(self.syntax[syntax])

    def __parse_directive_pass(self, syntax: str | List) -> ASTNode | List[ASTNode]:
        self.__parse(syntax)
        return []

    def __parse_directive_delimiter(self, syntax: list) -> ASTNode | List[ASTNode]:
        if not isinstance(syntax, list) or len(syntax) != 2:
            raise self.error(f"DELIMITER: Expected list of length 2")
        unit_syntax, delimiter = syntax
        return self.__parse([unit_syntax, "REPEAT", [delimiter, unit_syntax]])



