from ..common.nodes import CombineableListNode, DictNode
from .version import assert_version


class Globals(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("version", callfunc=assert_version)
        super().add_attr("environment_variables", EnvironmentVariables, [])
        super().add_attr("expression_custom_functions", ExpressionCustomFunctions, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: str = self["version"]
        self.environment_variables: EnvironmentVariables = self["environment_variables"]
        self.expression_custom_functions: ExpressionCustomFunctions = self[
            "expression_custom_functions"
        ]


class EnvironmentVariables(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        cls.recognize_all()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ExpressionCustomFunctions(CombineableListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


Globals.declare_attrs()
EnvironmentVariables.declare_attrs()
ExpressionCustomFunctions.declare_attrs()
