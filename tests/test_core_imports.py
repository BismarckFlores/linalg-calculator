"""Compatibilidad de las rutas públicas tras organizar el motor por áreas."""

from importlib import import_module
import unittest

from core.linear_algebra.handlers.matrix import Matrix
from core.linear_algebra.systems import solve
from core.number_systems.roman import read
from core.numerical_methods.bisection import bisect


class CoreImportsTests(unittest.TestCase):
    def test_legacy_paths_export_the_canonical_symbols(self):
        for name, symbol in (("matrix", Matrix), ("systems", solve), ("roman", read), ("bisection", bisect)):
            with self.subTest(name=name):
                self.assertIs(import_module(f"core.{name}"), import_module(symbol.__module__))
