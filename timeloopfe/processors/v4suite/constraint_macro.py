"""!@brief Defines constraint macros to be used for simplifying constraint
specification.
"""

from typing import Union
from ...v4spec import constraints
from ...v4spec.constraints import Factors, ProblemDataspaceList
from ...processors.processor import Processor
from ...v4spec.constraints import Iteration, Temporal, Spatial, Dataspace
from ...processors.v4suite.references2copies import References2CopiesProcessor


def factors_only_init(x) -> Union[Factors, None]:
    if x is None:
        return None
    return Factors.factory(x)


class ConstraintMacroProcessor(Processor):
    """!@brief Defines constraint macros to be used for simplifying constraint
    specification.

    Iteration constraint macros:
    - factors_only: Only the listed factors are allowed. Other factors are
                    set to 1.
                    e.g. factors_only: "A=5" -> factors: A=5, B=1, C=1, ...
    - no_reuse:     No reuse allowed. In spatial loops, this means no multicast
                    or reduction. In temporal loops, this means data is flushed
                    between iterations of upper loops.
    - no_iteration_over_dataspaces:
        Takes a list of dataspaces. Iteration over all factors of these
        dataspaces is disabled. e.g. no_iteration_over_dataspaces: ["Weights"]
        -> factors: R=1 S=1 C=1 M=1 if the factors in weights are RSCM
    Dataspace constraint macros:
    - keep_only: Only the listed dataspaces are kept. All other dataspaces
                 are bypassed.
    - bypass_only: Only the listed dataspaces are bypassed. All other
                   dataspaces are kept.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_elems(self):
        with self.responsible_for_removing_elems():  # type: ignore
            Iteration.init_elem("factors_only", None, None, factors_only_init)

            pds = ProblemDataspaceList
            pds_constructor = lambda x: pds(x) if x is not None else None

            Iteration.init_elem("no_reuse", (pds, None), None, pds_constructor)
            Iteration.init_elem(
                "no_iteration_over_dataspaces",
                (pds, None),
                None,
                pds_constructor,
            )
            Dataspace.init_elem(
                "keep_only", (pds, None), None, pds_constructor
            )
            Dataspace.init_elem(
                "bypass_only", (pds, None), None, pds_constructor
            )

    def process(self):
        super().process()
        self.must_run_after(References2CopiesProcessor)
        prob_shape = self.spec.problem.shape
        prob_data_spaces = [ds.name for ds in prob_shape.data_spaces]
        prob_dimensions = prob_shape.dimensions

        def debug_message(x, kind):
            self.logger.debug('Found %s constraint "%s"', kind, str(x))

        for p in self.spec.get_nodes_of_type(ProblemDataspaceList):
            if "*" in p:
                self.logger.debug(
                    '"%s" contains "*", replacing with all dataspaces', str(p)
                )
                for ds in prob_data_spaces:
                    if ds not in p:
                        p.append(ds)
                p.remove("*")

        for constraint in self.spec.get_nodes_of_type(Iteration):
            debug_message(constraint, "iteration")
            constraint: Iteration = constraint  # type: ignore
            ctype = type(constraint)
            if (ds := constraint.pop("no_reuse", None)) is not None:
                ds = prob_data_spaces if ds is True or "*" in ds else ds
                if isinstance(constraint, Temporal):
                    constraint.combine(Temporal(no_temporal_reuse=ds))
                elif isinstance(constraint, Spatial):
                    constraint.combine(Spatial(no_multicast_no_reduction=ds))

            constraint: Iteration = constraint  # type: ignore
            if (
                factors := constraint.pop("factors_only", None)  # type: ignore
            ) is not None:
                debug_message(factors, "factors_only")
                factors: Factors = factors
                fnames = factors.get_factor_names()
                for p in prob_dimensions:
                    if p not in fnames:
                        factors.add_equal_factor(p, 1)
                constraint.factors.combine(factors)  # type: ignore

            if (
                ds := constraint.pop("no_iteration_over_dataspaces", None)
            ) is not None:
                debug_message(ds, "no_iteration_over_dataspaces")
                dataspaces = [prob_shape.name2dataspaces(d) for d in ds]
                constraint.factors.combine(  # type: ignore
                    Factors(
                        list(f"{f}=1" for d in dataspaces for f in d.factors)
                    )
                )

        for constraint in self.spec.get_nodes_of_type(constraints.Dataspace):
            constraint: Dataspace = constraint  # type: ignore
            debug_message(constraint, "dataspace")
            ctype = type(constraint)
            if (ds := constraint.pop("keep_only", None)) is not None:
                debug_message(ds, "keep_only")
                keep = ds
                bypass = list(set(prob_data_spaces) - set(ds))
                constraint.combine(ctype(bypass=bypass, keep=keep))

            if (ds := constraint.pop("bypass_only", None)) is not None:
                debug_message(ds, "bypass_only")
                keep = list(set(prob_data_spaces) - set(ds))
                bypass = ds
                constraint.combine(ctype(bypass=bypass, keep=keep))
