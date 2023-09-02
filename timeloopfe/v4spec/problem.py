from numbers import Number
from ..parsing.nodes import ListNode, DictNode
from typing import List, Set, Union


class Problem(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("instance", Instance)
        super().init_elem("shape", Shape)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance: Instance = self["instance"]
        self.shape: Shape = self["shape"]


class Shape(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str, "")
        super().init_elem("dimensions", ListNode)
        super().init_elem("data_spaces", ProblemDataspaceList)
        super().init_elem("coefficients", ListNode, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.dimensions: ListNode = self["dimensions"]
        self.data_spaces: DataSpace = self["data_spaces"]
        self.coefficients: ListNode = self["coefficients"]

    def name2dataspace(self, name: Union[str, List[str]]) -> Union["DataSpace", List["DataSpace"]]:
        if isinstance(name, List):
            return [self.name2dataspace(n) for n in name]
        if isinstance(name, DataSpace):
            return name
        for ds in self.data_spaces:
            if ds.name == name:
                return ds
        raise ValueError(f"Data space {name} not found")

    def dataspace2dims(self, name: Union[str, List[str]]) -> List[str]:
        ds = self.name2dataspace(name)
        factors = set()
        dimensions = set(self.dimensions)
        for d in (ds if isinstance(ds, list) else [ds]):
            factors.update(set(d.factors) & dimensions)
        return list(factors)

    def dataspace2unique_dims(self, name: str) -> List[str]:
        ds = self.name2dataspace(name)
        ds = ds if isinstance(ds, list) else [ds]
        other_ds = [d for d in self.data_spaces if d not in ds]
        return list(
            set(self.dataspace2dims(name)) - set(self.dataspace2dims(other_ds))
        )


class ProblemDataspaceList(ListNode):
    @ classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", DataSpace)


class Instance(DictNode):
    @ classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("densities", DensityList, {})
        super().init_elem(
            "", (int, str), part_name_match=True, no_change_key=True
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DataSpace(DictNode):
    @ classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str)
        super().init_elem("projection", list)
        super().init_elem("read_write", (str, bool, int), False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name: str = self["name"]
        self.projection: list = self["projection"]
        self.factors: list = []

        projection = [x for x in self.projection]
        while projection:
            factor = projection.pop(0)
            if isinstance(factor, list):
                projection += factor
            else:
                self.factors.append(factor)


class DensityList(DictNode):
    @ classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "", Density, part_name_match=True, no_change_key=True
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Density(DictNode):
    @ classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("density", (Number, str))
        super().init_elem(
            "distribution",
            ("fixed_structured", "hypergeometric", "banded"),
        )
        super().init_elem("band_width", int, 0)  # Banded
        super().init_elem("workload_tensor_size", int, 0)  # Hypergeometric

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.density: Number = self["density"]
        self.distribution: str = self["distribution"]


Problem.init_elems()
Shape.init_elems()
Instance.init_elems()
DataSpace.init_elems()
ProblemDataspaceList.init_elems()
DensityList.init_elems()
Density.init_elems()
