import time
from . import arch, constraints, problem, variables
from ..parsing.nodes import DictNode, ListNode, Node
from .arch import Architecture
from .constraints import Constraints, ConstraintsList
from .problem import Problem
from .variables import Variables
from .components import Components
from .mapper import Mapper
from .sparse_optimizations import SparseOptimizations

from typing import List, Union

def class2obj(x):
    return x() if isinstance(x, type) else x

class Specification(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("architecture", Architecture)
        super().init_elem("components", Components, {}, part_name_match=True)
        super().init_elem("constraints", Constraints, {}, part_name_match=True)
        super().init_elem("mapping", ConstraintsList, [], part_name_match=True)
        super().init_elem("problem", Problem)
        super().init_elem("sparse_optimizations", SparseOptimizations, {})
        super().init_elem("variables", Variables, {})

        super().init_elem("ignore", part_name_match=True, no_change_key=True)
        super().init_elem("mapper", Mapper, {})
        super().init_elem("processors", ListNode, [])

    def _early_init_processors(self, **kwargs):
        class Mys(ListNode):
            @classmethod
            def init_elems(cls, *args, **kwargs):
                super().init_elems(*args, **kwargs)
                super().init_elem("", callfunc=class2obj)

        if "processors" not in kwargs:
            from ..processors.v4_standard_suite import STANDARD_SUITE

            kwargs["processors"] = STANDARD_SUITE

        Mys.init_elems()
        self.processors = Mys(kwargs.get("processors", []))
        for p in self.processors:
            p.init_elems()

    def __init__(self, *args, **kwargs):
        if self.parsing_enabled():
            Node.reset_all_elems()
            self._early_init_processors(
                **kwargs
            )  # Because processors define init_elems
            if "processors" in kwargs:
                kwargs.pop("processors")

        super().__init__(*args, **kwargs)
        self.architecture: arch.Architecture = self["architecture"]
        self.constraints: constraints.Constraints = self["constraints"]
        self.mapping: constraints.Constraints = self["mapping"]
        self.problem: problem.Problem = self["problem"]
        self.variables: variables.Variables = self["variables"]
        self.processors: ListNode = self["processors"]
        self.components: ListNode = self["components"]
        self.mapper: Mapper = self["mapper"]
        self.sparse_optimizations: SparseOptimizations = self[
            "sparse_optimizations"
        ]
        self._processors_run = []

    def process(
        self,
        with_processors: Union["Processor", List["Processor"]] = None,
        check_types: bool = True,
        check_types_ignore_empty: bool = True,
    ):
        """!@brief Process the specification.
        !@param with_processors A list of processors to use. If None, use the
                                processors defined in the specification. If
                                anything else, use the given processors.
        !@param check_types Whether to check the types of the specification
                            after processing.
        !@param check_types_ignore_empty Whether to ignore empty lists, dicts,
                                         and None values when checking types.
        """
        processors = (
            self.processors if with_processors is None else with_processors
        )
        if not isinstance(processors, (list, tuple)):
            processors = [processors]

        overall_start_time = time.time()
        for i, p in enumerate(processors):
            # If the processor isn't initialized, initialize it
            p = class2obj(p)
            self.processors[i] = p
            self.logger.info("Running processor %s", p.__class__.__name__)
            start_time = time.time()
            p.spec = self
            p.process()
            self.logger.info(
                "Processor %s done after %.2f seconds",
                p.__class__.__name__,
                time.time() - start_time,
            )
            self._processors_run.append(p)
        if check_types:
            self.check_unrecognized(ignore_empty=check_types_ignore_empty)
        self.logger.info(
            "Specification processed in %.2f seconds",
            time.time() - overall_start_time,
        )

    @classmethod
    def from_yaml_files(cls, *args, **kwargs) -> "Specification":
        Node.reset_all_elems()
        return super().from_yaml_files(*args, **kwargs)  # type: ignore


Specification.init_elems()
