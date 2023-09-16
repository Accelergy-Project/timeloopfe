"""!@brief Enables the dummy table for Accelergy to placeholder energy/area."""
from ...v4spec.arch import Element
from ...processors.processor import Processor


class EnableDummyTableProcessor(Processor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process(self):
        super().process()
        for c in self.spec.get_nodes_of_type((Element)):
            c.required_actions.extend(["read", "write", "update", "leak"])
            c.attributes["technology"] = -1
