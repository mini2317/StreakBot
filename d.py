n = int(input())
a = "ABCDEFGHIJ"
table = [['.']*20 for i in range(10)]
for i in range(n):
    t = input()
    table[a.index(t[0])][int(t[1:]) - 1] = 'o'
for i in range(10):
    print(''.join(table[i]))
