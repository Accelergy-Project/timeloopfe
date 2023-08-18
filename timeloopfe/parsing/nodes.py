"""!@brief Node classes for parsing and processing specification trees."""
from abc import ABC
import copy
import glob
import inspect
import logging
import os
from typing import (
    Callable,
    Any,
    Dict,
    Optional,
    Set,
    TypeVar,
    Union,
    List,
    Tuple,
    Iterable,
    Type,
)
import accelergy.utils.yaml as yaml


class NodeException(Exception):
    """!@brief Exception for nodes."""


class Unspecified:
    """!@brief Class to represent an unspecified value."""

    def __str__(self):
        return "REQUIRED"

    def __repr__(self):
        return "REQUIRED"


default_unspecified_ = Unspecified()

T = TypeVar("T", bound="Node")


def is_subclass(x: Any, of: Any) -> bool:
    return inspect.isclass(x) and issubclass(x, of)


class TypeSpecifier:
    """!@brief Class to represent a type specifier.
    !@var name Name of the type specifier.
    !@var required_type Required type of the type specifier.
    !@var default Default value of the type specifier.
    !@var callfunc Function to call to cast the value to the required type.
    !@var should_have_been_removed_by The class that should have removed this
                                      key from the containing node.
    !@var part_name_match Whether or not the name of the type specifier is
                          allowed to be a substring of the key.
    !@var no_change_key Only used with part_name_match=True. If True, the key
                        will not be changed when the type specifier is casted.
                        If false, the key will be changed to the name of the
                        type specifier.
    """

    id2casted = {}

    def __init__(
        self,
        name: str,
        required_type: Type,
        default: Any = default_unspecified_,
        callfunc: Union[Callable, None] = None,
        should_have_been_removed_by: Type = None,
        part_name_match: bool = False,
        no_change_key: bool = False,
    ):
        self.name: str = name
        self.required_type: Type = required_type
        self.default: Any = default
        self.callfunc: Callable = callfunc
        # Check if required type is a class and inherit from Node
        if self.callfunc is None and is_subclass(required_type, Node):
            self.callfunc = required_type
            rt = required_type

            def callfunc(x, __node_skip_parse=False):
                if isinstance(x, rt):
                    return x
                return rt(x, __node_skip_parse=__node_skip_parse)

            callfunc.__name__ = required_type.__name__
            self.callfunc = callfunc
            # self.callfunc = lambda x: x if isinstance(x, rt) else rt(x)
        self.should_have_been_removed_by: Type = should_have_been_removed_by
        self.set_from: Any = self.should_have_been_removed_by
        self.part_name_match: bool = part_name_match
        self.no_change_key: bool = no_change_key

    def removed_by_str(self):
        if self.should_have_been_removed_by is not None:
            rmclass = getattr(
                self.should_have_been_removed_by,
                "__class__",
                self.should_have_been_removed_by,
            )
            rmname = getattr(
                rmclass,
                "__name__",
                rmclass,
            )
            return (
                f"This should have been removed or transformed by "
                f"{rmname}, but was not. "
                f"Did something go wrong in the parsing?"
            )
        return ""

    def cast_check_type(self, value: Any, node: "Node", key: str) -> Any:
        if value is default_unspecified_:
            assert self.default is not default_unspecified_, (
                "Can not call cast_check_type() with default_unspecified_"
                "if default value is also default_unspecified_."
            )
            value = copy.deepcopy(self.default)

        try:
            casted = self.cast(value)
        except Exception as exc:
            callname = (
                self.callfunc.__name__
                if isinstance(self.callfunc, type)
                else self.callfunc.__name__
                if isinstance(self.callfunc, Callable)
                else str(self.callfunc)
            )
            casted_successfully = False
            try:  # If we can cast without parsing lower-level nodes, then
                # the exception came from below and we should re-raise it.
                value = self.cast(value, True, was_default=default)
                casted_successfully = True
            except Exception:
                pass  # This level is the problem. Re-raise NodeException
                # with more info.
            global _last_non_node_exception
            if not isinstance(exc, NodeException):
                _last_non_node_exception = exc
            if casted_successfully:
                raise exc

            estr = ""
            if _last_non_node_exception is not None:
                estr = "\n\n" + str(_last_non_node_exception)

            raise NodeException(
                f'Error calling cast function "{callname}" '
                f'for value "{value}" in {node.get_name()}[{key}]. '
                f"{self.removed_by_str()}{estr}"
            ) from exc
        self.check_type(casted, node, key)
        return casted

    def cast(self, value: Any, __node_skip_parse: bool = False) -> Any:
        tag = Node.get_tag(value)
        primitive = type(value) in (int, float, bool, str, bytes, type(None))
        id2cast_key = (id(value), id(self.callfunc), __node_skip_parse)

        if not primitive and id2cast_key in self.id2casted:
            value = self.id2casted[id2cast_key]
        elif self.callfunc is not None:
            if __node_skip_parse:
                value = self.callfunc(
                    value, __node_skip_parse=__node_skip_parse
                )
            else:
                value = self.callfunc(value)
            if not primitive:
                self.id2casted[id2cast_key] = value
        try:
            value.tag = tag
        except AttributeError:
            pass
        return value

    def check_type(self, value: Any, node: "Node", key: str):
        if value == self.default or self.required_type is None:
            return
        t = (
            self.required_type
            if isinstance(self.required_type, tuple)
            else (self.required_type,)
        )
        for s in t:
            if isinstance(s, str) and str(value) == s:
                return True
            if isinstance(s, type) and isinstance(value, s):
                return True
            if s is None and value is None:
                return True
        raise TypeError(
            f"Expected one of {self.required_type}, got {type(value)} "
            f'with value "{value}" in {node.get_name()}[{key}]. '
            f"{self.removed_by_str()}"
        )


def isempty(x: Iterable) -> bool:
    if x is None:
        return True
    if isinstance(x, (Node)):
        return x.isempty()
    try:
        return len(x) == 0
    except TypeError:
        return False


class StackManager:
    def __init__(self, stack: List[Any], add_elem: Any):
        self.stack = stack
        self.add_elem = add_elem

    def __enter__(self):
        rval = self.stack[-1] if self.stack else None
        self.stack.append(self.add_elem)
        return rval

    def __exit__(self, *args):
        self.stack.pop()


_parent_stack: List["Node"] = []
_subclassed: Set[Type] = set()
_responsible_for_removing_elems: Any = None
_last_non_node_exception: Exception = None
_enable_parse_stack: List[bool] = [True]


def disable_node_parsing_context() -> StackManager:
    """!@brief Returns a context manager that disables node parsing."""
    return StackManager(_enable_parse_stack, False)


def parsing_enabled() -> bool:
    """!@brief Returns True if node parsing is enabled."""
    return _enable_parse_stack[-1]


class Node(ABC):
    """
    !@brief Abstract base class for all nodes in the tree.
    !@var parent_node The parent node of this node.
    !@var _param_type_specifiers Dictionary of type specifiers for this class.
    !@var Node_all_recognized Whether all elements under this node should be
                              recognized.
    !@var __currently_parsing_index The index of the element currently being
                                    parsed in the parse tree.
    !@var logger The logger for this class.
    """

    def __init__(self, *args, **kwargs):
        self.parent_node: Node = None
        # Keep in memory such that the ID is not reused.
        self._init_args: Tuple = (args, kwargs)
        self.__currently_parsing_index: Union[int, str] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def init_elems(cls, *args, **kwargs):
        """!@brief Initialize the elements of this node."""
        setattr(cls, "_param_type_specifiers", {})
        setattr(cls, "Node_all_recognized", False)
        cls.init_elem(
            "ignore",
            required_type=None,
            default=None,
            part_name_match=True,
            no_change_key=True,
        )
        _subclassed.add(cls)

    @classmethod
    def reset_all_elems(cls):
        for s in _subclassed:
            s.init_elems()

    @classmethod
    def recognize_all(cls, recognize_all: bool = True):
        """
        !@brief Set whether all elements under this node should be recognized.
        !@param recognize_all If True, all elements under this node will be
                              recognized. If False, only elements that are
                              explicitly specified in the class will be
                              recognized.
        """
        if cls is Node or cls is DictNode or cls is ListNode:
            raise ValueError(
                f'Called recognize_all() on class "{cls}".'
                f"Call this method on a subclass of Node or DictNode."
            )
        setattr(cls, "Node_all_recognized", recognize_all)

    @classmethod
    def _get_type_specifiers(cls) -> Dict[str, TypeSpecifier]:
        """
        !@brief Get the type specifiers for this node.
        !@return A dictionary mapping element keys or tags to TypeSpecifier
                 objects.
        """
        classname = cls.__name__
        if not hasattr(cls, "_param_type_specifiers"):
            raise AttributeError(
                f"Class {classname} inherits from DictNode but does not have "
                f"a _param_type_specifiers attribute. Was __init__() "
                f"called before {classname}.init_elems()?"
            )
        rval = {}
        for c in cls.mro()[::-1]:  # Iterate through superclasses
            rval.update(getattr(c, "_param_type_specifiers", {}))
        return rval

    def _get_all_recognized(self):
        recognized = lambda x: getattr(x, "Node_all_recognized", 0)
        return any([recognized(c) for c in self.__class__.mro()])

    @staticmethod
    def _get_tag(x) -> str:
        tag = getattr(x, "tag", None)
        if isinstance(tag, str):
            return tag
        if tag is None:
            return ""
        if not hasattr(tag, "value"):
            raise ValueError(
                f"Tag '{tag}' in {x}.tag is not a string "
                f"and has no 'value' attribute."
            )
        if tag.value is None:
            return ""
        return tag.value

    def get_tag(self) -> str:
        """!@brief Get the tag of this node."""
        return Node._get_tag(self)

    def _get_index2checker(
        self, key2elem: Optional[List[Tuple[str, Any]]] = None
    ) -> Dict[Union[str, int], TypeSpecifier]:
        specifiers = self._get_type_specifiers()
        if key2elem is not None:
            index2checker = {}
            for i, (k, v) in enumerate(key2elem):
                index2checker[i] = specifiers.get(k, None)
                if index2checker[i] is None:
                    for s in specifiers.values():
                        if s.part_name_match and s.name in k:
                            index2checker[i] = s
                            break
            return index2checker
        if isinstance(self, DictNode):
            index2checker = {k: specifiers.get(k, None) for k in self.keys()}
            for k, v in index2checker.items():
                if v is None:
                    for s in specifiers.values():
                        if s.part_name_match and s.name in k:
                            index2checker[k] = s
                            break
            return index2checker
        if isinstance(self, ListNode):
            checks = {}
            for k, v in enumerate(self):
                check = specifiers.get(Node._get_tag(v), None)
                if check is None:
                    check = specifiers.get("!" + v.__class__.__name__, None)
                checks[k] = check
            return checks
        raise ValueError(
            f"Called _get_index2checker on {self.__class__}"
            f"which is not a DictNode or ListNode."
        )

    def items(self) -> Iterable[Tuple[Union[str, int], Any]]:
        """!@brief Get iterable of (key, value) or (index, value) pairs."""
        if isinstance(self, dict):
            return super().items()  # type: ignore
        return enumerate(self)  # type: ignore

    def combine_index(self, key: Union[str, int], value: T) -> T:
        """!@brief Combine the value at the given key with the given value.
        If there is no value at the given key, sets the value at the given key.
        If there is, attempts to combine the two values.
        !@param key The key to combine.
        !@param value The value to combine.
        !@return The combined value.
        """
        # Done to get rid of type warnings
        s: DictNode = self  # type: ignore
        if key in s:
            s[key] = Node.try_combine(s[key], value, self, str(key))
        else:
            s[key] = value
        if isinstance(s[key], Node):
            s[key].parent_node = self
        return s[key]

    @classmethod
    def parsing_enabled(cls) -> bool:
        """!@brief Returns True if node parsing is enabled."""
        return parsing_enabled()

    def _parse_elem(
        self,
        key: Union[str, int],
        check: TypeSpecifier,
        value_override: Any = None,
    ):
        if value_override is not None:
            v = value_override
        elif isinstance(self, DictNode) and check is not None:
            v = self.pop(key)  # Remove so we can add back with checker name
        else:
            v = self[key]

        if v is default_unspecified_:
            if check.default is default_unspecified_:
                rq, found = [key], []
                for k, v in self._get_index2checker().items():
                    if (
                        (self[k] is default_unspecified_)
                        and (v is not None)
                        and v.default is default_unspecified_
                    ):
                        rq.append(k)
                    elif self[k] is not default_unspecified_:
                        found.append(k)
                rq = "Required keys not found: " + ", ".join(rq)
                found = "Found keys: " + ", ".join(found)
                raise KeyError(
                    f'Missing required key "{key}" in {self}. {rq}. {found}.'
                )

        self.__currently_parsing_index = key
        for reserved in ["tag", "parent_node"]:
            if key == reserved:
                tagstr = (
                    (
                        f"If you'd like to set the tag of "
                        f"this node in Python, set it through the tag "
                        f"attribute. Example: mynode.tag = '!MyTag'. Error in "
                        f"{self.get_name()} {self}"
                    )
                    if reserved == "tag"
                    else ""
                )
                raise ValueError(
                    f"The key {reserved} is reserved for use by the YAML "
                    f"parser. Please use a different key. Found in "
                    f"{self.get_name()}. {tagstr}"
                )
        tag = Node._get_tag(v)
        if check is not None:
            v = check.cast_check_type(v, self, key)

        if isinstance(v, Node):
            v.tag = tag
        # Check for alt name
        if isinstance(self, DictNode) and check is not None:
            newkey = key if check.no_change_key else check.name
            try:
                self.combine_index(newkey, v)
            except Exception as exc:
                raise ValueError(
                    f'Could not combine values in indices "{key}" and '
                    f'"{newkey}" in {self.get_name()}. '  # type: ignore
                ) from exc
        else:
            self[key] = v
        self.__currently_parsing_index = None

    def _parse_elems(self):
        if not parsing_enabled():
            return
        with StackManager(_parent_stack, self) as parent:
            self.parent_node = parent
            for k, check in self._get_index2checker().items():
                self._parse_elem(k, check)
            self._check_unrecognized(ignore_should_have_been_removed_by=1)

    def _parse_extra_elems(self, key2elem: List[Tuple[str, Any]]):
        if not parsing_enabled():
            return
        with StackManager(_parent_stack, self) as parent:
            self.parent_node = parent
            checkers = self._get_index2checker(key2elem)
            for (_, check), (k, v) in zip(checkers.items(), key2elem):
                try:
                    self._parse_elem(k, check, v)
                except Exception as exc:
                    raise ValueError(
                        f"Failed to combine duplicate element in key [{k}]. "
                        f"There are two ways to fix this: "
                        f"1. Remove the duplicate key '{k}'. "
                        f"2. Ensure that the duplicate values are "
                        f"identical or able to be combined. "
                    ) from exc
            self._check_unrecognized(ignore_should_have_been_removed_by=1)

    def get_name(self, seen: Union[Set, None] = None) -> str:
        if seen is None:
            seen = set()
        if id(self) in seen:
            return f"{self.__class__.__name__}"
        seen.add(id(self))
        namekey = ""
        if isinstance(self, dict) and "name" in self:
            namekey = f'({self["name"]})'
        parentname = ""
        if self.parent_node is not None:
            parent = self.parent_node
            idx = ""
            if isinstance(parent, ListNode) and self in parent:
                idx = parent.index(self)
            elif isinstance(parent, DictNode) and self in parent.values():
                idx = next(k for k, v in parent.items() if v == self)
            elif parent.__currently_parsing_index is not None:
                idx = parent.__currently_parsing_index
            parentname = f"{self.parent_node.get_name(seen)}[{idx}]."
        return f"{parentname}{self.__class__.__name__}{namekey}"

    def check_unrecognized(
        self,
        ignore_empty: bool = False,
        ignore_should_have_been_removed_by=False,
    ):
        """!@brief Check for unrecognized keys in this node and all subnodes.
        Also checks for correct types.
        !@param ignore_empty If True, ignore empty nodes.
        !@param ignore_should_have_been_removed_by If True, ignore nodes that
                                                   should have been removed by
                                                   a processor.
        """
        self.recursive_apply(
            lambda x: x._check_unrecognized(
                ignore_empty, ignore_should_have_been_removed_by
            ),
            self_first=True,
        )

    def recursive_apply(
        self, func: callable, self_first: bool = False, applied_to: set = None
    ) -> Any:
        """!@brief Apply a function to this node and all subnodes.
        !@param func The function to apply.
        !@param self_first If True, apply the function to this node before
                           applying it to subnodes. Otherwise, apply the
                           the function to subnodes before applying it to this
                           node.
        !@param applied_to A set of ids of nodes that have already been
                           visited. Prevents infinite recursion.
        """
        if applied_to is None:
            applied_to = set()
        if id(self) in applied_to:
            return self
        applied_to.add(id(self))
        if self_first:
            rval = func(self)
        for _, v in self.items():
            if isinstance(v, Node):
                v.recursive_apply(func, self_first, applied_to)
        if self_first:
            return rval
        return func(self)

    def clean_empties(self):
        """!@brief Remove empty nodes from this node and all subnodes."""

        def clean(x):
            items = list((x.items()) if isinstance(x, dict) else enumerate(x))
            for k, v in items[::-1]:
                if v is None or isempty(v):
                    del x[k]

        self.recursive_apply(clean)
        clean(self)

    def isempty(self) -> bool:
        """!@brief Return True if this node is empty. Good to override."""
        if isinstance(self, (DictNode, ListNode)):
            return len(self) == 0
        return False

    def isempty_recursive(self) -> bool:
        """!@brief Return True if this node or all subnodes are empty."""

        empties = set()

        def emptycheck(x):
            if all(id(v) in empties for _, v in x.items()):
                empties.add(id(x))
            else:
                raise StopIteration

        try:
            self.recursive_apply(emptycheck, self_first=False)
        except StopIteration:
            return False
        return True

    @classmethod
    def init_elem(
        cls,
        key_or_tag: str,
        required_type: Optional[
            Union[
                type, Tuple[type, ...], Tuple[None, ...], Tuple[str, ...], None
            ]
        ] = None,
        default: Any = default_unspecified_,
        callfunc: Optional[Callable] = None,
        part_name_match: Optional[bool] = None,
        no_change_key: Optional[bool] = None,
    ):
        """!@brief Initialize a type specifier for this class.
        !@param key_or_tag The key/tag or tag to use for this type specifier.
        !@param required_type The type of value that this type specifier
        !@param default The default value to use if the key/tag is not found.
        !@param callfunc A function to call on the value before returning it.
        !@param part_name_match If True, the key/tag will match if it is a
                                substring of the actual key/tag.
        !@param no_change_key If True, a parsed key will not be changed when
                              a partial name match is found. Otherwise, the
                              parsed key will be changed to the actual key.
        """
        if not hasattr(cls, "_param_type_specifiers"):
            raise ValueError(
                f"Class {cls.__name__} must call super.init_elems() before "
                f"super.init_elem()."
            )

        checker = TypeSpecifier(
            name=key_or_tag,
            required_type=required_type,
            default=default,
            callfunc=callfunc,
            should_have_been_removed_by=_responsible_for_removing_elems,
            part_name_match=part_name_match,
            no_change_key=no_change_key,
        )
        getattr(cls, "_param_type_specifiers")[key_or_tag] = checker

        def assert_key(self):
            if key_or_tag not in self:
                raise KeyError(
                    f"Key '{key_or_tag}' not found in {self.get_name()}."
                )

        if is_subclass(cls, DictNode):

            def getter(self):
                assert_key(self)
                return self[key_or_tag]

            def setter(self, value):
                self[key_or_tag] = value

            def deleter(self):
                assert_key(self)
                del self[key_or_tag]

            prop = property(getter, setter, deleter)
            setattr(cls, key_or_tag, prop)

    def _check_unrecognized(
        self, ignore_empty=False, ignore_should_have_been_removed_by=False
    ):
        if self._get_all_recognized():
            return
        if isinstance(self, ListNode) and not self._get_type_specifiers():
            return

        classname = self.__class__.__name__
        if isinstance(self, DictNode):
            name = f"dict {classname} {self.get_name()}"
            keytag = "key"
        else:
            name = f"list {classname} {self.get_name()}"
            keytag = "tag"

        recognized = self._get_type_specifiers()
        checks = self._get_index2checker()
        rkeys = list(recognized.keys())

        if len(rkeys) == 1 and rkeys[0] == "ignore":
            return

        for k, v in checks.items():
            if ignore_empty and (self[k] is None or isempty(self[k])):
                continue

            if v is None and isinstance(self, ListNode):
                v = recognized.get("!" + self[k].__class__.__name__, None)

            if v is None:
                has_tag = hasattr(self[k], "tag")
                idxstr = f" index {k}" if keytag == "tag" else ""
                t = Node._get_tag(self[k]) if keytag == "tag" else k
                tag_clarif = "(no .tag in Python object, no !TAG in YAML)"
                if has_tag or keytag != "tag":
                    tag_str = f"'{t}'"
                else:
                    tag_str = f"'{t}' {tag_clarif}"
                raise ValueError(
                    f"Unrecognized {keytag} {tag_str} in {name}{idxstr}.  "
                    f"Recognized {keytag}s: {list(recognized.keys())}. If "
                    f"this {keytag} SHOULD have been recognized but was not, "
                    f"ensure that it is specified in {classname}.init_elems() "
                    f"and that init_elems is called before instantiation of "
                    f"{classname}."
                )
            v.check_type(self[k], self, k)
            if (
                v.should_have_been_removed_by is not None
                and not ignore_should_have_been_removed_by
            ):
                key = Node._get_tag(self[k]) if keytag == "tag" else k
                s = f'Found {keytag} "{key}" in {name}[{k}].'
                raise ValueError(f"{s} {v.removed_by_str()}")

    def get_nodes_of_type(self, node_type: Type[T]) -> List[T]:
        """!@brief Return a list of all subnodes of a given type.
        !@param node_type The type of node to search for.
        !@param found A set of nodes that have already been found. Prevents
                      infinite recursion.
        """
        found = []
        found_ids = set()

        def search(x):
            for c in [v for _, v in x.items()]:
                if isinstance(c, node_type) and id(c) not in found_ids:
                    found_ids.add(id(c))
                    found.append(c)

        self.recursive_apply(search, self_first=True)
        self.logger.debug("Found %d nodes of type %s.", len(found), node_type)
        return found

    def get_setter_lambda(self, keytag: Union[str, int]) -> Callable:
        """!@brief Get a function that can be used to set a value in
        this node. The setter takes one argument, the value to set.
        !@param keytag The key or tag to set.
        """

        def setval(x):
            if isinstance(x, Node) and isinstance(self, Node):
                x.parent_node = self
            self[keytag] = x  # type: ignore

        return setval

    def get_combiner_lambda(self, keytag: Union[str, int]) -> Callable:
        """!@brief Get a function that can be used to combine a value
        to this node. The combiner takes one argument, the value to combine.
        !@param keytag The key or tag to combine.
        """
        return lambda x: self.combine_index(keytag, x)

    def get_setters_for_keytag(
        self, keytag: str, recursive: bool = True
    ) -> List[Tuple[Any, Callable]]:
        """!@brief Get a list of tuples of the form (value, setter) for all
        keys/tags in this node that match the given key/tag. A setter is a
        function that can be used to set a value in this node.
        !@param keytag The key or tag to search for.
        !@param recursive If True, search recursively.
        """
        rval = []

        def search(node: Node):
            for i, x in node.items():
                if i == keytag or Node._get_tag(x) == keytag:
                    rval.append((x, node.get_setter_lambda(i)))

        search(self)
        if recursive:
            self.recursive_apply(search)
        self.logger.debug("Found %d nodes for keytag %s.", len(rval), keytag)
        return rval

    def get_combiners_for_keytag(
        self, keytag: str, recursive: bool = True
    ) -> List[Tuple[Any, Callable]]:
        """!@brief Get a list of tuples of the form (value, combiner) for all
        keys/tags in this node that match the given key/tag. A combiner is a
        function that can be used to combine a value to this node.
        !@param keytag The key or tag to search for.
        !@param recursive If True, search recursively.
        """
        rval = []

        def search(node: Node):
            for i, x in node.items():
                if i == keytag or Node._get_tag(x) == keytag:
                    rval.append((x, node.get_setter_lambda(i)))

        search(self)
        if recursive:
            self.recursive_apply(search)
        self.logger.debug("Found %d nodes for keytag %s.", len(rval), keytag)
        return rval

    def get_setters_for_type(
        self, t: Type, recursive: bool = True
    ) -> List[Tuple[Any, Callable]]:
        """!@brief Get a list of tuples of the form (value, setter) for all
        keys/tags in this node that match the given type. A setter is a
        function that can be used to set a value in this node.
        !@param t The type to search for.
        !@param recursive If True, search recursively.
        """
        rval = []

        def search(node: Node):
            for i, x in node.items():
                if isinstance(x, t):
                    rval.append((x, node.get_setter_lambda(i)))

        search(self)
        if recursive:
            self.recursive_apply(search)
        self.logger.debug("Found %d nodes for type %s.", len(rval), t)
        return rval

    def get_combiners_for_type(
        self, t: Type, recursive: bool = True
    ) -> List[Tuple[Any, Callable]]:
        """!@brief Get a list of tuples of the form (value, combiner) for all
        keys/tags in this node that match the given type. A combiner is a
        function that can be used to combine a value to this node.
        !@param t The type to search for.
        !@param recursive If True, search recursively.
        """
        rval = []

        def search(node: Node):
            for i, x in node.items():
                if isinstance(x, t):
                    rval.append((x, node.get_setter_lambda(i)))

        search(self)
        if recursive:
            self.recursive_apply(search)
        self.logger.debug("Found %d nodes for type %s.", len(rval), t)
        return rval

    def __str__(self):
        return self.get_name()

    def __format__(self, format_spec):
        return str(self)

    @staticmethod
    def try_combine(
        a: Any,
        b: Any,
        innonde: Union["Node", None] = None,
        index: Union[int, str, None] = None,
    ) -> Any:
        """!@brief Try to combine two values.
        !@param a The first value.
        !@param b The second value.
        !@param innonde The node that contains the values. For error messages.
        !@param index The index of the values in the node. For error messages.
        """
        if a is None or isempty(a) or a is default_unspecified_:
            return b
        if b is None or isempty(b) or b is default_unspecified_:
            return a

        contextstr = ""
        if innonde is not None:
            contextstr = "" if innonde is None else f" In {innonde.get_name()}"
            if index is not None:
                contextstr += f"[{index}]"
        if a.__class__ != b.__class__:
            raise ValueError(
                f"Can not combine different classes {a.__class__.__name__} "
                f"and {b.__class__.__name__}.{contextstr}"
            )
        if isinstance(f := getattr(a, "combine", None), Callable):
            return f(b)
        raise ValueError(
            f"Can not combine {a} and {b}. {a.__class__.__name__} does not "
            f"have a combine() method.{contextstr}"
        )

    def is_defined_non_default_non_empty(self, key: str) -> bool:
        """!@brief Returns True if the given key is defined in this node and
        is not the default value and is not empty."""
        idx2checker = self._get_index2checker()
        if key not in idx2checker:
            return False
        try:
            v = self[key]  # type: ignore
        except (KeyError, IndexError):
            return False
        if v is None or Node.isempty(v) or v == idx2checker[key].default:
            return False
        return True

    # pylint: disable=useless-super-delegation
    def __getitem__(self, key: Union[str, int]) -> Any:
        # pylint: disable=no-member
        return super().__getitem__(key)  # type: ignore

    # pylint: disable=useless-super-delegation
    def __setitem__(self, key: Union[str, int], value: Any):
        # pylint: disable=no-member
        super().__setitem__(key, value)  # type: ignore


class ListNode(Node, list):
    """!@brief A node that is a list of other nodes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        __node_skip_parse = kwargs.pop("__node_skip_parse", False)
        myname = self.__class__.__name__
        for a in args:
            if isinstance(a, set):
                a = list(a)
            if isinstance(a, list):
                self.extend(a)
            else:
                raise TypeError(f"ListNode {myname} got a non-list: {a}")
        if kwargs:
            raise TypeError(f"ListNode {myname} got keyword args: {kwargs}")
        if not __node_skip_parse:
            self._parse_elems()


class CombineableListNode(ListNode):
    """!@brief A list node that can be combined with others by extending."""

    def combine(self, other: "CombineableListNode") -> "CombineableListNode":
        """!@brief Extends this list with the contents of another list."""
        if not isinstance(other, self.__class__):
            raise ValueError(
                f"Can not combine different classes {self.__class__.__name__} "
                f"and {other.__class__.__name__}."
            )
        self.extend(other)
        return self


class DictNode(Node, dict):
    """!@brief A node that is a dictionary of other nodes."""

    def __init__(self, *args, __node_skip_parse=False, **kwargs):
        __node_skip_parse = kwargs.pop("__node_skip_parse", False)
        super().__init__(*args, **kwargs)

        for a in args:
            if isinstance(a, dict):
                self.update(a)
            else:
                raise TypeError(f"DictNode got a non-dict: {a}")
        self.update(kwargs)
        for k, v in self._get_type_specifiers().items():
            if k not in self and not v.no_change_key:
                self[k] = default_unspecified_
        if not __node_skip_parse:
            self._parse_elems()

    @classmethod
    def require_one_of(cls, *args):
        """!@brief Require that at least one of the given keys is present."""
        _require_one_of = getattr(cls, "_require_one_of", [])
        if not _require_one_of:
            cls._require_one_of = _require_one_of
        cls._require_one_of.append(args)

    @classmethod
    def require_all_or_none_of(cls, *args):
        """!@brief Require that all or none of the given keys are present."""
        _require_all_or_none_of = getattr(cls, "_require_all_or_none_of", [])
        if not _require_all_or_none_of:
            cls._require_all_or_none_of = _require_all_or_none_of
        cls._require_all_or_none_of.append(args)

    def combine(self, other: "DictNode") -> "DictNode":
        """!@brief Combines this dictionary with another dictionary.
        If a key is present in both dictionaries, the values are combined.
        Otherwise, the key is taken from whichever dictionary has it.
        """
        keys = set(self.keys()) | set(other.keys())
        # Make sure the classes are the same
        if not isinstance(other, self.__class__):
            raise ValueError(
                f"Can not combine different classes {self.__class__.__name__} "
                f"and {other.__class__.__name__}."
            )
        for k in keys:
            mine, others = self.get(k, None), other.get(k, None)
            if mine is None:
                self[k] = others
            elif others is None:
                other[k] = mine
            elif isempty(mine):
                self[k] = others
            elif isempty(others):
                self[k] = mine
            elif mine == others:
                pass
            else:
                self[k] = Node.try_combine(mine, others)
        return self

    @classmethod
    def from_yaml_files(
        cls, *files: Union[str, List[str]], **kwargs
    ) -> "DictNode":
        """!@brief Loads a dictionary from a list of yaml files. Each yaml file
        should contain a dictionary. Dictionaries are in the given order.
        Keyword arguments are also added to the dictionary.
        !@param files A list of yaml files to load.
        !@param kwargs Extra keyword arguments to add to the dictionary.
        """
        allfiles = []
        for f in files:
            if isinstance(f, (list, tuple)):
                allfiles.extend(f)
            else:
                allfiles.append(f)
        files = allfiles
        rval = {}
        key2file = {}
        extra_elems = []
        to_parse = []
        for f in files:
            logging.info("Loading yaml file %s", f)
            globbed = [x for x in glob.glob(f) if os.path.isfile(x)]
            if not globbed:
                raise FileNotFoundError(f"Could not find file {f}")
            for g in globbed:
                if any(os.path.samefile(g, x) for x in to_parse):
                    logging.info(
                        'Ignoring duplicate file "%s" in yaml load', g
                    )
                else:
                    to_parse.append(g)

        for f in to_parse:
            if not f.endswith(".yaml"):
                continue
            logging.info("Loading yaml file %s", f)
            loaded = yaml.load_yaml(f)
            if not isinstance(loaded, dict):
                raise ValueError(
                    f"Expected a dictionary from file {f}, got {type(loaded)}"
                )
            for k, v in loaded.items():
                if k in rval:
                    logging.info("Found extra top-key %s in %s", k, f)
                    extra_elems.append((k, v))
                else:
                    logging.info("Found top-key %s in %s", k, f)
                    key2file[k] = f
                    rval[k] = v

        c = cls(**rval, **kwargs)
        logging.info(
            "Parsing extra elements %s", ", ".join([x[0] for x in extra_elems])
        )
        c._parse_extra_elems(extra_elems)
        return c

    def _check_alias(self, key) -> None:
        if not isinstance(key, str):
            return
        aliases_with = None
        if "_" in key and key.replace("_", "-") in self:
            aliases_with = key.replace("_", "-")
        if "-" in key and key.replace("-", "_") in self:
            aliases_with = key.replace("-", "_")
        if "-" in key:
            for k in self._get_index2checker().keys():
                if k == key.replace("-", "_"):
                    aliases_with = k
                    break

        if aliases_with is not None:
            raise KeyError(
                f'Key "{key}" is an alias for "{aliases_with}" in {self}. '
                f"Use the alias instead."
            )

    def __getitem__(self, __key: Any) -> Any:
        self._check_alias(__key)
        return super().__getitem__(__key)

    def __setitem__(self, __key: Any, __value: Any) -> None:
        self._check_alias(__key)
        super().__setitem__(__key, __value)

    def get(self, __key: Any, __default: Any = None) -> Any:
        self._check_alias(__key)
        return super().get(__key, __default)

    def setdefault(self, __key: Any, __default: Any = None) -> Any:
        self._check_alias(__key)
        return super().setdefault(__key, __default)

    def pop(self, __key: Any, __default: Any = None) -> Any:
        self._check_alias(__key)
        return super().pop(__key, __default)

    def check_unrecognized(self, *args, **kwargs) -> None:
        super().check_unrecognized(*args, **kwargs)
        checkers = self._get_index2checker()

        def check(keys: list, expected: Union[tuple, str], countstr: str):
            found = []
            for k in keys:
                v, checker = self.get(k, None), checkers.get(k, None)
                if (
                    v is not None
                    and checker is not None
                    and v != checker.default
                ):
                    found.append(k)
            countmatch = len(found) == expected
            if isinstance(expected, tuple):
                countmatch = len(found) in expected
            if not countmatch:
                raise KeyError(
                    f"Expected {countstr} of {keys} in {self}, "
                    f"found {len(found)}. Values: "
                    f'{", ".join([f"{k}: {self[k]}" for k in found])}'
                )

        for required_one in getattr(self, "_require_one_of", []):
            check(required_one, (1,), "exactly one")
        for required_all in getattr(self, "_require_all_or_none_of", []):
            check(required_all, (0, len(required_all)), "all or none")


DictNode.init_elems()
ListNode.init_elems()
CombineableListNode.init_elems()
