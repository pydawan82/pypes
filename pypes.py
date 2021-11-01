from typing import Any, Callable, Generic, Iterable, Iterator, List, Tuple, TypeVar, Union
import time

T = TypeVar("T")
U = TypeVar("U")


def _getitem(stream: "Stream[T]", position: int) -> T:
    try:
        if type(stream) == Stream:
            return stream._stream[position]
    except TypeError:
        pass

    iter = stream.__iter__()
    count = 0

    try:
        while count<position:
            next(iter)
            count +=1
            
        return next(iter)
    except StopIteration:
        return IndexError("Index out of bounds")


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

    _stream: Iterable[T]
    """The underlying iterable resource of this Stream."""

    def __init__(self, stream: Iterable[T]) -> None:
        """Creates a new Stream given an iterable object."""
        super().__init__()

        self._stream = stream

    def map(self, mapping: Callable[[T], U]) -> "Stream[U]":
        """Maps each element of the stream to another with the mapping function"""
        return Stream(map(mapping, self))

    def filter(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """Filters elements of the stream that matches the predicate."""
        return Stream(filter(predicate, self))

    def filter_none(self) -> "Stream[T]":
        """Filters None values."""

        return self.filter(lambda x: x != None)

    def for_each(self, function: Callable[[T], Any]):
        """Apply the given function for each element of the stream"""

        for value in self:
            function(value)

    def for_each_and(self, function: Callable[[T], Any], between: Callable[[], Any]):
        iter = self.__iter__()

        try:
            value = next(iter)
            while True:
                function(value)
                value = next(iter)
                between()
        except StopIteration:
            pass
    
    def for_each_sleep(self, function: Callable[[T], Any], secs: float):
        self.for_each_and(function, lambda: time.sleep(secs))

    def reduce(self, reducer: Callable[[T, T], T], initial_value: T = None) -> Optional[T]:
        """
        Performs reduction over the elements of the stream using the reduction function.
        Reduction is performed left to right.
        Returns an optional value.
        """

        iter = self.__iter__()
        try:
            accumulator = initial_value if initial_value!=None else next(iter, None)
        except StopIteration:
            return Optional()

        for value in iter:
            accumulator = reducer(accumulator, value)

        return Optional(accumulator)

    def count(self) -> int:
        """Returns the number of elements in this stream."""
        return len(self._stream)

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

    def first_where(self, predicate: Callable[[T], bool]) -> Optional[T]:
        """Returns an optional value. The value is the first one that matches the predicate."""
        for value in self:
            if predicate(value):
                return Optional(value)

        return Optional()

    def only(self, length: int) -> "Stream[T]":
        return _OnlyStream(self, length)

    def skip(self, length: int) -> "Stream[T]":
        return _SkipStream(self, length)

    def drop_while(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """Returns a stream where items are dropped while the predicate is true"""
        return _DropStream(self, predicate)

    def take_while(self, predicate: Callable[[T], bool]) -> "Stream[T]":
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
            return ZipStream(*self._streams, stream)
        else:
            return ZipStream(self, stream)

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
        return list(self)

    def tuple(self) -> Tuple[T]:
        """
        Creates a tuple from this Stream.
        Equivalent to `tuple(self)`
        """
        return tuple(self)

    def get(self, position: int) -> T:
        """
        Returns the nth element in this stream
        """
        return _getitem(self, position)

    def __getitem__(self, position: int) -> T:
        return self.get(position)

    def __iter__(self) -> Iterator[T]:
        """Iterates over the elements of this stream."""
        return self._stream.__iter__()


class CatStream(Stream[T]):
    _streams: Tuple[Iterable[T]]

    def __init__(self, *streams: Iterable[T]) -> None:
        self._streams = streams

    def __iter__(self) -> Iterator[T]:
        for stream in self._streams:
            for value in stream:
                yield value


class ZipStream(Stream[Tuple[T]]):
    _streams: Tuple[Iterable[T]]

    def __init__(self, *streams: Iterable[T]) -> None:
        self._streams = streams

    def __iter__(self) -> Iterator[Tuple[T]]:
        for values in zip(*self._streams):
            yield values

class _DropStream(Stream[T]):
    stream: Iterable[T]
    predicate: Callable[[T], bool]

    def __init__(self, stream: Iterable[T], predicate: Callable[[T], bool]):
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
    stream: Iterable[T]
    predicate: Callable[[T], bool]

    def __init__(self, stream: Iterable[T], predicate: Callable[[T], bool]):
        self.stream = stream
        self.predicate = predicate

    def __iter__(self) -> Iterator[T]:
        for value in self.stream:
            if self.predicate(value):
                yield value
            else:
                break

class _OnlyStream(Stream[T]):
    stream: Iterable[T]
    length: int

    def __init__(self, stream: Iterable[T], length: int):
        self.stream = stream
        self.length = length

    def __iter__(self) -> Iterator[T]:
        for value,_ in zip(self.stream, range(self.length)):
            yield value
    
    def get(self, position:int):
        if position >= self.length:
            raise IndexError("Index out of bounds")
        return _getitem(self.stream, position) 

class _SkipStream(Stream[T]):
    stream: Iterable[T]
    length: int

    def __init__(self, stream: Iterable[T], length: int):
        self.stream = stream
        self.length = length

    def __iter__(self) -> Iterator[T]:
        iter = self.stream.__iter__()
        for value, _ in zip(iter, range(self.length)):
            pass
        
        for value in iter:
            yield value
        
    def get(self, position:int):
        return _getitem(self.stream, position+self.length)