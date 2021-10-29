from pypes import Stream


def pair(x: int):
    return x % 2 == 0


def square(x: int):
    return x**2


def main():
    stream = (Stream(range(10))
              & Stream(range(10, 20))
              & Stream(range(20, 30))
              & Stream(range(30, 40))
              )

    (stream
     .map(lambda t: sum(t))
     .dropWhile(lambda x: x<80)
     .for_each(print)
     )


if __name__ == '__main__':
    main()
