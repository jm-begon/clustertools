# -*- coding: utf-8 -*-


from nose.tools import assert_in, assert_not_in
from nose.tools import assert_equal
from nose.tools import with_setup
from nose.tools import assert_true, assert_false


from clustertools.state import *
from clustertools.storage import PickleStorage

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


__EXP_NAME__ = "ClustertoolsTest"


def purge():
    storage = PickleStorage(__EXP_NAME__)
    try:
        storage.delete()
    except OSError:
        pass
    return storage


def prep():
    storage = purge()
    storage.init()

# ------------------------------------------------------------------------ STATE

def test_reset_state():
    for state_cls in PendingState, RunningState, CompletedState, \
                     IncompleteState, CriticalState, PartialState:
        state = state_cls(__EXP_NAME__, "test_comp")
        assert_true(isinstance(state.reset(), LaunchableState))
    state = AbortedState(__EXP_NAME__, "test_comp",
                         ManualInterruption("Test interruption"))
    assert_true(isinstance(state.reset(), LaunchableState))


def test_abort_state():
    for state_cls in PendingState, RunningState, CompletedState, \
                     IncompleteState, CriticalState, PartialState, \
                     LaunchableState:
        state = state_cls(__EXP_NAME__, "test_comp")
        state = state.abort(ManualInterruption("Test interruption"))
        assert_true(isinstance(state, AbortedState))


def test_computation_state_routine():
    # Is this routine working ?
    state = PendingState(__EXP_NAME__, "test_comp")
    state = state.to_running()
    state = state.to_critical()
    assert_true(state.first_critical)
    state.to_completed()
    assert_true(True)


def test_computation_state_failed_routine():
    # Is this routine working ?
    state = PendingState(__EXP_NAME__, "test_comp")
    state = state.to_running()
    state = state.abort(ManualInterruption("Test interruption"))
    assert_true(isinstance(state, AbortedState))


def test_partial_computation_state_routine():
    # Is this routine working ?
    state = PendingState(__EXP_NAME__, "test_comp")
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
def test_monitor_refresh():
    pending = PendingState(__EXP_NAME__, "test_pending")
    running = RunningState(__EXP_NAME__, "test_running")
    completed = CompletedState(__EXP_NAME__, "test_completed")
    launchable = LaunchableState(__EXP_NAME__, "test_lauchable")
    partial = PartialState(__EXP_NAME__, "test_partial")
    first_critical = CriticalState(__EXP_NAME__, "test_first_critical",
                                   first_critical=True)
    not_first_critical = CriticalState(__EXP_NAME__, "test_not_first_critical",
                                       first_critical=False)
    aborted = AbortedState(__EXP_NAME__, "test_aborted",
                           ManualInterruption("Test interruption"))
    incomplete = IncompleteState(__EXP_NAME__, "incomplete")

    storage = PickleStorage(__EXP_NAME__)
    for state in pending, running, completed, launchable, partial, \
                 first_critical, not_first_critical, aborted, incomplete:
        storage.update_state(state)

    monitor = Monitor(__EXP_NAME__)

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
    assert_equal(len(monitor.count_by_state()), 4)


@with_setup(prep, purge)
def test_monitor_incomplete_to_launchable():
    incomplete = IncompleteState(__EXP_NAME__, "incomplete")
    partial = PartialState(__EXP_NAME__, "test_partial")
    not_first_critical = CriticalState(__EXP_NAME__, "test_not_first_critical",
                                       first_critical=False)
    first_critical = CriticalState(__EXP_NAME__, "test_first_critical",
                                   first_critical=True)
    aborted = AbortedState(__EXP_NAME__, "test_aborted",
                           ManualInterruption("Test interruption"))

    storage = PickleStorage(__EXP_NAME__)
    for state in incomplete, partial, not_first_critical, aborted, \
            first_critical:
        storage.update_state(state)

    monitor = Monitor(__EXP_NAME__)

    # partial and not_first_critical are incomplete
    assert_in(partial.comp_name, monitor.incomplete_computations())
    assert_in(not_first_critical.comp_name, monitor.incomplete_computations())
    assert_in(incomplete.comp_name, monitor.incomplete_computations())
    assert_in(first_critical.comp_name, monitor.launchable_computations())
    assert_in(aborted.comp_name, monitor.aborted_computations())

    monitor.incomplete_to_launchable()

    assert_in(incomplete.comp_name, monitor.launchable_computations())
    assert_in(partial.comp_name, monitor.launchable_computations())
    assert_in(not_first_critical.comp_name, monitor.launchable_computations())
    assert_in(first_critical.comp_name, monitor.launchable_computations())
    assert_in(aborted.comp_name, monitor.aborted_computations())


@with_setup(prep, purge)
def test_monitor_aborted_to_launchable():
    incomplete = IncompleteState(__EXP_NAME__, "incomplete")
    completed = CompletedState(__EXP_NAME__, "completed")
    aborted = AbortedState(__EXP_NAME__, "test_aborted",
                           ManualInterruption("Test interruption"))

    storage = PickleStorage(__EXP_NAME__)
    for state in incomplete, completed, aborted:
        storage.update_state(state)

    monitor = Monitor(__EXP_NAME__)
    monitor.aborted_to_launchable()

    assert_in(aborted.comp_name, monitor.launchable_computations())
    for state in incomplete, completed:
        assert_not_in(state.comp_name, monitor.launchable_computations())




# ------------------------------------------------------------------------ YIELD

@with_setup(prep, purge)
def test_yield_not_done_computation():
    # exp = Experiment(__EXP_NAME__)
    # exp.add_params(p1=1, p2=[2, 3], p3="param")
    # exp.add_params(p1=4, p2=5)
    #
    # ls = list(exp)
    # comp_name = lambda t:t[0]
    # now = launchable_jobs_update(__EXP_NAME__, [comp_name(t) for t in ls])
    #
    # completed_job_update(__EXP_NAME__, comp_name(ls[0]), now)
    # completed_job_update(__EXP_NAME__, comp_name(ls[-1]), now)
    #
    # historic = Monitor(exp.name)
    # print historic.job_dict
    #
    # remains = list(yield_not_done_computation(exp))
    # print remains
    # assert_equal(len(remains), len(ls)-2)
    # for t in ls[1:-1]:
    #     assert_in(t, remains)
    pass


