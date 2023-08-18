import sys
from ..processors.processor import Processor


class VariablesFromCLIProcessor(Processor):
    def process(self):
        for arg in sys.argv[1:]:
            if "=" in arg:
                key, value = arg.split("=")
                self.spec.variables[key] = value
