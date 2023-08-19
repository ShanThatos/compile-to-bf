from .units import *
from .registers import *

def bfasm_prettyprint_mem(mem, ptr):
    last_line = len(mem) // USIZE
    # ranges = [range(-2, 2), range(last_line-20, last_line+2)]
    ranges = [range(-2, last_line+2)]

    while len(mem) % USIZE:
        mem.append(0)
    
    # compute marker location
    cmi = next(i for i in range(0, len(mem), USIZE) if mem[i] == 255)
    labels = {
        0: "shifter1",
        USIZE: "shifter2",
        cmi - 3 * USIZE: "query_data",
        cmi - 2 * USIZE: "compute_extra",
        cmi - 1 * USIZE: "query",
        cmi: "compute",
        cmi + 1 * USIZE: "ins_router"
    }
    for i, (reg, _) in enumerate(REGISTERS):
        labels[cmi + (2 + i) * USIZE] = reg

    output = ""
    line_num = -2
    i = 0
    while i < len(mem):
        if not any(line_num in r for r in ranges):
            line_num += 1
            i += USIZE
            continue

        if line_num is not None:
            output += f"{line_num:>4d}: "
            line_num += 1

        line_mem = mem[i:i+USIZE]
        line = [f" {x:>3d}" for x in line_mem]
        for j in range(USIZE):
            if i + j == ptr:
                line[j] = ">" + line[j][1:]
        output += " ".join(line)

        lbl = labels.get(i, "--")
        output += f"    {lbl:16s}"

        data_value = sum(x * (256**j) for j, x in enumerate(reversed(line_mem[unit.data.i0:unit.data.il+1])))
        output += f"  {data_value:>10d}"

        output += "\n"
        i += USIZE
    
    max_line_length = max(len(l) for l in output.split("\n"))
    sep = "=" * (max_line_length + 3)
    output = "\n" + sep + "\n" + output + sep

    print(output)

    # exit()

