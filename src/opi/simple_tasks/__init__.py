"""
High-level task interface for OPI.

Public API
----------
.. autosummary::
   :toctree: generated/

   Task
   TaskCompleted
   SinglePointTask
   OptTask
   EnGradTask
   SinglePointCompleted
   OptCompleted
   EnGradCompleted
"""

from opi.simple_tasks.base import Task, TaskCompleted, TaskParams

__all__ = (
    "Task",
    "TaskCompleted",
    "TaskParams",
)
