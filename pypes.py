from typing import Any, Callable, Generic, Iterable, Iterator, List, TypeVar, Union


T = TypeVar("T")
U = TypeVar("U")


class Optional(Generic[T]):
    """
    A class representing an optional value. 
    A value is considered present if the value is not None.
    """

    value: Union[T, None]

    def __init__(self, value: T = None) -> None:
        """
        Creates a new Optional with the given value.
        If no value or null is given, the Optional is considered as empty. 
        """
        super().__init__()

        self.value = value

    def is_present(self) -> bool:
        """Returns true if a value is present"""
        return self.value != None

    def value_else(self, other: T) -> T:
        """If a value is present returns the value; returns the other value otherwise."""

        return self.value if self.is_present() else other

    def if_present(self, function: Callable[[T], U]) -> Union[U, None]:
        """Returns the result of the given function if a value is present; None otherwise."""
        return function(self.value) if self.is_present() else None

    def stream(self) -> bool:
        """Returns a 1 long Stream with a value if present; an empty Stream otherwise"""
        return Stream(self)

    def __sizeof__(self) -> int:
        return 1 if self.value != None else 0

    def __iter__(self):
        if self.value != None:
            yield self.value


class Stream(Generic[T]):
    """A wrapper class to pipeline functional operations."""

    stream: Iterable[T]
    """The underlying iterable resource of this Stream."""

    def __init__(self, stream: Iterable[T]) -> None:
        """Creates a new Stream given an iterable object."""
        super().__init__()

        self.stream = stream

    def map(self, mapping: Callable[[T], U]) -> "Stream[U]":
        """Maps each element of the stream to another with the mapping function"""
        return Stream(map(mapping, self))

    def filter(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """Filters elements of the stream that matches the predicate."""
        return Stream(filter(predicate, self))

    def filterNone(self) -> "Stream[T]":
        """Filters None values."""

        return self.filter(lambda x: x != None)

    def for_each(self, function: Callable[[T], Any]):
        """Apply the given function for each element of the stream"""

        for value in self:
            function(value)

    def reduce(self, reducer: Callable[[T, T], T], initial_value: T = None) -> Optional[T]:
        """
        Performs reduction over the elements of the stream using the reduction function.
        Reduction is performed left to right.
        Returns an optional value.
        """

        skip_first = initial_value == None
        accumulator = initial_value if not skip_first else self.stream[0]

        for value in self:
            if skip_first:
                skip_first = False
                continue

            accumulator = reducer(accumulator, value)

        return Optional(accumulator)

    def count(self) -> int:
        """Returns the number of elements in this stream."""
        return len(self.stream)

    def join(self, separator="") -> str:
        """Maps elements to their string representation and join them using the given separator."""
        return self.map(str).reduce(lambda x, y: x+separator+y).value_else("")

    def sum(self, initial_value) -> T:
        """
        Returns the sum of the elements of this stream permormed left to right.
        Elements of this stream must support addition.
        Initial value
        """
        return self.reduce(lambda x, y: x+y, initial_value).value

    def firstWhere(self, predicate: Callable[[T], bool]) -> Optional[T]:
        """Returns an optional value. The value is the first one that matches the predicate."""
        for value in self:
            if predicate(value):
                return Optional(value)

        return Optional()

    def dropWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        pass

    def takeWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        pass

    def list(self) -> List[T]:
        """
        Creates a list with the elements of this stream.
        Thus, the stream must be bounded.
        """
        return list(self.stream)

    def __iter__(self) -> Iterator[T]:
        """Iterates over the elements of this stream."""
        return self.stream.__iter__()


class CatStream(Stream[T]):
    stream1: Stream[T]
    stream2: Stream[T]

    def __init__(self, stream1: Stream[T], stream2: Stream[T]) -> None:
        self.stream1 = stream1
        self.stream2 = stream2

    def __iter__(self) -> Iterator[T]:
        for value in self.stream1:
            yield value
        for value in self.stream2:
            yield value


class TupleStream(Stream[T]):
    stream1: Stream[T]
    stream2: Stream[T]

    def __init__(self, stream1: Stream[T], stream2: Stream[T]) -> None:
        self.stream1 = stream1
        self.stream2 = stream2

    def __iter__(self) -> Iterator[T]:
        for value in zip(self.stream1, self.stream2):
            yield value