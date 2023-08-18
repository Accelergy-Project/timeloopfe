from ..parsing.nodes import DictNode, ListNode


class Mapper(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().recognize_all()
        super().init_elem("out_prefix", str, "timeloop_mapper")
        super().init_elem("num_threads", int, 8)
        super().init_elem("optimization_metric", OptimizationMetrics, [])
        super().init_elem("search_size", int, None)
        super().init_elem("timeout", int, 1000)
        super().init_elem("victory_condition", int, None)
        super().init_elem("sync_interval", int, None)
        super().init_elem("log_interval", int, 1)
        super().init_elem("log_oaves", bool, False)
        super().init_elem("log_oaves_mappings", bool, False)
        super().init_elem("log_stats", bool, False)
        super().init_elem("log_suboptimal", bool, False)
        super().init_elem("live_status", bool, False)
        super().init_elem("diagnostics", bool, False)
        super().init_elem("penalize_consecutive_bypass_fails", bool, False)
        super().init_elem("emit_whoop_nest", bool, False)
        super().init_elem(
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
        super().init_elem("filter_revisits", bool, False)
        super().init_elem("max_permutations_per_if_visit", int, 16)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_prefix: str = self["out_prefix"]
        self.num_threads: int = self["num_threads"]
        self.optimization_metric: OptimizationMetrics = self[
            "optimization_metric"
        ]
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
        self.max_permutations_per_if_visit: int = self[
            "max_permutations_per_if_visit"
        ]

class OptimizationMetrics(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "", ("delay", "energy", "edp", "last_level_accesses")
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

Mapper.init_elems()
OptimizationMetrics.init_elems()
