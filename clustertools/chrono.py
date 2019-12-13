import datetime
import time as py_time


def duration_str(duration_in_sec):
    return "{}".format(datetime.timedelta(seconds=duration_in_sec))


class ProgressMonitor(object):
    def __init__(self, progress=0, duration_padding=0):
        self.decay_rate = .9
        self.average_speed = None
        self.progress = progress
        self.start = py_time.time()
        self.duration_padding = duration_padding

    def __repr__(self):
        return "{}(progress={}, duration_padding={})" \
               "".format(self.__class__.__name__,
                         repr(self.progress),
                         repr(self.duration_padding))

    def restart(self):
        self.start = py_time.time()

    def update_progress(self, progress):
        current_speed = progress / (py_time.time() - self.start)
        avg_speed = current_speed if self.average_speed is None \
            else self.average_speed
        self.average_speed = self.decay_rate * avg_speed \
                             + (1 - self.decay_rate) * current_speed
        self.progress = progress

    def __str__(self):
        now = py_time.time()
        elapsed = now - self.start + self.duration_padding

        if self.average_speed is None:
            return "{:.2f} % | Elapsed: {}".format(self.progress * 100,
                                                   duration_str(elapsed))

        # Average speed is known; it is possible to compute estimates
        eta = (1 - self.progress) / self.average_speed
        total_duration = elapsed + eta
        return "{:.2f} % | Elapsed: {} | ETA: {} | ETD: {}" \
               "".format(self.progress*100,
                         duration_str(elapsed),
                         duration_str(eta),
                         duration_str(total_duration))


class LabeledTime(object):
    def __init__(self, label, time=None):
        if time is None:
            time = py_time.time()
        self.label = label
        self.time = time

    def __repr__(self):
        return "{}(label={}, time={})".format(self.__class__.__name__,
                                              repr(self.label),
                                              repr(self.time))


class Chronometer(object):
    @classmethod
    def chrono_from_progress_monitor(cls, progress, label="start"):
        return cls([LabeledTime(label, progress.start)])

    def __init__(self, laps=None):
        self.laps = [] if laps is None else laps

    def __repr__(self):
        return "{}(laps={})" \
               "".format(self.__class__.__name__, repr(self.laps))

    def new_lap(self, label=None):
        if label is None:
            label = "lap-{}".format(len(self.laps))
        self.laps.append(LabeledTime(label))

    def total_duration(self):
        return py_time.time() - self.laps[0].time

    def lap_duration(self, lap_index=None):
        if lap_index is None:
            return py_time.time() - self.laps[-1].time

        return self.laps[lap_index] - self.laps[lap_index-1]

    def stop(self, label="end"):
        self.new_lap(label)

    def duration_till_last_lap(self):
        return self.laps[-1].time - self.laps[0].time

    def yield_durations(self):
        for labeled_time in self.laps:
            yield labeled_time.label, labeled_time.time


class BrokenWatch(object):
    def update_progress(self, progress):
        pass

    def yield_user_durations(self):
        raise StopIteration()

    def yield_progress_durations(self):
        raise StopIteration()

    def total_duration(self):
        return 0

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)


class Watch(BrokenWatch):
    @classmethod
    def reset(cls, watch):
        progress = watch.last_update
        padding = watch.get_padding()
        progress_monitor = ProgressMonitor(progress, padding)
        return cls(progress_monitor, watch.update_rate,
                   progress_chronos=watch.progress_chronos,
                   user_chronos=watch.user_chronos)

    def __init__(self, progress_monitor, update_rate=0.1, progress_chronos=None,
                 user_chronos=None):
        self.progress_monitor = progress_monitor
        self.update_rate = update_rate

        self.progress_chronos = [] if progress_chronos is None else progress_chronos
        self.user_chronos = [] if user_chronos is None else user_chronos

    def __repr__(self):
        return "{}(progress_monitor={}, update_rate={}, progress_chronos={}, " \
               "user_chronos={})" \
               "".format(self.__class__.__name__,
                         repr(self.progress_monitor),
                         repr(self.update_rate),
                         repr(self.progress_chronos),
                         repr(self.user_chronos))

    @property
    def last_update(self):
        return self.progress_monitor.progress

    def __enter__(self):
        p_chrono = Chronometer.chrono_from_progress_monitor(self.progress_monitor)
        self.progress_chronos.append(p_chrono)
        self.user_chronos.append(Chronometer())

    def __exit__(self, exc_type, exc_val, exc_tb):
        label = "end" if exc_type is None else str(exc_val)
        self.progress_chronos[-1].new_lap(label)
        if exc_val is None:
            self.progress_monitor.update_progress(1.)
        self.stop()

    def update_progress(self, progress):
        if progress - self.last_update > 1/(self.update_rate*100):
            self.progress_chronos[-1].new_lap("{:.2f} % completion"
                                              "".format(progress))
        self.progress_monitor.update_progress(progress)

    def new_lap(self, label=None):
        self.user_chronos[-1].new_lap(label)

    def stop(self, label="end"):
        self.user_chronos[-1].stop(label)

    def yield_user_durations(self):
        for chrono in self.user_chronos:
            for x in chrono.yield_durations():
                yield x

    def yield_progress_durations(self):
        for chrono in self.progress_chronos:
            for x in chrono.yield_durations():
                yield x

    def get_padding(self):
        return self.progress_chronos.duration_till_last_lap()


