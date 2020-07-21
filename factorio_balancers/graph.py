from enum import Enum, auto
from fractions import Fraction


class Belt:
    def __init__(self, capacity=1, next=None, node=None):
        self.next = next
        self.node = node
        self.capacity = capacity
        self.__content = Fraction(0, 1)

    def __repr__(self):
        return f"<Belt( {self.__content} of {self.capacity} )>"

    @property
    def content(self):
        return self.__content

    @content.setter
    def content(self, value):
        if value > self.capacity:
            raise ValueError(
                f"Content can't exceed capacity: {value}/{self.capacity}")
        self.__content = value

    @property
    def available(self):
        return self.capacity - self.content

    @property
    def percentage(self):
        return (self.content / self.capacity) * 100.0

    @property
    def full(self):
        return self.content == self.capacity

    @property
    def empty(self):
        return self.content == 0

    def supply(self, amount=None):
        if amount is None or amount > self.capacity:
            amount = self.capacity
        if not isinstance(amount, Fraction):
            amount = Fraction(amount)
        result = amount - self.content
        self.content = amount
        return result

    def clear(self, amount=None):
        if amount is None:
            amount = self.content
        self.content -= amount
        return amount

    def transfer(self):
        if self.next is None:
            return

        available = self.next.available
        if available < self.content:
            self.content -= available
            self.next.content += available
        else:
            self.next.content += self.content
            self.content = 0

class Splitter:
    class Priority(Enum):
        off = None
        left = 'left'
        right = 'right'

    def __init__(self, entity=None,
                 uid=None,
                 lane_side=None, sideload=None, straight=None,
                 input_priority=None, output_priority=None):
        self.uid = uid
        self.entity = entity
        self.lane_side = lane_side
        self.sideload = sideload
        if self.entity is not None:
            self.entity._has_node = True
            if self.lane_side is not None:
                setattr(self.entity, f'_node_{self.lane_side}', self)
            elif self.sideload is not None:
                setattr(self.entity, f'_node_sideload_{self.sideload}', self)
            else:
                self.entity._node = self

        self.input_left = None
        self.input_right = None

        self.output_left = None
        self.output_right = None

        self._input_priority = input_priority
        self._output_priority = output_priority

    @property
    def input_priority(self):
        return self._input_priority or getattr(
            self.entity, 'input_priority', None)

    @property
    def output_priority(self):
        return self._output_priority or getattr(
            self.entity, 'output_priority', None)

    def get_inputs(self):
        inputs = [self.input_left, self.input_right]
        return [input for input in inputs if input]

    def get_outputs(self):
        outputs = [self.output_left, self.output_right]
        return [output for output in outputs if output]

    def get_available_inputs(self):
        inputs = [self.input_left, self.input_right]
        if self.input_priority == self.Priority.left.value:
            if self.input_left and self.input_left.content > 0:
                inputs = [self.input_left]
        elif self.input_priority == self.Priority.right.value:
            if self.input_right and self.input_right.content > 0:
                inputs = [self.input_right]
        inputs = [input for input in inputs
                  if input and input.content > 0]
        return inputs

    def get_available_outputs(self):
        outputs = [self.output_left, self.output_right]
        if self.output_priority == self.Priority.left.value:
            if self.output_left and self.output_left.available > 0:
                outputs = [self.output_left]
        elif self.output_priority == self.Priority.right.value:
            if self.output_right and self.output_right.available > 0:
                outputs = [self.output_right]
        outputs = [output for output in outputs
                   if output and output.available > 0]
        return outputs

    def balance(self):
        inputs = self.get_available_inputs()
        outputs = self.get_available_outputs()
        while inputs and outputs:
            available_space = min(
                [output.available for output in outputs]) * len(outputs)
            available_content = min(
                [input.content for input in inputs]) * len(inputs)
            if available_content > available_space:
                amount = available_space
            else:
                amount = available_content
            for input in inputs:
                input.content -= amount / len(inputs)
            for output in outputs:
                output.content += amount / len(outputs)
            inputs = self.get_available_inputs()
            outputs = self.get_available_outputs()

    @property
    def percentage(self):
        inputs = self.get_inputs()
        total = sum([input.available for input in inputs])
        return total / len(inputs)

    def make_networkx_graph(self, g, parent_name, node_colors, edge_colors):
        outputs = self.get_outputs()
        node_name = f'{self.uid}'
        if parent_name:
            edge_colors[(parent_name, node_name)] = self.percentage / 100.0
            g.add_edges_from([(parent_name, node_name)])
        for belt in outputs:
            if belt.next:
                belt.next.node.make_networkx_graph(
                    g, node_name, node_colors, edge_colors)
            elif belt in self.entity.blueprint._output_belts:
                for i, output in enumerate(self.entity.blueprint._output_belts):
                    if belt == output:
                        edge_colors[(node_name, f'output {i}')] = self.percentage / 100.0
                        g.add_edges_from([(node_name, f'output {i}')])
                        break
