
def b256(n, size):
    n %= 256**size
    ret = []
    while len(ret) < size:
        ret.append(n % 256)
        n //= 256
    return list(reversed(ret))

