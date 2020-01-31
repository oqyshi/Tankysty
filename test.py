def f(n):
    return str(bin(n)).count('1')

def g(n):
    return f(n) > 7


rez = 0
for i in range(1024):
    if g(i):
        rez += 1
print(rez)