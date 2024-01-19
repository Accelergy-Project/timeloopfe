from ..common.nodes import DictNode, ListNode
from .version import assert_version


class Mapper(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().recognize_all()
        super().add_attr("version", callfunc=assert_version)
        super().add_attr("out_prefix", str, "timeloop_mapper")
        super().add_attr("num_threads", int, 8)
        super().add_attr("optimization_metric", OptimizationMetrics, [])
        super().add_attr("search_size", int, None)
        super().add_attr("timeout", int, 1000)
        super().add_attr("victory_condition", int, None)
        super().add_attr("sync_interval", int, None)
        super().add_attr("log_interval", int, 1)
        super().add_attr("log_oaves", bool, False)
        super().add_attr("log_oaves_mappings", bool, False)
        super().add_attr("log_stats", bool, False)
        super().add_attr("log_suboptimal", bool, False)
        super().add_attr("live_status", bool, False)
        super().add_attr("diagnostics", bool, False)
        super().add_attr("penalize_consecutive_bypass_fails", bool, False)
        super().add_attr("emit_whoop_nest", bool, False)
        super().add_attr("max_temporal_loops_in_a_mapping", int, -1)
        super().add_attr(
            "algorithm",
            (
                "random",
                "exhaustive",
                "linear_pruned",
                "hybrid",
                "random_pruned",
            ),
            "hybrid",
        )
        super().add_attr("filter_revisits", bool, False)
        super().add_attr("max_permutations_per_if_visit", int, 16)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: str = self["version"]
        self.out_prefix: str = self["out_prefix"]
        self.num_threads: int = self["num_threads"]
        self.optimization_metric: OptimizationMetrics = self["optimization_metric"]
        self.search_size: int = self["search_size"]
        self.timeout: int = self["timeout"]
        self.victory_condition: int = self["victory_condition"]
        self.sync_interval: int = self["sync_interval"]
        self.log_interval: int = self["log_interval"]
        self.log_oaves: bool = self["log_oaves"]
        self.log_oaves_mappings: bool = self["log_oaves_mappings"]
        self.log_stats: bool = self["log_stats"]
        self.log_suboptimal: bool = self["log_suboptimal"]
        self.live_status: bool = self["live_status"]
        self.diagnostics: bool = self["diagnostics"]
        self.penalize_consecutive_bypass_fails: bool = self[
            "penalize_consecutive_bypass_fails"
        ]
        self.emit_whoop_nest: bool = self["emit_whoop_nest"]
        self.algorithm: str = self["algorithm"]
        self.filter_revisits: bool = self["filter_revisits"]
        self.max_permutations_per_if_visit: int = self["max_permutations_per_if_visit"]


class OptimizationMetrics(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", ("delay", "energy", "edp", "last_level_accesses"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


Mapper.declare_attrs()
OptimizationMetrics.declare_attrs()
