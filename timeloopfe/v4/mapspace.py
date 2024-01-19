from ..common.nodes import DictNode
from .version import assert_version


class Mapspace(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("version", callfunc=assert_version)
        super().add_attr("template", str, "ruby")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: str = self["version"]
        self.template: str = self["template"]


Mapspace.declare_attrs()
