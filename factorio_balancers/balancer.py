import os
from itertools import combinations
from progress.bar import Bar
from fractions import Fraction
from py_factorio_blueprints import Blueprint
from py_factorio_blueprints.util import Vector
from factorio_balancers.utils import catch, get_nr_of_permutations
from factorio_balancers.graph import Splitter, Belt
from factorio_balancers.entity_mixins import (
    entity_prototypes, Splitter as SplitterMixin,
    Belt as BeltMixin, Underground as UndergroundMixin)
from factorio_balancers.exceptions import *


class MyBar(Bar):
    def finish(self, clear=True):
        if clear:
            self.clearln()
            print('\x1b[?25h', end='')
        else:
            super().finish()


class OptionalBar:
    def __init__(self, *args, verbose, **kwargs):
        self.verbose = verbose
        if self.verbose:
            self.bar = MyBar(*args, **kwargs)

    def finish(self, *args, **kwargs):
        if self.verbose:
            self.bar.finish(*args, **kwargs)

    def next(self, *args, **kwargs):
        if self.verbose:
            self.bar.finish(*args, **kwargs)


def is_close(a, b, rel_tol=1e-06, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


class Balancer(Blueprint):
    def __init__(self, *args, verbose=False, **kwargs):
        Blueprint.import_prototype_data(
            f"{os.path.dirname(__file__)}/../entity_data.json")
        self._verbose = verbose
        super().__init__(
            *args, custom_entity_prototypes=entity_prototypes, **kwargs)

        self.recompile_entities()
        if self._verbose:
            print("Before padding")
            self.print2d()
        self.pad_connections()
        if self._verbose:
            print("After padding")
            self.print2d()
        inputs, outputs = self._get_external_connections()
        if self._verbose:
            print(f"Nr of inputs and outputs: {len(inputs)}, {len(outputs)}")
            print(f"Inputs: {inputs}")
            print(f"Outputs: {outputs}")

        nodes = self._get_nodes()
        if self._verbose:
            print(f"Number of nodes {len(nodes)}")
            print(f"Nodes {nodes}")

        for i, node in enumerate(nodes):
            node.node_number = i

        self.generate_simulation()

    def print2d(self):
        maxx, minx, maxy, miny = self.maximum_values
        width = maxx - minx + 1
        height = maxy - miny + 1
        offset = Vector(minx, miny)
        data = [[" " for _ in range(width)] for _ in range(height)]

        for entity in self.entities:
            for i, coord in enumerate(entity.coordinates):
                position = coord - offset
                x, y = position.round()
                data[y][x] = entity.name.data['ascii'][entity.direction // 2][i]
        print()
        for line in data:
            r = ""
            for char in line:
                r += char
            print(r)
        print()

    def _get_nodes(self):
        return [
            entity
            for entity in self.entities
            if isinstance(entity, SplitterMixin) or entity.has_sideloads]

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

        if self._verbose:
            print(f"Inputs: {self._input_belts}")
            print(f"Outputs: {self._output_belts}")
            print(f"Splitters: {self._splitters}")
        for entity in self._get_nodes():
            if not entity._traversed:
                raise IllegalConfiguration(
                    message="The balancer is not fully connected")

    def cycle(self):
        for splitter in self._splitters:
            splitter.balance()
        for belt in self._belts:
            belt.transfer()

    def clear(self):
        total = 0
        for belt in self._belts:
            total += belt.clear()
            if belt.next:
                total += belt.next.clear()
        return total

    def fill(self):
        total = 0
        for belt in self._belts:
            total += belt.supply()
            if belt.next:
                total += belt.next.supply()
        return total

    def supply(self, *args, **kwargs):
        return [
            belt.supply(*args, **kwargs)
            for belt in self._input_belts]

    def drain(self, **kwargs):
        return [
            belt.clear(**kwargs)
            for belt in self._output_belts]

    def recompile_entities(self):
        for entity in self.entities:
            entity.reset()
        exceptions = self.setup_transport_lines()
        nr_exceptions = len(exceptions)
        if nr_exceptions > 0:
            if self._verbose:
                self.print2d()
            raise IllegalConfigurations(*exceptions)

        self.has_sideloads = self._has_sideloads()

    def _get_external_connections(self):
        inputs = []
        outputs = []
        inputs = [entity
                  for entity in self.entities
                  if entity.has_no_inputs and entity.input_belt_check()]
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

        self.pad_entities(inputs, inp=True)
        self.pad_entities(outputs, out=True)

    def pad_entities(self, entities, **kwargs):
        for entity in entities:
            if isinstance(entity, SplitterMixin):
                break
        else:
            return
        for entity in entities:
            entity.pad_connection(**kwargs)

    def setup_transport_lines(self):
        exceptions = []
        for entity in self.entities:
            e = catch(entity.setup_transport_lines,
                      exceptions=IllegalConfiguration)
            if e is not None and e not in exceptions:
                exceptions.append(e)
        return exceptions

    def _has_sideloads(self):
        for entity in self.entities:
            if entity.has_sideloads:
                return True
        return False

    def _parse_balancer(self):
        for entity in self._get_nodes():
            splitter = Splitter(entity=entity)
            self._splitters.append(splitter)
        inputs, outputs = self._get_external_connections()
        self._input_belts = []
        self._output_belts = []
        for input in inputs:
            assert isinstance(input, (BeltMixin, UndergroundMixin))
            belt = input._trace_nodes(
                Belt(capacity=input.name.data['belt_speed']),
                input.position)
            assert len(outputs) == len(self._output_belts)
            self._input_belts.append(belt)

    def _parse_lane_balancer(self):
        raise RuntimeError("Lane balancers are currently not supported")
        for entity in self._get_nodes():
            if isinstance(entity, SplitterMixin):
                splitter_left = Splitter(entity=entity, lane_side='left')
                splitter_right = Splitter(entity=entity, lane_side='right')
            elif isinstance(entity, BeltMixin):
                pass
            elif isinstance(entity, UndergroundMixin):
                pass
            else:
                raise Exception('what')

    def graph_check(self):
        """
        Recursively traverse all the nodes from a single input, going both
        forward and backwards through the graph.
        Checks whether all nodes have been traversed. If not, this means the
        graph is not fully connected.
        """
        if self._verbose:
            print("All nodes:")
        for node in self._get_nodes():
            print(f"    {node}")
            node._traversed = False

        start_node = self._inputs[0]
        if self._verbose:
            print(f"start node: {start_node}")

        self._traverse_node(start_node)
        for node in self.nodes:
            if not node._traversed:
                return False
        return True

    def _traverse_node(self, node):
        if self._verbose:
            print(f"traversing node: {node}")
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

    def test_output_balance(self, verbose=False, trickle=False, **kwargs):
        bar = OptionalBar(
            '   -- Progress',
            verbose=verbose,
            max=len(self._input_belts) + 1,
            suffix='%(percent)d%%')

        amount = Fraction(1, 4) if trickle else None
        for input in self._input_belts:
            self.clear()
            drained = self.drain()
            supplied = input.supply(amount)
            while not is_close(sum(drained), supplied):
                self.cycle()
                drained = self.drain()
                supplied = input.supply(amount)

            if len(set(drained)) > 1:
                bar.finish()
                return False
            bar.next()

        self.clear()
        drained = self.drain()
        supplied = self.supply(amount)
        while not is_close(sum(drained), sum(supplied)):
            self.cycle()
            drained = self.drain()
            supplied = self.supply(amount)
        bar.finish()
        if len(set(drained)) > 1:
            return False
        return True

    def test_input_balance(self, verbose=False, trickle=False, **kwargs):
        bar = OptionalBar(
            '   -- Progress',
            verbose=verbose,
            max=len(self._output_belts) + 1,
            suffix='%(percent)d%%')

        amount = Fraction(1, 4) if trickle else None
        for output in self._output_belts:
            self.fill()
            drained = output.clear(amount)
            supplied = self.supply()
            while not is_close(drained, sum(supplied)):
                self.cycle()
                drained = output.clear(amount)
                supplied = self.supply()

            if len(set(supplied)) > 1:
                bar.finish()
                return False
            bar.next()

        self.fill()
        drained = self.drain(amount=amount)
        supplied = self.supply()
        while not is_close(sum(drained), sum(supplied)):
            self.cycle()
            drained = self.drain(amount=amount)
            supplied = self.supply()
        bar.finish()
        if len(set(supplied)) > 1:
            return False
        return True

    def test_throughput(
            self, inputs=None, outputs=None, verbose=False, **kwargs):
        if inputs is None:
            inputs = self._input_belts
        if outputs is None:
            outputs = self._output_belts

        def drain(a):
            return [b.clear() for b in a]

        def supply(a):
            return [b.supply() for b in a]

        self.clear()
        drained = drain(outputs)
        supplied = supply(inputs)
        clean_input = supplied
        while not is_close(sum(drained), sum(supplied)):
            drained = drain(outputs)
            self.cycle()
            supplied = supply(inputs)

        worst_percentage = 100.0
        for output in outputs:
            percentage = output.percentage
            if not is_close(worst_percentage, percentage) and \
                    percentage < worst_percentage:
                worst_percentage = percentage
        drained = drain(outputs)

        if is_close(sum(clean_input), sum(drained)):
            return True, worst_percentage
        if worst_percentage < 100.0:
            return False, worst_percentage
        return True, worst_percentage

    def throughput_sweep(self, extensive=False, verbose=False, **kwargs):
        if extensive:
            i_range = range(
                1,
                min(
                    len(self._input_belts),
                    len(self._output_belts)))
            nr_of_permutations = get_nr_of_permutations(
                len(self._input_belts),
                len(self._output_belts),
                len(self._input_belts))
        else:
            i_range = range(1, 3)
            nr_of_permutations = get_nr_of_permutations(
                len(self._input_belts),
                len(self._output_belts),
                2)
        bar = OptionalBar(
            '   -- Progress', verbose=verbose, max=nr_of_permutations)

        results = []

        for i in i_range:
            for inputs in combinations(self._input_belts, i):
                for outputs in combinations(self._output_belts, i):
                    results.append(
                        self.test_throughput(inputs=inputs, outputs=outputs))
                    bar.next()
        bar.finish()
        return results

    def test_throughput_unlimited(self, **kwargs):
        results = self.throughput_sweep(**kwargs)
        limited = False
        worst = 100.0
        for unlimited, percentage in results:
            if not unlimited:
                limited = True
                if not is_close(worst, percentage) and \
                        percentage < worst:
                    worst = percentage

        return not limited, worst

    def test(self, balance=True, throughput=True, trickle=False,
             sweep=False, extensive_sweep=False, verbose=False):
        self.clear()
        if verbose:
            print(f"Testing a {len(self._input_belts)} - "
                  f"{len(self._output_belts)} balancer.")

        results = {}

        if balance:
            if verbose:
                print("\n  Testing balance.")
            output_balanced = self.test_output_balance(verbose=verbose)
            results['output_balanced'] = output_balanced
            if verbose:
                print(f"   -- Output is {'' if output_balanced else 'NOT '}"
                      f"balanced.")

            input_balanced = self.test_input_balance(verbose=verbose)
            results['input_balanced'] = input_balanced
            if verbose:
                print(f"   -- Input is {'' if input_balanced else 'NOT '}"
                      f"balanced.")
        if trickle:
            if verbose:
                print("\n  Testing balance using trickle.")
            output_balanced = self.test_output_balance(
                verbose=verbose, trickle=True)
            results['output_balanced_trickle'] = output_balanced
            if verbose:
                print(f"   -- Output is {'' if output_balanced else 'NOT '}"
                      f"balanced with a trickle.")
            input_balanced = self.test_input_balance(
                verbose=verbose, trickle=True)
            results['input_balanced_trickle'] = input_balanced
            if verbose:
                print(f"   -- Input is {'' if input_balanced else 'NOT '}"
                      f"balanced with a trickle.")

        if throughput:
            full_throughput, worst = self.test_throughput(verbose=verbose)
            if verbose:
                print("\n  Testing regular throughput.")
            results['full_throughput'] = full_throughput
            if full_throughput:
                if verbose:
                    print("   -- Full throughput on regular use")
            else:
                results['full_throughput_bottleneck'] = worst
                if verbose:
                    print(f"   -- Limited throughput to {worst} on "
                          f"regular use on at least one of the outputs.")

        if sweep or extensive_sweep:
            if verbose:
                print(f"\n  {'Extensive' if extensive_sweep else 'Regular'} "
                      f"throughput sweep")
            unlimited, worst = self.test_throughput_unlimited(
                extensive=extensive_sweep, verbose=verbose)
            if not unlimited:
                print(f"   -- At least one bottleneck exists that "
                      f"limits throughput to {worst}%.")
                results['largest_bottleneck'] = worst
            else:
                print(f"   -- No bottlenecks with any combinations of"
                      f" {'any number of' if extensive_sweep else '1 or 2'} "
                      f"any number of inputs and outputs.")

            if extensive_sweep:
                results['throughput_unlimited'] = unlimited
            else:
                results['throughput_unlimited_candidate'] = unlimited

        if verbose:
            print("\n")
        return results
