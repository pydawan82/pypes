from pypes import CatStream, Stream, TupleStream


def pair(x: int):
    return x % 2 != 0


def main():
    s1 = Stream(range(10))
    s2 = Stream(range(10,20))

    TupleStream(s1, s2).for_each(print)
    CatStream(s1, s2).for_each(print)

if __name__ == '__main__':
    main()
