import subprocess
import shutil
import sys
import time

from pathlib import Path
from typing import List

from bfasm.compile import BFunCompiler
from bf.bfc import main as bfcmain

def collect_flags(args: List[str]) -> List[str]:
    flags = []
    for arg in args:
        if arg.startswith("-"):
            flags.extend(arg[1:])
    return flags

def main(args: List[str]):
    shutil.rmtree("./bin/", ignore_errors=True)
    Path("./bin/").mkdir(parents=True, exist_ok=True)
    Path("./bin/passes").mkdir(parents=True, exist_ok=True)

    flags = collect_flags(args)
    compile_bf_to_c = "c" in flags
    compile_c_to_executable = "e" in flags
    run_binary = "r" in flags
    if compile_c_to_executable and not compile_bf_to_c:
        print("error: cannot compile to executable without compiling to c first")
        return
    if run_binary and not compile_c_to_executable:
        print("error: cannot run without compiling to executable first")
        return

    print("bfun to bf...")
    start_time = time.time()
    bf_code = BFunCompiler(args[-1], "./spec.json").compile_to_bf(True)
    
    if compile_bf_to_c:
        print("bf to c...")
        bfcmain(["bin/code.bf", "bin/code.c"])
    
    if compile_c_to_executable:
        print("c to executable...")
        subprocess.run(["gcc", "bin/code.c", "-o", "bin/code"])
    compile_time = time.time() - start_time
    
    if run_binary:
        print("running...")
        start_time = time.time()
        subprocess.run(["bin/code"])
        run_time = time.time() - start_time

    print()
    print(f"bf code size:\t {len(bf_code)}")
    print(f"compile time:\t {compile_time:.3f}s")
    if run_binary:
        print(f"run time:\t {run_time:.3f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
