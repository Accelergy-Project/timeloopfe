from ..common.nodes import DictNode

class Ert(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)

        super().add_attrs("tables", ErtTables)

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
        super().add_attrs("actions", Actions)

class Actions(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)

        super().add_attrs("", Action)

class Action(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)

        super().add_attrs("name", str)
        super().add_attrs("arguments", ActionArguments)
        super().add_attrs("energy", float)

class ActionArguments(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)

for cls in [Ert, Tables, Table, Actions, Action, ActionArguments]:
    cls.declare_attrs()

