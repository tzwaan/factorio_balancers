#!/usr/bin/env python

import logging

from factorio_balancers import Balancer
from argparse import ArgumentParser
from py_factorio_blueprints.exceptions import InvalidExchangeString


logger = logging.getLogger('factorio_balancers')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

formatter = logging.Formatter('%(message)s')


parser = ArgumentParser(
    description="Test a balancer configuration for its properties")
parser.add_argument(
    "-f", "--file", dest="filename",
    metavar="FILE",
    help="The file from which to read the blueprint string")
parser.add_argument(
    "-nb", "--nobalance", dest="balance", action='store_false', default=True,
    help="If for any reason you don't want to test the balance of the balancer")
parser.add_argument(
    "-t", "--trickle", dest='trickle', action='store_true', default=False,
    help="Performs a balance test using belts that are not full")
parser.add_argument(
    "--throughput", dest='throughput', action='store_true', default=False,
    help="Performs a throughput test to determine bottlenecks on regular use")
parser.add_argument(
    "-s", "--sweep", dest="sweep", default=False, action='store_true',
    help="Performs a throughput test on all combinations where exactly 1 or 2 inputs and outputs are used")
parser.add_argument(
    "-es", "--extensivesweep", dest="extensive",
    default=False, action='store_true',
    help="Performs a throughput test on all combinations of the same number of inputs and outputs")
parser.add_argument(
    "--string", dest="string", default=False,
    help="The blueprint string to parse", metavar="STRING")
parser.add_argument(
    "--silent", dest="verbose", default=True, action='store_false',
    help="Tell the script not to write intermediate data to the screen.\nNote: this prints raw function results on exit that are very user-unfriendly.")
parser.add_argument(
    '--debug', dest='debug', default=False, action='store_true',
    help="Write additional debug info to the screen when parsing and testing")

args = parser.parse_args()

if args.verbose:
    console_handler.setLevel(logging.INFO)
if args.debug:
    console_handler.setLevel(logging.DEBUG)

console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

if not args.filename and not args.string:
    logger.error("No file or string specified.")
    parser.parse_args(['-h'])

if not args.string:
    logger.debug("Reading blueprint string from ", args.filename)
    file = open(args.filename, 'r')
    string = file.read()
    logger.debug("The blueprint string: \n", string)
else:
    string = args.string

try:
    balancer = Balancer(string=string, verbose=args.verbose)
except InvalidExchangeString:
    logger.error("Error - Either the string was formatted wrong, or the blueprint contained non-belt entities.")
    logger.info("Exiting.")
    exit()

def add_property(props, condition, prop):
    if condition:
        props.append(prop)

properties = []

add_property(properties, args.balance, 'balance.output')
add_property(properties, args.balance, 'balance.input')
add_property(properties, args.trickle, 'balance.output.trickle')
add_property(properties, args.trickle, 'balance.input.trickle')
add_property(properties, args.sweep, 'throughput.unlimited.candidate')
add_property(properties, args.extensive, 'throughput.unlimited')

results = balancer.test(
    properties=properties, verbose=args.verbose)
print(results)
