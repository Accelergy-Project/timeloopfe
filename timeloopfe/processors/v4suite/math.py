"""!@brief Solves equations in the architecture, variables, and problem. """
import copy
import re
from typing import Union
from ...parsing.nodes import Node
from ...v4spec.arch import (
    ArchNode,
    Hierarchical,
    Parallel,
    Element,
    Container,
    Leaf,
)
from ...v4spec.specification import Specification
from accelergy.parsing_utils import (
    parse_expressions_sequentially_replacing_bindings,
)
from ...v4spec.problem import Problem
from ...processors.processor import Processor
from ...processors.v4suite.references2copies import References2CopiesProcessor


class MathProcessor(Processor):
    """!@brief Solves equations in the architecture, variables, and problem.
    The following rules are followed:
    - Variables:
        What is done: All expressions are solved
        Context available: Previous variables

    - Architecture attributes:
        What is done: All expressions are solved
        Context available: Variables, previous attributes, attributes of
                           containing containers
    - Architecture spatial:
        What is done: All expressions are solved
        Context available: Variables, attributes, attributes of containing
                           containers

    - Constraints:
        What is done: Variable names are substituted with their values. Full
                      expressions are not solved.
        Context available: Variables, attributes, attributes of containing
                           containers

    - Problem Factors:
        What is done: Variable names are substituted with their values. Full
                      expressions are not solved.
        Context available: Variables
    """

    def process(self):
        super().process()
        self.must_run_after(References2CopiesProcessor)
        variables = self._get_parsed_variables() if self.spec.variables else {}
        self._parse_architecture(variables)
        self._parse_problem(variables)

    def _get_parsed_variables(
        self, context: dict = None, variables: dict = None
    ) -> dict:
        context = {} if context is None else context
        variables = self.spec.variables if variables is None else variables
        variables.update(parse_expressions_sequentially_replacing_bindings(
            expression_dictionary=self.spec.variables,
            binding_dictionary={},
            location="top-level context variables ",
            strings_allowed=True,
        ))
        return variables

    def _parse_dictnode(
        self, context: dict, node: dict, name: str, strings_allowed: bool,
        propagate_required_keys: bool = False
    ) -> None:
        node.update(
            parse_expressions_sequentially_replacing_bindings(
                expression_dictionary=node,
                binding_dictionary=context,
                location=name,
                strings_allowed=strings_allowed,
                propagate_keys=propagate_required_keys,
            )
        )
        context = {**context, **node}
        for k, v in node.items():
            if isinstance(v, dict):
                self._parse_dictnode(
                    context, v, f"{name}.{k}", strings_allowed)

    def try_to_number(self, s: str) -> Union[int, float, str]:
        for totry in [int, float]:
            try:
                return totry(s)
            except ValueError:
                pass
        return s

    def var_replace(self, node: Node, context: dict) -> None:
        for k, v in node.items():
            if isinstance(v, str):
                for k2, v2 in context.items():
                    # Only match whole words
                    v = re.sub(rf"\b{k2}\b", str(v2), v)
                node[k] = self.try_to_number(v)

    def _parse_architecture(self, context=None, node: ArchNode = None) -> dict:
        context = self.spec.variables if context is None else context
        node = self.spec.architecture if node is None else node

        if isinstance(node, (Hierarchical, Parallel)):
            context = {**context}
            for n in node.nodes:
                if isinstance(n, Leaf):
                    context.setdefault(n.name, n)
            for e in node.nodes:
                self._parse_architecture(context, e)

        elif isinstance(node, Leaf):
            self._parse_dictnode(
                context, node.attributes, f"{node.name} attributes", True, True
            )
            new_context = {**context, **node.attributes}
            self._parse_dictnode(
                context, node.spatial, f"{node.name} spatial", False, False
            )
            node.constraints.recursive_apply(
                lambda c: self.var_replace(c, new_context)
            )
            if isinstance(node, Container):
                context = new_context
            if node.name not in context:
                context[node.name] = node

        return context

    def _parse_problem(self, context=None, problem: Problem = None) -> dict:
        context = self.spec.variables if context is None else context
        problem = self.spec.problem if problem is None else problem
        problem.recursive_apply(lambda x: self.var_replace(x, context))
