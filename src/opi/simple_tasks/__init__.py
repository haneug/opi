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
from opi.simple_tasks.results import EnGradCompleted, OptCompleted, SinglePointCompleted
from opi.simple_tasks.tasks import EnGradTask, OptTask, SinglePointTask

__all__ = (
    "Task",
    "TaskCompleted",
    "TaskParams",
    "SinglePointTask",
    "OptTask",
    "EnGradTask",
    "SinglePointCompleted",
    "OptCompleted",
    "EnGradCompleted",
)
