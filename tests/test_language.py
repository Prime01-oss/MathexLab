from mathexlab.kernel.session import KernelSession
from mathexlab.kernel.executor import execute


def test_simple_index():
    s = KernelSession()
    execute("x = 1:5", s)
    execute("y = x(1)", s)
    assert s.globals["y"] == 1


def test_range_index():
    s = KernelSession()
    execute("x = 1:5", s)
    execute("y = x(2:4)", s)
    assert s.globals["y"] == [2, 3, 4]


def test_end_index():
    s = KernelSession()
    execute("x = 1:5", s)
    execute("y = x(end)", s)
    assert s.globals["y"] == 5
