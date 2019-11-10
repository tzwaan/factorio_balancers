from py_factorio_blueprints import Blueprint
from py_factorio_blueprints.entity import Direction
from factorio_balancers.utils import catch


class EntityError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nr = len(args)

    def __eq__(self, other):
        if len(self.args) != len(other.args):
            return False
        for arg in self.args:
            if arg not in self.args:
                return False
        return True


class IllegalEntity(EntityError):
    pass


class IllegalEntities(EntityError):
    def __repr__(self):
        result = "IllegalEntities({nr},".format(nr=self.nr)
        for exception in self.args:
            result += "\n    {}".format(repr(exception))
        result += ")"
        return result


class IllegalConfiguration(EntityError):
    pass


class IllegalConfigurations(EntityError):
    def __repr__(self):
        result = "IllegalConfigurations({nr},".format(nr=self.nr)
        for exception in self.args:
            result += "\n    {}".format(repr(exception))
        result += ")"
        return result


UNDERGROUND_DISTANCE = {
    'underground-belt': 4,
    'fast-undergroud-belt': 6,
    'express-underground-belt': 8
}


class Balancer(Blueprint):
    BELT_ENTITIES = (
        'transport-belt',
        'fast-transport-belt',
        'express-transport-belt',
    )
    UNDERGROUND_ENTITIES = (
        'underground-belt',
        'fast-underground-belt',
        'express-underground-belt',
    )
    SPLITTER_ENTITIES = (
        'splitter',
        'fast-splitter',
        'express-splitter',
    )
    ALLOWED_ENTITIES = (
        BELT_ENTITIES + UNDERGROUND_ENTITIES + SPLITTER_ENTITIES
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.recompile_entities()
        self.generate_simulation()

    def generate_simulation(self):
        self.splitters = []
        self.belts = []
        self.inputs = []
        self.outputs = []

        if self.contains_sideloads:
            self._parse_lane_balancer()
        else:
            self._parse_balancer()

    def recompile_entities(self):
        exceptions = self._check_illegal_entities()
        nr_exceptions = len(exceptions)
        if nr_exceptions > 0:
            raise IllegalEntities(*exceptions)

        self._init_entities()

        exceptions = self._check_configuration()
        nr_exceptions = len(exceptions)
        if nr_exceptions > 0:
            raise IllegalConfigurations(*exceptions)

        self.contains_sideloads = self._contains_sideloads()

    def _init_entities(self):
        for entity in self.entities:
            self._init_entity(entity)

    def _init_entity(self, entity):
        entity._is_underground = entity.name in Balancer.UNDERGROUND_ENTITIES
        entity._is_belt = entity.name in Balancer.BELT_ENTITIES

        if entity.name in Balancer.SPLITTER_ENTITIES:
            entity._is_splitter = True
            entity._partner_forward = {
                "left": None,
                "right": None
            }
            entity._partner_backward = {
                "left": None,
                "right": None
            }
        else:
            entity._is_splitter = False
            entity._partner_forward = None
            entity._partner_backward = None
            entity._partner_left = None
            entity._partner_right = None

    def _check_illegal_entities(self):
        exceptions = [IllegalEntity(entity)
                      for entity in self.entities
                      if entity.name not in Balancer.ALLOWED_ENTITIES]
        return exceptions

    def _check_configuration(self):
        def _check_belt_configuration(belt):
            position = belt.position + belt.direction.vector
            if self[position] is None:
                return
            if self[position].direction == belt.direction.rotate(2):
                raise IllegalConfiguration(belt, self[position])
            if self[position].direction != belt.direction and \
                    self[position]._is_splitter:
                raise IllegalConfiguration(belt, self[position])
            self._set_as_partner(belt, self[position])
            return

        def _check_underground_configuration(underground):
            if (
                    underground.type == "input" and
                    underground._partner_forward is None or
                    underground.type == "output" and
                    underground._partner_backward is None):
                partner = self._find_underground_partner(underground)
                if partner is None and underground.type == "input":
                    raise IllegalConfiguration(underground)
                if underground.type == "input":
                    self._set_as_partner(underground, partner)
                else:
                    self._set_as_partner(partner, underground)

            if underground.type == "output":
                position = underground.position + underground.direction.vector
                if self[position] is None:
                    return
                if self[position].direction == underground.direction.rotate(2):
                    raise IllegalConfiguration(underground, self[position])
                if self[position].direction != underground.direction and \
                        self[position]._is_splitter:
                    raise IllegalConfiguration(underground, self[position])
            return

        def _check_splitter_configuration(splitter):
            positions = [coordinate + splitter.direction.vector
                         for coordinate in splitter.coordinates]
            for position in positions:
                if self[position] is not None:
                    self._set_as_partner(splitter, self[position])

        def _check_entity_configuration(entity):
            if entity._is_belt:
                return _check_belt_configuration(entity)
            elif entity._is_underground:
                return _check_underground_configuration(entity)
            elif entity._is_splitter:
                return _check_splitter_configuration(entity)

        exceptions = []
        for entity in self.entities:
            e = catch(_check_entity_configuration, entity,
                      exceptions=(IllegalConfiguration))
            if e is None:
                continue
            if e not in exceptions:
                exceptions.append(e)
        return exceptions

    def _contains_sideloads(self):
        def make_vec_dir_tuples(directions, entity):
            # rotate input directions to match entity direction
            directions = [direction + entity.direction
                          for direction in directions]
            # make rotated directions into
            # offset vectors + opposite direction tuples
            directions = [
                (direction.vector, direction.rotate(2))
                for direction in directions]
            return directions

        def _belt_contains_sideloads(belt):
            # assume belt direction is up
            directions = [
                Direction.right(),
                Direction.down(),
                Direction.left()
            ]
            directions = make_vec_dir_tuples(directions, belt)

            nr_inputs = 0
            position = belt.position
            for vector, direction in directions:
                position = belt.position + vector
                if self[position] is None:
                    continue
                if self[position].type == "input":
                    continue
                if self[position].direction == direction:
                    nr_inputs += 1
                if nr_inputs > 1:
                    return True
            return False

        def _underground_contains_sideloads(underground):
            # assume belt direction is up
            directions = [
                Direction.right(),
                Direction.left()
            ]
            directions = make_vec_dir_tuples(directions, underground)

            for vector, direction in directions:
                position = underground.position + vector
                if self[position] is None:
                    continue
                if self[position].type == "input":
                    continue
                if self[position].direction == direction:
                    return True
            return False

        def _splitter_contains_sideloads(splitter):
            return False

        def _entity_contains_sideloads(entity):
            if entity._is_belt:
                return _belt_contains_sideloads(entity)
            elif entity._is_underground:
                return _underground_contains_sideloads(entity)
            elif entity._is_splitter:
                return _splitter_contains_sideloads(entity)

        for entity in self.entities:
            if _entity_contains_sideloads(entity):
                return True
        return False

    def _parse_balancer(self):
        pass

    def _parse_lane_balancer(self):
        pass

    def _splitter_side(self, splitter, position):
        rot_amount = splitter.direction // -2

        side_vector = position - splitter.position
        side_vector = side_vector.rotate(rot_amount)
        if side_vector.x < 0:
            return "left"
        elif side_vector.x > 0:
            return "right"
        else:
            return "middle"

    def _set_as_partner(self, inp, out):
        # direction of out compared to inp
        direction = out.direction - inp.direction

        if inp._is_splitter and out._is_splitter:
            if not direction.isUp:
                raise IllegalConfiguration(inp, out)
            side = self._splitter_side(inp, out.position)
            if side == "left":
                inp._partner_forward["left"] = out
                out._partner_backward["right"] = inp
            elif side == "right":
                inp._partner_forward["right"] = out
                out._partner_backward["left"] = inp
            elif side == "middle":
                inp._partner_forward["right"] = out
                inp._partner_forward["left"] = out
                out._partner_backward["right"] = inp
                out._partner_backward["left"] = inp
        if not out._is_splitter:
            if inp._is_splitter:
                side = self._splitter_side(inp, out.position)
                inp._partner_forward[side] = out
            else:
                inp._partner_forward = out
            if direction.isLeft:
                out._partner_left = inp
            elif direction.isUp:
                out._partner_backward = inp
            elif direction.isRight:
                out._partner_right = inp
            elif direction.isDown:
                raise IllegalConfiguration(inp, out)
        elif not inp._is_splitter and out._is_splitter:
            if not direction.isUp:
                raise IllegalConfiguration(inp, out)
            side = self._splitter_side(out, inp.position)
            out._partner_backward[side] = inp
            inp._partner_forward = out

    def _find_underground_partner(self, underground):
        max_distance = UNDERGROUND_DISTANCE[underground.name] + 1
        if underground.type == "output":
            direction = underground.direction.rotate(2)
        else:
            direction = underground.direction
        vector = direction.vector
        partner = None

        for i in range(1, max_distance):
            entity = self[underground.position + (vector * i)]
            if entity is None:
                continue
            elif entity.name != underground.name:
                continue
            elif entity.direction == underground.direction \
                    and underground.type == "input" \
                    and entity.type == "input":
                raise IllegalConfiguration(underground, entity)
            elif entity.direction == underground.direction.rotate(2) \
                    and underground.type == "input":
                raise IllegalConfiguration(underground, entity)
            elif entity.direction == underground.direction.rotate(2) \
                    and underground.type == "output" \
                    and entity.type == "output":
                raise IllegalConfiguration(underground, entity)
            elif entity.direction == underground.direction \
                    and entity.type != underground.type:
                partner = entity
                break
        return partner

