from ..parsing.nodes import DictNode, ListNode, Node
from ..v4spec.components import Components
from typing import List, Union


class Specification(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("components", Components, {}, part_name_match=True)
        super().init_elem("processors", ListNode, [])
        super().init_elem("", part_name_match=True, no_change_key=True)

    def _early_init_processors(self, **kwargs):
        class Mys(ListNode):
            @classmethod
            def init_elems(cls, *args, **kwargs):
                super().init_elems(*args, **kwargs)
                super().init_elem("", callfunc=lambda x: x(self))

        Mys.init_elems()
        self.processors = Mys(kwargs.get("processors", []))
        for p in self.processors:
            p.init_elems()

    def __init__(self, *args, **kwargs):
        Node.reset_all_elems()
        self._early_init_processors(
            **kwargs
        )  # Because processors define init_elems
        if "processors" in kwargs:
            kwargs.pop("processors")

        super().__init__(*args, **kwargs)
        self.processors: ListNode = self["processors"]
        self.components: ListNode = self["components"]
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

        for p in processors:
            # If the processor isn't initialized, initialize it
            if isinstance(p, type):
                p = p(self)
            p.process()
            self._processors_run.append(p)
        if check_types:
            self.check_unrecognized(ignore_empty=check_types_ignore_empty)

    @classmethod
    def from_yaml_files(cls, *args, **kwargs) -> "Specification":
        Node.reset_all_elems()
        return super().from_yaml_files(*args, **kwargs)  # type: ignore


Specification.init_elems()
