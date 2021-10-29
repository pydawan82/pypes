from pypes import Stream


def pair(x: int):
    return x % 2 != 0


def main():
    res = Stream(range(10)).filter(pair).map(lambda x: x*x).map(str).sum("")

    print(res)

    Stream(range(10)).map(lambda x: x *
                          x).filter(pair).firstWhere(lambda x: x > 50).if_present(print)


if __name__ == '__main__':
    main()
