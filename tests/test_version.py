# coding: utf-8

import garden_party


def test_version():
    assert hasattr(garden_party, '__version__')
    assert isinstance(garden_party.__version__, str)
    assert garden_party.__version__ >= '18.5.0'
