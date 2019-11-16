

class Splitter():
    def __init__(self, entity=None, lane_balance_side=None):
        self.entity = entity
        if self.entity is not None:
            self.entity._simulator = self

        self._lane_balance_side = lane_balance_side

        self._input_left = None
        self._input_right = None
        self._input_priority = None

        self._output_left = None
        self._output_right = None
        self._output_priority = None

    def __repr__(self):
        return "<Splitter ({entity}, inputs=({in_left}, {in_right}), outputs=({out_left}, {out_right}))>".format(
            entity=self.entity,
            in_left=str(self._input_left),
            in_right=str(self._input_right),
            out_left=str(self._output_left),
            out_right=str(self._output_right)
        )

    def __str__(self):
        return "<Splitter ({entity})>".format(entity=self.entity.name)

    def _get_inputs(self, empty=True):
        inputs = []
        if self._input_left is not None:
            if self._input_left.out > 0 or empty:
                inputs.append(self._input_left)
        if self._input_right is not None:
            if self._input_right.out > 0 or empty:
                inputs.append(self._input_right)
        return inputs

    inputs = property(_get_inputs)

    def _get_outputs(self, full=True):
        outputs = []
        if self._output_left is not None:
            if self._output_left.inp < self._output_left.size or full:
                outputs.append(self._output_left)
        if self._output_right is not None:
            if self._output_right.inp < self._output_right.size or full:
                outputs.append(self._output_right)
        return outputs

    outputs = property(_get_outputs)

    def set_input_priority(self, side=None):
        if side is not None and side != 'left' and side != 'right':
            raise ValueError("Invalid side supplied: {}".format(side))
        self._input_priority = side

    def set_output_priority(self, side=None):
        if side != "left" and side != "right":
            side = None
        self._output_priority = side

    def add_input(self, belt, side=None, priority=False):
        if side is not None and side != 'left' and side != 'right':
            raise ValueError("Invalid side supplied: {}".format(side))
        if side is None:
            if self._input_left is None:
                side = "left"
            elif self._input_right is None:
                side = "right"

        if side == "left":
            if self._input_left is not None:
                print("Side already connected")
                return
            self._input_left = belt
            if priority:
                self._input_priority = "left"
        elif side == "right":
            if self._input_right is not None:
                print("Side already connected")
                return
            self._input_right = belt
            if priority:
                self._input_priority = "right"

    def add_output(self, belt, side=None, priority=False):
        if side is not None and side != 'left' and side != 'right':
            raise ValueError("Invalid side supplied: {}".format(side))
        if side is None:
            if self._output_left is None:
                side = "left"
            elif self._output_right is None:
                side = "right"

        if side == "left":
            if self._output_left is not None:
                print("Side already connected")
                return
            self._output_left = belt
            if priority:
                self._output_priority = "left"
        elif side == "right":
            if self._output_right is not None:
                print("Side already connected")
                return
            self._output_right = belt
            if priority:
                self._output_priority = "right"

    def split(self):
        inputs = self._get_inputs(empty=False)
        outputs = self._get_outputs(full=False)
        input_priority = self._input_priority is not None
        output_priority = self._output_priority is not None
        while inputs and outputs:
            moving_total = 0
            rest = 0
            if self._input_priority == "left":
                moving_total, _ = self._input_left.drain()
            elif self._input_priority == "right":
                moving_total, _ = self._input_right.drain()
            if moving_total == 0:
                smallest = min(inputs, key=lambda belt: belt.out).out
                input_priority = False

                for belt in inputs:
                    belt.out -= smallest
                    moving_total += smallest

            if output_priority:
                if self._output_priority == "left":
                    rest = self._output_left.add(moving_total)
                elif self._output_priority == "right":
                    rest = self._output_right.add(moving_total)
                if rest == moving_total:
                    output_priority = False
                moving_total = rest

            feed = moving_total / len(outputs)
            for belt in outputs:
                rest += belt.add(feed)
            if rest > 0:
                if input_priority:
                    if self._input_priority == "left":
                        rest = self._input_left.add(rest)
                    elif self._input_priority == "right":
                        rest = self._input_right.add(rest)
                feedback = rest / len(inputs)
                for belt in inputs:
                    belt.out += feedback

            inputs = [belt for belt in inputs if belt.out > 0]
            outputs = [belt for belt in outputs if belt.inp < belt.size]
