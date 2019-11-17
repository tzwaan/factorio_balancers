from py_factorio_blueprints import Blueprint, BaseEntity
from py_factorio_blueprints.entity import Direction
from factorio_balancers.utils import catch
from factorio_balancers import Splitter, Belt


class EntityError(Exception):
    def __init__(self, *args, message="", **kwargs):
        super().__init__(*args, **kwargs)
        self.nr = len(args)
        self.message = message

    def __repr__(self):
        result = "<{} (".format(type(self).__name__)
        if self.message != "":
            result += "{}: ".format(self.message)
        for arg in self.args:
            result += "{}, ".format(arg)
        result += ")>"
        return result

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
        if self.message != "":
            message = "{}\n".format(self.message)
        else:
            message = ""
        result = "IllegalEntities ({message}Number of errors: {nr},".format(
            nr=self.nr, message=message)
        for exception in self.args:
            result += "\n    {}".format(repr(exception))
        result += ")"
        return result


class IllegalConfiguration(EntityError):
    pass


class IllegalConfigurations(EntityError):
    def __repr__(self):
        if self.message != "":
            message = "{}\n".format(self.message)
        else:
            message = ""
        result = "IllegalConfigurations ({message}Number of errors: {nr}," \
            .format(nr=self.nr, message=message)
        for exception in self.args:
            result += "\n    {}".format(repr(exception))
        result += ")"
        return result


class BalancerEntityMixin():
    def __init__(self):
        self._is_underground = self.name in Balancer.UNDERGROUND_ENTITIES
        self._is_belt = self.name in Balancer.BELT_ENTITIES
        self._is_splitter = self.name in Balancer.SPLITTER_ENTITIES

        self.reset()

    def reset(self):
        self._simulator = None

        if self._is_splitter:
            self._partner_forward = {
                "left": None,
                "right": None
            }
            self._partner_backward = {
                "left": None,
                "right": None
            }
        else:
            self._partner_forward = None
            self._partner_backward = None
            self._partner_left = None
            self._partner_right = None

    @property
    def has_no_inputs(self):
        if self._is_splitter:
            return (
                self._partner_backward["left"] is None and
                self._partner_backward["right"] is None
            )
        else:
            return (
                self._partner_left is None and
                self._partner_right is None and
                self._partner_backward is None
            )

    @property
    def has_no_outputs(self):
        if self._is_splitter:
            return (
                self._partner_forward["left"] is None and
                self._partner_forward["right"] is None
            )
        else:
            return self._partner_forward is None

    @property
    def has_sideloads(self):
        if self._is_belt:
            return self._belt_has_sideloads
        elif self._is_underground:
            return self._underground_has_sideloads
        elif self._is_splitter:
            return self._splitter_has_sideloads

    def _make_vec_dir_tuples(self, directions):
        # rotate input directions to match entity direction
        directions = [direction + self.direction
                      for direction in directions]
        # make rotated directions into
        # offset vectors + opposite direction tuples
        directions = [
            (direction.vector, direction.rotate(2))
            for direction in directions]
        return directions

    @property
    def _belt_has_sideloads(self):
        # assume belt direction is up
        directions = [
            Direction.right(),
            Direction.down(),
            Direction.left()
        ]
        directions = self._make_vec_dir_tuples(directions)

        nr_inputs = 0
        position = self.position
        for vector, direction in directions:
            position = self.position + vector
            if self.blueprint[position] is None:
                continue
            if self.blueprint[position].type == "input":
                continue
            if self.blueprint[position].direction == direction:
                nr_inputs += 1
            if nr_inputs > 1:
                return True
        return False

    @property
    def _underground_has_sideloads(self):
        # assume belt direction is up
        directions = [
            Direction.right(),
            Direction.left()
        ]
        directions = self._make_vec_dir_tuples(directions)

        for vector, direction in directions:
            position = self.position + vector
            if self.blueprint[position] is None:
                continue
            if self.blueprint[position].type == "input":
                continue
            if self.blueprint[position].direction == direction:
                return True
        return False

    @property
    def _splitter_has_sideloads(splitter):
        return False

    def splitter_side(self, position):
        if not self._is_splitter:
            return NotImplemented
        rot_amount = self.direction // -2

        side_vector = position - self.position
        side_vector = side_vector.rotate(rot_amount)
        if side_vector.x < 0:
            return "left"
        elif side_vector.x > 0:
            return "right"
        else:
            return "middle"

    def pad_connection(self, inp=False, out=False):
        offsets = []
        if inp:
            offsets.append(self.direction.rotate(2).vector)
        if out:
            offsets.append(self.direction.vector)
        name = entity_to_belt_name(self)

        for position in self.coordinates:
            for offset in offsets:
                self.blueprint.createEntity(
                    name,
                    position + offset,
                    self.direction)


def entity_to_belt_name(entity):
    if entity.name.startswith('express'):
        return 'express-transport-belt'
    elif entity.name.startswith('fast'):
        return 'fast-transport-belt'
    else:
        return 'transport-belt'


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

    def __init__(self, *args, print2d=False, **kwargs):
        self._print2d = True
        super().__init__(*args, entity_mixins=[BalancerEntityMixin], **kwargs)

        self.recompile_entities()
        self.pad_connections()
        self.recompile_entities()
        if print2d:
            self.print2D()
        inputs, outputs = self._get_external_connections()
        print("Nr of inputs and outputs: {}, {}".format(len(inputs), len(outputs)))
        print("Inputs: {}".format(inputs))
        print("Outputs: {}".format(outputs))

        self.generate_simulation()

    def generate_simulation(self):
        self._splitters = []
        self._belts = []
        self._inputs = []
        self._outputs = []

        if self.has_sideloads:
            self._parse_lane_balancer()
            return
        else:
            self._parse_balancer()

        print("Belts: {}".format(self._belts))
        print("Splitters: {}".format(self._splitters))
        if not self.traverse_nodes():
            raise IllegalConfiguration(
                message="The balancer is not fully connected")

    def recompile_entities(self):
        exceptions = self._check_illegal_entities()
        nr_exceptions = len(exceptions)
        if nr_exceptions > 0:
            if self._print2d:
                self.print2D()
            raise IllegalEntities(*exceptions)

        for entity in self.entities:
            entity.reset()
        exceptions = self._check_configuration()
        nr_exceptions = len(exceptions)
        if nr_exceptions > 0:
            if self._print2d:
                self.print2D()
            raise IllegalConfigurations(*exceptions)

        self.has_sideloads = self._has_sideloads()

    def _get_external_connections(self):
        inputs = []
        outputs = []
        inputs = [entity
                  for entity in self.entities
                  if entity.has_no_inputs and self._input_belt_check(entity)]
        outputs = [entity
                   for entity in self.entities
                   if entity.has_no_outputs]
        return inputs, outputs

    def _input_belt_check(self, entity):
        if entity._is_splitter:
            return True
        elif entity._partner_forward is None:
            raise IllegalConfiguration(
                entity,
                message="Entity has no forward partner")
        elif entity._partner_forward.has_sideloads:
            return False
        else:
            return self._input_belt_check(entity._partner_forward)

    def pad_connections(self):
        inputs, outputs = self._get_external_connections()

        self._pad_entities(inputs, inp=True)
        self._pad_entities(outputs, out=True)

    def _pad_entities(self, entities, **kwargs):
        for entity in entities:
            if entity._is_splitter:
                break
        else:
            return
        for entity in entities:
            entity.pad_connection(**kwargs)

    def _check_illegal_entities(self):
        exceptions = [IllegalEntity(entity,
                                    message="Entity not allowed in balancer")
                      for entity in self.entities
                      if entity.name not in Balancer.ALLOWED_ENTITIES]
        return exceptions

    def _check_configuration(self):
        def _check_belt_configuration(belt):
            position = belt.position + belt.direction.vector
            if self[position] is None:
                return
            if self[position].direction == belt.direction.rotate(2):
                raise IllegalConfiguration(belt, self[position],
                                           message="Entities facing eachother")
            if self[position].direction != belt.direction and \
                    self[position]._is_splitter:
                raise IllegalConfiguration(belt, self[position],
                                           message="Sideloading onto splitter")
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
                    raise IllegalConfiguration(
                        underground, message="Lone underground input")
                if underground.type == "input":
                    self._set_as_partner(underground, partner)
                else:
                    self._set_as_partner(partner, underground)

            if underground.type == "output":
                position = underground.position + underground.direction.vector
                if self[position] is None:
                    return
                if self[position].direction == underground.direction.rotate(2):
                    raise IllegalConfiguration(
                        underground, self[position],
                        message="Undergrounds have conflicting directions")
                if self[position].direction != underground.direction and \
                        self[position]._is_splitter:
                    raise IllegalConfiguration(
                        underground, self[position],
                        message="Sideloading onto splitter")
                self._set_as_partner(underground, self[position])
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
                      exceptions=IllegalConfiguration)
            if e is None:
                continue
            if e not in exceptions:
                exceptions.append(e)
        return exceptions

    def _has_sideloads(self):
        for entity in self.entities:
            if entity.has_sideloads:
                return True
        return False

    def _trace_belt(self, entity, position):
        if entity._is_splitter:
            return entity, position
        elif entity._partner_forward is None:
            return entity, entity.position
        elif entity._partner_forward._simulator is not None:
            return entity._partner_forward, entity.position
        else:
            return self._trace_belt(entity._partner_forward, entity.position)

    def _trace_node(self, node):
        """
        Trace nodes for a regular balancer.
        No sideloading permitted
        """
        if node.entity._is_splitter:
            trace_targets = [(node.entity._partner_forward["left"], "left"),
                             (node.entity._partner_forward["right"], "right")]
            trace_targets = [target for target in trace_targets
                             if target[0] is not None]
        else:
            trace_targets = [(node.entity, None)]

        for trace_target, from_side in trace_targets:
            target_entity, position = self._trace_belt(
                trace_target, node.entity.position)
            target_node = target_entity._simulator
            if type(target_node) is Splitter:
                to_side = target_entity.splitter_side(position)
            else:
                to_side = None

            if self.connect_nodes(node, target_node,
                                  from_side=from_side, to_side=to_side):
                if target_node != node:
                    self._trace_node(target_node)

    def _parse_balancer(self):
        for entity in self.entities:
            if entity._is_splitter:
                splitter = Splitter(entity=entity)
                self._splitters.append(splitter)
            if entity.has_no_inputs:
                belt = Belt(entity=entity)
                self._belts.append(belt)
                self._inputs.append(belt)

            elif entity.has_no_outputs:
                belt = Belt(entity=entity)
                self._belts.append(belt)
                self._outputs.append(belt)
        for node in self._inputs:
            print("tracing from input node: {}".format(node))
            self._trace_node(node)

    def _parse_lane_balancer(self):
        pass

    def _set_as_partner(self, inp, out):
        # direction of out compared to inp
        direction = out.direction - inp.direction

        if inp._is_splitter and out._is_splitter:
            if not direction.isUp:
                raise IllegalConfiguration(
                    inp, out,
                    message="Entities facing eachother")
            side = inp.splitter_side(out.position)
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
                side = inp.splitter_side(out.position)
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
                raise IllegalConfiguration(inp, out,
                                           message="Entities facing eachother")
        elif not inp._is_splitter and out._is_splitter:
            if not direction.isUp:
                raise IllegalConfiguration(inp, out,
                                           message="Sideloading onto splitter")
            side = out.splitter_side(inp.position)
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
                raise IllegalConfiguration(
                    underground, entity,
                    message="Two underground inputs in a row")
            elif entity.direction == underground.direction.rotate(2) \
                    and underground.type == "input":
                raise IllegalConfiguration(
                    underground, entity,
                    message="Two connected underground inputs")
            elif entity.direction == underground.direction.rotate(2) \
                    and underground.type == "output" \
                    and entity.type == "output":
                raise IllegalConfiguration(
                    underground, entity,
                    message="Two connected underground outputs")
            elif entity.direction == underground.direction \
                    and entity.type != underground.type:
                partner = entity
                break
        return partner

    def connect_nodes(self, from_node, to_node, from_side=None, to_side=None):
        if type(from_node) is Splitter and from_side is None:
            raise IllegalConfiguration(
                from_node.entity, from_node,
                message="No side supplied")
        if type(to_node) is Splitter and to_side is None:
            raise IllegalConfiguration(
                to_node.entity, to_node,
                message="No side supplied")

        if from_side == "middle" or to_side == "middle":
            raise IllegalConfiguration(
                from_side, to_side,
                message="Illegal side supplied")

        if type(from_node) is not Splitter:
            if from_node._output is not None:
                return False
            from_node._output = to_node
            if to_side == "left":
                to_node._input_left = from_node
            else:
                to_node._input_right = from_node
        elif type(to_node) is not Splitter:
            if to_node._input is not None:
                return False
            to_node._input = from_node
            if from_side == "left":
                from_node._output_left = to_node
            else:
                from_node._output_right = to_node
        elif type(from_node) is Splitter and type(to_node) is Splitter:
            # Todo supply proper belt properties (size)
            if from_side == "left" and from_node._output_left is not None:
                return False
            elif from_side == "right" and from_node._output_right is not None:
                return False
            belt = Belt()
            self._belts.append(belt)
            belt._input = from_node
            belt._output = to_node
            if from_side == "left":
                from_node._output_left = belt
            else:
                from_node._output_right = belt
            if to_side == "left":
                to_node._input_left = belt
            else:
                to_node._input_right = belt
        return True

    @property
    def nodes(self):
        return self._belts + self._splitters

    def traverse_nodes(self):
        """
        Recursively traverse all the nodes from a single input, going both
        forward and backwards through the graph.
        Checks whether all nodes have been traversed. If not, this means the
        graph is not fully connected.
        """
        print("All nodes:")
        for node in self.nodes:
            print("    {}".format(node))
            node._traversed = False

        start_node = self._inputs[0]
        print("start node: {}".format(start_node))

        self._traverse_node(start_node)
        for node in self.nodes:
            if not node._traversed:
                return False
        return True

    def _traverse_node(self, node):
        print("traversing node: {}".format(node))
        if node is None or node._traversed:
            return
        node._traversed = True

        if type(node) is Belt:
            self._traverse_node(node._input)
            self._traverse_node(node._output)
        else:
            self._traverse_node(node._input_left)
            self._traverse_node(node._input_right)
            self._traverse_node(node._output_left)
            self._traverse_node(node._output_right)
