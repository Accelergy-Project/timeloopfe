from numbers import Number
from typing import Union
from ..parsing.nodes import DictNode, CombineableListNode, ListNode
from accelergy import version


class Components(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("version", str, version.__version__, callfunc=str)
        super().init_elem("classes", CombineableListNode, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: str = self["version"]
        self.classes: CombineableListNode = self["classes"]


class ComponentsList(CombineableListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, *kwargs)
        super().init_elem("", CompoundComponent)


class CompoundComponent(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str)
        super().init_elem("attributes", ComponentAttributes, {})
        super().init_elem("subcomponents", SubcomponentList, [])
        super().init_elem("actions", ActionsList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.attributes: ComponentAttributes = self["attributes"]
        self.subcomponents: SubcomponentList = self["SubcomponentList"]
        self.actions: ActionsList = self["actions"]


class SubcomponentList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "", Subcomponent, part_name_match=True, no_change_key=True
        )


class Subcomponent(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str)
        super().init_elem("attributes", ComponentAttributes, {})
        super().init_elem("area_share", (Number, str), 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.attributes: ComponentAttributes = self["attributes"]
        self.area_share: Union[Number, str] = self["area_share"]


class ComponentAttributes(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", part_name_match=True, no_change_key=True)


class ActionsList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", Action, part_name_match=True, no_change_key=True)


class Action(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str)
        super().init_elem("arguments", DictNode, {})
        super().init_elem("subcomponents", ActionSubcomponentsList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.arguments: DictNode = self["arguments"]
        self.subcomponents: ActionSubcomponentsList = self["subcomponents"]


class ActionSubcomponentsList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem(
            "",
            SubcomponentActionGroup,
            part_name_match=True,
            no_change_key=True,
        )


class SubcomponentActionGroup(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str)
        super().init_elem("actions", SubcomponentActionList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.actions: SubcomponentActionList = self["arguments"]


class SubcomponentActionList(ListNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("", SubcomponentAction)


class SubcomponentAction(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        super().init_elem("name", str)
        super().init_elem("arguments", DictNode, {})
        super().init_elem("action_share", (str, float), 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.arguments: DictNode = self["arguments"]
        self.action_share: Union[str, float] = self["action_share"]


Components.init_elems()
ComponentsList.init_elems()
CompoundComponent.init_elems()
SubcomponentList.init_elems()
Subcomponent.init_elems()
ComponentAttributes.init_elems()
ActionsList.init_elems()
Action.init_elems()
ActionSubcomponentsList.init_elems()
SubcomponentActionGroup.init_elems()
SubcomponentActionList.init_elems()
SubcomponentAction.init_elems()
