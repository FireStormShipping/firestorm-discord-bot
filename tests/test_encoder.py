import json
import unittest

from app.app_types import DatasetEntry
from app.dataset_encoder import JsonEncoder, TableEncoder


class UnknownType:
    def __init__(self):
        self.value = 'a'

class TestTableEncoder(unittest.TestCase):
    def test_unknown_type(self):
        obj = UnknownType()
        enc = TableEncoder()

        with self.assertRaises(TypeError):
            enc.encode(obj)
        with self.assertRaises(NotImplementedError):
            enc.decode("random", "random_type")

    def test_sample_table(self):
        sample = """
| UID | Pool | Prompt | Weight | Sensitivity | Enabled | Flags |
| 1 | test | test | 1 | S | True | test |
"""
        enc = TableEncoder()
        header = enc.get_header_pretty()
        self.assertTrue(header in sample)

        entry = DatasetEntry(1, "test", "test", 1, "S", True, "test")
        row = enc.encode(entry)
        self.assertTrue(row in sample)

    def test_disabled_entry_row(self):
        enc = TableEncoder()
        entry = DatasetEntry(2, "pool", "prompt", 3, "Q", False, "")
        row = enc.encode(entry)
        self.assertEqual(row, "| 2 | pool | prompt | 3 | Q | False |  |\n")

class TestJsonEncoder(unittest.TestCase):
    def test_unknown_type(self):
        obj = UnknownType()
        enc = JsonEncoder()

        with self.assertRaises(TypeError):
            enc.encode(obj)
        with self.assertRaises(NotImplementedError):
            enc.decode("random", "random_type")

    def test_sample_entry_full_singleflag(self):
        sample = """{
    "text": "test",
    "weight": 2,
    "sensitivity": "E",
    "flags": [
        "flag"
    ]
}"""
        enc = JsonEncoder()
        entry = DatasetEntry(1, "test", "test", 2, "E", True, "flag")
        output = json.dumps(enc.encode(entry), indent=4)
        self.assertEqual(sample, output)

    def test_sample_entry_multiflags1(self):
        sample = """{
    "text": "test",
    "weight": 2,
    "sensitivity": "E",
    "flags": [
        "flag1",
        "flag2"
    ]
}"""
        enc = JsonEncoder()
        entry = DatasetEntry(1, "test", "test", 2, "E", True, "flag1,flag2")
        output = json.dumps(enc.encode(entry), indent=4)
        self.assertEqual(sample, output)

    def test_sample_entry_multiflags2(self):
        sample = """{
    "text": "test",
    "weight": 2,
    "sensitivity": "E",
    "flags": [
        "flag1",
        "flag2"
    ]
}"""
        enc = JsonEncoder()
        entry = DatasetEntry(1, "test", "test", 2, "E", True, "flag1, flag2")
        output = json.dumps(enc.encode(entry), indent=4)
        self.assertEqual(sample, output)

    def test_sample_entry_basic(self):
        sample = """{
    "text": "test2"
}"""
        enc = JsonEncoder()
        entry = DatasetEntry(1, "test", "test2", 1, "S", True, "")
        output = json.dumps(enc.encode(entry), indent=4)
        self.assertEqual(sample, output)

    def test_disabled_entry(self):
        sample = """{
    "text": "test2",
    "enabled": false
}"""
        enc = JsonEncoder()
        entry = DatasetEntry(1, "test", "test2", 1, "S", False, "")
        output = json.dumps(enc.encode(entry), indent=4)
        self.assertEqual(sample, output)

    def test_entry_with_escaping(self):
        sample = """{
    "text": "test2",
    "flags": [
        "A",
        "\\"extras\\" / poly"
    ]
}"""
        enc = JsonEncoder()
        entry = DatasetEntry(1, "test", "test2", 1, "S", True, "A,\"extras\" / poly")
        output = json.dumps(enc.encode(entry), indent=4)
        self.assertEqual(sample, output)
