from itertools import groupby


def all_equal(iterable: list):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)