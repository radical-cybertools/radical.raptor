# RADICAL-Raptor

Raptor is a master/worker executor for high-throughput tasks on HPC
allocations. A `RaptorMaster` runs three ZMQ bridges (request, result and
control) built on [radical.utils](https://github.com/radical-cybertools/radical.utils).
Workers are typically started one per node via `srun`. They pull tasks in
bulk and run them in a pool of slots: executables via fork/exec, Python
functions in-slot. Load balancing comes from the pull model itself, so there
is no central scheduler.

## Installation

```sh
pip install .                  # core: radical.utils, cloudpickle
pip install '.[rhapsody]'      # plus the rhapsody execution backend (Python >= 3.11)
```

## Usage

```python
import radical.raptor as rr

master = rr.RaptorMaster(workdir='/shared/fs/run', bulk_size=16,
                         result_cb=lambda task, state: print(task['uid'], state))

# start workers, e.g. one per node inside a Slurm allocation:
#   srun --nodes=N --ntasks=N --ntasks-per-node=1 \
#        python -m radical.raptor.worker --info /shared/fs/run/raptor.master.json
# (master.worker_cli_args() gives the same addresses as CLI arguments)

master.wait_workers(count=2)
master.submit([{'uid': 'task.%06d' % i, 'executable': '/bin/date'}
               for i in range(1000)])
master.wait()
master.terminate()
```

Tasks are plain dicts:
- **executable tasks:** `executable`, `arguments`, `environment`, `cores`,
  `timeout`;
- **function tasks:** `mode='function'`, `function_blob` (a path to a
  cloudpickled callable on a shared filesystem), `args`, `kwargs`.

Results carry `stdout`, `stderr`, `exit_code` and, for function tasks,
`return_value`.

### With rhapsody

`radical.raptor.rhapsody_backend.RaptorBackend` is a
[rhapsody](https://github.com/radical-cybertools/rhapsody) execution backend.
It attaches to a rhapsody `Session` like the built-in backends, launches the
workers via `srun` itself, and accepts both executable and function
`ComputeTask`s.

### Examples

- `examples/driver.py`: master plus local or srun workers, with a throughput
  report.
- `examples/rhapsody_session.py`, `examples/rhapsody_bench.py`: Raptor
  through a rhapsody `Session`.
- `examples/slurm/launch.sh`: master and an explicit `srun` worker step.

## Development

Branches follow the RADICAL-Cybertools model:
- `devel` is the default and integration branch: feature and fix branches
  merge there via PRs.
- `master` carries releases, tagged `vX.Y.Z` (see `CHANGES.md`).

Tests: `pytest tests/unittests/`. They run a master with local workers, so no
Slurm is needed.

## License

MIT, see `LICENSE.md`.
