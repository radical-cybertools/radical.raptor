#!/usr/bin/env python3

'''
End-to-end check without Slurm: a RaptorMaster plus two worker processes
started locally, running executable and function tasks.
'''

import os
import sys
import subprocess

import cloudpickle
import pytest

from radical.raptor import RaptorMaster


# ------------------------------------------------------------------------------
#
@pytest.mark.timeout(120)
def test_local_master_workers(tmp_path):

    results = dict()

    def cb(task, state):
        results[task['uid']] = (state, task)

    master  = RaptorMaster(workdir=str(tmp_path), bulk_size=2, result_cb=cb)
    workers = list()

    try:
        for i in range(2):
            env = dict(os.environ, SLURM_PROCID=str(i))
            workers.append(subprocess.Popen(
                [sys.executable, '-m', 'radical.raptor.worker',
                 *master.worker_cli_args(), '--nslots', '2'],
                cwd=str(tmp_path), env=env))

        assert master.wait_workers(2, timeout=60) == 2

        # defined locally so that cloudpickle serializes it by value: the
        # workers cannot import this test module
        def add(a, b):
            return a + b

        blob = os.path.join(str(tmp_path), 'add.pkl')
        with open(blob, 'wb') as fout:
            cloudpickle.dump(add, fout)

        tasks  = [{'uid': 'exe.%02d' % i, 'executable': '/bin/echo',
                   'arguments': ['hello', str(i)]} for i in range(8)]
        tasks += [{'uid': 'func.%02d' % i, 'mode': 'function',
                   'function_blob': blob, 'args': [i, 10], 'kwargs': {}}
                  for i in range(8)]

        master.submit(tasks)
        assert master.wait(count=len(tasks), timeout=60) == len(tasks)

        for i in range(8):
            state, task = results['exe.%02d' % i]
            assert state == 'DONE', task
            assert task['stdout'].strip() == 'hello %d' % i

            state, task = results['func.%02d' % i]
            assert state == 'DONE', task
            assert task['return_value'] == i + 10

        assert master.stats['pending'] == 0

    finally:
        master.terminate()
        for proc in workers:
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()


# ------------------------------------------------------------------------------
