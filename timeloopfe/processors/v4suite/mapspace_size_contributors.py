"""!@brief Estimates how much each element contributes to the mapspace size.
NOTE: Numbers are NOT precise and are only meant to guide the user in 
understanding the mapspace size.
"""
from collections import defaultdict
from math import factorial
import math
from ...processors.v4suite.constraint_attacher import (
    ConstraintAttacherProcessor,
)
from ...processors.v4suite.constraint_macro import ConstraintMacroProcessor
from .dataspace2branch import Dataspace2BranchProcessor
from ...processors.v4suite.permutation_optimizer import (
    PermutationOptimizerProcessor,
)
from ...v4spec.arch import Leaf, Storage
from ...v4spec.constraints import Iteration
from ...processors.processor import Processor
from typing import List, Tuple


def get_prime_factors(x: int) -> List[int]:
    prime_factors = []
    for i in range(2, x + 1):
        if i * i > x:
            break
        while x % i == 0:
            prime_factors.append(i)
            x //= i
    if x > 1:
        prime_factors.append(x)
    return prime_factors


class MapspaceSizeContributorsProcessor(Processor):
    """!@brief Estimates how much each element contributes to the mapspace
    size. NOTE: Numbers are NOT precise and are only meant to guide the user
    in understanding the mapspace size.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process(self):
        super().process()
        # Assert that the constraint attacher processor has already run
        self.must_run_after(ConstraintAttacherProcessor)
        self.must_run_after(ConstraintMacroProcessor, ok_if_not_found=True)
        self.must_run_after(
            PermutationOptimizerProcessor, ok_if_not_found=True
        )
        self.must_run_after(Dataspace2BranchProcessor, ok_if_not_found=True)
        totals = {}

        dim2factors = {
            d: self.spec.problem.instance[d]
            for d in self.spec.problem.shape.dimensions
        }
        dim2factors_unpruned = {k: v for k, v in dim2factors.items()}
        dim2factors_set = {d: [] for d in dim2factors}
        dim2constraints = {d: [] for d in dim2factors}

        dim2factors = defaultdict(lambda: 1, dim2factors)
        dim2factors_set = defaultdict(list, dim2factors_set)
        dim2constraints = defaultdict(list, dim2constraints)

        dim2max = {}

        for c in self.spec.get_nodes_of_type(Iteration):
            for d, op, factor in c.factors.get_split_factors():
                if op == "<=":
                    dim2max[d] = factor
                factor = int(factor)
                if factor == 0:
                    factor = dim2factors[d]
                if factor == -1:
                    continue
                if factor > 1 and dim2factors[d] % factor == 0:
                    dim2factors_set[d].append(factor)
                    dim2constraints[d].append(c)
                elif factor != 1 and factor != 0:
                    self.logger.info(
                        f"Ignoring factor {factor} for dimension {d} in {c}. "
                        f"Does not divide {dim2factors[d]}"
                    )
        for d, factors in dim2factors_set.items():
            for factor in factors:
                dim2factors[d] = dim2factors[d] // factor
        for d, factors in dim2factors.items():
            if d == 0:
                raise ValueError(
                    f"Over-constrainted dimension {d} has no possible mapping."
                    f"Constrainted by: "
                    f"{', '.join(str(c) for c in dim2constraints[d])}"
                )

        dim2factors = {d: get_prime_factors(f) for d, f in dim2factors.items()}
        dim2factors = {d: f for d, f in dim2factors.items() if len(f) >= 1}

        for d, factors in dim2factors.items():
            self.logger.info(f"Factors for mapping {d}: {factors}")

        def factor_permutation_opts(
            x: Iteration, get_unconstrained: bool = False
        ) -> Tuple[int, int]:
            factors = {d: f for d, _, f in x.factors.get_split_factors()}
            n = 1
            unconstrained = set()
            for d, f in dim2factors.items():
                if d in factors:
                    continue  # Constrainted

                max_factor = dim2max.get(d, x.default_max_factor)
                if max_factor is not None:
                    possibilities = [d for d in f if d <= x.default_max_factor]
                else:
                    possibilities = f

                if possibilities == []:
                    continue  # Constrainted

                # Multiply n by the number of unique combinations of factors
                unique2count = {
                    u: possibilities.count(u) for u in set(possibilities)
                }
                n *= math.prod(unique2count.values())
                unconstrained.add(d)

            dims = set(dim2factors_unpruned.keys())
            p = factorial(
                len(dims) - len(dims.intersection(set(x.permutation)))
            )
            return (n, p) if not get_unconstrained else (n, p, unconstrained)

        all_results = []
        for leaf in self.spec.get_nodes_of_type(Leaf):
            results = {
                "Dataspace": 1,
                "Temporal Factors": 1,
                "Temporal Permutation": 1,
                "Spatial Factors": 1,
                "Spatial Permutation": 1,
                "Spatial Split": 1,
                "Temporal Dimensions": "",
                "Spatial Dimensions": "",
            }

            c = leaf.constraints
            if isinstance(leaf, Storage):
                dataspaces = set(
                    d.name for d in self.spec.problem.shape.data_spaces
                )
                dataspaces -= set(c.dataspace.bypass)
                dataspaces -= set(c.dataspace.keep)
                results["Dataspace"] = 2 ** len(dataspaces)

                n, p, s = factor_permutation_opts(c.temporal, True)
                results["Temporal Factorizations"] = n
                results["Temporal Permutations"] = p
                results["Temporal Dimensions"] = "".join(s)

            if leaf.spatial.get_fanout() > 1:
                n, p, s = factor_permutation_opts(c.spatial, True)
                results["Spatial Factorizations"] = n
                results["Spatial Permutations"] = p
                results["Spatial Dimensions"] = "".join(s)

                fanoutX = leaf.spatial.meshX
                fanoutY = leaf.spatial.meshY
                if fanoutX is not None and fanoutX != 1:
                    if fanoutY is not None and fanoutY != 1:
                        if c.spatial.split is not None:
                            results["Spatial Split"] = len(s) + 1

            results["Total"] = math.prod(
                v for v in results.values() if isinstance(v, int)
            )
            results = {k: v for k, v in results.items() if v and v != 1}
            if results:
                all_results.append((leaf, results))
            for k, v in results.items():
                if isinstance(v, int):
                    totals[k] = totals.get(k, 1) * v

        def d2str(x):
            return ", ".join(f"{k}: {v}" for k, v in x.items())

        for r in all_results:
            self.logger.info(f"{r[0].name}: {d2str(r[1])}")
        self.logger.info(f"Total: {d2str(totals)}")
