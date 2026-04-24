# Overview
This repository presents a sample workflow of collective algorithm generation & simulation using the Chakra ET representation.

Users define custom collective algorithms using the MSCCLang DSL, where the resulting collective algorithm is represented in Chakra ET.
This Chakra ET representation of the *collective algorithm* is fed into the ASTRA-sim distributed ML simulator, along with the *workload* represented in Chakra ET.

A detailed discussion on the background of this work and motivation for a common collective algorithm representation is provided in our paper, "Towards a Standardized Representation for Deep Learning Collective Algorithms" ([arxiv link](https://arxiv.org/abs/2408.11008)). Also citable by:

>@ARTICLE{10910230,
  author={Yoo, Jinsun and Won, William and Cowan, Meghan and Jiang, Nan and Klenk, Benjamin and Sridharan, Srinivas and Krishna, Tushar},
  journal={IEEE Micro}, 
  title={Toward a Standardized Representation for Deep Learning Collective Algorithms}, 
  year={2025},
  volume={45},
  number={2},
  pages={46-55},
  doi={10.1109/MM.2025.3547363}}



## Directory Structure
The repository is a collection of the following submodules:
```
- astra-sim: The ASTRA-sim simulator and its collective API extension. This collective API extension allows users to define the collective algorithm, instead of using or writing the default algorithms defined in the simulator's System layer. 
- chakra: An updated version which includes the converter from MSCCL-IR to Chakra ET for collective communication algorithms. 
- msccl-tools (as-is): Provides examples of the MSCCLang DSL to define collective algorithms.
- visualizer: A tool to visualize a collective algorithm represented with Chakra using TEN. 
```

# Running the Workflow
## Setup
```bash
git clone git@github.com:mlcommons/chakra
cd chakra
pip install .

git clone git@github.com:astra-sim/collectiveapi​
cd collectiveapi​
git submodule init​
git submodule update​
cd msccl-tools​
pip install .
```

## Generating Collective Algorithm ET
```
cd $REPO_PATH
mkdir demo_allreduce
python3 msccl-tools/examples/mscclang/allreduce_a100_ring.py \
    64 1 1 > \
    demo_allreduce/mscclir.xml

python chakra_converter/et_converter.py \
    --input_filename ./demo_allreduce/mscclir.xml \
    --output_filename ./demo_allreduce/mscclang_graph
```

## Running the Simulation in ASTRA-sim
### Setting up Dependencies
Please refer to the [ASTRA-sim wiki](https://astra-sim.github.io/astra-sim-docs/getting-started/setup.html) for required setup environments. 

```bash
cd astra-sim
bash build/astra_analytical/build.sh
```

## Generating Workload ET
```bash
cd extern/graph_frontend/chakra
python3 -m utils.et_generator.et_generator --num_npus 64 --num_dims 1 --default_comm_size 16384
```


## Running the simulation
```bash
cd ../astra-sim
export SYSTEM_CONFIG="./inputs/system/Ring.json"
export MEMORY_CONFIG="./inputs/remote_memory/analytical/no_memory_expansion.json"
export WORKLOAD_CONFIG="./extern/graph_frontend/chakra/one_comm_coll_node_allreduce"
export NETWORK_CONFIG="./inputs/network/analytical/Ring.yml"

# Run
./build/astra_analytical/build/bin/AstraSim_Analytical_Congestion_Unaware \
    --workload-configuration=$WORKLOAD_CONFIG \
    --system-configuration=$SYSTEM_CONFIG \
    --network-configuration=$NETWORK_CONFIG \
    --remote-memory-configuration=$MEMORY_CONFIG
```

## Visualizing the algorithm
Please refer to [visualizer/README.md](visualizer/README.md)
