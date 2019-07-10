def arbitrary(iterable):
    try:
        return next(iter(iterable))
    except StopIteration:
        raise IndexError("Iterable is empty")