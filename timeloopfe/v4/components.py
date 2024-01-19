from numbers import Number
from typing import Any, Dict, Optional, Union
from ..common.nodes import DictNode, CombineableListNode, ListNode, FlatteningListNode
from .version import assert_version


class Components(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("version", callfunc=assert_version)
        super().add_attr("classes", FlatteningListNode, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version: str = self["version"]
        self.classes: FlatteningListNode = self["classes"]
    
    def parse_expressions(self, symbol_table: Optional[Dict[str, Any]] = None, 
                          parsed_ids: Optional[set] = None):
        pass


class ComponentsList(FlatteningListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, *kwargs)
        super().add_attr("", CompoundComponent)


class CompoundComponent(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str)
        super().add_attr("attributes", ComponentAttributes, {})
        super().add_attr("subcomponents", SubcomponentList, [])
        super().add_attr("actions", ActionsList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.attributes: ComponentAttributes = self["attributes"]
        self.subcomponents: SubcomponentList = self["SubcomponentList"]
        self.actions: ActionsList = self["actions"]


class SubcomponentList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", Subcomponent, part_name_match=True, no_change_key=True)


class Subcomponent(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str)
        super().add_attr("attributes", ComponentAttributes, {})
        super().add_attr("area_share", (Number, str), 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.attributes: ComponentAttributes = self["attributes"]
        self.area_share: Union[Number, str] = self["area_share"]


class ComponentAttributes(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", part_name_match=True, no_change_key=True)


class ActionsList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", Action, part_name_match=True, no_change_key=True)


class Action(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str)
        super().add_attr("arguments", DictNode, {})
        super().add_attr("subcomponents", ActionSubcomponentsList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.arguments: DictNode = self["arguments"]
        self.subcomponents: ActionSubcomponentsList = self["subcomponents"]


class ActionSubcomponentsList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr(
            "",
            SubcomponentActionGroup,
            part_name_match=True,
            no_change_key=True,
        )


class SubcomponentActionGroup(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str)
        super().add_attr("actions", SubcomponentActionList, [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.actions: SubcomponentActionList = self["arguments"]


class SubcomponentActionList(ListNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("", SubcomponentAction)


class SubcomponentAction(DictNode):
    @classmethod
    def declare_attrs(cls, *args, **kwargs):
        super().declare_attrs(*args, **kwargs)
        super().add_attr("name", str)
        super().add_attr("arguments", DictNode, {})
        super().add_attr("action_share", (str, float), 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = self["name"]
        self.arguments: DictNode = self["arguments"]
        self.action_share: Union[str, float] = self["action_share"]


Components.declare_attrs()
ComponentsList.declare_attrs()
CompoundComponent.declare_attrs()
SubcomponentList.declare_attrs()
Subcomponent.declare_attrs()
ComponentAttributes.declare_attrs()
ActionsList.declare_attrs()
Action.declare_attrs()
ActionSubcomponentsList.declare_attrs()
SubcomponentActionGroup.declare_attrs()
SubcomponentActionList.declare_attrs()
SubcomponentAction.declare_attrs()
