from numbers import Number
from ..common.nodes import ListNode, DictNode
from typing import List, Set, Union
from .version import assert_version


class Problem(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("version", callfunc=assert_version)
        super().add_attr("instance", Instance)
        super().add_attr("shape", Shape)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: str = self["version"]
        self.instance: Instance = self["instance"]
        self.shape: Shape = self["shape"]


class Shape(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str, "")
        super().add_attr("dimensions", ListNode)
        super().add_attr("data_spaces", ProblemDataspaceList)
        super().add_attr("coefficients", ListNode, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.dimensions: ListNode = self["dimensions"]
        self.data_spaces: DataSpace = self["data_spaces"]
        self.coefficients: ListNode = self["coefficients"]

    def name2dataspace(
        self, name: Union[str, List[str]]
    ) -> Union["DataSpace", List["DataSpace"]]:
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
        for d in ds if isinstance(ds, list) else [ds]:
            factors.update(set(d.factors) & dimensions)
        return list(factors)

    def dataspace2unique_dims(self, name: str) -> List[str]:
        ds = self.name2dataspace(name)
        ds = ds if isinstance(ds, list) else [ds]
        other_ds = [d for d in self.data_spaces if d not in ds]
        return list(set(self.dataspace2dims(name)) - set(self.dataspace2dims(other_ds)))


class ProblemDataspaceList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", DataSpace)


class Instance(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("densities", DensityList, {})
        super().add_attr("", int, part_name_match=True, no_change_key=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DataSpace(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str)
        super().add_attr("projection", list)
        super().add_attr("read_write", (str, bool, int), False)

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
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", Density, part_name_match=True, no_change_key=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Density(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("density", (Number, str))
        super().add_attr(
            "distribution",
            ("fixed_structured", "hypergeometric", "banded"),
        )
        super().add_attr("band_width", int, 0)  # Banded
        super().add_attr("workload_tensor_size", int, 0)  # Hypergeometric

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.density: Number = self["density"]
        self.distribution: str = self["distribution"]


Problem.declare_attrs()
Shape.declare_attrs()
Instance.declare_attrs()
DataSpace.declare_attrs()
ProblemDataspaceList.declare_attrs()
DensityList.declare_attrs()
Density.declare_attrs()
