from os.path import exists

from tests.project_root import get_project_root


def test_project_root():
    assert exists(get_project_root() + "/poetry.lock")
    assert exists(get_project_root() + "/.pre-commit-config.yaml")
