import sys

def prettyprint_mem(mem, ptr, block_size=2**32, line_num=None):
    i = 0
    while len(mem) % block_size:
        mem.append(0)
    print("\n" + "=" * (block_size * 5 + 5))
    while i < len(mem):
        if line_num is not None:
            print(f"{line_num:>3d}:", end=" ")
            line_num += 1

        line_mem = mem[i:i+block_size]
        line = [f" {x:>3d}" for x in line_mem]
        for j in range(block_size):
            if i + j == ptr:
                line[j] = ">" + line[j][1:]
        print(" ".join(line))
        i += block_size
    print("=" * (block_size * 5 + 5))


def run_bf(code, mem=[0], ptr=0, callback=None):
    pc = process_bf(code)
    mem, ptr = run_inner_bf(pc, mem, ptr, callback)
    return mem, ptr

def run_inner_bf(pc, mem, ptr, callback=None):
    for cs in pc:
        if isinstance(cs, list):
            while mem[ptr] != 0:
                mem, ptr = run_inner_bf(cs, mem, ptr, callback)
        else:
            ch, amt = cs
            if ch == "[-]":
                mem[ptr] = 0
            elif ch == "+":
                mem[ptr] = (mem[ptr] + amt) % 256
            elif ch == "-":
                mem[ptr] = (mem[ptr] - amt) % 256
            elif ch == ">":
                ptr += amt
                while ptr >= len(mem):
                    mem.extend([0] * 10)
            elif ch == "<":
                ptr -= amt
                if ptr < 0:
                    raise Exception("Pointer out of bounds")
            elif ch == ".":
                for _ in range(amt):
                    sys.stdout.write(chr(mem[ptr]))
                sys.stdout.flush()
            elif ch == ",":
                for _ in range(amt):
                    mem[ptr] = ord(sys.stdin.read(1))
            elif ch == "@":
                if callback: callback(mem, ptr)
    return mem, ptr

def process_bf(code):
    pc = []
    i = 0
    while i < len(code):
        ch = code[i]
        if code[i:i+3] == "[-]":
            pc.append(("[-]", 1))
            i += 2
        elif ch == "[":
            start = i + 1
            depth = 1
            while depth > 0:
                i += 1
                if i == len(code):
                    raise Exception("Unmatched '['")
                elif code[i] == "[":
                    depth += 1
                elif code[i] == "]":
                    depth -= 1
            
            inner_code = code[start:i]
            pc.append(process_bf(inner_code))
        else:
            amt = 0
            while i < len(code) and code[i] == ch:
                amt += 1
                i += 1
            i -= 1
            pc.append((ch, amt))
        i += 1
    return pc

