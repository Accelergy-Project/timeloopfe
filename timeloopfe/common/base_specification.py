import copy
import time
from typing import Any, Dict, List, Optional, Union
from .nodes import DictNode, ListNode, Node, TypeSpecifier, CombineableListNode
from .processor import Processor, ProcessorError, References2CopiesProcessor


def class2obj(x):
    return x() if isinstance(x, type) else x


class BaseSpecification(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("ignore", part_name_match=True, no_change_key=True)
        super().add_attr("processors", ListNode, [])
        super().add_attr("_required_processors", ListNode, [])
        super().add_attr("_parsed_expressions", bool, False)
        super().add_attr("_processors_run", ListNode, [])

    def _claim_nodes(self, *args, **kwargs):
        def claim_node(n: Node):
            if isinstance(n, Node):
                n.spec = self

        self.recursive_apply(claim_node)

    def _processors_declare_attrs(self, *args, **kwargs):
        Node.reset_processor_elems()
        for p in self.processors + self._required_processors:
            p.spec = self  # MAKE SURE THIS IS KEPT UP TO DATE
            p.declare_attrs()

    def _early_init_processors(self, _required_processors: List["Processor"], **kwargs):
        class ProcessorListHolder(ListNode):
            @classmethod
            def declare_attrs(cls, *args, **kwargs):
                super().declare_attrs(*args, **kwargs)
                super().add_attr("", callfunc=class2obj)

        kwargs.setdefault("processors", [])
        kwargs["_required_processors"] = _required_processors

        ProcessorListHolder.declare_attrs()
        self.processors = ProcessorListHolder(kwargs["processors"])
        self._required_processors = ProcessorListHolder(kwargs["_required_processors"])
        self._processors_declare_attrs()

    def __init__(self, *args, **kwargs):
        TypeSpecifier.reset_id2casted()
        self._processor_attributes = {}
        Node.set_global_spec(self)
        self.spec = self

        self._early_init_processors(**kwargs)  # Because processors define declare_attrs

        super().__init__(*args, **kwargs)
        TypeSpecifier.reset_id2casted()

        self.processors: ListNode = self["processors"]
        self._required_processors: ListNode = self["_required_processors"]
        self._processors_run: List[Processor] = self["_processors_run"]
        self._parsed_expressions = self["_parsed_expressions"]
        self.preserve_references = kwargs.get("preserve_references", False)

        if not self.preserve_references:
            self.process(References2CopiesProcessor, check_types=False)

    def needs_processing(
        self,
        with_processors: Optional[List["Processor"]] = None,
        to_run: Optional[List["Processor"]] = None,
    ):
        if with_processors is None:
            with_processors = self.processors + [References2CopiesProcessor]
        to_check = (to_run or []) + self._processors_run

        for p in with_processors:
            for x in to_check:
                # If p is a class, check if x is an instance of that class
                if isinstance(p, type) and isinstance(x, p):
                    break
                elif isinstance(x, type) and isinstance(p, x):
                    break
                elif p == x:
                    break
            else:
                return True
        return False

    def process(
        self,
        with_processors: Union["Processor", List["Processor"]] = None,
        check_types: bool = False,
        check_types_ignore_empty: bool = True,
        reprocess: bool = True,
    ):
        """!@brief Process the specification.
        !@param with_processors A list of processors to use. If None, use the
                                processors defined in the specification. If
                                anything else, use the given processors.
        !@param check_types Whether to check the types of the specification
                            after processing.
        !@param check_types_ignore_empty Whether to ignore empty lists, dicts,
                                         and None values when checking types.
        !@param reprocess Whether to reprocess the specification if it has
                          already been processed.
        """
        prev_global_spec = Node.get_global_spec()
        try:
            Node.set_global_spec(self)
            if with_processors is None:
                processors = self.processors
            else:
                if not isinstance(with_processors, (list, tuple)):
                    with_processors = [with_processors]
                processors = [p for p in with_processors]

            if self.needs_processing([References2CopiesProcessor], processors):
                self.process(References2CopiesProcessor, check_types=False)

            overall_start_time = time.time()
            for i, p in enumerate(processors):
                if not self.needs_processing([p]) and (
                    not reprocess
                    or p == References2CopiesProcessor
                    or isinstance(p, References2CopiesProcessor)
                ):
                    continue
                # If the processor isn't initialized, initialize it
                p_cls = p
                p = class2obj(p)
                Node.reset_processor_elems(p.__class__)
                processors[i] = p
                self.logger.info("Running processor %s", p.__class__.__name__)
                start_time = time.time()
                p.process(self)
                self.logger.info(
                    "Processor %s done after %.2f seconds",
                    p.__class__.__name__,
                    time.time() - start_time,
                )
                self._processors_run.append(p_cls)
            if check_types:
                self.check_unrecognized(ignore_empty=check_types_ignore_empty)
            self.logger.info(
                "Specification processed in %.2f seconds",
                time.time() - overall_start_time,
            )
        finally:
            Node.set_global_spec(prev_global_spec)

    @classmethod
    def from_yaml_files(cls, *args, **kwargs) -> "Specification":
        return super().from_yaml_files(*args, **kwargs)  # type: ignore

    def parse_expressions(
        self,
        symbol_table: Optional[Dict[str, Any]] = None,
        parsed_ids: Optional[set] = None,
    ):
        if self.needs_processing([References2CopiesProcessor]):
            raise ProcessorError(
                f"Must run References2CopiesProcessor before "
                f"parsing expressions. Either call __init__ with "
                f"preserve_references=False or call process() with "
                f"any arguments."
            )
        symbol_table = {} if symbol_table is None else symbol_table.copy()
        parsed_ids = set() if parsed_ids is None else parsed_ids
        parsed_ids.add(id(self))
        symbol_table["spec"] = self
        super().parse_expressions(symbol_table, parsed_ids)
        self.check_unrecognized(ignore_should_have_been_removed_by=1)
        self._parsed_expressions = True

    def _process(self):
        spec = copy.deepcopy(self)
        if not spec._parsed_expressions:
            spec.parse_expressions()
        if spec.needs_processing():
            spec.process(check_types=True, reprocess=False)
        spec.process(spec._required_processors)
        spec.check_unrecognized()
        return spec


BaseSpecification.declare_attrs()
