# EXP-20261005-0003 - append-only CUDA telemetry clarification

The completed analysis said the PVM harness did not measure peak CUDA allocator/reservation bytes. That wording was too broad: the trusted WorkerResources source reset cumulative peaks at worker start and sampled torch.cuda.max_memory_allocated/max_memory_reserved every0.1s. The preserved device journals contain these observations. They were omitted from the previous report and lack a guaranteed synchronized final boundary sample. Treat them as sampled cumulative observations,not exact final peaks,inference-only memory,total driver/context VRAM or energy. No completed plan,result,gate or decision changes.

Archived device records=85; maximum last-sample allocated=80080896bytes; reserved=98566144bytes. Full raw bytes remain in the immutable0003 runtime archive.

New prospectively frozen v9 adds synchronized phase/final allocator snapshots and distinct RSS reporting. Its measured timings,models and scientific gates remain unchanged; instrumentation overhead is charged.
