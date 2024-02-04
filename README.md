# About
The Timeloop Front-End (TimeloopFE) is a Python front-end interface to the
Timeloop infrastructure, which allows users to model tensor accelerators and
explore the vast space of architectures, workloads, and mappings.

TimeloopFE provides a rich Python interface, error checking, and automation
tools. With closely-aligned Python and YAML interfaces, TimeloopFE is designed
to enable easy design space exploration and automation.

### Installation
First, ensure that Timeloop and Accelergy are installed following the
[Timeloop+Accelergy install instructions](https://timeloop.csail.mit.edu/installation).

To install timeloopfe, run the following commands: 
```bash 
git clone https://github.com/Accelergy-Project/timeloopfe.git 
pip3 install ./timeloopfe
```

### Tutorials and Examples
Tutorials and examples available in the [Timeloop and Accelergy exercises
repository](https://github.com/Accelergy-Project/timeloop-accelergy-exercises.git).
In this repository, examples can be found in the `workspace/baseline_designs`
directory and tutorials can be found in the `workspace/exercises` directory.

### Minimal Usage
TimeloopFE interface provides two primary functions: - Input file gathering &
error checking - Python interface for design space exploration
```python 
import timeloopfe.v4 as tl
from joblib import Parallel, delayed

# Basic setup. Gathers input files, checks for errors
spec = tl.Specification.from_yaml_files(
  "your_input_file.yaml", "your_other_input_file.yaml"
) 
tl.call_mapper(spec, output_dir="your_output_dir")


# Multiprocessed design space exploration
def run_mapper_with_spec(buf_size: int):
  spec = tl.Specification.from_yaml_files(
    "your_input_file.yaml", "your_other_input_file.yaml"
  )
  spec.architecture.find("my_buffer").attributes.depth = buf_size
  return tl.call_mapper(spec, output_dir=f"outputs_bufsize={buf_size}")

buf_sizes = [1024, 2048, 4096, 8192, 16384]
results = Parallel(n_jobs=8)(
  delayed(run_mapper_with_spec)(buf_size) for buf_size in buf_sizes
)
```

Please visit the [Timeloop and Accelergy exercises
repository](https://github.com/Accelergy-Project/timeloop-accelergy-exercises.git)
for more examples and tutorials.
