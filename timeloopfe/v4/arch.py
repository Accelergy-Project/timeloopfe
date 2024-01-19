from abc import ABC
from logging import Logger
from numbers import Number
from typing import Any, Dict, List, Optional, Tuple, Union
from ..common.nodes import DictNode, ListNode, Node
from . import constraints
from .sparse_optimizations import SparseOptimizationGroup
from .version import assert_version

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
            except (AttributeError, ValueError):
                pass
        raise ValueError(f"Leaf {name} not found in {self}")

    def find(self, *args, **kwargs) -> "Leaf":
        return self.name2leaf(*args, **kwargs)

    def name2constraints(self, name: str) -> "constraints.ConstraintGroup":
        return self.name2leaf(name).constraints


class ArchNodes(ArchNode, ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr(
            "!Component",
            (Storage, Network, Compute, Nothing, Component),
            callfunc=component_factory,
        )
        super().add_attr("!Container", Container)
        super().add_attr("!Hierarchical", Hierarchical)
        super().add_attr("!Parallel", Parallel)
        super().add_attr("!Pipelined", Pipelined)
        super().add_attr("!Nothing", Nothing)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def combine(self, other: "ArchNodes") -> "ArchNodes":
        return ArchNodes(self + other)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def parse_expressions(
        self,
        symbol_table: Optional[Dict[str, Any]] = None,
        parsed_ids: Optional[set] = None,
    ):
        n_symbol_table = {} if symbol_table is None else symbol_table.copy()
        for l in self.get_nodes_of_type(Leaf):
            n_symbol_table[l.name] = l

        def callfunc(x, sym_table):
            if isinstance(x, Container) and not sym_table.get("_in_parallel", False):
                sym_table.setdefault("_parent_container_attributes", {})
                sym_table.update(x.attributes)
            return x

        return super().parse_expressions(n_symbol_table, parsed_ids, callfunc)


class Branch(ArchNode, DictNode, ABC):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("nodes", ArchNodes, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nodes: ArchNodes = self["nodes"]

    def parse_expressions(
        self,
        symbol_table: Optional[Dict[str, Any]] = None,
        parsed_ids: Optional[set] = None,
    ):
        n_symbol_table = {} if symbol_table is None else symbol_table.copy()
        n_symbol_table["_in_parallel"] = isinstance(self, Parallel)
        return super().parse_expressions(symbol_table, parsed_ids)


class Hierarchical(Branch):
    pass


class Parallel(Branch):
    pass


class Pipelined(Branch):
    pass


class Architecture(Hierarchical):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("version", callfunc=assert_version)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: Union[str, Number] = self["version"]

    def combine(self, other: "Architecture") -> "Architecture":
        self.logger.warning(
            "Multiple architectures found. Appending the nodes from one arch "
            "to the other. Ignore this warning if this was intended."
        )
        self.nodes += other.nodes
        return self


class Leaf(ArchNode, DictNode, ABC):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str)
        # Class named _class to avoid clashing with class keyword
        super().add_attr("attributes", Attributes, {})
        super().add_attr("spatial", Spatial, {})
        super().add_attr("constraints", constraints.ConstraintGroup, {})
        super().add_attr("sparse_optimizations", SparseOptimizationGroup, {})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.attributes: Attributes = self["attributes"]
        self.spatial: Spatial = self["spatial"]
        self.constraints: constraints.ConstraintGroup = self["constraints"]
        self.sparse_optimizations: SparseOptimizationGroup = self[
            "sparse_optimizations"
        ]

    def parse_expressions(
        self,
        symbol_table: Optional[Dict[str, Any]] = None,
        parsed_ids: Optional[set] = None,
    ):
        n_symbol_table = {} if symbol_table is None else symbol_table.copy()

        def callfunc(x, sym_table):
            # Fill the attributes with the parent attributes
            sym_table["attributes"] = {
                **sym_table.get("_parent_container_attributes", {}),
                **sym_table.get("attributes", {}),
            }
            return x

        callfunc(None, n_symbol_table)
        super().parse_expressions(n_symbol_table, parsed_ids)
        return self.attributes


class Component(Leaf, ABC):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("class", str)
        super().add_attr("subclass", str, None)
        super().add_attr("required_actions", list, [])
        super().add_attr("area_share", Number, None)
        super().add_attr("enabled", bool, True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._class: str = self["class"]
        self.subclass: str = self["subclass"]
        self.required_actions: List[str] = self["required_actions"]
        self.area_share: float = self["area_share"]
        self.enabled: bool = self["enabled"]

    def _check_unrecognized(self, *args, **kwargs):
        return super()._check_unrecognized(*args, **kwargs)


class Container(Leaf, ABC):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("networks", Networks, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.networks: Networks = self["networks"]


class Networks(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", Network)


class Storage(Component):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("attributes", StorageAttributes, {})

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.attributes: StorageAttributes = self["attributes"]


class Compute(Component):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class Network(Component):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class Spatial(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("meshX", (int), 1)
        super().add_attr("meshY", (int), 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.meshX: int = self["meshX"]
        self.meshY: int = self["meshY"]

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
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("has_power_gating", (str, bool), False)
        super().add_attr("", part_name_match=True, no_change_key=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_parse = True


class StorageAttributes(Attributes):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("datawidth", (str, int))
        super().add_attr("technology", (str, int), None)
        super().add_attr("n_banks", (str, int), 2)
        super().add_attr("block_size", (str, int), None)
        super().add_attr("cluster_size", (str, int), 1)
        super().add_attr("width", (str, int), None)
        super().add_attr("depth", (str, int), None)
        super().add_attr("entries", (str, int), None)
        super().add_attr("sizeKB", (str, int), None)
        super().add_attr("reduction_supported", (str, bool), True)
        super().add_attr("multiple_buffering", (str, Number), 1)
        super().add_attr("min_utilization", (str, Number), 0)
        # Bandwidth and latency
        super().add_attr("shared_bandwidth", (str, Number), None)
        super().add_attr("read_bandwidth", (str, Number), None)
        super().add_attr("write_bandwidth", (str, Number), None)
        super().add_attr("network_fill_latency", (str, int), None)
        super().add_attr("network_drain_latency", (str, int), None)
        super().add_attr("per_dataspace_bandwidth_consumption_scale", dict, {})
        # Overbooking
        super().add_attr("allow_overbooking", (str, bool), False)
        # Sparse optimization
        super().add_attr("metadata_block_size", (str, int), None)
        super().add_attr("metadata_datawidth", (str, int), None)
        super().add_attr("metadata_storage_width", (str, int), None)
        super().add_attr("metadata_storage_depth", (str, int), None)
        super().add_attr("concordant_compressed_tile_traversal", (str, bool), None)
        super().add_attr("tile_partition_supported", (str, bool), None)
        super().add_attr("decompression_supported", (str, bool), None)
        super().add_attr("compression_supported", (str, bool), None)

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
        self.reduction_supported: Union[str, bool] = self["reduction_supported"]
        self.multiple_buffering: Union[str, Number] = self["multiple_buffering"]
        self.min_utilization: Union[str, Number] = self["min_utilization"]
        self.shared_bandwidth: Union[str, Number] = self["shared_bandwidth"]
        self.read_bandwidth: Union[str, Number] = self["read_bandwidth"]
        self.write_bandwidth: Union[str, Number] = self["write_bandwidth"]
        self.network_fill_latency: Union[str, int] = self["network_fill_latency"]
        self.network_drain_latency: Union[str, int] = self["network_drain_latency"]
        self.allow_overbooking: Union[str, bool] = self["allow_overbooking"]
        self.metadata_block_size: Union[str, int] = self["metadata_block_size"]
        self.metadata_datawidth: Union[str, int] = self["metadata_datawidth"]
        self.metadata_storage_width: Union[str, int] = self["metadata_storage_width"]
        self.metadata_storage_depth: Union[str, int] = self["metadata_storage_depth"]
        self.concordant_compressed_tile_traversal: Union[str, bool] = self[
            "concordant_compressed_tile_traversal"
        ]
        self.tile_partition_supported: Union[str, bool] = self[
            "tile_partition_supported"
        ]
        self.decompression_supported: Union[str, bool] = self["decompression_supported"]
        self.compression_supported: Union[str, bool] = self["compression_supported"]


class Nothing(Component):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = "nothing"
        if "class" not in kwargs:
            kwargs["class"] = "nothing"
        super().__init__(self, *args, **kwargs)


def component_factory(*args, **kwargs) -> "Component":
    all_args = list(args) + ([kwargs] if kwargs else [])
    f = "Pass either a dictionary or keyword arguments, but not both."
    if len(all_args) > 1:
        raise TypeError(f"Too many arguments given to component_factory(). {f}")
    if len(all_args) == 0:
        raise TypeError(f"No dictionary given to component_factory(). {f}")
    if not isinstance(all_args[0], dict):
        raise TypeError(f"No dictionary given to component_factory(). {f}")

    kwargs = all_args[0]
    assert "class" in kwargs, f"Component missing 'class' attribute."
    assert isinstance(
        kwargs.get("class", None), str
    ), f'Component "class" attribute must be a string. Got {kwargs["class"]}'
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
        f"Unknown element class {element_class}. " f"Accepted classes: {class2class}"
    )


def dummy_storage(name: str) -> "Storage":
    attrs = {"width": 1, "depth": 1, "datawidth": 1, "technology": -1}
    args = {"name": name, "class": "dummy_storage", "attributes": attrs}
    return component_factory(**args)


Attributes.declare_attrs()
Spatial.declare_attrs()
Component.declare_attrs()
Storage.declare_attrs()
Compute.declare_attrs()
Network.declare_attrs()
Container.declare_attrs()
ArchNodes.declare_attrs()
Hierarchical.declare_attrs()
Parallel.declare_attrs()
Pipelined.declare_attrs()
Architecture.declare_attrs()
Leaf.declare_attrs()
Networks.declare_attrs()
Branch.declare_attrs()
Nothing.declare_attrs()
StorageAttributes.declare_attrs()
