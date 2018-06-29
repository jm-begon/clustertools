# -*- coding: utf-8 -*-
import os
import signal

import time
from nose.tools import assert_equal, assert_not_equal
from nose.tools import assert_raises
from nose.tools import assert_true

from clustertools.util import reorder, escape, SigHandler, SignalExecption, \
    call_with, hashlist, deprecated

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


def test_call_with():
    def f(a, b, **others):
        return a+b

    assert_equal(5, call_with(f, {"a": 2, "c": 10}, b=3, d=50))

    class C(object):
        def __init__(self, c, d):
            self.c = c
            self.d = d

    c = call_with(C, {"a": 2, "c": 10}, b=3, d=50)
    assert_equal(10, c.c)
    assert_equal(50, c.d)


def test_reorder():
    ls = list(range(10))
    indices = [2, 4, 1, 5]
    ls2 = reorder(ls, indices, in_place=True)
    assert_equal(ls2, ls[:len(indices)])
    assert_equal(len(ls2), len(indices))
    assert_equal(ls2, indices)

    ls = list(range(10))
    indices = [2, 4, 1, 5]
    ls2 = reorder(ls, indices, in_place=False)
    assert_not_equal(ls2, ls)
    assert_equal(len(ls2), len(indices))
    assert_equal(ls2, indices)


def test_escape():
    s1 = "print 'hello'"
    expected1 = "print\\ \\'hello\\'"
    assert_equal(escape(s1), expected1)

    s2 = 'print "hello"'
    expected2 = 'print\\ \\"hello\\"'
    assert_equal(escape(s2), expected2)


def test_hashlist():
    h1 = hashlist(["a"])
    h2 = hashlist(["a", 1])

    assert_not_equal(h1, h2)


def test_deprecated():
    @deprecated
    def deprect_func():
        pass
    deprect_func()
    assert_true(True)


class SignalCallback(object):

    def __init__(self):
        self.keyboard_interrupt = False
        self.system_exit = False
        self.sig_num = -1

    def callback(self, exception):
        print(exception)
        if isinstance(exception, SignalExecption):
            self.sig_num = exception.sig_num
        if isinstance(exception, KeyboardInterrupt):
            self.keyboard_interrupt = True
        if isinstance(exception, SystemExit):
            self.system_exit = True


def test_sig_handler():
    # Keyboard interrupt
    def key_interrupt(signal_callback):
        with SigHandler(signal_callback.callback):
            raise KeyboardInterrupt()

    sc = SignalCallback()
    assert_raises(KeyboardInterrupt, key_interrupt, signal_callback=sc)
    assert_true(sc.keyboard_interrupt)

    # System exit
    def sys_exit(signal_callback):
        with SigHandler(signal_callback.callback):
            raise SystemExit(1)

    sc = SignalCallback()
    assert_raises(SystemExit, sys_exit, signal_callback=sc)
    assert_true(sc.system_exit)

    # Signals
    def catch(*args, **kwargs):
        pass

    for sig_num in signal.SIGINT, signal.SIGTERM:
        handler_bu = signal.getsignal(sig_num)
        sc = SignalCallback()
        try:
            signal.signal(sig_num, catch)
            with SigHandler(sc.callback):
                os.kill(os.getpid(), sig_num)
                time.sleep(1)
            assert_equal(sig_num, sc.sig_num)
        finally:
            signal.signal(sig_num, handler_bu)


