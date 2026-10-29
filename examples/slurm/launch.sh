#!/bin/bash
# Run a Raptor master plus srun-launched workers by hand, without rhapsody.
#
# Run from inside a Slurm allocation (salloc/sbatch), with radical.raptor
# installed in the active Python.  The master (via examples/driver.py) writes
# its info file into the shared work directory; an explicit srun step then
# starts one worker per node, which reads the bridge addresses from that file.
#
# Usage:  launch.sh <workdir> <nworkers> <nslots> <ntasks> <bulk> [exe]
#         (workdir must be on a filesystem shared by all nodes)

set -eux

HERE=$(cd "$(dirname "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

WORKDIR=${1:?usage: launch.sh <workdir> <nworkers> <nslots> <ntasks> <bulk> [exe]}
NWORKERS=${2:-2}
NSLOTS=${3:-64}
NTASKS=${4:-100}
BULK=${5:-8}
EXE=${6:-/bin/true}

mkdir -p "$WORKDIR"
INFO=$WORKDIR/raptor.master.json
rm -f "$INFO"

# 1) start master + driver in the background; it waits for $NWORKERS workers
$PYTHON "$HERE/driver.py" \
    --workdir "$WORKDIR" --ntasks "$NTASKS" --workers "$NWORKERS" \
    --bulk "$BULK" --nslots "$NSLOTS" --exe "$EXE" &
DRIVER_PID=$!

# 2) wait for the master to publish its info file
for i in $(seq 1 300); do [ -f "$INFO" ] && break; sleep 0.2; done

# 3) launch the workers via srun across the allocation (one per node)
srun --overlap --nodes="$NWORKERS" --ntasks="$NWORKERS" --ntasks-per-node=1 \
     --cpu-bind=none \
     $PYTHON -m radical.raptor.worker --info "$INFO" --nslots "$NSLOTS" --prefetch 4 &
SRUN_PID=$!

# 4) wait for the driver (it submits, waits, reports, terminates the workers)
wait $DRIVER_PID
wait $SRUN_PID 2>/dev/null || true
echo "raptor run complete; see $WORKDIR/summary.json"
