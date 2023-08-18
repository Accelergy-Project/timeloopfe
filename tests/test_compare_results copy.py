import shutil
import threading
import unittest
import os

from accelergy.utils import yaml
from timeloopfe.version_transpilers.v4to3 import transpile

from timeloopfe.v4spec.specification import Specification

from timeloopfe.processors.v4_standard_suite import (
    References2CopiesProcessor,
    VariablesFromCLIProcessor,
    ConstraintMacroProcessor,
    ConstraintAttacherProcessor,
    Dataspace2BranchProcessor,
    MathProcessor,
    MapspaceSizeContributorsProcessor,
    EnableDummyTableProcessor,
)

PROBLEM_FILE = "problem.yaml"
MAPPER_FILE = "mapper_quick.yaml"


class TestCompareResults(unittest.TestCase):
    def grabstats(self, path: str) -> str:
        contents = open(path).read()
        # Grab contents between lines containing "Summary Stats" and "Computes"
        start, end = None, None
        for i, line in enumerate(contents.split("\n")):
            if "Summary Stats" in line:
                start = i
            if start is not None and "Computes" in line:
                end = i
                break
        return "\n".join(contents.split("\n")[start:end])

    def run_timeloop(self, start_dir: str) -> None:
        environ_vars = {
            "TIMELOOP_OUTPUT_STAT_SCIENTIFIC": "1",
            "TIMELOOP_OUTPUT_STAT_DEFAULT_FLOAT": "0",
            "TIMELOOP_ENABLE_FIRST_READ_ELISION": "0",
        }

        environstr = " ".join(k + "=" + v for k, v in environ_vars.items())
        cmd = f"cd {start_dir} ; {environstr} timeloop_mapper inputs/*.yaml >> output.log 2>&1"
        with open(os.path.join(start_dir, "output.log"), "w") as f:
            f.write(cmd + "\n")
            f.write("\n")
        os.system(cmd)

    def run_test(
        self,
        start_dir: str,
        raw_inputs: list = None,
        preproces_inputs: list = None,
        problem: str = PROBLEM_FILE,
        extra: str = "",
    ):
        if raw_inputs is None:
            raw_inputs = os.path.join(start_dir, "arch.yaml")
        if preproces_inputs is None:
            preproces_inputs = os.path.join(
                start_dir, "arch_new_constraints_in.yaml"
            )
        start_dir += extra

        if isinstance(raw_inputs, str):
            raw_inputs = [raw_inputs]
        if isinstance(preproces_inputs, str):
            preproces_inputs = [preproces_inputs]
        processors = [
            References2CopiesProcessor,
            VariablesFromCLIProcessor,
            ConstraintMacroProcessor,
            ConstraintAttacherProcessor,
            Dataspace2BranchProcessor,
            MathProcessor,
            MapspaceSizeContributorsProcessor,
            EnableDummyTableProcessor,
        ]

        this_script_dir = os.path.dirname(os.path.realpath(__file__))
        preproces_inputs = [
            os.path.join(this_script_dir, "..", "arch_spec_examples", i)
            for i in preproces_inputs + [problem, MAPPER_FILE]
        ]
        raw_inputs = [
            os.path.join(this_script_dir, "..", "arch_spec_examples", i)
            for i in raw_inputs + [problem, MAPPER_FILE]
        ]

        ppdir = os.path.join(
            this_script_dir, "compare", start_dir, "preprocessed"
        )
        rawdir = os.path.join(this_script_dir, "compare", start_dir, "raw")
        ppdir = os.path.abspath(ppdir)
        rawdir = os.path.abspath(rawdir)
        for target in [ppdir, rawdir]:
            if os.path.exists(target):
                shutil.rmtree(target)
            os.makedirs(target, exist_ok=True)
            os.makedirs(os.path.join(target, "inputs"), exist_ok=True)

        for f in raw_inputs:
            shutil.copy(f, os.path.join(rawdir, "inputs"))

        # Run the preprocdataspacesor
        spec = Specification.from_yaml_files(
            *preproces_inputs, processors=processors
        )
        spec.process()
        yaml.write_yaml_file(
            os.path.join(ppdir, "inputs/arch.yaml"), transpile(spec)
        )

        t1 = threading.Thread(target=self.run_timeloop, args=(ppdir,))
        t2 = threading.Thread(target=self.run_timeloop, args=(rawdir,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        o1 = open(os.path.join(ppdir, "output.log")).readlines()
        o2 = open(os.path.join(rawdir, "output.log")).readlines()
        headings = [
            "Factorization options",
            "LoopPermutation",
            "Spatial",
            "DatatypeBypass",
        ]
        o1 = [
            (i, l) for i, l in enumerate(o1) if any(h in l for h in headings)
        ]
        o2 = [
            (i, l) for i, l in enumerate(o2) if any(h in l for h in headings)
        ]
        for (i1, l1), (i2, l2) in zip(o1, o2):
            self.assertEqual(
                l1,
                l2,
                f"Line {i1}/output.log in {ppdir} differs "
                f"from line {i2}/output.log in {rawdir}",
            )

        for i, (l1, l2) in enumerate(zip(o1, o2)):
            if any(
                x in l1
                for x in [
                    "Factorization options",
                    "LoopPermutation",
                    "Spatial",
                    "DatatypeBypass",
                ]
            ):
                self.assertEqual(l1, l2, f"Line {i} differs")

        # Compare the results
        stats1 = os.path.join(ppdir, "timeloop_mapper.stats.txt")
        stats2 = os.path.join(rawdir, "timeloop_mapper.stats.txt")
        self.assertEqual(self.grabstats(stats1), self.grabstats(stats2))

    def test_eyriss_like(self):
        return self.run_test("eyeriss_like")

    def test_eyeriss_like_separate_constraints(self):
        return self.run_test(
            "eyeriss_like",
            preproces_inputs="eyeriss_like/arch_new.yaml",
            extra="_separate_constraints",
        )

    def test_simba_like(self):
        return self.run_test("simba_like")

    def test_simba_like_separate_constraints(self):
        return self.run_test(
            "simba_like",
            preproces_inputs="simba_like/arch_new.yaml",
            extra="_separate_constraints",
        )

    def test_simple_output_stationary(self):
        return self.run_test("simple_output_stationary")

    def test_simple_output_stationary_separate_constraints(self):
        return self.run_test(
            "simple_output_stationary",
            preproces_inputs="simple_output_stationary/arch_new.yaml",
            extra="_separate_constraints",
        )

    def test_simple_pim(self):
        return self.run_test("simple_pim")

    def test_simple_pim_separate_constraints(self):
        return self.run_test(
            "simple_pim",
            preproces_inputs="simple_pim/arch_new.yaml",
            extra="_separate_constraints",
        )

    def test_simple_weight_stationary(self):
        return self.run_test("simple_weight_stationary")

    def test_simple_weight_stationary_separate_constraints(self):
        return self.run_test(
            "simple_weight_stationary",
            preproces_inputs="simple_weight_stationary/arch_new.yaml",
            extra="_separate_constraints",
        )

    def test_sparse_tensor_core_like(self):
        return self.run_test(
            "sparse_tensor_core_like",
            problem="problem_sparse_tensor_core.yaml",
        )

    def test_sparse_tensor_core_like_separate_constraints(self):
        return self.run_test(
            "sparse_tensor_core_like",
            problem="problem_sparse_tensor_core.yaml",
            preproces_inputs="sparse_tensor_core_like/arch_new.yaml",
            extra="_separate_constraints",
        )
