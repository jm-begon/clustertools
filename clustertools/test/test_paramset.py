from nose.tools import assert_equal, assert_in, assert_less, assert_raises, \
    with_setup, assert_true

from clustertools import ParameterSet, ConstrainedParameterSet, \
    PrioritizedParamSet, ExplicitParameterSet


# --------------------------------------------------------- ExplicitParameterSet
def test_explicit_paramset():
    ps = ExplicitParameterSet()
    ps.add_parameter_tuple(p1=1, p2=2, p3="param")
    ps.add_parameter_tuple(p1=1, p2=3, p3="param")
    ps.add_parameter_tuple(p1=1, p2=5, p3="param")
    ps.add_parameter_tuple(p1=4, p2=2, p3="param")
    ps.add_parameter_tuple(p1=4, p2=3, p3="param")
    ps.add_parameter_tuple(p1=4, p2=5, p3="param")

    assert_equal(len(ps), 6)

    cart_prod = [
        {"p1": 1, "p2": 2, "p3": "param"},
        {"p1": 1, "p2": 3, "p3": "param"},
        {"p1": 1, "p2": 5, "p3": "param"},
        {"p1": 4, "p2": 2, "p3": "param"},
        {"p1": 4, "p2": 3, "p3": "param"},
        {"p1": 4, "p2": 5, "p3": "param"},
    ]

    assert_equal(len(ps), 6)
    i = 0
    for _, param_dict in ps:
        assert_in(param_dict, cart_prod)
        i += 1
    assert_equal(i, 6)
    assert_equal(len(ps), 6)


# ------------------------------------------------------- Cartesian ParameterSet
def test_paramset_yield():
    ps = ParameterSet()

    assert_equal(len(ps), 1)  # The null dictionary

    ps.add_parameters(p1=1, p2=[2, 3], p3="param")
    ps.add_parameters(p1=4, p2=5)

    cart_prod = [
        {"p1": 1, "p2": 2, "p3": "param"},
        {"p1": 1, "p2": 3, "p3": "param"},
        {"p1": 1, "p2": 5, "p3": "param"},
        {"p1": 4, "p2": 2, "p3": "param"},
        {"p1": 4, "p2": 3, "p3": "param"},
        {"p1": 4, "p2": 5, "p3": "param"},
    ]

    assert_equal(len(ps), 6)
    i = 0
    for _, param_dict in ps:
        assert_in(param_dict, cart_prod)
        i += 1
    assert_equal(i, 6)
    assert_equal(len(ps), 6)


def test_paramset_list_insertion():
    ps = ParameterSet()
    ps.add_single_values(p1=(1, 2, 3), p2=(1, 2))
    assert_equal(len(ps), 1)
    for _, param_dict in ps:
        assert_equal(param_dict, {"p1": (1, 2, 3), "p2": (1, 2)})


def test_paramset_separator():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2], p2=["a", "b"])
    ps.add_separator(p3="param")
    ps.add_parameters(p1=3)

    assert_equal(len(ps), 6)
    for i, param_dict in ps:
        assert_equal(param_dict["p3"], "param")
        if i < 4:
            assert_in(param_dict["p1"], [1, 2])
        else:
            assert_equal(param_dict["p1"], 3)

    ps.add_parameters(p2="c")
    assert_equal(len(ps), 9)
    count = 0
    for i, param_dict in ps:
        assert_equal(param_dict["p3"], "param")
        if i < 4:
            assert_in(param_dict["p1"], [1, 2])
            assert_in(param_dict["p2"], ["a", "b"])
        if param_dict["p1"] == 3 and param_dict["p2"] == "c":
            count += 1

    assert_equal(count, 1)

    assert_raises(ValueError, ps.add_parameters, p4=10)


def test_paramset_getitem():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2], p2=["a", "b"])
    ps.add_separator(p3="param")
    ps.add_parameters(p1=3, p2="c")

    for i, param_dict in ps:
        assert_equal(param_dict, ps[i])


def test_paramset_get_indices_with():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2], p2=["a", "b"])
    ps.add_separator(p3="param")
    ps.add_parameters(p1=3, p2="c")

    for index in ps.get_indices_with(p1={3}):
        assert_less(3, index)  # 0,1,2,3 --> [1,2] x [a,b]
        assert_equal(ps[index]["p1"], 3)

    assert_equal(len(list(ps.get_indices_with(p1={4}))), 0)


# ------------------------------------------------------ ConstrainedParameterSet

def test_constrainparamset():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2, 3], p2=["a", "b"])

    cps = ConstrainedParameterSet(ps)
    cps.add_constraints(c1=lambda p1, p2: True if p2 == "a" else p1 % 2 == 0)

    assert_equal(len(cps), 4)  # (1, a), (2, a), (3, a), (2, b)

    expected = [{"p1": 1, "p2": "a"},
                {"p1": 2, "p2": "a"},
                {"p1": 3, "p2": "a"},
                {"p1": 2, "p2": "b"},
                ]
    for _, param_dict in cps:
        assert_in(param_dict, expected)


# ---------------------------------------------------------- PrioritizedParamSet
def test_prioritized_paramset():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2, 3, 4], p2=["a", "b", "c"])

    pps = PrioritizedParamSet(ps)
    pps.prioritize("p2", "b")
    pps.prioritize("p1", 2)
    pps.prioritize("p1", 3)
    pps.prioritize("p2", "c")

    expected = [
        (4, {"p1": 2, "p2": "b"}),   # 12 = 0 2^0 + 0 2^1 + 1 2^2 + 1 2^ 3
        (7, {"p1": 3, "p2": "b"}),   # 10 = 0 2^0 + 1 2^1 + 0 2^2 + 1 2^ 3
        (1, {"p1": 1, "p2": "b"}),   # 8 = 0 2^0 + 0 2^1 + 0 2^2 + 1 2^ 3
        (10, {"p1": 4, "p2": "b"}),  # 8 = 0 2^0 + 0 2^1 + 0 2^2 + 1 2^ 3

        (5, {"p1": 2, "p2": "c"}),  # 5 = 1 2^0 + 0 2^1 + 1 2^2 + 0 2^ 3
        (3, {"p1": 2, "p2": "a"}),  # 4 = 0 2^0 + 0 2^1 + 1 2^2 + 0 2^ 3

        (8, {"p1": 3, "p2": "c"}),  # 3 = 1 2^0 + 1 2^1 + 0 2^2 + 0 2^ 3
        (6, {"p1": 3, "p2": "a"}),  # 2 = 0 2^0 + 2 2^1 + 0 2^2 + 0 2^ 3


        (2, {"p1": 1, "p2": "c"}),   # 1 = 1 2^0 + 0 2^1 + 0 2^2 + 0 2^ 3
        (11, {"p1": 4, "p2": "c"}),  # 1 = 1 2^0 + 0 2^1 + 0 2^2 + 0 2^ 3


        (0, {"p1": 1, "p2": "a"}),   # 0 = 0 2^0 + 0 2^1 + 0 2^2 + 0 2^ 3
        (9, {"p1": 4, "p2": "a"}),   # 0 = 0 2^0 + 0 2^1 + 0 2^2 + 0 2^ 3
    ]
    result = list(pps)
    assert_equal(result, expected)