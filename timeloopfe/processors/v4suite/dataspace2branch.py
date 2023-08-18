"""!@brief Resolves which data spaces are kept in which branches."""
from typing import Set
from .constraint_attacher import ConstraintAttacherProcessor
from .constraint_macro import ConstraintMacroProcessor
from ...v4spec.arch import Branch, Parallel
from ...parsing.nodes import Node
from ...v4spec.constraints import Dataspace
from ..processor import Processor
from .references2copies import References2CopiesProcessor


class Dataspace2BranchProcessor(Processor):
    """!@brief Resolves which data spaces are kept in which branches."""

    def get_problem_ds_names(self) -> Set[str]:
        return set([x.name for x in self.spec.problem.shape.data_spaces])

    def _get_kept_dataspaces(self, b: Node) -> Set[str]:
        return set().union(*[d.keep for d in b.get_nodes_of_type(Dataspace)])

    def _parse_branch(self, branch: Branch, dataspaces: Set[str]) -> Set[str]:
        subnodes = branch.nodes
        all_ds = self.get_problem_ds_names()
        if isinstance(branch, Parallel):
            data_spaces_remaining = set(dataspaces)
            idx2keep = [self._get_kept_dataspaces(s) for s in subnodes]
            for i, s1 in enumerate(subnodes):
                for j, s2 in enumerate(subnodes[i + 1 :]):
                    shared = idx2keep[i].intersection(idx2keep[j + i + 1])
                    if shared:
                        raise ValueError(
                            f"DataSpaces {shared} are kept in two peer "
                            f"branches {s1} and {s2}. Each data space can "
                            f"only be kept in one branch. Full !Parallel node: "
                            f"{branch}."
                        )

            remaining_ds = data_spaces_remaining - set().union(*idx2keep)
            if remaining_ds:
                ds_list = "[" + ", ".join(remaining_ds) + "]"
                raise ValueError(
                    f"Can not find branch for {remaining_ds} in "
                    f"{branch}. If you would like to bypass all branches, add "
                    f"a new branch '- !Container "
                    f"{{constraints: {{dataspaces: {{keep: {ds_list}}}}}}}'"
                    f"to the !Parallel node. If you would like a data space to "
                )

            for i, s in enumerate(subnodes):
                keep = idx2keep[i]
                bypass = all_ds - keep
                self.logger.info(
                    'Branch "%s" keeps %s and bypasses %s.', s, keep, bypass
                )
                for ds in s.get_nodes_of_type(Dataspace):
                    ds.combine(Dataspace(bypass=list(bypass)))
                if isinstance(s, Branch):
                    self._parse_branch(s, keep)
        else:
            for s in subnodes:
                if isinstance(s, Branch):
                    self._parse_branch(s, dataspaces)

    def process(self):
        super().process()
        self.must_run_after(References2CopiesProcessor)
        self.must_run_after(ConstraintMacroProcessor, ok_if_not_found=True)
        self.must_run_after(ConstraintAttacherProcessor)
        self._parse_branch(self.spec.architecture, self.get_problem_ds_names())
