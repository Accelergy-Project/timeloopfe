from abc import ABC
from numbers import Number
from typing import List, Tuple, Union
from ..parsing.nodes import DictNode, ListNode, Node
from . import constraints
from .sparse_optimizations import SparseOptimizationGroup

BUFFER_CLASSES = ("DRAM", "SRAM", "regfile", "smartbuffer", "storage")
COMPUTE_CLASSES = ("mac", "intmac", "fpmac", "compute")
NETWORK_CLASSES = ("XY_NoC", "Legacy", "ReductionTree", "SimpleMulticast")
NOTHING_CLASSES = ("nothing",)


class ArchNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def name2leaf(self, name: str) -> "Leaf":
        if isinstance(self, Leaf) and getattr(self, "name", None) == name:
            return self
        for element in self if isinstance(self, list) else self.values():
            try:
                return element.name2leaf(name)
            except ValueError:
                pass
        raise ValueError(f"Leaf {name} not found in {self}")

    def name2constraints(self, name: str) -> "constraints.ConstraintGroup":
        return self.name2leaf(name).constraints


class ArchNodes(ArchNode, ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "!Element",
            (Storage, Network, Compute, Nothing, Element),
            callfunc=element_factory,
        )
        super().init_elem("!Container", Container)
        super().init_elem("!Hierarchical", Hierarchical)
        super().init_elem("!Parallel", Parallel)
        super().init_elem("!Pipelined", Pipelined)
        super().init_elem("!Nothing", Nothing)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"


class Branch(ArchNode, DictNode, ABC):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("nodes", ArchNodes, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nodes: ArchNodes = self["nodes"]


class Hierarchical(Branch):
    pass


class Parallel(Branch):
    pass


class Pipelined(Branch):
    pass


class Architecture(Hierarchical):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("version", (str, Number))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: Union[str, Number] = self["version"]


class Leaf(ArchNode, DictNode, ABC):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str)
        # Class named _class to avoid clashing with class keyword
        super().init_elem("attributes", Attributes, {})
        super().init_elem("spatial", Spatial, {})
        super().init_elem("constraints", constraints.ConstraintGroup, {})
        super().init_elem("sparse_optimizations", SparseOptimizationGroup, {})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.attributes: Attributes = self["attributes"]
        self.spatial: Spatial = self["spatial"]
        self.constraints: constraints.ConstraintGroup = self["constraints"]
        self.sparse_optimizations: SparseOptimizationGroup = self[
            "sparse_optimizations"
        ]


class Element(Leaf, ABC):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("class", str)
        super().init_elem("subclass", str, None)
        super().init_elem("required_actions", list, [])
        super().init_elem("area_share", Number, None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._class: str = self["class"]
        self.subclass: str = self["subclass"]
        self.required_actions: List[str] = self["required_actions"]
        self.area_share: float = self["area_share"]


class Container(Leaf, ABC):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("networks", Networks, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.networks: Networks = self["networks"]


class Networks(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", Network)


class Storage(Element):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("attributes", StorageAttributes, {})

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.attributes: StorageAttributes = self["attributes"]


class Compute(Element):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class Network(Element):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class Spatial(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("meshX", (int, str), 1)
        super().init_elem("meshY", (int, str), 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.meshX: Union[int, str] = self["meshX"]
        self.meshY: Union[int, str] = self["meshY"]

    def validate_fanout(self):
        for target in ["meshX", "meshY"]:
            v = self[target]
            assert int(v) == v, f"{target} must be an integer, but is {v}"
            assert v > 0, f"{target} must be positive, but is {v}"

    def get_fanout(self):
        return self.meshX * self.meshY

    def to_fanout_string(self):
        return f"[1..{self.get_fanout()}]"


class Attributes(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", part_name_match=True, no_change_key=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StorageAttributes(Attributes):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("datawidth", (str, int))
        super().init_elem("technology", (str, int), None)
        super().init_elem("n_banks", (str, int), 2)
        super().init_elem("block_size", (str, int), None)
        super().init_elem("cluster_size", (str, int), 1)
        super().init_elem("width", (str, int), None)
        super().init_elem("depth", (str, int), None)
        super().init_elem("entries", (str, int), None)
        super().init_elem("sizeKB", (str, int), None)
        super().init_elem("reduction_supported", (str, bool), True)
        super().init_elem("multiple_buffering", (str, Number), 1)
        super().init_elem("min_utilization", (str, Number), 0)
        # Bandwidth and latency
        super().init_elem("shared_bandwidth", (str, Number), None)
        super().init_elem("read_bandwidth", (str, Number), None)
        super().init_elem("write_bandwidth", (str, Number), None)
        super().init_elem("network_fill_latency", (str, int), None)
        super().init_elem("network_drain_latency", (str, int), None)
        # Overbooking
        super().init_elem("allow_overbooking", (str, bool), False)
        # Sparse optimization
        super().init_elem("metadata_block_size", (str, int), None)
        super().init_elem("metadata_datawidth", (str, int), None)
        super().init_elem("metadata_storage_width", (str, int), None)
        super().init_elem("metadata_storage_depth", (str, int), None)
        super().init_elem(
            "concordant_compressed_tile_traversal", (str, bool), None
        )
        super().init_elem("tile_partition_supported", (str, bool), None)
        super().init_elem("decompression_supported", (str, bool), None)
        super().init_elem("compression_supported", (str, bool), None)

        super().require_one_of("entries", "sizeKB", "depth")
        super().require_one_of("block_size", "cluster_size")
        super().require_all_or_none_of(
            "metadata_block_size",
            "metadata_datawidth",
            "metadata_storage_width",
            "metadata_storage_depth",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datawidth: Union[str, int] = self["datawidth"]
        self.technology: Union[str, int] = self["technology"]
        self.n_banks: Union[str, int] = self["n_banks"]
        self.block_size: Union[str, Number] = self["block_size"]
        self.cluster_size: Union[str, Number] = self["cluster_size"]
        self.depth: Union[str, Number] = self["depth"]
        self.entries: Union[str, Number] = self["entries"]
        self.sizeKB: Union[str, Number] = self["sizeKB"]
        self.reduction_supported: Union[str, bool] = self[
            "reduction_supported"
        ]
        self.multiple_buffering: Union[str, Number] = self[
            "multiple_buffering"
        ]
        self.min_utilization: Union[str, Number] = self["min_utilization"]
        self.shared_bandwidth: Union[str, Number] = self["shared_bandwidth"]
        self.read_bandwidth: Union[str, Number] = self["read_bandwidth"]
        self.write_bandwidth: Union[str, Number] = self["write_bandwidth"]
        self.network_fill_latency: Union[str, int] = self[
            "network_fill_latency"
        ]
        self.network_drain_latency: Union[str, int] = self[
            "network_drain_latency"
        ]
        self.allow_overbooking: Union[str, bool] = self["allow_overbooking"]
        self.metadata_block_size: Union[str, int] = self["metadata_block_size"]
        self.metadata_datawidth: Union[str, int] = self["metadata_datawidth"]
        self.metadata_storage_width: Union[str, int] = self[
            "metadata_storage_width"
        ]
        self.metadata_storage_depth: Union[str, int] = self[
            "metadata_storage_depth"
        ]
        self.concordant_compressed_tile_traversal: Union[str, bool] = self[
            "concordant_compressed_tile_traversal"
        ]
        self.tile_partition_supported: Union[str, bool] = self[
            "tile_partition_supported"
        ]
        self.decompression_supported: Union[str, bool] = self[
            "decompression_supported"
        ]
        self.compression_supported: Union[str, bool] = self[
            "compression_supported"
        ]


class Nothing(Element):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = "nothing"
        if "class" not in kwargs:
            kwargs["class"] = "nothing"
        super().__init__(self, *args, **kwargs)


def element_factory(*args, **kwargs) -> "Element":
    all_args = list(args) + ([kwargs] if kwargs else [])
    f = "Pass either a dictionary or keyword arguments, but not both."
    if len(all_args) > 1:
        raise TypeError(f"Too many arguments given to element_factory(). {f}")
    if len(all_args) == 0:
        raise TypeError(f"No dictionary given to element_factory(). {f}")
    if not isinstance(all_args[0], dict):
        raise TypeError(f"No dictionary given to element_factory(). {f}")

    kwargs = all_args[0]
    assert "class" in kwargs, f"Element missing 'class' attribute."
    assert isinstance(
        kwargs.get("class", None), str
    ), f'Element "class" attribute must be a string. Got {kwargs["class"]}'
    element_class = kwargs["class"]
    class2class = {
        BUFFER_CLASSES: Storage,
        COMPUTE_CLASSES: Compute,
        NETWORK_CLASSES: Network,
        NOTHING_CLASSES: Nothing,
    }

    for c, target in class2class.items():
        if any([e in element_class for e in c]):
            return target(**kwargs)

    raise ValueError(
        f"Unknown element class {element_class}. "
        f"Accepted classes: {class2class}"
    )


def dummy_storage(name: str) -> "Storage":
    attrs = {"width": 1, "depth": 1, "datawidth": 1, "technology": -1}
    args = {"name": name, "class": "dummy_storage", "attributes": attrs}
    return element_factory(**args)


Attributes.init_elems()
Spatial.init_elems()
Element.init_elems()
Storage.init_elems()
Compute.init_elems()
Network.init_elems()
Container.init_elems()
ArchNodes.init_elems()
Hierarchical.init_elems()
Parallel.init_elems()
Pipelined.init_elems()
Architecture.init_elems()
Leaf.init_elems()
Networks.init_elems()
Branch.init_elems()
Nothing.init_elems()
StorageAttributes.init_elems()
