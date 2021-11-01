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
    stream = Stream(list(range(100))).only(15)
    print(stream[10])

if __name__ == '__main__':
    main()
