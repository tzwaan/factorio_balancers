from py_factorio_blueprints.entity_mixins import BaseMixin
from py_factorio_blueprints.util import Vector
from factorio_balancers.exceptions import *
from factorio_balancers.graph import Belt as GraphBelt
from enum import Enum


class Connection:
    class Type(Enum):
        INPUT = 'input'
        OUTPUT = 'output'

    def __init__(self, entity, conn_type, multi_input=True):
        assert conn_type in Connection.Type
        self.__multi_input = multi_input
        self.__entity = entity
        self.__type = conn_type
        if self.type == Connection.Type.INPUT:
            self.__connections = []
        else:
            self.__connection = None

    @property
    def type(self):
        return self.__type

    @property
    def entity(self):
        if not (self.type == Connection.Type.OUTPUT or not self.__multi_input):
            raise AttributeError("Connection has no attribute 'entity'")
        if self.__connection is None:
            return None
        return self.__connection.__entity

    @property
    def connected(self):
        if self.type == Connection.Type.INPUT:
            return len(self.__connections) > 0
        else:
            return self.__connection is not None

    @property
    def entities(self):
        if not (self.type == Connection.Type.INPUT and self.__multi_input):
            raise AttributeError("Connection has no attribute 'entities'")
        return [conn.__entity for conn in self.__connections]

    def connect(self, other):
        if not isinstance(other, Connection):
            raise TypeError(Connection)
        if self.type == Connection.Type.INPUT:
            assert other.type == Connection.Type.OUTPUT
            other.__connection = self
            if not self.__multi_input:
                assert len(self.__connections) == 0
            assert len(self.__connections) < 3
            if other not in self.__connections:
                self.__connections.append(other)
        else:
            assert other.type == Connection.Type.INPUT
            self.__connection = other
            assert len(other.__connections) < 3
            if self not in other.__connections:
                other.__connections.append(self)

    def disconnect(self, other):
        assert isinstance(other, Connection)
        if self.type == Connection.Type.INPUT:
            assert other.type == Connection.Type.OUTPUT
            self.__connections.remove(other)
            other.__connection = None
        else:
            assert other.type == Connection.Type.INPUT
            self.__connection = None
            other.__connections.remove(self)


class BalancerEntity(BaseMixin):
    def input_belt_check(self):
        if not self.forward.connected:
            raise IllegalConfiguration(
                self,
                message="Entity has no forward partner")
        elif self.forward.entity.has_sideloads:
            return False
        else:
            return self.forward.entity.input_belt_check()

    def side_from_position(self, position):
        rot_amount = self.direction // -2
        side_vector = position - self.position
        side_vector = side_vector.rotate(rot_amount)
        if side_vector.x < 0:
            return 'left'
        elif side_vector.x > 0:
            return 'right'
        else:
            return None

    @property
    def coordinates(self):
        return [self.position]

    def pad_connection(self, inp=False, out=False):
        names = {
            1: 'transport-belt',
            2: 'fast-transport-belt',
            3: 'express-transport-belt',
        }
        name = names[self.name.data['belt_speed']]

        if inp:
            new = self.blueprint.entities.make(
                name=name,
                position=self.position + self.direction.rotate(2).vector,
                direction=self.direction)
            connection1 = self.backward
            connection2 = new.forward
            connection1.connect(connection2)
        if out:
            new = self.blueprint.entities.make(
                name=name,
                position=self.position + self.direction.vector,
                direction=self.direction)
            connection1 = self.forward
            connection2 = new.backward
            connection1.connect(connection2)

    def _trace_nodes(self, belt, position, lane=None):
        speed = self.name.data['belt_speed']
        if speed < belt.capacity:
            belt.capacity = speed
        if isinstance(self.forward.entity, (Belt, Underground)):
            return self.forward.entity._trace_nodes(belt, self.position, lane=lane)
        elif isinstance(self.forward.entity, Splitter):
            self.forward.entity._trace_nodes(belt, self.position, lane=lane)
            return belt
        elif self.forward.entity is None:
            self.blueprint._belts.append(belt)
            self.blueprint._output_belts.append(belt)


class Belt(BalancerEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__forward = Connection(self, Connection.Type.OUTPUT)
        self.__backward = Connection(self, Connection.Type.INPUT)

    def _trace_nodes(self, belt, position, lane=None):
        if lane is None or not getattr(self, '_has_node', False):
            return super()._trace_nodes(belt, self.position, lane=lane)

        def opposite(a):
            return {'left': 'right', 'right': 'left'}[a]

        speed = self.name.data['belt_speed']
        if speed < belt.capacity:
            belt.capacity = speed
        side = self.side_from_position(position)
        if side is None:
            node = getattr(self, f'_node_{lane}')
            field = f'input_{opposite(lane)}'
            if getattr(node, field) is None:
                setattr(node, field, GraphBelt(capacity=speed, node=node))
                belt.next = getattr(node, field)
            else:
                raise IllegalConfiguration(
                    "Can't connect to the same side twice")
        else:
            node = getattr(self, f'_node_sideload_{side}')
            field = f'input_{lane}'
            if getattr(node, field) is None:
                setattr(node, field, GraphBelt(capacity=speed, node=node))
                belt.next = getattr(node, field)
            else:
                raise IllegalConfiguration(
                    "Can't connect to the same side twice")
        self.blueprint._belts.append(belt)

        lane_side = lane if side is None else side
        if getattr(self, f'_traversed_{lane_side}', False):
            return belt
        setattr(self, f'_traversed_{lane_side}', True)

        node = getattr(self, f'_node_{lane_side}')
        field = f'output_{opposite(lane_side)}'
        setattr(node, field, GraphBelt(capacity=speed, node=node))
        super()._trace_nodes(
            getattr(node, field),
            self.position, lane=lane_side)
        return belt

    @property
    def forward(self):
        return self.__forward

    @property
    def backward(self):
        return self.__backward

    def reset(self):
        pass

    def get_connection_for(self, position, conn_type):
        if conn_type == Connection.Type.INPUT:
            return self.backward
        else:
            return self.forward

    @property
    def has_sideloads(self):
        return len(self.backward.entities) > 1

    @property
    def has_no_inputs(self):
        return not self.backward.connected

    @property
    def has_no_outputs(self):
        return not self.forward.connected

    def setup_transport_lines(self):
        position = self.position + self.direction.vector
        other = self.blueprint.entities[position]
        if not other:
            return
        elif len(other) > 1:
            raise IllegalConfiguration(
                self, other,
                message="More than one entity occupying the same space")
        other = other[0]
        if other.direction == self.direction.rotate(2):
            raise IllegalConfiguration(
                self, other, message="Entities facing each other")
        if other.direction != self.direction and isinstance(other, Splitter):
            raise IllegalConfiguration(
                self, other, message="Sideloading onto a splitter")
        self.forward.connect(
            other.get_connection_for(
                position, Connection.Type.INPUT))


class Splitter(BalancerEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__forward_left = Connection(
            self, Connection.Type.OUTPUT, multi_input=False)
        self.__forward_right = Connection(
            self, Connection.Type.OUTPUT, multi_input=False)
        self.__backward_left = Connection(self, Connection.Type.INPUT)
        self.__backward_right = Connection(self, Connection.Type.INPUT)

    @property
    def forward_left(self):
        return self.__forward_left

    @property
    def forward_right(self):
        return self.__forward_right

    @property
    def backward_left(self):
        return self.__backward_left

    @property
    def backward_right(self):
        return self.__backward_right

    def reset(self):
        pass

    @property
    def coordinates(self):
        amount = self.direction // 2
        vectors = [
            Vector(-0.5, 0).rotate(amount),
            Vector(0.5, 0).rotate(amount)]
        return [self.position + vector
                for vector in vectors]

    def get_connection_for(self, position, conn_type):
        rot_amount = self.direction // -2

        side_vector = position - self.position
        side_vector = side_vector.rotate(rot_amount)
        if side_vector.x < 0:
            if conn_type == Connection.Type.INPUT:
                return self.backward_left
            else:
                return self.forward_left
        else:
            if conn_type == Connection.Type.INPUT:
                return self.backward_right
            else:
                return self.forward_right

    @property
    def has_sideloads(self):
        return False

    def input_belt_check(self):
        return True

    @property
    def has_no_inputs(self):
        return not self.backward_right.connected and \
               not self.backward_left.connected

    @property
    def has_no_outputs(self):
        return not self.forward_left.connected and \
               not self.forward_right.connected

    def setup_transport_lines(self):
        positions = [coordinate + self.direction.vector
                     for coordinate in self.coordinates]
        for position in positions:
            other = self.blueprint.entities[position]
            if not other:
                continue
            elif len(other) > 1:
                raise IllegalConfiguration(
                    self, other,
                    message="More than one entity occupying the same space")
            other = other[0]
            if other.direction == self.direction.rotate(2):
                raise IllegalConfiguration(
                    self, other, message="Entities facing each other")
            if other.direction != self.direction and isinstance(other, Splitter):
                raise IllegalConfiguration(
                    self, other, message="Sideloading onto a splitter")
            connection1 = self.get_connection_for(
                position, Connection.Type.OUTPUT)
            connection2 = other.get_connection_for(
                position, Connection.Type.INPUT)
            connection1.connect(connection2)

    def pad_connection(self, inp=False, out=False):
        names = {
            1: 'transport-belt',
            2: 'fast-transport-belt',
            3: 'express-transport-belt',
        }
        name = names[self.name.data['belt_speed']]

        left, right = self.coordinates
        if inp:
            new_left = self.blueprint.entities.make(
                name=name,
                position=left + self.direction.rotate(2).vector,
                direction=self.direction)
            new_right = self.blueprint.entities.make(
                name=name,
                position=right + self.direction.rotate(2).vector,
                direction=self.direction)
            self.backward_left.connect(new_left.forward)
            self.backward_right.connect(new_right.forward)
        if out:
            new_left = self.blueprint.entities.make(
                name=name,
                position=left + self.direction.vector,
                direction=self.direction)
            new_right = self.blueprint.entities.make(
                name=name,
                position=right + self.direction.vector,
                direction=self.direction)
            self.forward_left.connect(new_left.backward)
            self.forward_right.connect(new_right.backward)

    def _trace_nodes(self, belt, position, lane=None):
        side = self.side_from_position(position)
        node = getattr(self, f'_node{f"_{lane}" if lane is not None else ""}')
        if side == 'left':
            if node.input_left is None:
                node.input_left = GraphBelt(
                    capacity=belt.capacity,
                    node=node)
                belt.next = node.input_left
            else:
                raise IllegalConfiguration(
                    "Can't connect to the same side twice")
        else:
            if node.input_right is None:
                node.input_right = GraphBelt(
                    capacity=belt.capacity,
                    node=node)
                belt.next = node.input_right
            else:
                raise IllegalConfiguration(
                    "Can't connect to the same side twice")
        self.blueprint._belts.append(belt)

        if getattr(self, f'_traversed{f"_{lane}" if lane else ""}', False):
            return belt
        setattr(self, f'_traversed{f"_{lane}" if lane else ""}', True)

        if self.forward_left.connected:
            node.output_left = GraphBelt(
                capacity=self.name.data['belt_speed'],
                node=node)
            self.forward_left.entity._trace_nodes(
                node.output_left, self.coordinates[0], lane=lane)
        if self.forward_right.connected:
            node.output_right = GraphBelt(
                capacity=self.name.data['belt_speed'],
                node=node)
            self.forward_right.entity._trace_nodes(
                node.output_right, self.coordinates[1], lane=lane)

        return belt


class Underground(BalancerEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__forward = Connection(self, Connection.Type.OUTPUT)
        self.__backward = Connection(self, Connection.Type.INPUT)

    @property
    def forward(self):
        return self.__forward

    @property
    def backward(self):
        return self.__backward

    def reset(self):
        pass

    @property
    def has_no_inputs(self):
        return not self.backward.connected
    @property

    def has_no_outputs(self):
        return not self.forward.connected

    def get_connection_for(self, position, conn_type):
        if conn_type == Connection.Type.INPUT:
            return self.backward
        else:
            return self.forward

    def find_partner(self):
        max_distance = self.name.data['max_distance'] + 1
        if self.type == 'output':
            direction = self.direction.rotate(2)
        else:
            direction = self.direction
        vector = direction.vector
        for i in range(1, max_distance + 1):
            entity = self.blueprint.entities[self.position + vector * i]
            if not entity:
                continue
            elif len(entity) > 1:
                raise IllegalConfiguration(
                    self, entity,
                    message="More than one entity occupying the same space")
            entity = entity[0]
            if entity.name != self.name:
                continue
            elif entity.direction == self.direction \
                    and self.type == 'input' \
                    and entity.type == 'input':
                raise IllegalConfiguration(
                    self, entity, message="Two underground inputs in a row")
            elif entity.direction == self.direction.rotate(2) \
                    and self.type == 'input':
                raise IllegalConfiguration(
                    self, entity,
                    message="Two connected underground inputs")
            elif entity.direction == self.direction.rotate(2) \
                    and self.type == 'output' \
                    and entity.type == 'output':
                raise IllegalConfiguration(
                    self, entity,
                    message="Two connected underground outputs")
            elif entity.direction == self.direction \
                    and entity.type != self.type:
                return entity
        return None

    @property
    def has_sideloads(self):
        for entity in self.backward.entities:
            if entity.direction != self.direction:
                return True
        else:
            return False

    def setup_transport_lines(self):
        partner = self.find_partner()
        if partner is None and self.type == 'input':
            raise IllegalConfiguration(
                self, message="Lone underground input")
        if partner is not None:
            if self.type == 'input':
                self.forward.connect(
                    partner.get_connection_for(
                        partner.position, Connection.Type.INPUT))
            else:
                self.backward.connect(
                    partner.get_connection_for(
                        partner.position, Connection.Type.OUTPUT))
        if self.type == 'output':
            Belt.setup_transport_lines(self)

    def _trace_nodes(self, belt, position, lane=None):
        if lane is None or not getattr(self, '_has_node', False):
            return super()._trace_nodes(belt, self.position, lane=lane)

        def opposite(a):
            return {'left': 'right', 'right': 'left'}[a]

        speed = self.name.data['belt_speed']
        if speed < belt.capacity:
            belt.capacity = speed
        side = self.side_from_position(position)
        if side is None:
            node = getattr(self, f'_node_{lane}')
            field = f'input_{opposite(lane)}'
            if getattr(node, field) is None:
                setattr(node, field, GraphBelt(capacity=speed, node=node))
                belt.next = getattr(node, field)
            else:
                raise IllegalConfiguration(
                    "Can't connect to the same side twice")
        else:
            node = getattr(self, f'_node_{side}')
            lane_check = lane
            if self.type == 'output':
                lane_check = opposite(lane)
            if side != lane_check:
                return belt
            field = f'input_{side}'
            if getattr(node, field) is None:
                setattr(node, field, GraphBelt(
                    capacity=speed, node=node))
                belt.next = getattr(node, field)
            else:
                raise IllegalConfiguration(
                    "Can't connect to the same side twice")
        self.blueprint._belts.append(belt)

        lane_side = lane if side is None else side
        if getattr(self, f'_traversed_{lane_side}', False):
            return belt
        setattr(self, f'_traversed_{lane_side}', True)

        node = getattr(self, f'_node_{lane_side}')
        field = f'output_{opposite(lane_side)}'
        setattr(node, field, GraphBelt(capacity=speed, node=node))
        super()._trace_nodes(
            getattr(node, field),
            self.position, lane=lane_side)
        return belt


entity_prototypes = {
    'transport-belt': {
        'mixins': [Belt],
    },
    'underground-belt': {
        'mixins': [Underground],
    },
    'splitter': {
        'mixins': [Splitter],
    },
}
