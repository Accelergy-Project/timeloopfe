"""!@brief Standard suite of processors for timeloopfe."""

from .v4suite import (
    constraint_attacher,
    constraint_macro,
    enable_dummy_table,
    mapspace_size_contributors,
    math,
    permutation_optimizer,
    references2copies,
    variables_from_cli,
    sparse_opt_attacher,
    required_actions,
    dataspace2branch,
)


ConstraintAttacherProcessor = constraint_attacher.ConstraintAttacherProcessor
ConstraintMacroProcessor = constraint_macro.ConstraintMacroProcessor
Dataspace2BranchProcessor = dataspace2branch.Dataspace2BranchProcessor
EnableDummyTableProcessor = enable_dummy_table.EnableDummyTableProcessor
MapspaceSizeContributorsProcessor = (
    mapspace_size_contributors.MapspaceSizeContributorsProcessor
)
MathProcessor = math.MathProcessor
PermutationOptimizerProcessor = (
    permutation_optimizer.PermutationOptimizerProcessor
)
References2CopiesProcessor = references2copies.References2CopiesProcessor
VariablesFromCLIProcessor = variables_from_cli.VariablesFromCLIProcessor
SparseOptAttacherProcessor = sparse_opt_attacher.SparseOptAttacherProcessor
RequiredActionsProcessor = required_actions.RequiredActionsProcessor
# Order matters here. The processors will be run in the order they appear in
# this list.
STANDARD_SUITE = [
    References2CopiesProcessor,
    ConstraintAttacherProcessor,
    SparseOptAttacherProcessor,
    ConstraintMacroProcessor,
    MathProcessor,
    Dataspace2BranchProcessor,
    PermutationOptimizerProcessor,
    RequiredActionsProcessor,
    MapspaceSizeContributorsProcessor,
]
