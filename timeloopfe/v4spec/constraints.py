import logging
from typing import Iterable, List, Optional, Tuple, Type, Union
from ..parsing.nodes import DictNode, ListNode, isempty, CombineableListNode
import timeloopfe.v4spec.problem as problem
import copy


def dummy_constraints(
    prob: problem.Problem, create_spatial_constraint: bool = False
) -> "ConstraintGroup":
    c = ConstraintGroup()
    c.temporal = Temporal(
        factors=list(f"{x}=1" for x in prob.shape.dimensions),
        permutation=copy.deepcopy(prob.shape.dimensions),
    )
    c.dataspace = Dataspace(bypass=[x.name for x in prob.shape.data_spaces])
    if create_spatial_constraint:
        c.spatial = Spatial(
            factors=c.temporal.factors,
            permutation=c.temporal.permutation,
        )
    return c


def constraint_factory(constraint: dict):
    if "type" not in constraint:
        raise ValueError("Constraint must have a type")
    ctype = constraint["type"]
    type2class = {
        "spatial": Spatial,
        "temporal": Temporal,
        "dataspace": Dataspace,
        "max_overbooked_proportion": MaxOverbookedProportion,
        "utilization": Utilization,
        # Legacy
        # "dataspace": Dataspace,
        # "bypassing": Dataspace,
        # "bypass": Dataspace,
        # "datatype": Dataspace,
    }
    if ctype not in type2class:
        raise ValueError(
            f"Constraint type '{ctype}' not recognized."
            f"Must be one of {list(type2class.keys())}"
        )
    return type2class[ctype](**constraint)


class Constraints(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("targets", ConstraintsList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.targets: ConstraintsList = self["targets"]


class ConstraintsList(CombineableListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "",
            (Spatial, Temporal, Dataspace, MaxOverbookedProportion),
            callfunc=constraint_factory,
        )


class Constraint(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("type", str, "")
        super().init_elem("target", str, "")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: str = self["type"]
        self.target: str = self["target"]
        self._disjoint_dataspaces_lists = []

    def isempty(self):
        return all(
            isempty(v) for k, v in self.items() if k not in ["type", "target"]
        )

    def clear_respecification(
        self, other: "Constraint", mine: dict, others: dict
    ):
        overlapping = set(mine.keys()) & set(others.keys())
        overlapping_not_equal = {k: mine[k] != others[k] for k in overlapping}
        problems = [
            f"{k}={mine[k]} AND {k}={others[k]}"
            for k, v in overlapping_not_equal.items()
            if v
        ]

        if problems:
            raise ValueError(
                f"Re-specification of {problems} in two "
                f"{self.__class__.__name__} constraints:\n{self}\nand {other}."
            )
        return mine, others

    def list_attrs_to_dict(self, attrs: List[str]) -> dict:
        flattened = {}
        for a in attrs:
            for k in self.get(a, []):
                if k in flattened and flattened[k] != a:
                    raise ValueError(
                        f"Re-specification of {k} found in {attrs} for "
                        f"constraint {self.__class__.__name__}."
                    )
                flattened[k] = a
        return flattened

    def set_list_attrs_from_dict(
        self, d: dict, attrs: Iterable[str] = (), cast_to_type: Type = list
    ) -> dict:
        lists = {k: cast_to_type() for k in attrs}
        for k, v in d.items():
            lists.setdefault(v, []).append(k)
        self.update(lists)

    def combine_list_attrs(
        self, other: "Constraint", attrs: List[str]
    ) -> "Constraint":
        if attrs[0] in self:
            mytype = type(self[attrs[0]])
        elif attrs[0] in other:
            mytype = type(other[attrs[0]])
        else:
            return self
        mine = self.list_attrs_to_dict(attrs)
        others = other.list_attrs_to_dict(attrs)
        a, b = self.clear_respecification(other, mine, others)
        self.set_list_attrs_from_dict({**a, **b}, attrs, mytype)
        other.set_list_attrs_from_dict({}, attrs, mytype)
        return self

    def combine(self, other: "Constraint") -> "Constraint":  # Override
        if self.type != other.type:
            raise ValueError("Cannot combine constraints of different types.")
        for ds in self._disjoint_dataspaces_lists:
            self.combine_list_attrs(other, ds)
        return super().combine(other)

    def __str__(self):
        return (
            f"{self.type} constraint(target={self.target}) {super().__str__()}"
        )


class ConstraintGroup(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("spatial", Spatial, {})
        super().init_elem("temporal", Temporal, {})
        super().init_elem("dataspace", Dataspace, {})
        super().init_elem(
            "max_overbooked_proportion", MaxOverbookedProportion, {}
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spatial: Spatial = self["spatial"]
        self.temporal: Temporal = self["temporal"]
        self.dataspace: Dataspace = self["dataspace"]
        self.max_overbooked_proportion: MaxOverbookedProportion = self[
            "max_overbooked_proportion"
        ]


class Iteration(Constraint):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("factors", Factors, [], Factors.factory)
        super().init_elem("permutation", Permutation, [], Permutation.factory)
        super().init_elem("default_max_factor", int, None)
        super().init_elem("remainders", str, None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.factors: Factors = self["factors"]
        self.permutation: Permutation = self["permutation"]
        self.default_max_factor: Optional[int] = self["default_max_factor"]
        self.remainders: str = self["remainders"]


class Spatial(Iteration):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "no_multicast_no_reduction", ProblemDataspaceList, []
        )
        super().init_elem("no_link_transfer", ProblemDataspaceList, [])
        super().init_elem("split", int, None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: str = "spatial"
        self.no_multicast_no_reduction: List[str] = self[
            "no_multicast_no_reduction"
        ]
        self.no_link_transfer: List[str] = self["no_link_transfer"]
        self.split: int = self["split"]
        self._disjoint_dataspaces_lists.append(("no_multicast_no_reduction",))
        self._disjoint_dataspaces_lists.append(("no_link_transfer",))


class Temporal(Iteration):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("no_temporal_reuse", ProblemDataspaceList, [])
        super().init_elem("rmw_on_first_writeback", ProblemDataspaceList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: str = "temporal"
        self.no_temporal_reuse: List[str] = self["no_temporal_reuse"]
        self.rmw_on_first_writeback: List[str] = self["rmw_on_first_writeback"]
        self._disjoint_dataspaces_lists.append(("no_temporal_reuse",))


class Dataspace(Constraint):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("bypass", ProblemDataspaceList, [])
        super().init_elem("keep", ProblemDataspaceList, [])
        super().init_elem("passthrough", ProblemDataspaceList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: str = "dataspace"
        self.bypass: List[str] = self["bypass"]
        self.keep: List[str] = self["keep"]
        self.passthrough: List[str] = self["passthrough"]
        self._disjoint_dataspaces_lists.append(("bypass", "keep"))


class MaxOverbookedProportion(Constraint):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("proportion", float, None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: str = "max_overbooked_proportion"
        self.proportion: Optional[float] = self["proportion"]


class Utilization(Constraint):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("min", (float, str), None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: str = "utilization"


class Permutation(ListNode):
    @staticmethod
    def factory(x: Union[str, list]) -> "Permutation":
        if isinstance(x, str):
            logging.warning(
                'Permutation given as string "%s". Trying to turn into a '
                "list.",
                str(x),
            )
            if "," in x:
                x = x.split(",")
            else:
                x = [y for y in x]
            x = [y.strip() for y in x if y]
        return Permutation(x)

    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)


class Factors(CombineableListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)

    @staticmethod
    def factory(x: Union[str, list]) -> "Factors":
        if isinstance(x, str):
            logging.warning(
                'Factors given as string "%s". Trying to turn into a list.',
                str(x),
            )
            if "," in x:
                x = x.split(",")
            elif " " in x:
                x = x.split(" ")
            else:
                x = [x]

        x = [
            "".join(y.strip() for y in Factors.splitfactor(x)) for x in x if x
        ]

        return Factors(x)

    @staticmethod
    def splitfactor(x: str) -> Tuple[str, str, str]:
        if "<=" in x:
            a, c = x.split("<=")
            return a, "<=", c
        elif "=" in x:
            a, c = x.split("=")
            return a, "=", c
        else:
            raise ValueError(
                f'Did not find an "=" or "<=" in factor "{x}".'
                f'Format each factor as "X=123" or "X<=123". Multiple factors '
                f"may be given as a comma-separated string, a space-separated "
                f"string, or a list of strings."
            )

    def get_split_factors(self) -> List[Tuple[str, str, str]]:
        return [self.splitfactor(x) for x in self]

    def get_factor_names(self) -> List[str]:
        return [self.splitfactor(x)[0] for x in self]

    def add_equal_factor(self, name: str, value: int):
        self.append(f"{name}={value}")
        self.check_unique_remove_repeat()

    def add_leq_factor(self, name: str, value: int):
        self.append(f"{name}<={value}")
        self.check_unique_remove_repeat()

    def check_unique_remove_repeat(self):
        unique = set()
        # Identical factors OK
        for i in range(len(self) - 1, -1, -1):
            if self[i] in unique:
                self.pop(i)
            unique.add(self[i])

        # Non-identical, but same name, not OK
        factor2val = {}
        for f in self:
            name, _, _ = self.splitfactor(f)
            if name in factor2val:
                raise ValueError(
                    f"Found two constraints {f} and {factor2val[name]} for "
                    f"the same variable {name} in {self}."
                )
            factor2val[name] = f

    def combine(self, other: "Factors") -> "Factors":
        super().combine(other)
        self.check_unique_remove_repeat()
        return self

    def get_minimum_product(self):
        """!@brief Get the product of all factors in this list."""
        allocated = 1
        for f in self:
            _, comparator, value = self.splitfactor(f)
            if comparator == "=" and int(value):
                allocated *= int(value)
        return allocated

    def add_eq_factor_iff_not_exists(self, name: str, value: int) -> bool:
        """!@brief Add an "name=value" factor iff "name" is not already in the
        factor list. Return True if the factor was added."""
        if name not in self.get_factor_names():
            self.add_equal_factor(name, value)
            return True
        return False

    def add_leq_factor_iff_not_exists(self, name: str, value: int) -> bool:
        """!@brief Add an "name<=value" factor iff "name" is not already in the
        factor list. Return True if the factor was added."""
        if name not in self.get_factor_names():
            self.add_leq_factor(name, value)
            return True
        return False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_unique_remove_repeat()


class ProblemDataspaceList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", str)


Constraints.init_elems()
Constraint.init_elems()
ConstraintGroup.init_elems()
Iteration.init_elems()
Spatial.init_elems()
Temporal.init_elems()
Dataspace.init_elems()
MaxOverbookedProportion.init_elems()
ConstraintsList.init_elems()
Factors.init_elems()
Utilization.init_elems()
Permutation.init_elems()
ProblemDataspaceList.init_elems()
