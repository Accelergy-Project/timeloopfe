from typing import List, Optional

from ..parsing.nodes import DictNode, ListNode, isempty


class SparseOptimizations(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("targets", SparseOptimizationsList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.targets: SparseOptimizationsList = self["targets"]


class SparseOptimizationsList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", SparseOptimizationGroup)


class SparseOptimizationGroup(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("target", str, None)
        super().init_elem("action_optimization", ActionOptimizationList, [])
        super().init_elem("representation_format", RepresentationFormat, {})
        super().init_elem("compute_optimization", ComputeOptimization, {})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target: str = self["target"]
        self.action_optimization: ActionOptimization = self[
            "action_optimization"
        ]
        self.representation_format: RepresentationFormat = self[
            "representation_format"
        ]
        self.compute_optimization: ComputeOptimization = self[
            "compute_optimization"
        ]

    def isempty(self) -> bool:
        return (
            isempty(self.get("action_optimization", None))
            and isempty(self.get("representation_format", None))
            and isempty(self.get("compute_optimization", None))
        )


class RepresentationFormat(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "data_spaces", RepresentationProblemDataspaceList, []
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_spaces: RepresentationProblemDataspaceList = self[
            "data_spaces"
        ]


class RepresentationProblemDataspaceList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", RepresentationDataSpace)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RepresentationDataSpace(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str)
        super().init_elem("ranks", RepresentationRankList)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target: str = self["name"]
        self.ranks: RepresentationRankList = self["ranks"]


class RepresentationRankList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", RepresentationRank)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranks: List[RepresentationRank] = self


class RepresentationRank(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("format", ("CP", "B", "RLE", "UOP"))
        super().init_elem("metadata_word_bits", int, None)
        super().init_elem("payload_word_bits", int, None)
        super().init_elem("flattened_rankIDs", (list), None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format: str = self["format"]
        self.metadata_word_bits: Optional[int] = self["metadata_word_bits"]
        self.flattened_rankIDs: list = self["flattened_rankIDs"]


class ActionOptimizationList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", ActionOptimization)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ComputeOptimization(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("type", ("gating", "skipping"), None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ActionOptimization(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("type", ("gating", "skipping", "spatial_skipping"))
        super().init_elem("options", ActionOptimizationOptionList)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: str = self["type"]


class ActionOptimizationOptionList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", ActionOptimizationOption)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ActionOptimizationOption(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("target", str)
        super().init_elem("condition_on", list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target: str = self["target"]
        self.condition_on: list = self["condition_on"]


SparseOptimizationGroup.init_elems()
RepresentationRankList.init_elems()
RepresentationProblemDataspaceList.init_elems()
RepresentationFormat.init_elems()
RepresentationDataSpace.init_elems()
RepresentationRank.init_elems()
ActionOptimizationList.init_elems()
ActionOptimization.init_elems()
ActionOptimizationOptionList.init_elems()
ActionOptimizationOption.init_elems()
SparseOptimizations.init_elems()
SparseOptimizationsList.init_elems()
ComputeOptimization.init_elems()
