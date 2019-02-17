from itertools import combinations
from factorio_balancers.blueprints import Blueprint, InvalidExchangeStringException
from factorio_balancers.blueprinttogrid import Grid_splitter, Blueprintgrid
from progress.bar import Bar
from fractions import Fraction
from operator import mul
from functools import reduce


def isclose(a, b, rel_tol=1e-06, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def boolean_permutations(number, length):
    for inputs in combinations(range(length), number):
        result = [False] * length
        for i in inputs:
            result[i] = True
        yield result


def nCk(n, k):
    return int(reduce(mul, (Fraction(n - i, i + 1) for i in range(k)), 1))


def nr_of_permutations(nr_inputs, nr_outputs, max_nr):
    perms = 0
    if nr_inputs < max_nr:
        max_nr = nr_inputs
    if nr_outputs < max_nr:
        max_nr = nr_outputs
    for i in range(1, max_nr + 1):
        perms += nCk(nr_inputs, i) * nCk(nr_outputs, i)
    return perms


class MyBar(Bar):
    def finish(self, clear=True):
        if clear:
            self.clearln()
            print('\x1b[?25h', end='')
        else:
            super().finish()


class Belt():
    def __init__(self, size=100, inp=None, out=None):
        self.size = size
        self.inp_splitter = inp
        self.out_splitter = out
        self.inp = 0
        self.out = 0

    def set_input_splitter(self, splitter):
        self.inp_splitter = splitter

    def set_output_splitter(self, splitter):
        self.out_splitter = splitter

    def add(self, amount):
        if self.inp + amount > self.size:
            rest = self.inp + amount - self.size
            self.inp = self.size
            return rest
        else:
            self.inp += amount
            return 0

    def provide(self, amount=None):
        if amount is None or amount > self.size:
            amount = self.size
        self.inp = amount
        return amount

    def fill(self):
        self.inp = self.size
        self.out = self.size

    def clear(self):
        self.inp = 0
        self.out = 0

    def drain(self):
        amount = self.out
        self.out = 0
        percentage = (amount / self.size) * 100
        return amount, percentage

    def transfer(self):
        output = self.inp + self.out
        if output > self.size:
            self.out = self.size
            self.inp = output - self.size
        else:
            self.out = output
            self.inp = 0


class Splitter():
    def __init__(self, inputs=[], outputs=[], position=(0, 0)):
        self._input_left = None
        self._input_right = None
        self._input_priority = None
        self._num_inputs = None

        self._output_left = None
        self._output_right = None
        self._output_priority = None
        self._num_outputs = 0
        self.position = position

    def add_output(self, belt, side=None, priority=False):
        if side is not None and side != 'left' and side != 'right':
            print("Invalid side of splitter")
            return
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

        belt.set_input_splitter(self)

    def set_input_priority(self, side=None):
        if side != "left" and side != "right":
            side = None
        self._input_priority = side

    def set_output_priority(self, side=None):
        if side != "left" and side != "right":
            side = None
        self._output_priority = side

    def add_input(self, belt, side=None, priority=False):
        if side is not None and side != 'left' and side != 'right':
            print("Invalid side of splitter")
            return
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

        belt.set_output_splitter(self)

    def get_inputs(self, empty=True):
        inputs = []
        if self._input_left is not None:
            if self._input_left.out > 0 or empty:
                inputs.append(self._input_left)
        if self._input_right is not None:
            if self._input_right.out > 0 or empty:
                inputs.append(self._input_right)
        return inputs

    inputs = property(get_inputs)

    def get_outputs(self, full=True):
        outputs = []
        if self._output_left is not None:
            if self._output_left.inp < self._output_left.size or full:
                outputs.append(self._output_left)
        if self._output_right is not None:
            if self._output_right.inp < self._output_right.size or full:
                outputs.append(self._output_right)
        return outputs

    outputs = property(get_outputs)

    @staticmethod
    def get_smallest_input(available_inputs):
        smallest_amount = float('inf')
        for belt in available_inputs:
            if belt.out < smallest_amount:
                smallest_amount = belt.out
        return smallest_amount

    def split(self):
        inputs = self.get_inputs(empty=False)
        outputs = self.get_outputs(full=False)
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

    def old_split(self):
        available_outputs = []
        available_inputs = []
        for belt in self.outputs:
            if belt.inp < belt.size:
                available_outputs += [belt]
        for belt in self.inputs:
            if belt.out > 0:
                available_inputs += [belt]

        while available_outputs and available_inputs:
            smallest = Splitter.get_smallest_input(available_inputs)
            moving_total = 0
            rest = 0
            for belt in available_inputs:
                belt.out -= smallest
                moving_total += smallest

            feed = moving_total / len(available_outputs)
            for belt in available_outputs:
                rest += belt.add(feed)
            if rest > 0:
                feedback = rest / len(available_inputs)
                for belt in available_inputs:
                    belt.out += feedback

            available_inputs = [belt for belt in available_inputs
                                if belt.out > 0]
            available_outputs = [belt for belt in available_outputs
                                 if belt.inp < belt.size]

    def print_splitter(self):
        text = "\nSplitter:" + str(self) + "\ninputs: "
        for belt in self.inputs:
            text += str(belt.out) + " "
        print(text)
        text = "outputs: "
        for belt in self.outputs:
            text += str(belt) + ": " + str(belt.inp) + " "
        print(text + "\n")


class Balancer():
    def __init__(self):
        self.splitters = []
        self.belts = []
        self.inputs = []
        self.outputs = []

    @property
    def nr_inputs(self):
        return len(self.inputs)

    @property
    def nr_outputs(self):
        return len(self.outputs)

    @staticmethod
    def valid_string(string):
        try:
            blueprint = Blueprint.from_exchange_string(string)
        except InvalidExchangeStringException:
            return False
        return blueprint.is_filtered(
            whitelist=['belt', 'splitter', 'underground-belt'])

    @staticmethod
    def valid_blueprint(blueprint):
        return blueprint.is_filtered(
            whitelist=['belt', 'splitter', 'underground-belt'])

    @classmethod
    def from_exchange_string(cls, string, print_result=False):
        try:
            blueprint = Blueprint.from_exchange_string(string)
        except InvalidExchangeStringException:
            if print_result:
                print("Not a valid exchange string")
            raise InvalidExchangeStringException

        if Balancer.valid_blueprint(blueprint):
            if print_result:
                print("This is a valid blueprint for a potential balancer.\n")
        else:
            if print_result:
                print("This blueprint is not valid")
            raise InvalidExchangeStringException

        balancer = cls.from_blueprint(blueprint, print_result=print_result)
        return balancer

    @classmethod
    def from_blueprint(cls, blueprint, print_result=False):
        balancer = cls()
        grid = Blueprintgrid.from_blueprint(blueprint)
        splitter_queue = []
        for splitter in grid.splitters:
            splitter.set_splitter(balancer.add_splitter())
            splitter_queue.append(splitter)

        while splitter_queue:
            splitter = splitter_queue.pop()

            if len(splitter.outputs) == 0:
                # print("no outputs")
                balancer.add_output(splitter.splitter)
                balancer.add_output(splitter.splitter)
            else:
                # print("at least one output: ", splitter.outputs)
                for output in splitter.outputs:
                    targets = output.trace_belt(forward=True)
                    if len(targets) > 1:
                        raise RuntimeError("Multiple targets should not be possible")
                    elif isinstance(targets[0], Grid_splitter):
                        if targets[0] in splitter_queue:
                            balancer.connect_splitters(splitter.splitter,
                                                       targets[0].splitter)
                    else:
                        balancer.add_output(splitter.splitter)

                    # print(targets, len(targets))
            if len(splitter.inputs) == 0:
                # print("no inputs")
                balancer.add_input(splitter.splitter)
                balancer.add_input(splitter.splitter)
            else:
                for input in splitter.inputs:
                    targets = input.trace_belt(forward=False)
                    # print(splitter.position)
                    # print("postition: ", splitter.position[0].x, splitter.position[0].y, "self: ", splitter, "targets:", targets)
                    if len(targets) > 1:
                        raise RuntimeError("Sideloading is currently not supported")
                    elif isinstance(targets[0], Grid_splitter):
                        if targets[0] in splitter_queue:
                            balancer.connect_splitters(targets[0].splitter, splitter.splitter)
                    else:
                        balancer.add_input(splitter.splitter)

        if print_result:
            grid.print_blueprint_grid()
        return balancer

    def connect_splitters(self, splitter1, splitter2, input_priority=False, output_priority=False):
        belt = Belt()
        self.belts.append(belt)
        splitter1.add_output(belt, priority=output_priority)
        splitter2.add_input(belt, priority=input_priority)

    def add_splitter(self, position=(0, 0)):
        splitter = Splitter(position=position)
        self.splitters.append(splitter)
        return splitter

    def add_input(self, splitter):
        belt = Belt()
        splitter.add_input(belt)
        self.belts.append(belt)
        self.inputs.append(belt)

    def add_output(self, splitter):
        belt = Belt()
        splitter.add_output(belt)
        self.belts.append(belt)
        self.outputs.append(belt)

    def estimate_iterations(self):
        return (len(self.splitters) * 2 + len(self.inputs) + len(self.outputs) + 1) * 4

    def provide(self, inputs=None):
        total = 0
        if inputs is None:
            inputs = [True] * len(self.inputs)
        elif len(self.inputs) != len(self.inputs):
            # print("Number of inputs doesn't match")
            return
        for i in range(len(self.inputs)):
            if inputs[i]:
                total += self.inputs[i].provide()
        return total

    def drain(self, outputs=None):
        if outputs is None:
            outputs = [True] * len(self.outputs)
        elif len(outputs) != len(self.outputs):
            # print("Number of outputs doesn't match")
            return
        output = [0] * len(self.outputs)
        for i in range(len(self.outputs)):
            if outputs[i]:
                output[i] = self.outputs[i].drain()
            else:
                output[i] = (None, None)
        return output

    def iterate(self):
        for splitter in self.splitters:
            splitter.split()
        for belt in self.belts:
            belt.transfer()

    def print_splitters(self):
        for splitter in self.splitters:
            splitter.print_splitter()

    def clear(self):
        for belt in self.belts:
            belt.clear()

    def fill(self):
        for belt in self.belts:
            belt.fill()

    def test_output_balance(self, iterations=0, verbose=False):
        if iterations == 0:
            iterations = self.estimate_iterations()
        if verbose:
            bar = MyBar('   -- Progress', max=len(self.inputs) + 1, suffix='%(percent)d%%')
        for i in range(len(self.inputs)):
            self.clear()
            inputs = [False] * len(self.inputs)
            inputs[i] = True

            for i in range(iterations):
                self.drain()
                self.provide(inputs)
                self.iterate()
            result = self.drain()
            for amount, _ in result[1:]:
                if not isclose(result[0][0], amount):
                    if verbose:
                        bar.finish()
                    return False
            if verbose:
                bar.next()
        self.clear()
        for i in range(iterations):
            self.drain()
            self.provide()
            self.iterate()
        result = self.drain()
        for number, _ in result[1:]:
            if not isclose(result[0][0], number):
                if verbose:
                    bar.finish()
                return False
        if verbose:
            bar.finish()

        return True

    def test_input_balance(self, iterations=0, verbose=False):
        if iterations == 0:
            iterations = self.estimate_iterations()
        if verbose:
            bar = MyBar('   -- Progress', max=len(self.outputs) + 1, suffix='%(percent)d%%')
        for i in range(len(self.outputs)):
            self.fill()
            drain = [False] * len(self.outputs)
            drain[i] = True

            for i in range(iterations):
                self.provide()
                self.iterate()
                self.drain(drain)
            for belt in self.inputs[1:]:
                if not isclose(self.inputs[0].inp, belt.inp):
                    if verbose:
                        bar.finish()
                    return False
            if verbose:
                bar.next()
        self.fill()
        for i in range(iterations):
            self.provide()
            self.iterate()
            self.drain()
        for belt in self.inputs[1:]:
            if not isclose(self.inputs[0].inp, belt.inp):
                if verbose:
                    bar.finish()
                return False
        if verbose:
            bar.finish()
        return True

    def throughput_sweep(self, extensive=False, iterations=0, verbose=False):
        if iterations == 0:
            iterations = self.estimate_iterations()

        results = []
        if extensive:
            i_range = range(1, min(len(self.inputs), len(self.outputs)) + 1)
            if verbose:
                bar = MyBar('   -- Progress', max=nr_of_permutations(len(self.inputs), len(self.outputs), len(self.inputs)))
        else:
            i_range = range(1, 3)
            if verbose:
                bar = MyBar('   -- Progress', max=nr_of_permutations(len(self.inputs), len(self.outputs), 2))
        for i in i_range:
            for inputs in boolean_permutations(i, len(self.inputs)):
                for outputs in boolean_permutations(i, len(self.outputs)):
                    results.append(self.test_throughput(inputs, outputs))
                    if verbose:
                        bar.next()
        if verbose:
            bar.finish()
        return results

    def test_throughput(self, inputs=None, outputs=None, iterations=0, verbose=False):
        if iterations == 0:
            iterations = self.estimate_iterations()
        self.clear()
        if verbose:
            bar = MyBar('   -- Progress', max=iterations, suffix='%(percent)d%%')
        input_amount = self.provide(inputs)
        for i in range(iterations):
            self.provide(inputs)
            self.iterate()
            result = self.drain(outputs)
            if verbose:
                bar.next()
        worst_result = None
        output_amount = 0
        for number, percentage in result:
            if number is not None:
                output_amount += number
            if percentage is not None and not isclose(percentage, 100):
                if worst_result is None or percentage < worst_result:
                    worst_result = percentage
        if verbose:
            bar.finish()
        if isclose(input_amount, output_amount):
            return True
        if worst_result is not None:
            return worst_result
        return True

    def test(self, iterations=0, balance=True, throughput=True, sweep=False, extensive_sweep=False, verbose=False):
        self.clear()
        if verbose:
            print("Testing a %d - %d balancer." % (len(self.inputs), len(self.outputs)))

        results = {}

        if balance:
            if verbose:
                print("\n  Testing balance.")
            if self.test_output_balance(iterations=iterations, verbose=verbose):
                if verbose:
                    print("   -- Output is balanced.")
                results['output_balanced'] = True
            else:
                if verbose:
                    print("   -- Output is NOT balanced.")
                results['output_balanced'] = False

            if self.test_input_balance(iterations=iterations, verbose=verbose):
                if verbose:
                    print("   -- Input is balanced.")
                results['input_balanced'] = True
            else:
                if verbose:
                    print("   -- Input is NOT balanced.")
                results['input_balanced'] = False

        if throughput:
            temp_result = self.test_throughput(iterations=iterations, verbose=verbose)
            if verbose:
                print("\n  Testing regular throughput.")
            if temp_result is True:
                results['full_throughput'] = True
                if verbose:
                    print("   -- Full throughput on regular use")
            else:
                results['full_throughput'] = False
                results['full_throughput_bottleneck'] = temp_result
                if verbose:
                    print("   -- Limited throughput to %1.2f%% on regular use on at least one of the outputs." % results['regular_throughput_bottleneck'])

        if sweep or extensive_sweep:
            if extensive_sweep:
                if verbose:
                    print("\n  Extensive throughput sweep.")
            else:
                if verbose:
                    print("\n  Regular throughput sweep.")
            results["throughput_sweep"] = self.throughput_sweep(extensive=extensive_sweep, iterations=iterations, verbose=verbose)
            largest_bottleneck = None
            for throughput in results["throughput_sweep"]:
                if throughput is not True and (largest_bottleneck is None or throughput < largest_bottleneck):
                    largest_bottleneck = throughput
            if largest_bottleneck is None:
                if extensive_sweep:
                    results['throughput_unlimited'] = True
                else:
                    results['throughput_unlimited_candidate'] = True
                if sweep:
                    if verbose:
                        print("   -- No bottlenecks with any combinations of 1 or 2 inputs and outputs.")
                else:
                    if verbose:
                        print("   -- No bottlenecks with any combinations of any number of inputs and outputs.")
            else:
                if extensive_sweep:
                    results['throughput_unlimited'] = False
                else:
                    results['throughput_unlimited_candidate'] = False
                results["largest_bottleneck"] = largest_bottleneck
                if verbose:
                    print("   -- At least one bottleneck exists that limits throughput to %1.2f%%." % largest_bottleneck)
        if verbose:
            print("\n")
        return results

    @classmethod
    def debug(cls):
        balancer = cls()
        splitter1 = balancer.add_splitter()
        splitter2 = balancer.add_splitter()
        splitter3 = balancer.add_splitter()
        splitter4 = balancer.add_splitter()

        balancer.add_output(splitter1)
        balancer.add_output(splitter1)
        balancer.add_output(splitter2)

        balancer.connect_splitters(splitter2, splitter4)
        balancer.connect_splitters(splitter3, splitter1, input_priority=True)
        balancer.connect_splitters(splitter3, splitter2, input_priority=True)
        balancer.connect_splitters(splitter4, splitter1)
        balancer.connect_splitters(splitter4, splitter2)

        balancer.add_input(splitter3)
        balancer.add_input(splitter3)

        balancer.test(verbose=True, sweep=True)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Test a balancer configuration for its properties")
    parser.add_argument("-f", "--file", dest="filename", help="The file from which to read the blueprint string", metavar="FILE")
    parser.add_argument("-nb", "--nobalance", dest="balance", action='store_false', default=True, help="If for any reason you don't want to test the balance of the balancer")
    parser.add_argument("-i", "--iterations", dest="iterations", default=0, type=int, metavar="NR_ITERATIONS",
                        help="The number of iterations you want the simulation to run in each test. If not set, will use an estimation based on the balancer design")
    parser.add_argument("-s", "--sweep", dest="sweep", default=False, action='store_true', help="Performs a throughput test on all combinations where exactly 1 or 2 inputs and outputs are used")
    parser.add_argument("-es", "--extensivesweep", dest="extensive", default=False, action='store_true', help="Performs a throughput test on all combinations of the same number of inputs and outputs")
    parser.add_argument("--string", dest="string", default=False, help="The blueprint string to parse", metavar="STRING")
    parser.add_argument("--silent", dest="verbose", default=True, action='store_false', help="Tell the script not to write intermediate data to the screen.\nNote: this prints raw function results on exit that are very user-unfriendly.")
    parser.add_argument("--debug", dest="debug", default=False, action="store_true", help="Calls the debug function, used for debugging... duh...")

    args = parser.parse_args()

    if args.debug:
        if args.filename:
            file = open(args.filename, 'r')
            string = file.read()
            if args.verbose:
                print("The blueprint string: \n", string)

        Balancer.debug()
        exit()

    if not args.filename and not args.string:
        print("No file or string specified.")
        parser.parse_args(['-h'])

    if not args.string:
        if args.verbose:
            print("Reading blueprint string from ", args.filename)
        file = open(args.filename, 'r')
        string = file.read()
        if args.verbose:
            print("The blueprint string: \n", string)
    else:
        string = args.string

    if args.iterations > 0:
        print("Nr of iterations: ", args.iterations)

    try:
        balancer = Balancer.from_exchange_string(string, print_result=args.verbose)
    except InvalidExchangeStringException:
        print("Error - Either the string was formatted wrong, or the blueprint contained non-belt entities.")
        print("Exiting.")
        exit()

    results = balancer.test(balance=args.balance, sweep=args.sweep, extensive_sweep=args.extensive, iterations=args.iterations, verbose=args.verbose)
    if not args.verbose:
        print(results)
