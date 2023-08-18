import os
import unittest
from timeloopfe.v4spec.specification import Specification
from timeloopfe.v4spec.arch import (
    Element,
    Hierarchical,
    Parallel,
    Pipelined,
)
from timeloopfe.processors.v4suite.math import MathProcessor
from timeloopfe.processors.v4suite.references2copies import (
    References2CopiesProcessor,
)


class TestMathProcessorParsing(unittest.TestCase):
    def get_spec(self, **kwargs) -> Specification:
        this_script_dir = os.path.dirname(os.path.realpath(__file__))
        return Specification.from_yaml_files(
            os.path.join(this_script_dir, "arch_nest.yaml"), **kwargs
        )

    def test_math_parsing(self):
        spec = self.get_spec(
            processors=[References2CopiesProcessor, MathProcessor]
        )
        arch = spec.architecture.nodes
        arch[0].attributes["test"] = "1 + 1"
        arch[0].attributes["test2"] = "1 + known_value"
        arch[0].attributes["test3"] = "len('abcd')"
        spec.variables["known_value"] = 2
        spec.process()
        arch = spec.architecture.nodes
        self.assertEqual(arch[0].attributes["test"], 2)
        self.assertEqual(arch[0].attributes["test2"], 3)
        self.assertEqual(arch[0].attributes["test3"], 4)

    def test_math_parsing_fail(self):
        spec = self.get_spec(
            processors=[References2CopiesProcessor, MathProcessor]
        )
        arch = spec.architecture.nodes
        arch[0].attributes["test"] = "intentionally invalid math. should fail."
        with self.assertRaises(SystemExit):
            spec.process()
