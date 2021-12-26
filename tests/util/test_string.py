from tripper.util.string import sort_and_simplify


def test_simplify():
    assert sort_and_simplify('bdde, d und fd,a') == 'a bdde d fd'
