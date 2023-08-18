""" !@brief Parses command line args "X=123" and adds them as spec variables.
"""
import sys
from ...processors.processor import Processor


class VariablesFromCLIProcessor(Processor):
    """!@brief Parses command line args "X=123" and adds them as spec
    variables."""

    def process(self):
        super().process()
        for arg in sys.argv[1:]:
            if "=" in arg:
                key, value = arg.split("=")
                self.spec.variables[key] = value
