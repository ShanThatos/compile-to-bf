import re
from functools import wraps

def simp(code):
    code = re.sub(r"[^<>+-.,\[\]@]", "", code)
    deletes = ["<>", "><", "+-", "-+"]
    replaces = {x:"" for x in deletes} | {"[[-]]":"[-]", "][-]": "]"}
    while any(k in code for k in replaces):
        for k,v in replaces.items():
            code = code.replace(k, v)
    return code


def simplify(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return simp(f(*args, **kwargs))
    return wrapper


def bf_f(n=1):
    return (">" if n > 0 else "<") * abs(n)

def bf_b(n=1):
    return ("<" if n > 0 else ">") * abs(n)

def bf_fb(n=1, code=""):
    return bf_f(n) + code + bf_b(n)

def bf_bf(n=1, code=""):
    return bf_b(n) + code + bf_f(n)

def bf_set(v: int, clear: bool = True):
    return clear * "[-]" + ("-" * (256 - v) if v > 128 else "+" * v)

def bf_glide_f(target: int, step: int):
    assert(target >= 250) # trying to only use high target values
    p = "+" * (256-target)
    m = "-" * (256-target)
    return f"{p}[{m}{'>' * step}{p}]{m}"

def bf_glide_b(target: int, step: int):
    assert(target >= 250) # trying to only use high target values
    p = "+" * (256-target)
    m = "-" * (256-target)
    return f"{p}[{m}{'<' * step}{p}]{m}"