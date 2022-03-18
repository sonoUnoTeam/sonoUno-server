from sonouno_server.config import CONFIG


def test_testing():
    assert CONFIG.testing


def test_mongo_uri():
    assert CONFIG.mongo_uri == 'mongodb://test_user:test_user@mongodb:27017/sonouno'
