# Independent event-pool engineering result

**Pass for the declared one-device resource preflight.** The exact frozen helper initialized and resolved all 65,536 event pairs / 131,072 CUDA events on pinned GPU0 in the pinned image, without a model, service or traffic. Source hashes match the prelaunch review; stdout is empty, exit code is zero, and all GPUs/containers were observed idle after cleanup. The independent supervisor disarmed after verifying idle.

Initialization took 1.387735 seconds; final resolution took 0.223248 seconds; script work took 2.062357 seconds. The component wrapper measured 4.389708 seconds / 0.001219363 visible-GPU-hours, and total supervision took 5.499941 seconds, within the 120-second ceiling. Process max RSS rose from 628,992 to 725,760 KiB during initialization, a 94.5 MiB increase, and ended at 731,136 KiB. CUDA device free memory was unchanged at the recorded resolution; PyTorch allocated/reserved memory was zero. These measurements do not establish that event resources consume no memory.

All empty event spans were finite and nonnegative, ranging 2.784 to 6.720 microseconds. They are engineering sanity measurements, not per-call overhead estimates for real inference. This result supports feasibility of the exact pool on one idle device. It does not prove equal eight-worker cost, unperturbed scheduling, candidate improvement or full live readiness. The separately required correctness, lifecycle, allocation and launch reviews remain in force.

- Pool result SHA256: `5452191a26eb2686ce584296107d7029e98c1a77cd212b5d35aa2ceaf0183f85`.
- Execution receipt: `057d02c309efa8203a9c9d5e7ee9477c35b1ecec67a011ae669829e9141229e0`.
- Helper: `94a09b758ee400f7e7de029b6c24b577eec1f37a6634161554399aa1e2eb034d`.
- Observer: `a09d9cbdfd5eb02a26df4468865286fc8bf2837ce1df1532d3113a924d4c9dbd`.
