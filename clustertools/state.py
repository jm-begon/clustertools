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

from clusterlib.scheduler import queued_or_running_jobs

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

    Note
    ----
    The `State` object contains a datetime. This is purely informative and is
    not considered as an essential component of the object. As such, it is
    not considered for repr or equailty
    """
    __metaclass__ = ABCMeta

    @classmethod
    def from_(cls, state):
        return cls(state.exp_name, state.comp_name)

    def __init__(self, exp_name, comp_name):
        self.exp_name = exp_name
        self.comp_name = comp_name
        self.date = datetime.now()

    def __repr__(self):
        return "{cls}(exp_name={exp_name}, comp_name={comp_name})" \
               "".format(cls=self.__class__.__name__,
                         exp_name=self.exp_name,
                         comp_name=self.comp_name)

    def __eq__(self, other):
        # Funny how the isinstance might break symmetry of equivalence
        return isinstance(other, self.__class__) and \
               other.exp_name == self.exp_name and \
               other.comp_name == self.comp_name

    def __hash__(self):
        # This is technically not consistent with equality since we are looking
        # for the exact class
        return hash(repr(self))

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
        # (rare)pending not in queued = has run and was stoppped --> launachable
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
    def get_name(self):
        return __COMPLETED__


class AbortedState(State):
    @classmethod
    def from_(cls, state, exception):
        return cls(state.exp_name, state.comp_name, exception)

    def __init__(self, exp_name, comp_name, exception):
        super(AbortedState, self).__init__(exp_name, comp_name)
        self.exception = exception

    def get_name(self):
        return __ABORTED__

    def __repr__(self):
        return "{cls}(exp_name={exp_name}, comp_name={comp_name}, " \
               "exception={exception})".format(cls=self.__class__.__name__,
                                               exp_name=self.exp_name,
                                               comp_name=self.comp_name,
                                               exception=repr(self.exception))


class IncompleteState(State):
    def get_name(self):
        return __INCOMPLETE__


# --------------------------------------------------------------- Working states
class WorkingState(State):
    __metaclass__ = ABCMeta

    def to_launchable(self):
        return self.reset()

    def to_aborted(self, exception):
        return AbortedState.from_(self, exception)


class RunningState(State):
    def get_name(self):
        return __RUNNING__

    def to_critical(self):
        return CriticalState.from_(self, first_critical=True)

    def is_not_up(self):
        return LaunchableState.from_(self)


class CriticalState(State):
    @classmethod
    def from_(cls, state, first_critical=False):
        return cls(state.exp_name, state.comp_name, first_critical)

    def __init__(self, exp_name, comp_name, first_critical=False):
        super(CriticalState, self).__init__(exp_name, comp_name)
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


class PartialState(State):
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
                 storage_factory=PickleStorage):
        self.exp_name = exp_name
        self.states = []
        self.state_dict = {}
        self.user = getpass.getuser() if user is None else user
        self.storage = storage_factory(experiment_name=self.exp_name)
        self.refresh()

    def refresh(self):
        states = self.storage.load_states()
        queued = frozenset(queued_or_running_jobs(self.user))
        self.states = []
        for state in states:
            if state.comp_name not in queued:
                state = state.is_not_up()
            self.states.append(state)

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

    def to_launchables(self, indices=None):
        if indices is None:
            indices = range(len(self.states))
        for index in indices:
            state = self.states[index]
            new_state = self.storage.update_state(state.reset())
            # In case of error, do not update locally
            self.states[index] = new_state

    def to_launchable(self, comp_name):
        indices = self._indices(predicate=(lambda s: s.comp_name == comp_name))
        self.to_launchables(indices)

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
