import unittest

from factorio_balancers.entity_mixins import Belt, Splitter, Underground


class TestEntityMixins(unittest.TestCase):
    def test_connections(self):
        belt1 = Belt()
        belt2 = Belt()
        belt1.forward.connect(belt2.backward)
        self.assertEqual(belt1.forward.entity, belt2)
        self.assertEqual(belt2.backward.entities[0], belt1)
