import os

import pytest


@pytest.fixture(scope='module')
def vcr_config():
    return {'match_on': ['method', 'path', 'raw_body']}


@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in tests/integration/cassettes/{module}/{test}.yaml
    return os.path.join('tests/integration/cassettes', request.module.__name__)
