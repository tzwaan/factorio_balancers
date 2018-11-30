import math


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


class Position():
    def __init__(self, x, y, direction=Direction.up):
        self.x = x
        self.y = y
        self.direction = direction


class Blueprintgrid():
    def __init__(self, width=1, height=1):
        self.width = width
        self.height = height
        self.entities = []
        self.grid = [[None for x in range(width)] for y in range(height)]

    @classmethod
    def from_blueprint(cls, blueprint):
        max_x, max_y = blueprint.make_positive_positions()
        max_x = math.ceil(max_x)
        max_y = math.ceil(max_y)

        grid = cls(width=max_x + 1, height=max_y + 1)

        for entity in blueprint.entities:
            if entity.info['prototype'] == 'belt':
                position = Position(entity.position['x'],
                                    entity.position['y'],
                                    entity.direction)
                belt = Grid_belt(position=position,
                                 speed=entity.info['transport-speed'])
                grid.add_entity(belt)
            elif entity.info['prototype'] == 'splitter':
                positions = []
                positions.append(Position(math.floor(entity.position['x']),
                                          math.floor(entity.position['y']),
                                          entity.direction))
                positions.append(Position(math.ceil(entity.position['x']),
                                          math.ceil(entity.position['y']),
                                          entity.direction))

                splitter = Grid_splitter(position=positions,
                                         speed=entity.info['transport-speed'])
                grid.add_entity(splitter)
            elif entity.info['prototype'] == 'underground-belt':
                position = Position(entity.position['x'],
                                    entity.position['y'],
                                    entity.direction)
                ug_belt = Grid_underground(position=position,
                                           speed=entity.info['transport-speed'],
                                           type=entity.type)
                grid.add_entity(ug_belt)

        grid.process_grid()

        return grid

    @property
    def splitters(self):
        splitters = []
        for entity in self.entities:
            if isinstance(entity, Grid_splitter):
                splitters.append(entity)
        return splitters

    def add_entity(self, entity, position=None):
        if position is not None:
            entity.position = position
        if isinstance(entity.position, list):
            positions = entity.position
        else:
            positions = [entity.position]
        # print(positions)

        for position in positions:
            # print(position)
            self.grid[position.y][position.x] = entity
        entity.set_grid(self)
        self.entities.append(entity)

    def process_grid(self):
        for entity in self.entities:
            # print("processing entity: (%d, %d)", entity.position.x, entity.position.y)
            if isinstance(entity, Grid_underground):
                entity.find_partner()
                entity.find_inputs()
            elif isinstance(entity, Grid_belt):
                entity.find_inputs()
            elif isinstance(entity, Grid_splitter):
                entity.find_inputs()

    def print_blueprint_grid(self):
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                if self.grid[y][x] is None:
                    line += " "
                else:
                    line += self.grid[y][x].print()
            print(line)
        print("")


class Grid_entity(object):
    def __init__(self, position=None, speed=1):
        self.inputs = []
        self.outputs = []
        self.speed = speed
        self.position = position

    def set_grid(self, grid):
        self.blueprintgrid = grid

    def print(self):
        return "X"

    @property
    def grid(self):
        return self.blueprintgrid.grid

    @property
    def direction(self):
        return self.position.direction

    def trace_belt(self, forward=True):
        results = []
        if forward:
            if len(self.outputs) == 0:
                # print("no outputs, returning self", self)
                return [self]
            elif len(self.outputs) > 1:
                raise RuntimeError("Entity other than splitter with multiple outputs is not possible")
            for out in self.outputs:
                results.extend(out.trace_belt(forward=True))
        else:
            if len(self.inputs) == 0:
                return [self]
            elif len(self.inputs) > 1:
                raise RuntimeError("Sideloading is currently not supported")
            for inp in self.inputs:
                results.extend(inp.trace_belt(forward=False))
        return results


class Grid_splitter(Grid_entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def direction(self):
        return self.position[0].direction

    def print(self):
        return "S"

    def set_splitter(self, splitter):
        self.splitter = splitter

    def trace_belt(self, forward=True):
        return [self]

    def find_inputs(self):
        for position in self.position:
            # print(position)
            dx, dy = Direction.to_delta(position.direction + 4)
            y = position.y + dy
            x = position.x + dx
            # print(x, y, position.direction)
            if x < 0 or x >= self.blueprintgrid.width or y < 0 or y >= self.blueprintgrid.height:
                continue
            source = self.grid[y][x]
            if isinstance(source, Grid_entity) and source.direction == self.direction:
                # print("found input", source)
                if isinstance(source, Grid_underground) and source.type == "input":
                    continue
                self.inputs.append(source)
                source.outputs.append(self)


class Grid_belt(Grid_entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def print(self):
        if self.direction == Direction.up:
            return "^"
        elif self.direction == Direction.right:
            return ">"
        elif self.direction == Direction.down:
            return "v"
        elif self.direction == Direction.left:
            return "<"

    def find_inputs(self):
        # print("finding inputs, I'm belt (%d, %d)" % (self.position.x, self.position.y))
        for i in range(2, 8, 2):
            dx, dy = Direction.to_delta(self.direction + i)
            x = self.position.x + dx
            y = self.position.y + dy
            # print(x, y)
            if x < 0 or x >= self.blueprintgrid.width or y < 0 or y >= self.blueprintgrid.height:
                continue
            source = self.grid[y][x]
            if isinstance(source, Grid_entity) and source.direction == (self.direction + i + 4) % 8:
                if isinstance(source, Grid_underground) and source.type == "input":
                    continue
                # if isinstance(source, Grid_splitter):
                #     print("found splitter source. my position: ", self.position.x, self.position.y)
                self.inputs.append(source)
                source.outputs.append(self)
        return


class Grid_underground(Grid_entity):
    def __init__(self, type='input', **kwargs):
        super().__init__(**kwargs)
        self.type = type
        self.has_partner = False

    def print(self):
        if self.type == "input":
            return "D"
        else:
            return "U"

    def find_inputs(self):
        if self.type == "output":
            dirstep = 4
        else:
            dirstep = 2
        for i in range(2, 8, dirstep):
            dx, dy = Direction.to_delta(self.direction + i)
            x = self.position.x + dx
            y = self.position.y + dy
            # print("UG belt, my position: (%d, %d)" % (self.position.x, self.position.y), "target: (%d, %d)"%(x,y))
            if x < 0 or x >= self.blueprintgrid.width or y < 0 or y >= self.blueprintgrid.height:
                continue
            source = self.grid[y][x]
            if isinstance(source, Grid_entity) and source.direction == (self.direction + i + 4) % 8:
                if isinstance(source, Grid_underground) and source.type == "input":
                    continue
                self.inputs.append(source)
                source.outputs.append(self)

    def find_partner(self):
        if self.has_partner:
            return
        max_distance = 2 + 2 * self.speed
        if self.type == 'input':
            dx, dy = Direction.to_delta(self.direction)
            for i in range(1, max_distance + 2):
                y = self.position.y + i * dy
                x = self.position.x + i * dx
                if x < 0 or x >= self.blueprintgrid.width or y < 0 or y >= self.blueprintgrid.height:
                    self.has_partner = False
                    return
                target = self.grid[y][x]
                if isinstance(target, Grid_underground) and target.direction == self.direction and target.speed == self.speed:
                    if target.type == "output":
                        # print("found partner")
                        # print("self: ", self.position.x, self.position.y, "partner: ", x, y)
                        self.outputs.append(target)
                        target.inputs.append(self)
                        self.has_partner = True
                        target.has_partner = True
                        return
                    self.has_partner = False
                    return
        else:
            dx, dy = Direction.to_delta(self.direction + 4)
            for i in range(1, max_distance + 2):
                y = self.position.y + i * dy
                x = self.position.x + i * dx
                if x < 0 or x >= self.blueprintgrid.width or y < 0 or y >= self.blueprintgrid.height:
                    self.has_partner = False
                    return
                target = self.grid[y][x]
                if isinstance(target, Grid_underground) and target.direction == self.direction and target.type == "input" and target.speed == self.speed:
                    # print("found partner")
                    # print("self: ", self.position.x, self.position.y, "partner: ", x, y)
                    self.inputs.append(target)
                    target.outputs = [self]
                    self.has_partner = True
                    target.has_partner = True
                    # print("inputs: ", self.inputs, "outputs", target.outputs)
                    return
        self.has_partner = False
