"""!@brief Optimizes permutation by pruning superfluous permutations."""
from ...processors.v4suite.constraint_attacher import (
    ConstraintAttacherProcessor,
)
from ...processors.v4suite.constraint_macro import ConstraintMacroProcessor
from .dataspace2branch import Dataspace2BranchProcessor
from ...v4spec.arch import Leaf, Storage
from ...processors.processor import Processor
from ...processors.v4suite.references2copies import References2CopiesProcessor


class PermutationOptimizerProcessor(Processor):
    """!@brief Optimizes permutation by pruning superfluous permutations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process(self):
        super().process()
        # Assert that the constraint attacher processor has already run
        self.must_run_after(ConstraintAttacherProcessor)
        self.must_run_after(References2CopiesProcessor)
        self.must_run_after(ConstraintMacroProcessor, ok_if_not_found=True)
        self.must_run_after(Dataspace2BranchProcessor, ok_if_not_found=True)
        problem = self.spec.problem

        constraints = []
        for c in self.spec.get_nodes_of_type(Leaf):
            if isinstance(c, Storage):
                constraints.append(c.constraints.temporal)
            if c.spatial.get_fanout() > 1:
                constraints.append(c.constraints.spatial)

        for c in constraints:
            for d, _, factor in c.factors.get_split_factors():
                if int(factor) == 1 and d not in c.permutation:
                    c.permutation.insert(0, d)
            for d in problem.shape.dimensions:
                if problem.instance[d] == 1 and d not in c.permutation:
                    c.permutation.insert(0, d)
