class Direction():
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


def catch(func, *args, handle=lambda e: e, exceptions=(Exception), **kwargs):
    try:
        return func(*args, **kwargs)
    except exceptions as e:
        return handle(e)
