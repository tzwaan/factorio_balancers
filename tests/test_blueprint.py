import unittest


from py_factorio_blueprints.exceptions import UnknownEntity
from factorio_balancers.balancer import Balancer
from factorio_balancers.exceptions import *


class TestBase(unittest.TestCase):
    def stringRaises(self, string, exceptions):
        with open(string) as f:
            string = f.read()
        with self.assertRaises(exceptions):
            balancer = Balancer(string=string)


class TestBlueprint(TestBase):
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
        balancer = Balancer(string=string)
