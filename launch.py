import subprocess
import shutil
import sys
import time

from pathlib import Path
from typing import List

from bfasm.compile import BFunCompiler
from bf.bfc import main as bfcmain

def main(args: List[str]):
    shutil.rmtree("./bin/", ignore_errors=True)
    Path("./bin/").mkdir(parents=True, exist_ok=True)
    Path("./bin/passes").mkdir(parents=True, exist_ok=True)

    print("bfun to bf...")
    start_time = time.time()
    bf_code = BFunCompiler(args[-1], "./spec.json").compile_to_bf(True)
    
    print("bf to c...")
    bfcmain(["bin/code.bf", "bin/code.c"])
    
    print("c to executable...")
    subprocess.run(["gcc", "bin/code.c", "-o", "bin/code"])
    compile_time = time.time() - start_time
    
    print("running...")
    start_time = time.time()
    subprocess.run(["bin/code"])
    run_time = time.time() - start_time

    print()
    print(f"bf code size:\t {len(bf_code)}")
    print(f"compile time:\t {compile_time:.3f}s")
    print(f"run time:\t {run_time:.3f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
