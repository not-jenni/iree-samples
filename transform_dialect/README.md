# Transform Dialect Tooling

This directory contains a few simple tools to enhance productivity of IREE
experiments based on the transform dialect.

## Script

Contains shell functions that simplify running IREE tools with the transform 
dialect. These should generally considered brittle and may be useful to some.

Assumptions are:
  1. execution starts from the IREE source dir root
  2. the IREE build directory lives at `./build`
  3. `./build/tools` is in the path 
  4. for CUDA execution, `nvprof` is in the path.


Disclaimers:
  1. since the exploration process can involve modfying source IR, transform IR
  and the compiler itself, each command compiles what it needs to simplify and 
  automate the process. This may be surprising if one does not want recompilation
  to occur.
  2. examples are restricted to the CUDA case for now.
  3. examples are restricted to 2-D redution cases for now.
  4. the stub file should have only 1 function for now, until we add a simple
  mlir-extract like tool to focus on a single function or until we have a better
  way to export transform IR and apply it to payload IR in different processes.

Note: the underlying helper functions `iree-transform-xxx` can be parameterized to
other backends and CUDA is not a stong restriction, just a convenience.

### Create a New Problem To Map

Run:
```
(\
  benchmark-transform-create \
  tests/transform_dialect/cuda/benchmark_linalg_reductions.stub.mlir \
  reduction_2d_static \
  123 \
  456 \
)
```

This should print something resembling:
```
==========================================================
Problem created successufully, reproduction instructions:
==========================================================
Transform dialect source file is: /tmp/reduction_2d_static_123x456.mlir
Transform dialect transform file is: /tmp/iree_transform_dialect_ac2e60.mlir
Dump transformed IR with: benchmark-transform-run-iree-opt /tmp/reduction_2d_static_123x456.mlir /tmp/iree_transform_dialect_ac2e60.mlir
Dump transformed PTX with: benchmark-transform-run-iree-compile /tmp/reduction_2d_static_123x456.mlir /tmp/iree_transform_dialect_ac2e60.mlir
Run nvprof with e.g.: benchmark-transform-run-nvprof /tmp/reduction_2d_static_123x456.mlir /tmp/iree_transform_dialect_ac2e60.mlir reduction_2d_static 123 456
==========================================================
```


### Produce Transformed IR

Manually modify the content of the transform IR file (or not) (i.e. /tmp/iree_transform_dialect_ac2e60.mlir), then run:

```
( \
  benchmark-transform-run-iree-opt \
  /tmp/reduction_2d_static_123x456.mlir \
  /tmp/iree_transform_dialect_ac2e60.mlir \
)
```

This should print the transformed IR (or appropriate error messages when relevant).

This provides an easy to interact with interpreted mode.

### Produce Transformed PTX

Once the transformed IR is in a satisfactory state, one can inspect the PTX.

```
( \
  benchmark-transform-run-iree-compile \
  /tmp/reduction_2d_static_123x456.mlir \
  /tmp/iree_transform_dialect_ac2e60.mlir \
)
```

This should print the transformed PTX (or appropriate error messages when relevant).

## Run and Benchmark

The following requires nvprof to be in the PATH.

When things look good, one can execute, get a filtered nvprof trace and a rough
estimate of the performace by pasting the last repro command:

```
( 
  benchmark-transform-run-nvprof \
  /tmp/reduction_2d_static_123x456.mlir \
  /tmp/iree_transform_dialect_ac2e60.mlir \
  reduction_2d_static \
  123 \
  456 \
)
```

Prints something resembling:
```
==========================================================
Reproduction instructions:
iree-transform-compile /tmp/reduction_2d_static_123x456.mlir -b cuda -c /tmp/iree_transform_dialect_ac2e60.mlir -- --iree-hal-benchmark-dispatch-repeat-count=6 | \
nvprof --print-gpu-trace iree-run-module --entry_function=reduction_2d_static --device=cuda --function_input="123x456xf32=1" | \
grep reduction_2d_static
==========================================================
==3499964== NVPROF is profiling process 3499964, command: iree-run-module --entry_function=reduction_2d_static --device=cuda --function_input="123x456xf32=1"
EXEC @reduction_2d_static
==3499964== Profiling application: iree-run-module --entry_function=reduction_2d_static --device=cuda --function_input="123x456xf32=1"
388.21ms  596.26us            (123 1 1)       (128 1 1)        18        0B      768B  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x456 [24]
388.80ms  3.2960us            (123 1 1)       (128 1 1)        18        0B      768B  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x456 [25]
388.81ms  2.8800us            (123 1 1)       (128 1 1)        18        0B      768B  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x456 [26]
388.81ms  2.9130us            (123 1 1)       (128 1 1)        18        0B      768B  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x456 [27]
388.82ms  2.8800us            (123 1 1)       (128 1 1)        18        0B      768B  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x456 [28]
388.82ms  2.8800us            (123 1 1)       (128 1 1)        18        0B      768B  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x456 [29]
reduction_2d_static --function_input="123x456xf32=1" P50: 2880.0000 ns 19.47500000000000000000 GElements/s
```

Note how the first instance takes significantly longer due to initial host->device
memory copies.

The reproduction instructions can be run independently and adapted.

It is the responsibility of the user to convert the number of elements processed
per second (i.e. the product of the sizes) to the relevant metric for the benchmark.
In the case of reduction_2d_static, a tensor<123x456xf32> is read and reduced into
a tensor<123xf32>. This corresponds to 4 bytes read per element and a negligible 
amount of bytes written per element.

This gives us roughly `80GB/s` read bandwidth, in `2.8us` (latency-bound).

We can generate and run another problem by adding the `run` argument:
```
( \
  benchmark-transform-create \
  tests/transform_dialect/cuda/benchmark_linalg_reductions.stub.mlir \
  reduction_2d_static \
  123 \
  45678 \
  run \
)
```

The various repro instructions are printed and the problem is also run:
```
==3504051== NVPROF is profiling process 3504051, command: iree-run-module --entry_function=reduction_2d_static --device=cuda --function_input="123x45678xf32=1"
EXEC @reduction_2d_static
==3504051== Profiling application: iree-run-module --entry_function=reduction_2d_static --device=cuda --function_input="123x45678xf32=1"
427.44ms  10.241ms            (123 1 1)       (256 1 1)        24        0B  1.2500KB  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x45678 [24]
437.69ms  42.434us            (123 1 1)       (256 1 1)        24        0B  1.2500KB  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x45678 [25]
437.73ms  42.499us            (123 1 1)       (256 1 1)        24        0B  1.2500KB  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x45678 [26]
437.77ms  42.498us            (123 1 1)       (256 1 1)        24        0B  1.2500KB  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x45678 [27]
437.82ms  42.531us            (123 1 1)       (256 1 1)        24        0B  1.2500KB  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x45678 [28]
437.86ms  42.530us            (123 1 1)       (256 1 1)        24        0B  1.2500KB  NVIDIA GeForce          1        13                     -                -  reduction_2d_static_dispatch_0_generic_123x45678 [29]
reduction_2d_static --function_input="123x45678xf32=1" P50: 42499.000 ns 132.20061648509376691216 GElements/s
```

This corresponds to roughly `528GB/s` read bandwidth.

As a rough point of reference, running the CUDA samples 
[bandwidth test](https://github.com/NVIDIA/cuda-samples/tree/master/Samples/1_Utilities/bandwidthTest) on this auhor's machines prints:

```
[CUDA Bandwidth Test] - Starting...
Running on...

 Device 0: NVIDIA GeForce RTX 2080 Ti
 Quick Mode

 Host to Device Bandwidth, 1 Device(s)
 PINNED Memory Transfers
   Transfer Size (Bytes)        Bandwidth(GB/s)
   32000000                     7.8

 Device to Host Bandwidth, 1 Device(s)
 PINNED Memory Transfers
   Transfer Size (Bytes)        Bandwidth(GB/s)
   32000000                     9.0

 Device to Device Bandwidth, 1 Device(s)
 PINNED Memory Transfers
   Transfer Size (Bytes)        Bandwidth(GB/s)
   32000000                     519.5

Result = PASS
```
