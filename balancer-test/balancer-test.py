from itertools import combinations
from blueprints import Blueprint
from blueprinttograph import *
import math


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def boolean_permutations(number, length):
    for inputs in combinations(range(length), number):
        result = [False] * length
        for i in inputs:
            result[i] = True
        yield result


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
    def __init__(self, inputs=[], outputs=[], position=(0,0)):
        self.inputs = []
        self.outputs = []
        self.position = position

    def add_output(self, belt):
        self.outputs.append(belt)
        belt.set_input_splitter(self)

    def add_input(self, belt):
        self.inputs.append(belt)
        belt.set_output_splitter(self)

    @staticmethod
    def get_smallest_input(available_inputs):
        smallest_amount = float('inf')
        for belt in available_inputs:
            if belt.out < smallest_amount:
                smallest_amount = belt.out
        return smallest_amount

    def split(self):
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

            available_inputs = [belt for belt in available_inputs if belt.out > 0]
            available_outputs = [belt for belt in available_outputs if belt.inp < belt.size]

    def print_splitter(self):
        text = "\nSplitter:" + str(self) + "\ninputs: "
        for belt in self.inputs:
            text += str(belt.out) + " "
        print(text)
        text = "outputs: "
        for belt in self.outputs:
            text += str(belt) + ": " +  str(belt.inp) + " "
        print(text + "\n")



class Balancer():
    def __init__(self):
        self.splitters = []
        self.belts = []
        self.inputs = []
        self.outputs = []

    @classmethod
    def from_blueprint(cls, blueprint):
        balancer = cls()
        graph = Blueprintgraph.from_blueprint(blueprint)
        splitter_queue = []
        for splitter in graph.splitters:
            splitter.set_splitter(balancer.add_splitter())
            splitter_queue.append(splitter)

        while splitter_queue:
            splitter = splitter_queue.pop()

            if len(splitter.outputs) == 0:
                print("no outputs")
                balancer.add_output(splitter.splitter)
                balancer.add_output(splitter.splitter)
            else:
                print("at least one output: ", splitter.outputs)
                for output in splitter.outputs:
                    targets = output.trace_belt(forward=True)
                    if len(targets) > 1:
                        raise RuntimeError("Multiple targets should not be possible")
                    elif isinstance(targets[0], Grid_splitter):
                        if targets[0] in splitter_queue:
                            balancer.connect_splitters(splitter.splitter, targets[0].splitter)
                    else:
                        balancer.add_output(splitter.splitter)

                    print(targets, len(targets))
            if len(splitter.inputs) == 0:
                print("no inputs")
                balancer.add_input(splitter.splitter)
                balancer.add_input(splitter.splitter)
            else:
                for input in splitter.inputs:
                    targets = input.trace_belt(forward=False)
                    #print(splitter.position)
                    #print("postition: ", splitter.position[0].x, splitter.position[0].y, "self: ", splitter, "targets:", targets)
                    if len(targets) > 1:
                        raise RuntimeError("Sideloading is currently not supported")
                    elif isinstance(targets[0], Grid_splitter):
                        if targets[0] in splitter_queue:
                            balancer.connect_splitters(targets[0].splitter, splitter.splitter)
                    else:
                        balancer.add_input(splitter.splitter)


        graph.print_blueprint_graph()

        return balancer

    def connect_splitters(self, splitter1, splitter2):
        belt = Belt()
        self.belts.append(belt)
        splitter1.add_output(belt)
        splitter2.add_input(belt)

    def add_splitter(self, position=(0,0)):
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
        return (len(self.splitters)*2 + len(self.inputs) + len(self.outputs) + 1) * 4

    def provide(self, inputs=None):
        if inputs is None:
            inputs = [True] * len(self.inputs)
        elif len(self.inputs) != len(self.inputs):
            print("Number of inputs doesn't match")
            return
        for i in range(len(self.inputs)):
            if inputs[i]:
                self.inputs[i].provide()

    def drain(self, outputs=None):
        if outputs is None:
            outputs = [True] * len(self.outputs)
        elif len(outputs) != len(self.outputs):
            print("Number of outputs doesn't match")
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

    def test_output_balance(self, iterations=0):
        if iterations == 0:
            iterations = self.estimate_iterations()
        for i in range(len(self.inputs)):
            self.clear()
            inputs = [False] * len(self.inputs)
            inputs[i] = True

            for i in range(iterations):
                balancer.drain()
                balancer.provide(inputs)
                balancer.iterate()
            result = balancer.drain()
            for amount, _ in result[1:]:
                if not isclose(result[0][0], amount):
                    return False
        self.clear()
        for i in range(iterations):
            balancer.drain()
            balancer.provide()
            balancer.iterate()
        result = balancer.drain()
        for number, _ in result[1:]:
            if not isclose(result[0][0], number):
                return False

        return True

    def test_input_balance(self, iterations=0):
        if iterations == 0:
            iterations = self.estimate_iterations()
        for i in range(len(self.outputs)):
            self.fill()
            drain = [False] * len(self.outputs)
            drain[i] = True

            for i in range(iterations):
                balancer.provide()
                balancer.iterate()
                balancer.drain(drain)
            for belt in self.inputs[1:]:
                if not isclose(self.inputs[0].inp, belt.inp):
                    return False
        self.fill()
        for i in range(iterations):
            balancer.provide()
            balancer.iterate()
            balancer.drain()
        for belt in self.inputs[1:]:
            if not isclose(self.inputs[0].inp, belt.inp):
                return False
        return True

    def throughput_sweep(self, extensive=False, iterations=0):
        if iterations == 0:
            iterations = self.estimate_iterations()
        if len(self.inputs) < 2 or len(self.outputs) < 2:
            print("Input or output is only 1 belt. Throughput sweep not possible")
            return False

        results = []
        if not extensive:
            for inputs in boolean_permutations(2, len(self.inputs)):
                for outputs in boolean_permutations(2, len(self.outputs)):
                    results.append(self.test_throughput(inputs, outputs))

        else:
            for i in range(1, len(self.inputs)):
                if i > len(self.outputs):
                    break
                for inputs in boolean_permutations(i, len(self.inputs)):
                    for outputs in boolean_permutations(i, len(self.outputs)):
                        results.append(self.test_throughput(inputs, outputs))

        return results

    def test_throughput(self, inputs=None, outputs=None, iterations=0):
        if iterations == 0:
            iterations = self.estimate_iterations()
        self.clear()
        for i in range(iterations):
            balancer.provide(inputs)
            balancer.iterate()
            result = balancer.drain(outputs)
        worst_result = None
        for number, percentage in result:
            if percentage is not None and not isclose(percentage, 100):
                if worst_result is None or percentage < worst_result:
                    worst_result = percentage
        if worst_result is not None:
            return worst_result
        return True


    def test(self, iterations=0, balance=True, throughput=True, sweep=False, extensive_sweep=False):
        self.clear()
        print("Testing a %d - %d balancer." % (len(self.inputs), len(self.outputs)))

        output_balanced = None
        input_balanced = None
        full_throughput = None
        full_sweep = None

        if balance:
            print("\n  Testing balance.")
            if self.test_output_balance(iterations=iterations):
                print("   -- Output is balanced.")
                output_balanced = True
            else:
                print("   -- Output is NOT balanced.")
                output_balanced = False

            if self.test_input_balance(iterations=iterations):
                print("   -- Input is balanced.")
                input_balanced = True
            else:
                print("   -- Input is NOT balanced.")
                input_balanced = False

        if throughput:
            full_throughput = self.test_throughput(iterations=iterations)
            print("\n  Testing regular throughput.")
            if full_throughput is True:
                print("   -- Full throughput on regular use")
            else:
                print("   -- Limited throughput to %1.2f%% on regular use on at least one of the outputs." % full_throughput)

        if sweep or extensive_sweep:
            print("\n  Extensive throughput test.")
            full_sweep = self.throughput_sweep(extensive=extensive_sweep, iterations=iterations)
            largest_bottleneck = None
            for throughput in full_sweep:
                if throughput is not True and (largest_bottleneck is None or throughput < largest_bottleneck):
                    largest_bottleneck = throughput
            if largest_bottleneck is None:
                if sweep:
                    print("   -- No bottlenecks with any combinations of 1 or 2 inputs and outputs.")
                else:
                    print("   -- No bottlenecks with any combinations of any number of inputs and outputs.")
            else:
                print("   -- At least one bottleneck exists that limits throughput to %1.2f%%." % largest_bottleneck)


        print("\n")
        return output_balanced, input_balanced, full_throughput, full_sweep


def test_function(balancer):

    # print("testing splitters")


    # splitter1 = balancer.add_splitter()
    # splitter2 = balancer.add_splitter()
    # balancer.add_input(splitter1)

    # print("splitter 1: ", splitter1, "splitter 2: ", splitter2)
    # print(balancer.splitters, balancer.inputs)
    # balancer.add_output(splitter1)
    # balancer.add_output(splitter2)
    # balancer.add_output(splitter2)
    # balancer.connect_splitters(splitter1, splitter2)
    # print(balancer.outputs)
    # for splitter in balancer.splitters:
    #     print(splitter.inputs)

    # print("splitter inputs: ", splitter1.inputs, splitter2.inputs)

    # balancer.provide([100])
    # balancer.print_splitters()
    # balancer.iterate()
    # balancer.print_splitters()
    # balancer.iterate()
    # balancer.print_splitters()
    # balancer.iterate()
    # balancer.print_splitters()

    # print(balancer.outputs)
    # for splitter in balancer.splitters:
    #     print(splitter.inputs)

    # print(balancer.drain())


    sp1 = balancer.add_splitter()
    sp2 = balancer.add_splitter()
    sp3 = balancer.add_splitter()
    sp4 = balancer.add_splitter()
    # sp5 = balancer.add_splitter()
    # sp6 = balancer.add_splitter()

    balancer.add_input(sp1)
    balancer.add_input(sp1)
    balancer.add_input(sp2)
    balancer.add_input(sp2)

    # balancer.add_output(sp5)
    # balancer.add_output(sp5)
    # balancer.add_output(sp6)
    # balancer.add_output(sp6)
    balancer.add_output(sp3)
    balancer.add_output(sp3)
    balancer.add_output(sp4)
    balancer.add_output(sp4)

    balancer.connect_splitters(sp1, sp3)
    balancer.connect_splitters(sp1, sp4)
    balancer.connect_splitters(sp2, sp3)
    balancer.connect_splitters(sp2, sp4)
    # balancer.connect_splitters(sp4, sp1)
    # balancer.connect_splitters(sp3, sp5)
    # balancer.connect_splitters(sp3, sp6)
    # balancer.connect_splitters(sp4, sp5)
    # balancer.connect_splitters(sp4, sp6)

    # balancer.provide([100, 100, 0])

    # balancer.iterate()
    # balancer.print_splitters()
    # balancer.iterate()
    # balancer.print_splitters()
    # balancer.iterate()
    # balancer.print_splitters()
    # balancer.iterate()
    # balancer.print_splitters()
    # for i in range(100):
    #     print(i)
    #     print(balancer.drain([True, True, True]))
    #     balancer.provide([100, 100, 0])
    #     balancer.iterate()
    return balancer



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

    args = parser.parse_args()

    if not args.filename and not args.string:
        print("No file or string specified.")
        parser.parse_args(['-h'])

    if not args.string:
        print("Reading blueprint string from ", args.filename)
        file = open(args.filename, 'r')
        string = file.read()
        print("The blueprint string: \n", string)
    else:
        string = args.string

    blueprint = Blueprint.from_exchange_string(string)
    print(blueprint)
    print(blueprint.materials())

    print("\n")
    blueprint.print_grid_array()

    balancer = Balancer.from_blueprint(blueprint)

    print(balancer)

    #balancer = test_function(balancer)

    balancer.test(balance=args.balance, sweep=args.sweep, extensive_sweep=args.extensive, iterations=args.iterations)


