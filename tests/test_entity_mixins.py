import unittest

from py_factorio_blueprints.exceptions import UnknownEntity

from factorio_balancers.entity_mixins import Belt, Splitter, Underground
from factorio_balancers.balancer import Balancer
from factorio_balancers.exceptions import *


class TestEntityMixins(unittest.TestCase):
    def test_connections(self):
        belt1 = Belt()
        belt2 = Belt()
        belt1.forward.connect(belt2.backward)
        self.assertEqual(belt1.forward.entity, belt2)
        self.assertEqual(belt2.backward.entities[0], belt1)

    def stringRaises(self, string, exceptions):
        with open(string) as f:
            string = f.read()
        with self.assertRaises(exceptions):
            balancer = Balancer(string=string, print2d=True)

    def test_illegal_entities(self):
        self.stringRaises(
            'blueprint_strings/illegal_entities.blueprint',
            UnknownEntity)

    def test_illegal_configurations(self):
        self.stringRaises(
            'blueprint_strings/illegal_belt_configuration.blueprint',
            IllegalConfigurations)
        self.stringRaises(
            'blueprint_strings/illegal_splitter_configuration1.blueprint',
            IllegalConfigurations)
        self.stringRaises(
            'blueprint_strings/illegal_splitter_configuration2.blueprint',
            IllegalConfigurations)
        self.stringRaises(
            'blueprint_strings/illegal_underground_configuration1.blueprint',
            IllegalConfigurations)
        self.stringRaises(
            'blueprint_strings/illegal_underground_configuration2.blueprint',
            IllegalConfigurations)

    def test_import(self):
        with open('blueprint_strings/4x4_balancer.blueprint') as f:
            string = f.read()
        balancer = Balancer(string=string, print2d=True)
