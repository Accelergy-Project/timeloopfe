"""!@brief Provides information on all node subtypes and their attributes."""
from .nodes import (
    Node,
    _subclassed,
    is_subclass,
    ListNode,
    default_unspecified_,
)
from typing import List, Union


def get_element_table(col_len: int = 18, trim_cols: bool = False) -> str:
    """!@brief Returns a table of all Node subclasses and their attributes."""
    result = []
    checker2str = [
        "key",
        "required_type",
        "default",
        "callfunc",
        "set_from",
    ]

    def formatter(x, capitalize: bool = False):
        if isinstance(x, (list, tuple)) and len(x) > 0:
            x = "/".join([str(getattr(y, "__name__", y)) for y in x])
        x = str(getattr(x, "__name__", x))
        if trim_cols:
            x = x[: col_len - 2]
        if capitalize:
            x = x.upper()
        if x == "":
            x = '""'
        return x.ljust(col_len)

    formatlist = lambda x, *a: ",".join([formatter(c, *a) for c in x])
    subclasses = [c for c in _subclassed]
    subclasses.sort(key=lambda x: x.__module__ + x.__name__)
    prev_module = None
    for subclass in subclasses:
        if subclass.__module__ != prev_module:
            result.append(
                "\n\n"
                + f"  {subclass.__module__}  ".center(
                    col_len * len(checker2str), "="
                )
            )
            prev_module = subclass.__module__
        result.append(f"\n==== {subclass.__name__} ====")
        result.append("  " + formatlist(checker2str, True))
        checkers = getattr(subclass, "_param_type_specifiers", {})
        for k, c in checkers.items():
            r = [k] + [getattr(c, x, None) for x in checker2str[1:]]
            result.append(formatlist(r))
    return "\n".join(result)


def get_property_tree(
    node: Union[Node, type], skip: Union[List[str], None] = None, n_levels=-1
) -> str:
    """
    !@brief Returns all node subtypes and their attributes in a tree format.
    """
    start = "[KEY_OR_TAG]: [EXPECTED_TYPE] [REQUIRED or = DEFAULT_VALUE]\n"
    start += "├─ SUBNODES (If applicable)\n"
    start += "\n"
    start += node.__name__ + "\n"
    return start + _get_property_tree(node, skip, n_levels)


def _get_property_tree(
    node: Union[Node, type], skip: Union[List[str], None] = None, n_levels=-1
) -> str:
    """
    !@brief Returns all node subtypes and their attributes in a tree format.
    """
    if n_levels == 0:
        return ""
    result = []
    skip = [] if skip is None else skip
    specifiers = []

    def replace_vpipes_with_str(
        s: str, replace_with: str, gap: int = 10
    ) -> str:
        lines = s.split("\n")
        i = gap
        start_idx = gap
        while i < len(lines):
            l = lines[i]
            if l[0] == "\u2502":
                pipelen = i - start_idx
                if pipelen == len(replace_with):
                    for j in range(start_idx, i):
                        lines[j] = replace_with[j - start_idx] + lines[j][1:]
                    start_idx = i + gap
                    i += gap
            else:
                start_idx = i + 1
            i += 1
        return "\n".join(lines)

    for k, v in list(node._get_type_specifiers().items()):
        if is_subclass(node, ListNode):
            default = ""
        elif v.part_name_match and v.no_change_key:
            k = f"*{k}*"
            default = "Optional"
        elif v.default is default_unspecified_:
            default = "REQUIRED"
        else:
            default = f"= '{'None' if v.default is None else v.default}'"

        rt = v.required_type
        if not isinstance(rt, (list, tuple)):
            rt = [rt]
        if all([not is_subclass(x, Node) for x in rt]):
            rt = ("/".join([str(getattr(y, "__name__", y)) for y in rt]),)

        rt = list(rt)
        specs_strs = [r.__name__ if isinstance(r, type) else r for r in rt]

        for s, r in zip(specs_strs, rt):
            specifiers.append((k, r, default, s))

    for i, (k, v, default, s) in enumerate(specifiers):
        pipechar = f"\u251C" if i < len(specifiers) - 1 else "\u2514"
        vpipe = f"\u2502" if i < len(specifiers) - 1 else " "
        if v in skip:
            result.append(f"{pipechar}\u2500 '{k}': {s} {default} ...")
        else:
            result.append(f"{pipechar}\u2500 '{k}': {s} {default}")
            if is_subclass(v, Node):
                subtree = _get_property_tree(v, skip + [v], n_levels - 1)
                if subtree:
                    subtree = replace_vpipes_with_str(subtree, k)
                    result.append(
                        f"{vpipe}  " + subtree.replace("\n", f"\n{vpipe}  ")
                    )
    return "\n".join(result)
