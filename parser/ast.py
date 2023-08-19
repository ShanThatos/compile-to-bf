
from typing import List, Callable, TYPE_CHECKING, Union

from .token import Token

if TYPE_CHECKING:
    from .main import ProceduralParser


class ASTNode:
    def __init__(self, name: str, children: List["ASTNode"] = [], parser: "ProceduralParser" = None):
        self.name = name
        self.children = children
        self.parser = parser
        self.parent: ASTNode = None
        self.index = -1
        self.index_children()
    
    def __repr__(self):
        return f"ASTNode({repr(self.name)}, {repr(self.children)})"
    
    def __iter__(self):
        yield self
        for child in self.children:
            yield from iter(child)

    @property
    def literals(self):
        return [x.token for x in self if isinstance(x, ASTLiteral)]
    
    @property
    def root(self):
        rt = self
        while rt.parent is not None:
            rt = rt.parent
        return rt

    @property
    def next_sibling(self):
        if self.parent is None: 
            return None
        if self.index + 1 < len(self.parent.children):
            return self.parent.children[self.index + 1]
        return None

    def get(self, name: str, idx: int = 0):
        o_idx = idx
        for child in self.children:
            if child.name == name:
                if idx == 0:
                    return child
                idx -= 1
        raise Exception(f"Could not find child with name {name} and index {o_idx}")
    
    def get_all(self, name: str):
        return [child for child in self.children if child.name == name]

    def index_children(self):
        for i, child in enumerate(self.children):
            child.parent = self
            child.index = i
            child.index_children()

    def inner_transform(self, transformer: Callable[["ASTNode"], Union["ASTNode", List]]):
        transformed = False
        ast = self
        self.index_children()
        i = 0
        while i < len(ast.children):
            new_ast = transformer(ast.children[i])
            if isinstance(new_ast, list):
                transformed = True
                ast.children[i:i+1] = new_ast
            elif isinstance(new_ast, ASTNode):
                transformed = True
                ast.children[i] = new_ast
            else:
                i += 1
                continue
            self.index_children()
        
        for child in ast.children:
            child_transformed = child.inner_transform(transformer)
            transformed = transformed or child_transformed
        return transformed

    def to_string(self):
        return "".join(str(x) for x in self.literals)

    def remove_self(self):
        if self.parent is None:
            raise Exception("Cannot remove_self root node")
        self.parent.children.pop(self.index)
        self.parent.index_children()

    @classmethod
    def transform(cls, root: "ASTNode", transformer: Callable[["ASTNode"], Union["ASTNode", List]]):
        transformed = False
        root.index_children()
        new_root = transformer(root)
        if new_root is not None:
            root = new_root
            transformed = True
        assert(isinstance(root, ASTNode))
        root.index_children()
        transformed = transformed or root.inner_transform(transformer)
        return root, transformed

class ASTLiteral(ASTNode):
    def __init__(self, name: str, token: Token, parser = None):
        super().__init__(name, parser=parser)
        self.token = token
    
    def __repr__(self):
        return f"ASTLiteral({repr(self.name)}, {repr(self.token)})"
