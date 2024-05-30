from ..common.nodes import DictNode

class Art(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attrs("tables", ArtTables)

class Tables(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attrs("", Table)

class Table(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attrs("name", str)
        super().add_attrs("area", float)

Art.declare_attrs()
Tables.declare_attrs()
Table.declare_attrs()

