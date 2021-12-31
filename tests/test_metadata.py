import pytest

from tripper.data_model import WikipediaWrapper


@pytest.fixture
def processor():
    return WikipediaWrapper('tmp', 'tmp', dict(title_thresh=.9, desc_thresh=.8))


def test_init():
    WikipediaWrapper('tmp', 'tmp', dict(title_thresh=.9, desc_thresh=.8))


def test_get_episodes(processor):
    print(processor.episodes)
    assert True


def test_try_predict_id(processor):
    assert processor.try_predict_id('Murot und das Murmeltier', 'ein Tatort')


def test_try_predict_id2(processor):
    print(processor.try_predict_id('Spielverderber', 'Schimanski '))
    assert True
