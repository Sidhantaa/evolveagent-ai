import threading
import time

from app.services.goal_service import GoalService
from app.services.storage_service import StorageService


# ------------------------------------------------------------------
# Round 30: update_goal()/add_task()/update_task()/touch_goal() had the same
# lost-update shape rounds 25-29 fixed elsewhere (read_list() + write_list()
# as two separate lock acquisitions). Real concurrent writers here are all
# HTTP (no background driver): two clients updating different tasks of the
# SAME goal, or a PATCH racing an add_task(). Independently confirmed via a
# standalone repro against the true unmodified code before writing any fix:
# a concurrent update_task() for a DIFFERENT task got silently lost.
# ------------------------------------------------------------------
def test_update_task_does_not_lose_a_concurrent_update_of_a_different_task(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    service = GoalService(storage)
    goal, _ = service.create_manual("Test Goal", "desc")
    t1 = service.add_task(goal.goal_id, {"title": "Task 1"})
    t2 = service.add_task(goal.goal_id, {"title": "Task 2"})

    entered = threading.Event()
    original_update_list = storage.update_list

    def _slow_update_list(filename, mutator):
        def _slow_mutator(items):
            entered.set()
            time.sleep(0.2)
            return mutator(items)
        return original_update_list(filename, _slow_mutator)

    storage.update_list = _slow_update_list

    def _update_t1():
        service.update_task(goal.goal_id, t1.task_id, {"status": "done"})

    thread = threading.Thread(target=_update_t1)
    thread.start()
    entered.wait(timeout=2)
    service.update_task(goal.goal_id, t2.task_id, {"status": "in_progress"})
    thread.join(timeout=2)

    _, final_graph = service.get_goal(goal.goal_id)
    statuses = {task["task_id"]: task["status"] for task in final_graph["tasks"]}
    assert statuses[t1.task_id] == "done"  # must not be lost -- failed before the fix
    assert statuses[t2.task_id] == "in_progress"  # must not be lost -- failed before the fix


def test_update_goal_does_not_lose_a_concurrent_touch_goal(tmp_path):
    """update_goal() (a PATCH) racing touch_goal() (fired by a concurrent
    add_task()/update_task() on the same goal) must not lose either write."""
    storage = StorageService(data_dir=str(tmp_path / "data"))
    service = GoalService(storage)
    goal, _ = service.create_manual("Another Goal", "desc")

    entered = threading.Event()
    original_update_list = storage.update_list

    def _slow_update_list(filename, mutator):
        def _slow_mutator(items):
            if filename == "goals.json":
                entered.set()
                time.sleep(0.2)
            return mutator(items)
        return original_update_list(filename, _slow_mutator)

    storage.update_list = _slow_update_list

    def _touch():
        service.touch_goal(goal.goal_id)

    thread = threading.Thread(target=_touch)
    thread.start()
    entered.wait(timeout=2)
    service.update_goal(goal.goal_id, {"title": "Renamed while touching"})
    thread.join(timeout=2)

    updated, _ = service.get_goal(goal.goal_id)
    assert updated["title"] == "Renamed while touching"  # must not be lost -- failed before the fix


def test_add_task_and_update_task_still_touch_goal_progress(tmp_path):
    """Sanity: the reentrancy-avoiding restructure (touch_goal() called
    OUTSIDE the task_graphs.json mutator) still updates progress correctly."""
    storage = StorageService(data_dir=str(tmp_path / "data"))
    service = GoalService(storage)
    goal, _ = service.create_manual("Progress Goal", "desc")
    task = service.add_task(goal.goal_id, {"title": "Only task"})
    updated, _ = service.get_goal(goal.goal_id)
    assert updated["progress_percent"] == 0

    service.update_task(goal.goal_id, task.task_id, {"status": "done"})
    updated, _ = service.get_goal(goal.goal_id)
    assert updated["progress_percent"] == 100
