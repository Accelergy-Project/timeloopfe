"""!@brief Takes constraints from constraints lists and attaches them to
objects in the architecture.
"""
from timeloopfe.processors.v4suite.sparse_opt_attacher import (
    SparseOptAttacherProcessor,
)
from timeloopfe.v4spec.arch import Compute, Element, Storage
from ...processors.v4suite.references2copies import References2CopiesProcessor
from ...parsing.nodes import Node
from ...processors.processor import Processor


class RequiredActionsProcessor(Processor):
    """!@brief Ensures that all elements have actions defined for Accelergy
    Storage:
    - read
    - write
    - update
    Storage if metadata attributes are present:
    - metadata_read
    - metadata_write
    - metadata_update
    Storage if sparse optimization is enabled:
    - gated_read
    - gated_write
    - gated_update
    - skipped_read
    - skipped_write
    - skipped_update
    - decompression_count
    - compression_count
    Storage if sparse and metadata are enabled:
    - gated_metadata_read
    - skipped_metadata_read
    - gated_metadata_write
    - skipped_metadata_write
    - gated_metadata_write
    - skipped_metadata_write
    Compute:
    - compute
    Compute if sparse optimization is enabled:
    - gated_compute
    - skipped_compute
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def check_storage(self, elem: Storage):
        sparse_opts = elem.sparse_optimizations

        has_metadata = elem.attributes.metadata_datawidth is not None
        sparse_rep = not Node.isempty_recursive(
            sparse_opts.representation_format
        )
        sparse_action = not Node.isempty_recursive(
            sparse_opts.action_optimization
        )
        read_write_update = [""]
        required_actions = ["leak"]
        if has_metadata:
            read_write_update.append("metadata_")
        if sparse_action:
            read_write_update.append("gated_")
            read_write_update.append("skipped_")
        if sparse_action and has_metadata:
            read_write_update.append("gated_metadata_")
            read_write_update.append("skipped_metadata_")
        if sparse_rep:
            required_actions += ["decompression_count", "compression_count"]
        for r in read_write_update:
            for a in ["read", "write", "update"]:
                required_actions.append(r + a)
        elem.required_actions = list(
            set(required_actions + elem.required_actions)
        )

    def check_compute(self, elem: Element):
        sparse_opts = elem.sparse_optimizations
        sparse_action = not Node.isempty(sparse_opts.action_optimization)
        required_actions = ["compute"]
        if sparse_action:
            required_actions += ["gated_compute", "skipped_compute"]
        elem.required_actions = list(
            set(required_actions + elem.required_actions)
        )

    def process(self):
        super().process()
        self.must_run_after(References2CopiesProcessor)
        self.must_run_after(SparseOptAttacherProcessor)
        for s in self.spec.architecture.get_nodes_of_type(Storage):
            self.check_storage(s)  # type: ignore
        for c in self.spec.architecture.get_nodes_of_type(Compute):
            self.check_compute(c)  # type: ignore
