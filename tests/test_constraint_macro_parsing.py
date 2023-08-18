import os
import unittest
from timeloopfe.processors.v4suite.references2copies import (
    References2CopiesProcessor,
)
from timeloopfe.v4spec.specification import Specification
from timeloopfe.processors.v4suite.constraint_macro import (
    ConstraintMacroProcessor,
)
from timeloopfe.v4spec import constraints


class TestConstraintMacroProcessorParsing(unittest.TestCase):
    def get_spec(self, **kwargs) -> Specification:
        this_script_dir = os.path.dirname(os.path.realpath(__file__))
        return Specification.from_yaml_files(
            os.path.join(this_script_dir, "arch_nest.yaml"), **kwargs
        )

    def test_keep_only(self):
        spec = self.get_spec(
            processors=[References2CopiesProcessor, ConstraintMacroProcessor]
        )
        ds = constraints.Dataspace(keep_only=["dataspace_A", "dataspace_B"])
        spec.constraints.targets.append(ds)
        spec.process()
        ds = spec.constraints.targets[-1]
        self.assertSetEqual(set(ds.keep), set(["dataspace_A", "dataspace_B"]))
        self.assertSetEqual(set(ds.bypass), set(["dataspace_C"]))

    def test_bypass_only(self):
        spec = self.get_spec(
            processors=[References2CopiesProcessor, ConstraintMacroProcessor]
        )
        ds = constraints.Dataspace(bypass_only=["dataspace_A"])
        spec.constraints.targets.append(ds)
        spec.process()
        ds = spec.constraints.targets[-1]
        self.assertSetEqual(set(ds.bypass), set(["dataspace_A"]))
        self.assertSetEqual(set(ds.keep), set(["dataspace_B", "dataspace_C"]))

    def test_factors_only(self):
        spec = self.get_spec(
            processors=[References2CopiesProcessor, ConstraintMacroProcessor]
        )
        it = constraints.Temporal(factors_only="A=2")
        spec.constraints.targets.append(it)
        spec.process()
        it = spec.constraints.targets[-1]
        self.assertSetEqual(
            set([(f, d) for f, _, d in it.factors.get_split_factors()]),
            set([("A", "2"), ("B", "1"), ("C", "1")]),
        )

    def test_no_reuse(self):
        spec = self.get_spec(
            processors=[References2CopiesProcessor, ConstraintMacroProcessor]
        )
        temporal = constraints.Temporal(no_reuse=["dataspace_A"])
        spatial = constraints.Spatial(no_reuse=["dataspace_B"])
        spec.constraints.targets.append(temporal)
        spec.constraints.targets.append(spatial)
        spec.process()
        temporal = spec.constraints.targets[-2]
        spatial = spec.constraints.targets[-1]
        self.assertEqual(temporal.no_temporal_reuse[0], "dataspace_A")
        self.assertEqual(spatial.no_multicast_no_reduction[0], "dataspace_B")
        self.assertEqual(len(temporal.no_temporal_reuse), 1)
        self.assertEqual(len(spatial.no_multicast_no_reduction), 1)

    def test_no_iteration_over_dataspaces(self):
        spec = self.get_spec(
            processors=[References2CopiesProcessor, ConstraintMacroProcessor]
        )
        it = constraints.Temporal(no_iteration_over_dataspaces=["dataspace_A"])
        it2 = constraints.Temporal(
            no_iteration_over_dataspaces=["dataspace_C"]
        )
        spec.constraints.targets.append(it)
        spec.constraints.targets.append(it2)
        spec.process()
        it = spec.constraints.targets[-2]
        it2 = spec.constraints.targets[-1]
        self.assertSetEqual(set(it.factors), {"A=1"})
        self.assertSetEqual(set(it2.factors), {"C=1"})
