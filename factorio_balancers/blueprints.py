"""blueprints.py

Routines for decoding, inspecting, manipulating, and re-encoding Factorio
blueprints.
MIT License

Copyright (c) 2017 Eric Burgess

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import base64
import collections
import json
import zlib
import math
from factorio_balancers.defaultentities import entity_data


class InvalidExchangeStringException(Exception):
    pass


class Entity(object):
    def __init__(self, data=None):
        self.data = data or {}
        if 'name' in self.data:
            if self.name in entity_data:
                self.info = entity_data[self.name]
        else:
            self.info = {}

    def __getattr__(self, attr):
        return self.inner_data.get(attr)

    @property
    def direction(self):
        return self.inner_data.get('direction') or 0

    @property
    def data_type(self):
        data_type, _ = next(iter(self.data.items()))
        return data_type

    @property
    def inner_data(self):
        return self.data

    def to_json_string(self, **kwargs):
        data = self.data.copy()
        json_str = json.dumps(
            data,
            separators=(",", ":"),
            ensure_ascii=False,
            **kwargs
        ).encode("utf8")
        return json_str

    def get_ascii(self):
        if self.name in entity_data and 'ascii' in entity_data[self.name]:
            direction = self.direction
            ascii_array = entity_data[self.name]['ascii'][direction // 2]
        else:
            ascii_array = [["X"]]
        return ascii_array


class EncodedBlob(object):
    """one Factorio json->gzip->base64 encoded blob"""

    def __init__(self, data=None, version_byte=None):
        self.data = data or {}
        self.version_byte = version_byte

    def __getattr__(self, attr):
        """Generically provide access to blueprint.data.blueprint.entities etc"""
        return self.inner_data.get(attr)

    @property
    def data_type(self):
        data_type, _ = next(iter(self.data.items()))
        return data_type

    @property
    def inner_data(self):
        _, inner_data = next(iter(self.data.items()))
        return inner_data

    @classmethod
    def from_exchange_string(cls, exchange_str):
        version_byte = exchange_str[0]
        try:
            decoded = base64.b64decode(exchange_str[1:])
        except (TypeError, base64.binascii.Error):
            raise InvalidExchangeStringException

        try:
            json_str = zlib.decompress(decoded).decode("UTF-8")
        except zlib.error:
            raise InvalidExchangeStringException
        data = json.loads(json_str, object_pairs_hook=collections.OrderedDict)
        return cls(data=data, version_byte=version_byte)

    @classmethod
    def from_exchange_file(cls, filename):
        return cls.from_exchange_string(open(filename).read().strip())

    @classmethod
    def from_json_string(cls, json_str):
        data = json.loads(json_str, object_pairs_hook=collections.OrderedDict)
        version_byte = data.pop("version_byte", None)
        return cls(data=data, version_byte=version_byte)

    @classmethod
    def from_json_file(cls, filename):
        return cls.from_json_string(open(filename).read().strip())

    def to_exchange_string(self, **kwargs):
        if self.version_byte is None:
            raise RuntimeError(
                "Attempted to convert to exchange string with no version_byte")
        json_str = self.to_json_string(**kwargs)
        compressed = zlib.compress(json_str, 9)
        encoded = base64.b64encode(compressed)
        return self.version_byte + encoded.decode()

    def to_exchange_file(self, filename):
        open(filename, "w").write(self.to_exchange_string())

    def to_json_string(self, **kwargs):
        data = self.data.copy()
        if self.version_byte is not None:
            data["version_byte"] = self.version_byte
        json_str = json.dumps(
            data,
            separators=(",", ":"),
            ensure_ascii=False,
            **kwargs
        ).encode("utf8")
        return json_str

    def to_json_file(self, filename, **kwargs):
        open(filename, "w").write(self.to_json_string(**kwargs))


class Blueprint(EncodedBlob):
    """one Factorio blueprint"""
    def __init__(self, data=None, version_byte=None):
        super().__init__(data, version_byte)
        self.objectify_entities()

    def is_filtered(self, whitelist=[], blacklist=[]):
        if whitelist:
            for entity in self.entities:
                if entity.info['prototype'] not in whitelist:
                    return False
        if blacklist:
            for entity in self.entities:
                if entity.info['prototype'] in blacklist:
                    return False
        return True

    def remove_entity_numbers(self):
        """Remove blueprint.data["blueprint"]["entities"][*]["entity_number"]"""
        next_number = 1
        for entity in self.entities:
            number = entity.pop("entity_number", None)
            # replace_entity_numbers assumes sequential numbers starting at 1
            # this assert will trigger bug reports if that assumption is wrong
            assert number == next_number or number is None
            next_number = next_number + 1

    def replace_entity_numbers(self):
        number = 1
        for entity in self.entities:
            entity["entity_number"] = number
            number = number + 1

    def materials(self):
        """Totals of each entity contained in the blueprint."""
        mats = {}
        for ent in self.entities:
            name = ent.name
            mats[name] = mats.setdefault(name, 0) + 1
        return mats

    def make_positive_positions(self):
        lowest_x = float('inf')
        lowest_y = float('inf')
        highest_x = -float('inf')
        highest_y = -float('inf')
        for entity in self.entities:
            if entity.position['x'] < lowest_x:
                lowest_x = math.floor(entity.position['x'])
            if entity.position['y'] < lowest_y:
                lowest_y = math.floor(entity.position['y'])
            if entity.position['x'] > highest_x:
                highest_x = entity.position['x']
            if entity.position['y'] > highest_y:
                highest_y = entity.position['y']
        for entity in self.entities:
            entity.position['x'] -= lowest_x
            entity.position['y'] -= lowest_y

        return highest_x - lowest_x, highest_y - lowest_y

    def objectify_entities(self):
        self.entities = list(map(
            lambda data: Entity(data=data),
            self.entities
        ))

    def to_json_string(self, **kwargs):
        self.entities = list(map(
            lambda entity: entity.data,
            self.entities
        ))
        json_str = super().to_json_string(**kwargs)
        self.objectify_entities()
        return json_str

    def get_grid_array(self):
        max_x, max_y = self.make_positive_positions()
        max_x = math.ceil(max_x)
        max_y = math.ceil(max_y)
        grid = [[None for x in range(max_x + 1)] for y in range(max_y + 1)]

        for entity in self.entities:
            grid[math.floor(entity.position['y'])][math.floor(entity.position['x'])] = entity
            grid[math.ceil(entity.position['y'])][math.ceil(entity.position['x'])] = entity

        return grid

    def print_grid_array(self, grid=None):
        if grid is None:
            grid = self.get_grid_array()

        output_grid = [[" " for x in range(len(grid[0]))] for y in range(len(grid))]

        for y, line in enumerate(grid):
            for x, entity in enumerate(line):
                if entity is None:
                    continue
                ascii_array = entity.get_ascii()
                for j, ascii_line in enumerate(ascii_array):
                    for i, character in enumerate(ascii_line):
                        output_grid[
                            math.floor(entity.position['y']) + j
                        ][
                            math.floor(entity.position['x']) + i] = character + "\u001b[0m"
        output = ""
        for line in output_grid:
            for entity in line:
                output += entity
            output += "\n"

        print(output)


class BlueprintBook(EncodedBlob):
    """one Factorio blueprint book, containing zero or more blueprints"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.objectify_blueprints()

    def objectify_blueprints(self):
        # convert internal blueprint dicts to Blueprint objects
        self.data["blueprint_book"]["blueprints"] = list(map(
            lambda data: Blueprint(data=data, version_byte=self.version_byte),
            self.data["blueprint_book"]["blueprints"]
        ))

    def to_json_string(self, **kwargs):
        # convert internal Blueprint objects back to dicts for serialization
        self.data["blueprint_book"]["blueprints"] = list(map(
            lambda blueprint: blueprint.data,
            self.data["blueprint_book"]["blueprints"]
        ))
        json_str = super().to_json_string(**kwargs)
        self.objectify_blueprints()
        return json_str

    def remove_indexes(self):
        """Remove self.data["blueprint_book"]["blueprints"][*]["index"]"""
        next_number = 0
        for blueprint in self.blueprints:
            number = blueprint.data.pop("index", None)
            # replace_indexes assumes sequential numbers starting at 0
            # this assert will trigger bug reports if that assumption is wrong
            assert number == next_number or number is None
            next_number = next_number + 1

    def replace_indexes(self):
        number = 0
        for blueprint in self.blueprints:
            blueprint.data["index"] = number
            number = number + 1
