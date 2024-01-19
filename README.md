## About
timeloopfe is a Python front-end interface to the Timeloop infrastructure,
which allows users to model tensor accelerators and explore the vast space of
architectures, workloads, and mappings.

Over the original Timeloop infrastructure, timeloopfe provides a richer
interface with a newly-designed architecture speficiation, processing /
automation tools, and a Python interface. The new interface also includes
rigorous type-checking and is fully extensible.


## Native Install
This install will:
- Install timeloop_model and timeloop_mapper on your system. This will NOT
  interfere with the existing timeloop-model and timeloop-mapper installations.
- Install the new Accelergy infrastructure, which is backwards compatible with
  the old infrastructure.

Run the following commands:
```bash
git clone https://github.com/Accelergy-Project/timeloopfe.git
cd timeloopfe
make install_infrastructure # Update accelergy & plug-ins to v4
make install_timeloop
pip3 install .
make clean
```

### Migrating from Timeloop v3
timeloopfe accepts either the existing v3 Timeloop input specification or the
new v4 specifications. The new v4 specification includes a new architecture
specification and new features.

timeloopfe also brings changes to the existing v3 specification. The previous
v3 interface uses a mix of dashes and underscores in its naming, and it accepts
multiple synonyms for the names of many objects. The new interface uses
underscores exclusively, and it uses a single name for each object.

The new keywords and new architecture specification are both optional. Based on
what features you want to use, you can choose to use the new keywords or
the new keywords + new architecture specification. The commands needed for
each are shown below:
- **BACKWARDS COMPATIBLE:** old specification, old keywords/synonyms (dashes & underscores): Use ```timeloopfe.v3spec```, ```tl.model(..., legacy_timeloop=True)```, and ```tl.mapper(..., legacy_timeloop=True)```.
- **NOT BACKWARDS COMPATIBLE:** old specification, new keywords (underscores only): Use ```timeloopfe.v3spec```, ```tl.model(...)```, and ```tl.mapper(...)```.
- **FULLY-NEW SPECIFICATION \<Recommended\>** new specification, new keywords (underscores only): Use ```timeloopfe.v4spec```, ```tl.model(...)```, and ```tl.mapper(...)```.

To update to the new keywords, use the ```update_timeloop_inputs.py``` script,
which automatically changes all dashed names to underscored names. Synonyms
will need to be updated manually. Built-in error checking will help you find
any synonym errors; simply run your file with the new interface and it will
tell you what needs to be changed.

To run ```update_timeloop_inputs.py```, place it in a directory with your input
files and run it with ```python3 update_timeloop_inputs.py```. It will
recursively search for all files in the directory and update them in-place.
Before making any changes, it will print a list of all changes to be made and
ask for confirmation.

## Examples
The ```examples``` directory contains examples of architecture
specifications written in the new format. There are three files of interest in
most examples:
- ```arch.yaml``` contains the architecture specification.
- ```arch_split.yaml``` contains the architecture specification, with
  constraints separated into a separate list. The specification is agnostic to
  whether constraints are specified in the object they constrain or in a
  separate list.
- ```arch_old.yaml``` contains the architecture specification in the old
  Timeloop format. This is provided for comparison.

### Running the Example Script
Any of the example architectures can be run by calling 
```python
python3 example.py <example number>
``` 
where ```<example number>``` is the number of the example. A full list of
examples can be shown by running ```python3 example.py -h```.

### Learning the for Experienced Timeloop Users
The specification format is designed to be easy to learn for experienced
Timeloop users. Explore the ```examples``` for examples of
architectures written in the old and new formats.

## Using timeloopfe
There are three steps to using Timeloop with timeloopfe:
1. Create a specification. This can be done by loading a YAML file, creating a
   specification from Python objects, or a combination of the two.
2. Process the specification. This calls a series of processors that apply
   changes to the specification. A standard suite of processors is provided in
   ```timeloopfe.processors.v4_standard_suite```, and custom processors can be
   created by subclassing ```timeloopfe.processors.Processor```.
3. Call Timeloop. Timeloop model or mapper can be called with the processed
   specification.

A full example is shown below:

```python
import timeloopfe as tl
from timeloopfe.v4spec.specification import Specification
from timeloopfe.processors.v4_standard_suite import STANDARD_SUITE

# Load a specification from a YAML file
spec = Specification.from_yaml_files(
    ["A.yaml", "B.yaml"]
    processors=STANDARD_SUITE
)

spec.process()
tl.model(spec, './outputsdir') # or tl.mapper or tl.accelergy
```

To run Timeloop using the old specification, use the following:
```python
import timeloopfe as tl
from timeloopfe.v3spec.specification import Specification
from timeloopfe.processors.v3_standard_suite import STANDARD_SUITE

# Load a specification from a YAML file
spec = Specification.from_yaml_files(
    ["A.yaml", "B.yaml"]
    processors=STANDARD_SUITE
)

tl.model(spec, './outputsdir') # or tl.mapper or tl.accelergy
# use tl.model(spec, './outputsdir', legacy_timeloop=True) to use the old
# keywords (mix of dashes and underscores, synonyms)
```

### Step 1: Creating a Specification
The top-level Specification object is the root of the specification. It is a
dictionary of objects, each of which contains another input to Timeloop.
Specifications can be loaded from YAML files or created from Python objects.
The ```Specification.from_yaml_files``` method is the YAML entry point, which
takes a list of YAML files as input. Each YAML file should contain a dictionary
at the top level. Keyword arguments can express additional top-level objects.

When the specification is initialized, sub-objects are hierarchically
initialized.

YAML files are structured as nested lists and maps (dictionaries). These will
be converted into Python objects. Keys and tags are to determine the structure
of YAML input files. Most maps have a set of expected keys, where each key has
an expected value type. Likewise, most lists have a set of expected tags, where
each tag has an expected value type. The parser will raise an error if a key or
tag is missing or unknown.

```yaml
# EXAMPLE:
#    The specification expects a top_level_dict with two keys: key1 and key2.
#    Key1 is a str, and key2 is a list. The list expects two tags: !A and !B.
#    !A is a str, and !B is an int.

top_level_dict: # Specification says key1 is a str and key2 is a list
  key1: value1
  key2:
    - !A # Tag !A tells the parser to expect a str
      abc
    - !B # Tag !B tells the parser to expect an int
      123
```

All keys and tags are context-dependent. A tree of expected keys, tags, and
types can be shown by running the following:
```python
from timeloopfe.v4spec.specification import Specification
from timeloopfe.parsing.doc import get_property_tree
print(get_property_tree(Specification))
```

Common sources of errors may be:
- An unexpected type (e.g., string where an integer is expected)
- A missing key or tag
- An unknown key or tag

### Step 2: Processing the Specification
The specification can be processed by calling the ```process``` method, which
sequentially calls the list of processors provided to the ```Specification```
constructor. The ```STANDARD_SUITE``` is a list of processors that are
recommended.

Of course, the specification can be edited directly instead of via processors.
However, processors are useful for portability.

Numerous methods are available to help crawl & process the specification. We
recommend looking through the example processors in the
```timeloopfe.processors.v4_standard_suite``` module for examples.

#### Creating Your Own Processors
To write your own processors, you may subclass
```timeloopfe.processors.Processor```. Processors are given a logger object and
the specification to process. Each edits the specification in-place. Look at
any of the processors in the ```timeloopfe.processors.v4_standard_suite```
module for examples. The
```timeloopfe/processors/v4suite/constraint_attacher.py``` is a good starting
point; it contains a simple example of a processor that attaches constraints to

Processors may define extra keys or tags that they use in the architecture
specification. They may do so in their init_elems method, which is called
before parsing begins. For example, code below shows a simple processor. The
```SimpleProcessor``` class defines defines a key ```simple_processor_attr```
for the Problem class. The value under the key is a string with a default value
of "". As this key is not natively supported, it should be removed by the
```SimpleProcessor``` in the ```process()``` method. If the
```SimpleProcessor``` does not remove the key, an error will be raised.

```python
from timeloopfe.v4spec.problem import Problem

class SimpleProcessor(Processor):
    """!@brief An example simple processor."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info("Initializing SimpleProcessor")

    def init_elems(self):
        """!@brief Initialize the elements that the processor handles."""
        with self.responsible_for_removing_elems():
            Problem.init_elem("simple_processor_attr", str, "")

    def process(self):
        """!@brief Process the specification. Remove elements that this
        processor is responsible for."""
        if "simple_processor_attr" in self.spec.problem:
            del self.spec.problem["simple_processor_attr"]
            self.logger.info('Deleted "simple_processor_attr"')
```

### Step 3: Calling Timeloop
Timeloop is called by the ```timeloopfe.model``` and ```timeloopfe.model```
functions. Accelergy verbose can be called with ```timeloopfe.accelergy```.
These functions are called using the following interface:

```python
def call_timeloop_mapper(
    specification: "Specification",
    output_dir: str,
    environment: Optional[Dict[str, str]] = None,
    extra_input_files: Optional[List[str]] = None,
    dump_intermediate_to: Optional[str] = None,
    log_to: Optional[Union[str, IO]] = None,
    legacy_timeloop: bool = False,
) -> int:
    """!@brief Call Timeloop Mapper from Python
    !@param specification The specification with which to call Timeloop.
    !@param input_content The content of the input file.
    !@param output_dir The directory to run Timeloop in.
    !@param environment A dictionary of environment variables to pass to
                        Timeloop.
    !@param extra_input_files A list of extra input files to pass to Timeloop.
    !@param dump_intermediate_to If not None, dump the input content to this
                                 file before calling Timeloop.
    !@param log_to If not None, log the output of the Timeloop call to this
                   file or file-like object.
    !@param legacy_timeloop If True, use the legacy Timeloop command.
    !@return The return code of the Timeloop call.
    """
```

## New v4 Architecture Specification
Check out the ```examples``` directory for examples of architecture
specifications.

The architecture is composed of leaf and branch nodes. Leaf nodes represent
objects in the architecture, while branch nodes represent the organization of
other nodes. Branches can be nested.

### Leaf Nodes
Leaf nodes denote the objects within an architecture.

Leaf objects are denoted in the following way:
```yaml
- !<LEAF_NOUN>
  attributes: {Dictionary of attributes}
  spatial: {meshX: <int>, meshY: <int>}
  constraints: {Dictionary of constraints}
```

The following types of leaves are supported. Notice that *the name of each leaf
is a noun describing the type of leaf*
- ```!Element``` objects include storage and compute units.
- ```!Container``` objects encompass other objects. They can be used to group
  objects together for the purpose of applying constraints or attributes to
  them.
- ```!Nothing``` objects are represent empty space or a lack of node in a
  location. For example, a ```!Nothing``` node may be used in a ```!Parallel```
  branch to process data that skips all other nodes in the branch.


### Branch Nodes
Branch nodes denote the organization of nodes in an architecture. Each branch
is a collection of nodes that are related to each other in some way. Branches
can be nested to any depth.

Branch objects are denoted in the following way:
```yaml
- !<BRANCHTYPE_ADJECTIVE>
  nodes: [List of nodes in this branch]
```

The following types of branches are supported. Notice that *the name of each
branch is an adjective describing the relations between the nodes it contains:*
- ```!Hierarchical``` nodes can move data between nodes that are lower/higher
  in the hierarchy. Nodes lower in the hierarchy (further from main memory) can
  use higher-level nodes as backing memory.
- ```!Pipelined``` nodes can not move data flexibly; each piece of data
  entering one end of the pipeline will exit the other end.
- ```!Parallel``` nodes process disjoint sets of data in parallel. Each
  dataspace traversing the parallel branch must traverse exactly one of the
  nodes within the branch.

### Expressing Spatial Fanout
Spatial fanout is expressed by adding a ```spatial``` attribute to a leaf node.
Under a hierarchy, this spatial fanout will be applied to all subsequent nodes
in the hierarchy. Multiple spatial fanouts in a hierarchy will be multiplied
together.

Spatial constraints are applied "between" the spatial elements in a fanout. For
example, consider the following:

```yaml
nodes: # Top-level hierarchy
- !Container
  name: top

- !Container # PE
  name: PE
  spatial: {meshY: 12}
  constraints:
    spatial: {factors: [P=12]}

- !Element # Storage
  name: spad
  class: storage
  attributes: {Omitted for brevity}

- !Element # MAC unit
  name: mac
  class: intmac
  attributes: {Omitted for brevity}
```

In this example, there are 12 PEs in the Y dimension of the array. Each PE has
a scratchpad and a MAC unit. A spatial factor of ```P=12``` is applied to the
PEs, meaning that each PE will process a different index of the ```P```
dimension of workload tensors.

Spatial fanouts are not allowed under pipeline or parallel branches.

### A Full Example
Below is the full specification of the Eyeriss architecture. Eyeriss has a DRAM
main memory, a global buffer for inputs and outputs, and a 2D array of
processing elements (PEs). Each PE has three parallel scratchpads to store
inputs, weights, and outputs. Each PE also has a MAC unit to perform
computations.

Containers are used to group the PEs together into a 2D array. We use two
levels of container to represent different spatial constraints for the X and Y
dimensions of the array.

A mix of block and flow style YAML is used. In general, flow style is used for
short lists / maps that can fit in a single line, while block style is used for
everything else.

```yaml
architecture:
  # ============================================================
  # Architecture Description
  # ============================================================
  version: 0.4
  nodes: # Top-level is hierarchical
  - !Element # DRAM main memory
    name: DRAM
    class: DRAM
    attributes: {type: "LPDDR4", width: 64, block_size: 8, datawidth: 8}

  - !Container # Eyeriss accelerator
    name: eyeriss
    attributes: {technology: "32nm"}
      
  - !Element # Global buffer for inputs & outputs
    name: shared_glb
    class: smartbuffer_SRAM
    attributes:
      memory_depth: 16384
      memory_width: 64
      n_banks: 32
      block_size: 8
      datawidth: 8
      read_bandwidth: 16
      write_bandwidth: 16
    constraints:
      dataspace: {keep: [Inputs, Outputs], bypass: [Weights]}

  - !Container # Each column of PEs produces a different psum row
    name: PE_column
    spatial: {meshX: 14}
    constraints:
      spatial:
        permutation: [N, C, P, R, S, Q, M]
        factors: [N=1, C=1, P=1, R=1, S=1]
        split: 7

  - !Container # Each PE in the column receives a different filter row
    name: PE
    spatial: {meshY: 12}
    constraints:
      spatial:
        split: 4
        permutation: [N, P, Q, R, S, C, M]
        factors: [N=1, P=1, Q=1, R=1]

  - !Parallel # Input/Output/Weight scratchpads in parallel
    nodes:
    - !Element # Input scratchpad
      name: ifmap_spad
      class: smartbuffer_RF
      attributes: {memory_depth: 12, memory_width: 16, datawidth: 8}
      constraints:
        dataspace: {keep: [Inputs]}
        temporal:
          permutation: [N, M, C, P, Q, R, S]
          factors: [N=1, M=1, C=1, P=1, Q=1, R=1, S=1]

    - !Element # Weight scratchpad
      name: weights_spad
      class: smartbuffer_RF
      attributes: {memory_depth: 192, memory_width: 16, datawidth: 8}
      constraints:
        dataspace: {keep: [Weights]}
        temporal: {factors: [N=1, M=1, P=1, Q=1, S=1]}

    - !Element # Output scratchpad
      name: psum_spad
      class: smartbuffer_RF
      attributes: 
        memory_depth: 16
        memory_width: 16
        datawidth: 16
        update_fifo_depth: 2
      constraints:
        dataspace: {keep: [Outputs]}
        temporal: {factors: [N=1, C=1, R=1, S=1, P=1, Q=1]}


  - !Element # MAC unit
    name: mac
    class: intmac
    attributes: {multiplier_width: 8, adder_width: 16}
```

### Other Inputs
Other inputs (e.g., constraints, mapper, sparse_optimizations) largely follow
the same format as existing Timeloop inputs. See the Timeloop documentation for
more information, or use the following commands to see the full structure of
all inputs:
```python
from timeloopfe.v4spec.specification import Specification
from timeloopfe.parsing.doc import get_property_tree
print(get_property_tree(Specification))
