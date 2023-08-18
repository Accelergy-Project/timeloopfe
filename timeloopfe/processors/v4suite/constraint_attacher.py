"""!@brief Takes constraints from constraints lists and attaches them to
objects in the architecture.
"""
from ...processors.v4suite.references2copies import References2CopiesProcessor
from ...parsing.nodes import DictNode
from ...processors.processor import Processor


class ConstraintAttacherProcessor(Processor):
    """!@brief Takes constraints from constraints lists and attaches them to
    objects in the architecture.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process_target(self, x):
        while x:
            constraint = x.pop(0)
            nodes = self.spec.architecture.get_nodes_of_type(DictNode)
            for c in nodes:
                if (
                    c.get("name", None) == constraint.target
                    and "constraints" in c
                ):
                    c["constraints"].combine_index(constraint.type, constraint)
                    break
            else:
                all_node_names = list(
                    c.get("name") for c in nodes if "name" in c
                )
                raise ValueError(
                    f"Constraint target '{constraint.target}' not found in "
                    f"the architecture. Problematic constraint: {constraint}."
                    f"Available targets: {all_node_names}."
                )

    def process(self):
        super().process()
        self.must_run_after(References2CopiesProcessor)
        self._process_target(self.spec.constraints.targets)
        self._process_target(self.spec.mapping)
