# -*- coding: utf-8 -*-

"""
Module :mod:`notification` manages the notification system.

Convention
----------
A computaiton absent from the notification db is considered in launchable state.
This avoid a useless call to the notification db

Note
----
A running job aborted for uncatchable reasons will stay in running state
although it is not running any longer. Refresh the historic to get it right
"""

from abc import ABCMeta, abstractmethod
import getpass
from datetime import datetime
from collections import defaultdict

from clustertools.chrono import ProgressMonitor
from .config import get_default_environment
from .storage import PickleStorage


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

# States
__RUNNING__ = "RUNNING"
__COMPLETED__ = "COMPLETED"
__ABORTED__ = "ABORTED"
__PENDING__ = "PENDING"
__LAUNCHABLE__ = "LAUNCHABLE"
__PARTIAL__ = "PARTIAL"
__INCOMPLETE__ = "INCOMPLETE"
__CRITICAL__ = "CRITIC"

__STATE__ = "STATE"
__DATE__ = "date"
__LASTSAVE__ = "last save"
__DURATION__ = "duration"
__EXCEPT__ = "exception"


# ============================= STATE AUTOMATON ============================= #

class State(object):
    """
    ``State``
    ==========
    State is which is a given computation

    Constructor arguments
    ---------------------
    comp_name: str
        The name of computation this state is linked to
    progress: 0 <= float <= 1
        The progress ratio of the task. 1 means it is finished (Default: 0)

    Equality
    --------
    State 'A' is equal to State 'B' if 'B is an instance of 'A' class and both
    'A' and 'B' have the same name
    """
    __metaclass__ = ABCMeta

    @classmethod
    def from_(cls, state):
        return cls(state.comp_name, progress_monitor=state.progress_monitor)

    @classmethod
    def default_progress(cls):
        return ProgressMonitor(0)

    def __init__(self, comp_name, progress_monitor=None):
        self.comp_name = comp_name
        if progress_monitor is None:
            progress_monitor = ProgressMonitor()
        self.progress_monitor = progress_monitor

    def __repr__(self):
        return "{cls}(comp_name={comp_name}, progress={progress})" \
               "".format(cls=self.__class__.__name__,
                         comp_name=repr(self.comp_name),
                         progress=repr(self.progress_monitor))

    def __eq__(self, other):
        # Funny how the isinstance might break symmetry of equivalence
        return isinstance(other, self.__class__) and \
               other.comp_name == self.comp_name

    def __hash__(self):
        # This is technically not consistent with equality since we are looking
        # for the exact class
        return hash(repr(self))

    def __setstate__(self, state):
        # Ensure correct unpickling with respect to previous class definition
        if "exp_name" in state:
            # The field 'exp_name' has been suppressed, this is
            # no longer the responsibility of the state to remember to which
            # experiment it belongs
            del state["exp_name"]
        if "progress" in state:
            # The field 'progress' has been suppressed in version 0.1.4
            # (merged with date in field `progress_monitor`)
            del state["progress"]
        if "date" in state:
            # The field 'progress' has been suppressed in version 0.1.4
            # (merged with progress in field `progress_monitor`)
            del state["date"]
        if "progress_monitor" not in state:
            state["progress_monitor"] = self.__class__.default_progress()
        self.__dict__.update(state)

    @abstractmethod
    def get_name(self):
        pass

    def reset(self):
        return LaunchableState.from_(self)

    def abort(self, exception):
        return AbortedState.from_(self, exception)

    def is_not_up(self):
        """Return the `State` corresponding to this `State` if it were
        discovered it is actually neither waiting nor working"""
        # running not up = stopped --> launchable
        # (rare)pending not in queued = has run and was stopped --> launchable
        # partial not up = incomplete
        # critical not in queued --> to check whether it was critical for the
        # first time
        return self


# --------------------------------------------------------------- Waiting states
class PendingState(State):
    def get_name(self):
        return __PENDING__

    def to_running(self):
        return RunningState.from_(self)

    def is_not_up(self):
        return LaunchableState.from_(self)


# --------------------------------------------------------------- Stopped states
class LaunchableState(State):
    def get_name(self):
        return __LAUNCHABLE__

    def to_pending(self):
        return PendingState.from_(self)


class CompletedState(State):
    @classmethod
    def default_progress(cls):
        return 1.

    def get_name(self):
        return __COMPLETED__


class AbortedState(State):
    @classmethod
    def from_(cls, state, exception):
        return cls(state.comp_name, progress_monitor=state.progress_monitor,
                   exception=exception)

    def __init__(self, comp_name, exception, progress_monitor=0.):
        super().__init__(comp_name, progress_monitor)
        self.exception = exception

    def get_name(self):
        return __ABORTED__

    def __repr__(self):
        return "{cls}(comp_name={comp_name}, progress={progress}, " \
               "exception={exception})".format(cls=self.__class__.__name__,
                                               comp_name=repr(self.comp_name),
                                               progress=repr(self.progress_monitor),
                                               exception=repr(self.exception))


class IncompleteState(State):
    def get_name(self):
        return __INCOMPLETE__

    def reset_progress_monitor(self, progress_monitor):
        self.progress_monitor = progress_monitor

    def abort(self, exception):
        return self  # Does not make sense to get aborted


# --------------------------------------------------------------- Working states
class WorkingState(State):
    __metaclass__ = ABCMeta

    def to_launchable(self):
        return self.reset()

    def to_aborted(self, exception):
        return AbortedState.from_(self, exception)


class RunningState(WorkingState):
    def get_name(self):
        return __RUNNING__

    def to_critical(self):
        return CriticalState.from_(self, first_critical=True)

    def is_not_up(self):
        return LaunchableState.from_(self)


class CriticalState(WorkingState):
    @classmethod
    def from_(cls, state, first_critical=False):
        return cls(state.comp_name, progress_monitor=state.progress_monitor,
                   first_critical=first_critical)

    def __init__(self, comp_name, progress_monitor=0., first_critical=False):
        super().__init__(comp_name, progress_monitor)
        self.first_critical = first_critical

    def get_name(self):
        return __CRITICAL__

    def to_completed(self):
        return CompletedState.from_(self)

    def to_partial(self):
        return PartialState.from_(self)

    def is_not_up(self):
        if self.first_critical:
            return LaunchableState.from_(self)
        else:
            # Might be corrupted but not likely
            return IncompleteState.from_(self)


class PartialState(WorkingState):
    def get_name(self):
        return __PARTIAL__

    def to_completed(self):
        return CompletedState.from_(self)

    def to_incomplete(self):
        return IncompleteState.from_(self)

    def to_critical(self):
        return CriticalState.from_(self, first_critical=False)

    def is_not_up(self):
        return IncompleteState.from_(self)


class ManualInterruption(Exception):
    pass


# ============================ EXPERIMENT MONITOR ============================ #

class Monitor(object):
    """
    `Monitor`
    ========
    A class which monitors the computations of a given experiment

    job_dict : mapping {comp_name -> state}
    state_dict: mapping {state -> job_dict}

    Note
    ----
    The number n of computations per experiment being usually low (a few
    thousands at most), it is not necessary to be better than O(n) per
    operations
    """
    def __init__(self, exp_name, user=None,
                 storage_factory=PickleStorage,
                 environment_cls=None):
        self.exp_name = exp_name
        self.states = []
        self.state_dict = {}
        self.user = getpass.getuser() if user is None else user
        self.storage = storage_factory(experiment_name=self.exp_name)
        self.environment_cls = get_default_environment(environment_cls)
        self.refresh()

    def refresh(self):
        up_jobs = self.environment_cls.list_up_jobs(self.user)
        states = self.storage.load_states()
        if up_jobs is None:
            self.states = states
            return

        self.states = []
        queued = frozenset(up_jobs)
        for state in states:
            if state.comp_name not in queued:
                state = state.is_not_up()  # The change is not in place
            self.states.append(state)

    def __repr__(self):
        return "{}(exp_name={}, user={}, storage_factory={}, " \
               "environment_cls={})".format(self.__class__.__name__,
                                            self.exp_name,
                                            repr(self.user),
                                            repr(self.storage),
                                            repr(self.environment_cls))

    def __len__(self):
        return len(self.states)

    def _filter(self, state_cls=State, predicate=(lambda x: True),
                extract=(lambda i, s: s)):
        return [extract(i, state) for i, state in enumerate(self.states) if
                isinstance(state, state_cls) and predicate(state)]

    def _indices(self, state_cls=State, predicate=(lambda x: True)):
        """Return a list of indices [i_1, i_2, ...i_p] for which
        predicate(self.state[i_j]) == True (1 <= j <= p)
        """
        return self._filter(state_cls=state_cls, predicate=predicate,
                            extract=(lambda i, s: i))

    def computation_names(self, state_cls=State):
        return set(self._filter(state_cls=state_cls,
                                extract=lambda i, s: s.comp_name))

    def aborted_computations(self):
        return self.computation_names(AbortedState)

    def launchable_computations(self):
        return self.computation_names(LaunchableState)

    def incomplete_computations(self):
        return self.computation_names(IncompleteState)

    def critical_computations(self):
        return self.computation_names(CriticalState)

    def unlaunchable_comp_names(self):
        """Return a set of computation names which are not to be launched"""
        launchables = self.launchable_computations()
        return frozenset(
            self._filter(predicate=lambda s: s.comp_name not in launchables,
                         extract=lambda i, s: s.comp_name))

    def partition_by_state(self):
        by_state = defaultdict(list)
        for state in self.states:
            by_state[state.get_name()].append(state)
        return by_state

    def count_by_state(self):
        return {k: len(v) for k, v in self.partition_by_state().items()}

    def get_working_progress(self):
        """Return a dict comp_name -> progress for Working state"""
        workings = self._filter(state_cls=WorkingState)
        return {s.comp_name: s.progress_monitor for s in workings}

    def to_launchables(self, indices=None):
        if indices is None:
            indices = range(len(self.states))
        for index in indices:
            state = self.states[index]
            new_state = self.storage.update_state(state.reset())
            # In case of error, do not update locally
            self.states[index] = new_state

    def to_launchable(self, comp_name):
        index = self._indices(predicate=(lambda s: s.comp_name == comp_name))[0]
        before = self.states[index].get_name()
        self.to_launchables([index])
        after = self.states[index].get_name()
        return before, after

    def reset(self, from_state=State, predicate=lambda x: True):
        self.to_launchables(self._indices(from_state, predicate))

    def aborted_to_launchable(self, predicate=lambda x: True):
        self.reset(AbortedState, predicate)

    def incomplete_to_launchable(self, predicate=lambda x: True):
        self.reset(IncompleteState, predicate)

    def abort(self, exception=ManualInterruption("Monitor interruption"),
              from_state=State, predicate=lambda x: True):
        indices = self._indices(from_state, predicate)
        for index in indices:
            state = self.states[index]
            new_state = AbortedState.from_(state, exception)
            self.storage.update_state(new_state)
            # In case of error, do not update locally
            self.states[index] = new_state
