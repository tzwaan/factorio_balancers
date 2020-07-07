from py_factorio_blueprints.entity import Direction


a = Direction(2)
b = Direction(5)

assert Direction(2) + Direction(3) == 5
assert Direction(2) + Direction(3) == Direction(5)
assert Direction(2) + Direction(7) == 1
assert Direction(2) + 7 == Direction(1)
assert type(Direction(2) + 7) == Direction
assert Direction(0).is_up
assert Direction(2).is_right
assert Direction.up().is_up
assert Direction(5) - Direction(2) == Direction(3)
assert Direction(4) / 2 == 2

print("All tests successfull")
