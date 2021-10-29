from typing import Any, Callable, Generic, Iterable, Iterator, List, Tuple, TypeVar, Union, overload


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
        return 1 if self.is_present() else 0

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
        """Returns a stream where items are dropped while the predicate is true"""
        return _DropStream(self, predicate)

    def takeWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """Returns a stream where items are taken while the predicate is true"""
        return _TakeStream(self, predicate)

    def append(self, stream: "Stream[T]") -> "Stream[T]":
        """Append the stream after this one"""
        return CatStream(self, stream)

    def __add__(self, stream: "Stream[T]") -> "Stream[T]":
        """Append the stream after this one"""
        return self.append(stream)

    def zip(self, stream: "Stream") -> "ZipStream":
        """
        Zips the stream.
        If the stream is already zipped, items are zipped at the same level of tuple.
        """

        if isinstance(self, ZipStream):
            return ZipStream(*self.streams, stream)
        else:
            return ZipStream(self.stream, stream)

    def __and__(self, stream: "Stream") -> "ZipStream":
        """
        Zips the stream.
        @see zip
        """
        return self.zip(stream)

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
    streams: List[Stream[T]]

    def __init__(self, *streams: Stream[T]) -> None:
        self.streams = streams

    def __iter__(self) -> Iterator[T]:
        for stream in self.streams:
            for value in stream:
                yield value


class ZipStream(Stream[Tuple[T]]):
    streams: Tuple[Stream[T]]

    def __init__(self, *streams: Stream[T]) -> None:
        self.streams = tuple(streams)

    def __iter__(self) -> Iterator[Tuple[T]]:
        for values in zip(*self.streams):
            yield values

class _DropStream(Stream[T]):
    stream: Stream[T]
    predicate: Callable[[T], bool]

    def __init__(self, stream: Stream[T], predicate: Callable[[T], bool]):
        self.stream = stream
        self.predicate = predicate

    def __iter__(self) -> Iterator[T]:
        dropping = True

        for value in self.stream:
            if dropping:
                if self.predicate(value):
                    continue
                else:
                    dropping = False

            yield value

class _TakeStream(Stream[T]):
    stream: Stream[T]
    predicate: Callable[[T], bool]

    def __init__(self, stream: Stream[T], predicate: Callable[[T], bool]):
        self.stream = stream
        self.predicate = predicate

    def __iter__(self) -> Iterator[T]:
        for value in self.stream:
            if self.predicate(value):
                yield value
            else:
                break
