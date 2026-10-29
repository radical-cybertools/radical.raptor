"""Raptor: a master/worker executor for high-throughput tasks.

A ``RaptorMaster`` owns ZMQ request/result/control bridges (radical.utils);
workers, typically one per node launched via ``srun``, pull tasks in bulk and
run them in a pool of slots: executables via fork/exec, Python functions
in-slot.

Layout:
  - master.py           : RaptorMaster -- creates the ZMQ bridges, submits
                          tasks, collects results, drives worker lifecycle.
  - worker.py           : worker entry point (``python -m radical.raptor.worker``).
  - rhapsody_backend.py : RaptorBackend, a rhapsody execution backend driving a
                          RaptorMaster (needs the ``rhapsody`` extra).
"""

__copyright__ = 'Copyright 2026, The RADICAL-Cybertools Team'
__license__   = 'MIT'

import os as _os

import radical.utils as _ru

from .master import RaptorMaster


# ------------------------------------------------------------------------------
# get version info
_mod_root = _os.path.dirname(__file__)

version_short, version_base, version_branch, version_tag, version_detail \
             = _ru.get_version(_mod_root)
version      = version_short
__version__  = version_detail

__all__ = ['RaptorMaster', 'version', '__version__']


# ------------------------------------------------------------------------------
