# Compile High Level to Brainf&ast;ck

April 2023, I followed up on my shower thoughts. I worked on this project for 4 months and I have 3 words: Challenging, Impractical, Nightmarish. 

## wtf is this?
- A way to make your friends question your sanity
- A way to make your friends question their sanity
- The only reason for you to confidently add brainf&ast;ck to your resume

For real though, this is a transpiler/compiler that takes in a custom high level language and outputs brainf&ast;ck code. And when I say transpiler/compiler, I truly mean it. 

## Why?
Because no one has done it before. I think. I hope. Because it's so weird to me that brainf&ast;ck is considered turing complete. Because after 30 years, I think it's time for brainf&ast;ck to be considered for practical uses, jk that's never happening. 

## How?
I'm not sure if I want to answer that right now. 

## What's the high level language?
I call it bfun. Internally, bfun is compiled to a custom assembly-like language called bfasm. The bfasm code is loaded into brainf&ast;ck memory (somewhat like a cpu & program memory). The cpu brainf&ast;ck code is then tacked onto the end of the bfasm-brainf&ast;ck code. 

The spec for bfun & bfasm is in [spec.json](spec.json). You can write bfun & bfasm code side-by-side! The code itself reads like a combination of C & Python. 

Check out the [standard library](./lib/) folder for some examples. You should also probably just import [lib/common.bfun](./lib/common.bfun) into your code. Division & modulus operators won't work without it. 

List of features: 
- registers
    - ip: instruction pointer
    - cr: comparison register
    - e0, e1: expression registers (used for computing expressions)
    - r0, r1, r2: general purpose registers (not saved across function calls)
    - cp: call pointer (used for function calls)
    - this: this pointer (used for object-oriented programming)
- ~25 asm-like instructions
- imports
- comments
- strings
- variables
- if/else statements
- while loops
    - continue, break
- expressions
    - relational operators (==, !=, <, <=, >, >=)
    - arithmetic operators (+, -, *, /, %)
    - assignment operators (=, +=, -=, *=, /=, %=)
    - index operator (arr[0])
    - function call operator (print(""))
    - attribute operator (this.wow)
- functions
    - variadic functions
    - return statement
- classes
    - fields
    - instanced methods

## Example Code
Here's a simple hello world program. 
```python
import "lib/common.bfun"
print("Hello World!")
```
Easy right? The resulting brainf&ast;ck code is 170,000+ characters long. Here it is: [examples/helloworld.bf](./examples/helloworld.bf). BTW, don't run this with your typical brainf&ast;ck interpreter. It'll take a while. Keep reading to find out which interpreter to use.

Let's look at a more complex example. Here's a program that prints some fibonacci numbers. 
```python
import "lib/common.bfun"
a = 1
b = 1
while (a < 2000) {
    print("%d\n", a)
    c = a + b
    a = b
    b = c
}
```
Here it is: [examples/fib.bf](./examples/fib.bf). Notice one thing, it goes beyond 255 :D. The brainf&ast;ck code itself is meant to be run in an 8-bit cell interpreter, but bfun & bfasm supports up to 32-bit integers. And theoretically, there's a single variable in my code that can be increased to make it support any number of bits even though brainf&ast;ck itself is limited to 8-bit cells. 

## How to run
Running the transpiler is a simple: 
```shell 
python launch.py <bfun file>
```
This will output a brainf&ast;ck file in the `bin/` folder.

Running the produced bf code is a different story. You can try running the code with a traditional brainf&ast;ck interpreter but it will not run fast enough -- trust me. I've tried. Here's the solution I came up with. I found an optimizing bf to C compiler called [bfc.py](https://www.nayuki.io/page/optimizing-brainfuck-compiler). I modified it slightly to support more brainf&ast;ck patterns. See [bf/bfc.py](bf/bfc.py). After that you can compile the C code to an executable and then run it. All of this can triggered with launch flags: 

```shell 
python launch.py -c <bfun file>
python launch.py -ce <bfun file>
python launch.py -cer <bfun file>
```

| Launch Flag | Result |
|- |- |
| -c | Compile bf to C |
| -e | Compile C to executable |
| -r | Run the executable |

You will need gcc on your PATH for the -e flag to work. 

## Brainf&ast;ck Implementation Details
This project was built to work with a mostly normal brainf&ast;ck implementation. This means: 
- 8-bit cells
- Unbounded memory
- Overflow/underflow wrapping
