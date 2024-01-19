from typing import List, Optional

from ..common.nodes import DictNode, ListNode, isempty
from .version import assert_version


class SparseOptimizations(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("version", callfunc=assert_version)
        super().add_attr("targets", SparseOptimizationsList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: str = self["version"]
        self.targets: SparseOptimizationsList = self["targets"]


class SparseOptimizationsList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", SparseOptimizationGroup)


class SparseOptimizationGroup(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("target", str, None)
        super().add_attr("action_optimization", ActionOptimizationList, [])
        super().add_attr("representation_format", RepresentationFormat, {})
        super().add_attr("compute_optimization", ComputeOptimization, {})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target: str = self["target"]
        self.action_optimization: ActionOptimization = self["action_optimization"]
        self.representation_format: RepresentationFormat = self["representation_format"]
        self.compute_optimization: ComputeOptimization = self["compute_optimization"]

    def isempty(self) -> bool:
        return (
            isempty(self.get("action_optimization", None))
            and isempty(self.get("representation_format", None))
            and isempty(self.get("compute_optimization", None))
        )


class RepresentationFormat(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("data_spaces", RepresentationProblemDataspaceList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_spaces: RepresentationProblemDataspaceList = self["data_spaces"]


class RepresentationProblemDataspaceList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", RepresentationDataSpace)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RepresentationDataSpace(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str)
        super().add_attr("ranks", RepresentationRankList)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target: str = self["name"]
        self.ranks: RepresentationRankList = self["ranks"]


class RepresentationRankList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", RepresentationRank)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranks: List[RepresentationRank] = self


class RepresentationRank(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("format", ("CP", "B", "RLE", "UOP"))
        super().add_attr("metadata_word_bits", int, None)
        super().add_attr("payload_word_bits", int, None)
        super().add_attr("flattened_rankIDs", (list), None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format: str = self["format"]
        self.metadata_word_bits: Optional[int] = self["metadata_word_bits"]
        self.flattened_rankIDs: list = self["flattened_rankIDs"]


class ActionOptimizationList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", ActionOptimization)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ComputeOptimization(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("type", ("gating", "skipping"), None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ActionOptimization(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("type", ("gating", "skipping", "spatial_skipping"))
        super().add_attr("options", ActionOptimizationOptionList)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: str = self["type"]


class ActionOptimizationOptionList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", ActionOptimizationOption)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ActionOptimizationOption(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("target", str)
        super().add_attr("condition_on", list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target: str = self["target"]
        self.condition_on: list = self["condition_on"]


SparseOptimizationGroup.declare_attrs()
RepresentationRankList.declare_attrs()
RepresentationProblemDataspaceList.declare_attrs()
RepresentationFormat.declare_attrs()
RepresentationDataSpace.declare_attrs()
RepresentationRank.declare_attrs()
ActionOptimizationList.declare_attrs()
ActionOptimization.declare_attrs()
ActionOptimizationOptionList.declare_attrs()
ActionOptimizationOption.declare_attrs()
SparseOptimizations.declare_attrs()
SparseOptimizationsList.declare_attrs()
ComputeOptimization.declare_attrs()
