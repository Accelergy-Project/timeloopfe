"""!@brief Takes sparse optimizations from sparse optimizations lists and 
attaches them to the architecture.
"""
from .references2copies import References2CopiesProcessor
from ...parsing.nodes import DictNode
from ..processor import Processor


class SparseOptAttacherProcessor(Processor):
    """!@brief Takes sparse optimizations from sparse optimizations lists and
    attaches them to the architecture.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process(self):
        super().process()
        self.must_run_after(References2CopiesProcessor)
        while self.spec.sparse_optimizations.targets:
            opt = self.spec.sparse_optimizations.targets.pop(0)
            nodes = self.spec.architecture.get_nodes_of_type(DictNode)
            for c in nodes:
                if (
                    c.get("name", None) == opt.target
                    and "sparse_optimizations" in c
                ):
                    c.combine_index("sparse_optimizations", opt)
                    break
            else:
                raise ValueError(
                    f"Sparse optimization target '{opt.target}' not found in "
                    f"the architecture. Problematic sparse optimization: {opt}"
                )
