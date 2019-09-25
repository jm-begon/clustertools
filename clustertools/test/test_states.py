# -*- coding: utf-8 -*-
from nose.tools import assert_in, assert_not_in
from nose.tools import assert_equal
from nose.tools import with_setup
from nose.tools import assert_true, assert_false


from clustertools.state import *
from clustertools.storage import PickleStorage
from clustertools.environment import BashEnvironment, SlurmEnvironment, \
    InSituEnvironment

from .util_test import pickle_prep, pickle_purge, __EXP_NAME__, with_setup_, \
    ListUpJobs, prep, purge, IntrospectStorage, get_exp_name

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


# ------------------------------------------------------------------------ STATE


def test_reset_state():
    for state_cls in PendingState, RunningState, CompletedState, \
                     IncompleteState, CriticalState, PartialState:
        state = state_cls("test_comp")
        assert_true(isinstance(state.reset(), LaunchableState))
    state = AbortedState("test_comp",
                         exception=ManualInterruption("Test interruption"))
    assert_true(isinstance(state.reset(), LaunchableState))


def test_abort_state():
    for state_cls in PendingState, RunningState, CompletedState, \
                     CriticalState, PartialState, \
                     LaunchableState:
        # IncompleteState cannot be aborted
        state = state_cls("test_comp")
        state = state.abort(ManualInterruption("Test interruption"))
        assert_true(isinstance(state, AbortedState))


def test_computation_state_routine():
    # Is this routine working ?
    state = PendingState("test_comp")
    state = state.to_running()
    state = state.to_critical()
    assert_true(state.first_critical)
    state.to_completed()
    assert_true(True)


def test_computation_state_failed_routine():
    # Is this routine working ?
    state = PendingState("test_comp")
    state = state.to_running()
    state = state.abort(ManualInterruption("Test interruption"))
    assert_true(isinstance(state, AbortedState))


def test_partial_computation_state_routine():
    # Is this routine working ?
    state = PendingState("test_comp")
    state = state.to_running()
    state = state.to_critical()
    assert_true(state.first_critical)
    # loop
    for _ in range(5):
        state = state.to_partial()
        state = state.to_critical()
        assert_false(state.first_critical)
    state.to_completed()
    assert_true(True)


# ---------------------------------------------------------------------- MONITOR
@with_setup(prep, purge)
def test_monitor_refresh_with_non_empty_list():
    monitor = Monitor(__EXP_NAME__, storage_factory=IntrospectStorage,
                      user=ListUpJobs.user,
                      environment_cls=ListUpJobs)

    storage = monitor.storage
    good_state = PendingState("save_galaxy")
    storage.update_state(good_state)

    wrong_state = PendingState("kiss_leia")
    storage.update_state(wrong_state)

    monitor.refresh()

    assert_in(good_state.comp_name, monitor.computation_names(PendingState))
    assert_in(wrong_state.comp_name, monitor.computation_names(LaunchableState))


@with_setup_(pickle_prep, pickle_purge)
def monitor_refresh(monitor, can_list):
    print(monitor)
    print("Can list?", can_list)

    pending = PendingState("test_pending")
    running = RunningState("test_running")
    completed = CompletedState("test_completed")
    launchable = LaunchableState("test_lauchable")
    partial = PartialState("test_partial")
    first_critical = CriticalState("test_first_critical",
                                   first_critical=True)
    not_first_critical = CriticalState("test_not_first_critical",
                                       first_critical=False)
    aborted = AbortedState("test_aborted",
                           exception=ManualInterruption("Test interruption"))
    incomplete = IncompleteState("incomplete")

    storage = PickleStorage(monitor.exp_name)
    for state in pending, running, completed, launchable, partial, \
                 first_critical, not_first_critical, aborted, incomplete:
        storage.update_state(state)

    monitor.refresh()

    if can_list:

        # Should be moved to launchable
        assert_in(pending.comp_name, monitor.launchable_computations())
        assert_in(running.comp_name, monitor.launchable_computations())
        assert_in(first_critical.comp_name, monitor.launchable_computations())

        # Should be moved to incomplete
        assert_in(partial.comp_name, monitor.incomplete_computations())
        assert_in(not_first_critical.comp_name, monitor.incomplete_computations())

        # At the right place
        assert_in(launchable.comp_name, monitor.launchable_computations())
        assert_in(completed.comp_name, monitor.computation_names(CompletedState))
        assert_in(aborted.comp_name, monitor.aborted_computations())
        assert_in(incomplete.comp_name, monitor.incomplete_computations())

        # 4 types of states: launchable, completed, incomplete, aborted
        print(monitor.count_by_state())
        assert_equal(len(monitor.count_by_state()), 4)

        # Nothing is running
        assert_equal(len(monitor.get_working_progress()), 0)
    else:
        for state, cls in (pending, PendingState), (running, RunningState), \
                          (completed, CompletedState), \
                          (launchable, LaunchableState), \
                          (partial, PartialState), \
                          (first_critical, CriticalState), \
                          (not_first_critical, CriticalState), \
                          (aborted, AbortedState), \
                          (incomplete, IncompleteState):
            assert_in(state.comp_name, monitor.computation_names(cls))

        # Running, Partial, Critical (first and not first) are Working jobs
        working_jobs = monitor.get_working_progress()
        assert_equal(len(working_jobs), 4)
        for state in running, partial, first_critical, not_first_critical:
            assert_in(state.comp_name, working_jobs)


def test_monitor_refresh_can_list():
    monitor = Monitor(get_exp_name(), environment_cls=SlurmEnvironment)
    monitor_refresh(monitor, SlurmEnvironment.is_usable())


def test_monitor_refresh_cannot_list():
    for env_cls in InSituEnvironment, BashEnvironment:
        monitor = Monitor(get_exp_name(), environment_cls=env_cls)
        monitor_refresh(monitor, False)


@with_setup_(pickle_prep, pickle_purge)
def monitor_incomplete_to_launchable(monitor, can_list):
    incomplete = IncompleteState("incomplete")
    partial = PartialState("test_partial")
    not_first_critical = CriticalState("test_not_first_critical",
                                       first_critical=False)
    first_critical = CriticalState("test_first_critical",
                                   first_critical=True)
    aborted = AbortedState("test_aborted",
                           ManualInterruption("Test interruption"))

    storage = PickleStorage(monitor.exp_name)
    for state in incomplete, partial, not_first_critical, aborted, \
            first_critical:
        storage.update_state(state)

    monitor.refresh()
    print("States:", monitor.states)
    print(monitor.computation_names(CriticalState))

    if can_list:
        # partial and not_first_critical have switched to incomplete
        assert_in(partial.comp_name, monitor.incomplete_computations())
        assert_in(not_first_critical.comp_name, monitor.incomplete_computations())
        # first_critical has become launchable
        assert_in(first_critical.comp_name, monitor.launchable_computations())
        # Nothing is running
        assert_equal(len(monitor.get_working_progress()), 0)
    else:
        # partial and not_first_critical are the same
        assert_in(partial.comp_name, monitor.computation_names(PartialState))
        assert_in(not_first_critical.comp_name,
                  monitor.computation_names(CriticalState))
        # first_critical is still critical
        assert_in(first_critical.comp_name,
                  monitor.computation_names(CriticalState))

    assert_in(incomplete.comp_name, monitor.incomplete_computations())
    assert_in(aborted.comp_name, monitor.aborted_computations())

    monitor.incomplete_to_launchable()

    assert_in(incomplete.comp_name, monitor.launchable_computations())
    if can_list:
        assert_in(partial.comp_name, monitor.launchable_computations())
        assert_in(not_first_critical.comp_name, monitor.launchable_computations())
        assert_in(first_critical.comp_name, monitor.launchable_computations())
    else:
        # partial and not_first_critical are the same
        assert_in(partial.comp_name, monitor.computation_names(PartialState))
        assert_in(not_first_critical.comp_name,
                  monitor.computation_names(CriticalState))
        # first_critical is still critical
        assert_in(first_critical.comp_name,
                  monitor.computation_names(CriticalState))

    assert_in(aborted.comp_name, monitor.aborted_computations())


def test_monitor_incomplete_to_launchable_can_list():
    monitor = Monitor(get_exp_name(), environment_cls=SlurmEnvironment)
    monitor_incomplete_to_launchable(monitor, SlurmEnvironment.is_usable())


def test_monitor_incomplete_to_launchable_cannot_list():
    for env_cls in InSituEnvironment, BashEnvironment:
        monitor = Monitor(get_exp_name(), environment_cls=env_cls)
        monitor_incomplete_to_launchable(monitor, False)


@with_setup(pickle_prep, pickle_purge)
def test_monitor_aborted_to_launchable():
    incomplete = IncompleteState("incomplete")
    completed = CompletedState("completed")
    aborted = AbortedState("test_aborted",
                           ManualInterruption("Test interruption"))

    storage = PickleStorage(get_exp_name())
    for state in incomplete, completed, aborted:
        storage.update_state(state)

    monitor = Monitor(get_exp_name())
    monitor.aborted_to_launchable()

    assert_in(aborted.comp_name, monitor.launchable_computations())
    for state in incomplete, completed:
        assert_not_in(state.comp_name, monitor.launchable_computations())

