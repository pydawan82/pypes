from pypes import Stream


def fibo():
    a = 0
    b = 1

    while True:
        yield a
        next = a+b
        a = b
        b = next


def main():
    stream = Stream(list(range(100)))
    print(stream[10])
    print(stream[20])

if __name__ == '__main__':
    main()
