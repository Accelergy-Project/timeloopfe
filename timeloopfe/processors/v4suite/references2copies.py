"""!@brief Converts references to copies in the specification."""
import copy
from typing import Any

from timeloopfe.v4spec.arch import Leaf
from ...processors.processor import Processor
from ...parsing.nodes import (
    Node,
)

logger = None
seen_ids = set()
visited = []


def refs2copies(n: Node):
    """!@brief Converts references to copies in the specification."""
    visited.append(n)  # Avoid garbage collection
    for i, x in n.items():
        if any(type(x) is t for t in [int, float, str, bool, type(None)]):
            continue
        if id(x) not in seen_ids:
            seen_ids.add(id(x))
            continue

        if isinstance(x, Node):
            logger.debug("Copying %s", str(x))  # type: ignore
            x.parent_node = None  # We'll fix this later
        n[i] = copy.deepcopy(x)
        seen_ids.add(id(n[i]))


# returned_ids = set()
# returned_id_2_obj = {}


def refs2copies_fast(n: Any, depth=0, seen_ids=None, visited=None) -> Any:
    if seen_ids is None:
        seen_ids = set()
    if visited is None:
        visited = []
    visited.append(n)  # Avoid garbage collection
    if isinstance(n, Node):
        n.parent_node = None

    if id(n) in seen_ids:
        n = copy.deepcopy(n)
    seen_ids.add(id(n))

    if not isinstance(n, Node):
        return n

    if isinstance(n, Node):
        for i, x in n.items():
            logger.debug(
                "Depth %s Copying %s in %s[%s]", depth, str(x), str(n), i
            )  # type: ignore
            n[i] = refs2copies_fast(x, depth + 1, seen_ids, visited)
            if isinstance(n[i], Node):
                n[i].parent_node = n
        n.parent_node = None
        # if id(n) not in seen_ids:
        #     seen_ids.add(id(n))
        #     return n

    # Check if we've already returned this node
    # if any(type(n) is t for t in [int, float, str, bool, type(None)]):
    #     return n
    # if id(n) in returned_ids:
    #     raise Exception("Already returned this node")
    # returned_ids.add(id(n))
    # returned_id_2_obj[id(n)] = n
    return n


def set_parents(n: Node):
    for _, x in n.items():
        if isinstance(x, Node):
            x.parent_node = n


class References2CopiesProcessor(Processor):
    """!@brief Converts references to copies in the specification."""

    def process(self):
        super().process()
        global logger
        logger = self.logger
        global seen_ids
        seen_ids = set()
        global visited
        visited = []
        if False:
            self.spec.recursive_apply(refs2copies)
            self.spec.recursive_apply(set_parents)
        else:
            processors = self.spec.processors
            self.spec.processors = []
            refs2copies_fast(self.spec)
            self.spec.processors = processors
