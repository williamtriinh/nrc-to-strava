def find(collection: list[any], predicate: callable) -> any:
    return next(x for x in collection if predicate(x))
