import os
import unittest
from timeloopfe.processors.v4suite.constraint_attacher import (
    ConstraintAttacherProcessor,
)
from timeloopfe.processors.processor import Processor
from timeloopfe.parsing.nodes import NodeException
from timeloopfe.v4spec.specification import Specification
from timeloopfe.v4spec.arch import (
    Element,
    Hierarchical,
    Leaf,
    Storage,
    StorageAttributes,
)
from timeloopfe.v4spec.constraints import Temporal
from timeloopfe.processors.v4suite.references2copies import (
    References2CopiesProcessor,
)


class NodeTest(unittest.TestCase):
    def get_spec(self, *args, **kwargs) -> Specification:
        this_script_dir = os.path.dirname(os.path.realpath(__file__))
        args = [os.path.join(this_script_dir, a) for a in args]
        return Specification.from_yaml_files(
            os.path.join(this_script_dir, "arch_nest.yaml"), *args, **kwargs
        )

    def test_missing_key(self):
        with self.assertRaises((KeyError)):
            Element({"name": "test"})

    def test_extra_key(self):
        with self.assertRaises(ValueError):
            Element({"name": "test", "class": "storage", "extra": "abc"})

    def test_unrecognized_tag(self):
        class Tagged:
            pass

        with self.assertRaises((KeyError, ValueError, NodeException)):
            Hierarchical(nodes=[Tagged()])

    def test_unrecognized_type_tag(self):
        class Tagged:
            pass

        x = Tagged()
        x.tag = "!Element"
        with self.assertRaises(TypeError):
            y = Hierarchical()
            y.nodes.append(x)
            y.check_unrecognized()

    def test_unrecognized_type_key(self):
        with self.assertRaises(((TypeError, NodeException))):
            Element({"name": 32, "class": "storage"})

    def test_should_have_been_removed_by(self):
        class Test(Processor):
            def init_elems(self):
                with self.responsible_for_removing_elems():
                    Element.init_elem("for_testing_ignoreme", str, "")

            def process(self):
                for e in self.spec.get_nodes_of_type(Element):
                    e.pop("for_testing_ignoreme", None)

        spec = self.get_spec(processors=[Test])
        spec.architecture.nodes.append(
            Element(
                {"name": ".", "class": "storage", "for_testing_ignoreme": "."}
            )
        )
        with self.assertRaises(ValueError):
            spec.check_unrecognized()
        spec.process()
        spec.check_unrecognized()

    def test_repeated_key_error(self):
        with self.assertRaises(ValueError):
            spec = self.get_spec("repeated_key_error.yaml")

    def test_multi_list_constraints(self):
        spec = self.get_spec(
            "multi_list_constraints.yaml",
            processors=[
                References2CopiesProcessor,
                ConstraintAttacherProcessor,
            ],
        )
        spec.process()
        for node in spec.architecture.get_nodes_of_type(Leaf):
            if node.name == "Hier_A":
                self.assertSetEqual(
                    set(node.constraints.dataspace.bypass),
                    set(["dataspace_B", "dataspace_C"]),
                )
                self.assertSetEqual(
                    set(node.constraints.dataspace.keep), set(["dataspace_A"])
                )
            elif node.name == "Hier_B":
                self.assertSetEqual(
                    set(node.constraints.dataspace.bypass),
                    set(["dataspace_A", "dataspace_C"]),
                )
                self.assertSetEqual(
                    set(node.constraints.dataspace.keep), set(["dataspace_B"])
                )
            else:
                self.assertSetEqual(
                    set(node.constraints.dataspace.bypass), set()
                )
                self.assertSetEqual(
                    set(node.constraints.dataspace.keep), set()
                )

    def test_repeated_node_init(self):
        t1 = Temporal(factors="A=1 B=2 C=3")
        t2 = Temporal(factors=t1.factors)
        self.assertEqual(t1, t2)

    def test_dash_alias_errors(self):
        x = Temporal(no_temporal_reuse=[])
        with self.assertRaises(KeyError):
            x["no-temporal-reuse"] = []
        with self.assertRaises(KeyError):
            x.get("no-temporal-reuse", None)
        with self.assertRaises(KeyError):
            x.pop("no-temporal_reuse", None)
        with self.assertRaises(KeyError):
            x.pop("no_temporal-reuse", None)
        with self.assertRaises(KeyError):
            x.setdefault("no-temporal-reuse", [])

    def test_multi_require_exactly_one(self):
        x = StorageAttributes(
            datawidth=5, depth=5, width=5, block_size=5, technology=5
        )
        x.check_unrecognized()
        with self.assertRaises(KeyError):
            x.cluster_size = 5
            x.check_unrecognized()

    def test_multi_require_all_or_none_of(self):
        x = StorageAttributes(
            datawidth=5, depth=5, width=5, block_size=5, technology=5
        )
        x.check_unrecognized()
        x.metadata_block_size = 1
        x.metadata_datawidth = 1
        x.metadata_storage_depth = 1
        x.metadata_storage_width = 1
        x.check_unrecognized()
        with self.assertRaises(KeyError):
            x.metadata_block_size = None
            x.check_unrecognized()
