from numbers import Number
from ..parsing.nodes import ListNode, DictNode


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

    def name2dataspaces(self, name: str) -> "DataSpace":
        for ds in self.data_spaces:
            if ds.name == name:
                return ds
        raise ValueError(f"Data space {name} not found")


class ProblemDataspaceList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", DataSpace)


class Instance(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("densities", DensityList, {})
        super().init_elem(
            "", (int, str), part_name_match=True, no_change_key=True
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DataSpace(DictNode):
    @classmethod
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
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "", Density, part_name_match=True, no_change_key=True
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Density(DictNode):
    @classmethod
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
