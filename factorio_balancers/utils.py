from functools import reduce
from fractions import Fraction
from operator import mul


class Direction:
    up = 0
    right = 2
    down = 4
    left = 6

    def to_delta(direction):
        direction = direction % 8
        if direction == Direction.up:
            return (0, -1)
        elif direction == Direction.right:
            return (1, 0)
        elif direction == Direction.down:
            return (0, 1)
        elif direction == Direction.left:
            return (-1, 0)
        return (0, 0)


def catch(func, *args, handle=lambda e: e, exceptions=(Exception,), **kwargs):
    try:
        return func(*args, **kwargs)
    except exceptions as e:
        return handle(e)


def get_nr_of_permutations(nr_inputs, nr_outputs, max_nr):
    def nCk(n, k):
        return int(reduce(mul, (Fraction(n - i, i + 1) for i in range(k)), 1))

    perms = 0
    if nr_inputs < max_nr:
        max_nr = nr_inputs
    if nr_outputs < max_nr:
        max_nr = nr_outputs
    for i in range(1, max_nr + 1):
        perms += nCk(nr_inputs, i) * nCk(nr_outputs, i)
    return perms
