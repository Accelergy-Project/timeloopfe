""" !@brief Base class for all processors."""
from abc import abstractmethod, ABC
import logging
from ..v4spec.problem import Problem
from ..v4spec.specification import Specification
from ..parsing import nodes as nodes
from typing import Optional


class Processor(ABC):
    """!@brief Base class for all processors.
    !@details Processors are used to modify the specification before it is
              passed to Accelergy/Timeloop.
    !@var spec: The specification to be processed.
    !@var _initialized: Whether the processor has been initialized.
    """

    def __init__(self, spec: Optional[Specification] = None):
        self.spec: Specification = spec
        self._initialized: bool = True
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def process(self):
        """!@brief Process the specification."""
        self.logger.debug(f"Processing...")

    def init_elems(self):
        """
        !@brief Initialize the elements that the processor is responsible for.
        !@note This method is called before process() is called. See the
               SimpleProcessor for an example.
        """

    def responsible_for_removing_elems(self):
        """!@brief Context manager to make the processor responsible for any
        elements that are initialized in init_elems(). This processor is
        responsible for removing those elements from the specification when
        it is done processing.
        """

        class MakeMeResponsible:
            def __init__(self, who: Processor):
                self.who = who
                self.prev = None

            def __enter__(self):
                self.prev = nodes._responsible_for_removing_elems
                nodes._responsible_for_removing_elems = self.who

            def __exit__(self, exc_type, exc_value, traceback):
                nodes._responsible_for_removing_elems = self.prev

        return MakeMeResponsible(self)

    def get_index(self, processor_type: type) -> int:
        """!@brief Get the index of the processor in the list of processors."""
        for i, processor in enumerate(self.spec.processors):
            if isinstance(processor, processor_type):
                return i
        return -1

    def must_run_after(self, other: type, ok_if_not_found: bool = False):
        """!@brief Ensure that this processor runs after another processor.
        !@param other: The processor that this processor must run after.
        !@param ok_if_not_found: If False, OK if the other processor is not
                                 found. If True, raise an exception if the
                                 other processor is not found.
        """
        other_idx = self.get_index(other)
        my_idx = self.get_index(self.__class__)
        if other_idx > my_idx or (other_idx == -1 and not ok_if_not_found):
            raise ProcessorException(
                f"{other.__name__} must run before {self.__class__.__name__}. "
                f"Please add {other.__name__} to the list of processors "
                f"before {self.__class__.__name__} in the spec."
            )

    def must_not_run_before(self, other: type, ok_if_not_found: bool = False):
        """!@brief Ensure that this processor runs before another processor.
        !@param other: The processor that this processor must run before.
        !@param ok_if_not_found: If False, OK if the other processor is not
                                 found. If True, raise an exception if the
                                 other processor is not found.
        """
        other_idx = self.get_index(other)
        my_idx = self.get_index(self.__class__)
        if other_idx < my_idx or (other_idx == -1 and not ok_if_not_found):
            raise ProcessorException(
                f"{other.__name__} must run after {self.__class__.__name__}. "
                f"Please add {other.__name__} to the list of processors "
                f"after {self.__class__.__name__} in the spec."
            )


class SimpleProcessor(Processor):
    """!@brief An example simple processor."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info("Initializing SimpleProcessor")

    def init_elems(self):
        """!@brief Initialize the elements that the processor handles."""
        with self.responsible_for_removing_elems():
            Problem.init_elem("simple_processor_attr", str, "")

    def process(self):
        """!@brief Process the specification. Remove elements that this
        processor is responsible for."""
        if "simple_processor_attr" in self.spec.problem:
            del self.spec.problem["simple_processor_attr"]
            self.logger.info('Deleted "simple_processor_attr"')


class ProcessorException(Exception):
    """!@brief Exception raised by processors."""
