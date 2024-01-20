"""!@brief Defines constraint macros to be used for simplifying constraint
specification.
"""

import math
from typing import Dict, List, Tuple, Union

from ...common.nodes import ListNode
from ...common.processor import Processor

from ..constraints import Factors, ProblemDataspaceList
from ..constraints import Iteration, Dataspace, Spatial
from ...common.processor import References2CopiesProcessor
from ..arch import Leaf
from ...v4 import Specification
from ..specification import Specification


def factors_only_init(x) -> Union[Factors, None]:
    if x is None:
        return None
    return Factors.factory(x)


def num2list_of_prime_factors(x: int):
    factors = []
    while x > 1:
        for i in range(2, x + 1):
            if x % i == 0:
                factors.append(i)
                x //= i
                break
    return factors


def get_call_stack_size():
    import inspect

    return len(inspect.stack())


def greedy_allocate(
    factors: Dict[str, int], capacity: int
) -> Tuple[Dict[str, int], Dict[str, int]]:
    best_alloc, best_utilization = [], 1
    if capacity <= 1:
        return best_alloc, best_utilization

    for k, v in factors.items():
        if v > capacity:
            remaining = math.ceil(v / capacity)
            alloc = math.ceil(v / remaining)
            remainder = v % alloc
            util = (alloc * (remaining - 1) + remainder) / remaining
            if util > best_utilization:
                best_utilization = util
                best_alloc = [(k, remainder, alloc)]
            # print(' ' * get_call_stack_size(),
            #   f'A: {k} = {alloc} -> {alloc} with capacity {capacity}. Utilization = {util}')

        for p in set(num2list_of_prime_factors(v)):
            if p > capacity:
                continue
            newfactors = {k: v for k, v in factors.items()}
            newfactors[k] //= p
            alloc, util = greedy_allocate(newfactors, capacity // p)
            util *= p
            # print(' ' * get_call_stack_size(),
            #       f'A: {k} = {p} -> {alloc} with capacity {capacity}. Utilization = {util}')
            if util > best_utilization:
                best_utilization = util
                best_alloc = [(k, p, p)] + alloc

    return best_alloc, best_utilization


class ConstraintMacroProcessor(Processor):
    """!@brief Defines constraint macros to be used for simplifying constraint
    specification.

    Iteration constraint macros:
    - factors_only: Only the listed factors are allowed. Other factors are
                    set to 1.
                    e.g. factors_only: "A=5" -> factors: A=5, B=1, C=1, ...
    - no_iteration_over_dataspaces:
        Takes a list of dataspaces. Iteration over all factors of these
        dataspaces is disabled. e.g. no_iteration_over_dataspaces: ["Weights"]
        -> factors: R=1 S=1 C=1 M=1 if the factors in weights are RSCM
    - must_iterate_over_dataspaces:
        Takes a list of dataspaces. Must iterate over the union of
        factors of these dataspaces.
    - maximize_dims: Takes a list of lists of dimensions. Each list of
                        dimensions is maximized. e.g. maximize_dims: [ [R, S],
                        [C, M] ] -> find the largest factors of R and S that
                        we can fit, then find the largest factors of C and M
                        that we can fit. In a spatial constraint, this
                        uses the fanout of the leaf. In a temporal constraint,
                        this uses a maximize_dims_capacity directive.

    Dataspace constraint macros:
    - keep_only: Only the listed dataspaces are kept. All other dataspaces
                 are bypassed.
    - bypass_only: Only the listed dataspaces are bypassed. All other
                   dataspaces are kept.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def declare_attrs(self):
        super().add_attr(Iteration, "factors_only", None, None, factors_only_init)

        pds = ProblemDataspaceList

        def pds_constructor(x):
            return pds(x) if x is not None else None

        super().add_attr(
            Iteration,
            "no_iteration_over_dataspaces",
            (pds, None),
            None,
            pds_constructor,
        )
        super().add_attr(
            Iteration,
            "must_iterate_over_dataspaces",
            (pds, None),
            None,
            pds_constructor,
        )
        super().add_attr(Iteration, "maximize_dims", ListNode, None)
        super().add_attr(Iteration, "maximize_dims_capacity", (int), None)

        super().add_attr(Dataspace, "keep_only", (pds, None), None, pds_constructor)
        super().add_attr(Dataspace, "bypass_only", (pds, None), None, pds_constructor)

    def get_unconstrained_dims(self, spec: Specification) -> Dict[str, int]:
        unconstrained = {k: v for k, v in spec.problem.instance.items()}
        for factors in spec.get_nodes_of_type(Factors):
            for name, operator, value in factors.get_split_factors():
                value = value or spec.problem.instance[name]
                if value > 0 and operator == "=":
                    unconstrained[name] = math.ceil(unconstrained[name] / value)
        return unconstrained

    def get_constrained_dims(
        self, factors: Factors, spec: Specification
    ) -> Dict[str, int]:
        constrained = {}
        for name, operator, value in factors.get_split_factors():
            value = value or spec.problem.instance[name]
            if value > 0 and operator in ["=", ">="]:
                constrained[name] = value
        return constrained

    def process(self, spec: Specification):
        super().process(spec)
        self.must_run_after(References2CopiesProcessor, spec)
        prob_shape = spec.problem.shape
        prob_data_spaces = [ds.name for ds in prob_shape.data_spaces]
        prob_dimensions = prob_shape.dimensions

        def debug_message(x, kind):
            self.logger.debug('Found %s constraint "%s"', kind, str(x))

        for p in spec.get_nodes_of_type(ProblemDataspaceList):
            if "*" in p:
                self.logger.debug(
                    '"%s" contains "*", replacing with all dataspaces', str(p)
                )
                for ds in prob_data_spaces:
                    if ds not in p:
                        p.append(ds)
                p.remove("*")

        for constraint in spec.get_nodes_of_type(Iteration):
            debug_message(constraint, "iteration")
            constraint: Iteration = constraint  # type: ignore
            if (
                factors := constraint.pop("factors_only", None)  # type: ignore
            ) is not None:
                debug_message(factors, "factors_only")
                factors: Factors = factors
                fnames = factors.get_factor_names()
                for p in prob_dimensions:
                    if p not in fnames:
                        factors.add_eq_factor(p, 1)
                constraint.factors.combine(factors)  # type: ignore

            if (ds := constraint.pop("no_iteration_over_dataspaces", None)) is not None:
                debug_message(ds, "no_iteration_over_dataspaces")
                dataspaces = [prob_shape.name2dataspace(d) for d in ds]
                constraint.factors.combine(  # type: ignore
                    Factors(
                        list(
                            f"{f}=1"
                            for d in dataspaces
                            for f in d.factors
                            if f in spec.problem.shape.dimensions
                        )
                    )
                )
            if (ds := constraint.pop("must_iterate_over_dataspaces", None)) is not None:
                debug_message(ds, "must_iterate_over_dataspaces")
                dataspaces = [prob_shape.name2dataspace(d) for d in ds]
                allfactors = set()
                for d in dataspaces:
                    allfactors.update(d.factors)
                notfactors = set(prob_dimensions) - allfactors

                constraint.factors.combine(  # type: ignore
                    Factors(
                        list(
                            f"{f}=1"
                            for f in notfactors
                            if f in spec.problem.shape.dimensions
                        )
                    )
                )

        for constraint in spec.get_nodes_of_type(Dataspace):
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

        unconstrained = self.get_unconstrained_dims(spec)

        # Spatial then temporal. Bottom up
        spatials, temporals = [], []
        for leaf in spec.architecture.get_nodes_of_type(Leaf)[::-1]:
            spatials.append((leaf, leaf.constraints.spatial))
            temporals.append((leaf, leaf.constraints.temporal))

        for leaf, constraint in spatials + temporals:
            maximize_dims = constraint.pop("maximize_dims")
            capacity = constraint.pop("maximize_dims_capacity", None)
            if maximize_dims is None or len(maximize_dims) == 0:
                continue
            if isinstance(constraint, Spatial) and capacity is None:
                capacity = leaf.spatial.get_fanout()
            else:
                assert capacity is not None, (
                    "Expected maximize_dims_capacity to be specified for "
                    "temporal constraints with a maximize_dims constraint."
                    "Please add an integer value for "
                    f"maximize_dims_capacity for {constraint}"
                )
            start_capacity = capacity

            if isinstance(maximize_dims[0], str):
                assert all(isinstance(x, str) for x in maximize_dims), (
                    'Expected "maximize_dims" to be a list of strings or a '
                    "list of lists. Got a mix of both."
                )
                maximize_dims = [maximize_dims]
            assert all(isinstance(x, list) for x in maximize_dims), (
                'Expected "maximize_dims" to be a list of strings or a '
                "list of lists. Got a mix of both."
            )
            for m in maximize_dims:
                factors: Factors = constraint.factors
                constrained_dims = self.get_constrained_dims(factors, spec)
                # Get usable maxf
                capacity = start_capacity
                for v in constrained_dims.values():
                    capacity //= v

                to_allocate = {}
                for dim in m:
                    if dim in factors.get_factor_names():
                        raise ValueError(
                            f'Cannot maximize dimension "{dim}" because it is '
                            f"already constrained to ."
                            f"{factors.name2factor(dim)} in {factors}."
                        )
                    if dim not in unconstrained:
                        raise ValueError(
                            f'Cannot maximize dimension "{dim}" because it is '
                            f"not a problem dimension. Problem dimensions are "
                            f"{prob_dimensions}."
                        )
                    to_allocate[dim] = unconstrained[dim]
                mins_maxes = {}
                # print(f'Greedy allocating {to_allocate} with capacity '
                #       f'{capacity} in {factors}={list(factors)}')
                # print(f'{maximize_dims=}, {m=}')
                for k, lo, hi in greedy_allocate(to_allocate, capacity)[0]:
                    mins_maxes.setdefault(k, [1, 1])
                    mins_maxes[k][0] *= lo
                    mins_maxes[k][1] *= hi
                for a in to_allocate:
                    mins_maxes.setdefault(a, [1, 1])
                # print(f' -> {mins_maxes}')

                for k, (_, maxv) in mins_maxes.items():
                    factors.add_eq_factor(k, maxv)
                    unconstrained[k] = math.ceil(unconstrained[k] / maxv)
                    # print(f'Unconstrained[{k}] = {unconstrained[k]}')

            if capacity <= 1 and isinstance(leaf, Spatial):
                for dim in factors.get_factor_names():
                    factors.add_eq_factor_iff_not_exists(dim, 1)
