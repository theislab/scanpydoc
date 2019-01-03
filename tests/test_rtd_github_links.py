# -*- coding: future-fstrings -*-
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from scanpydoc.rtd_github_links import github_url

HERE = Path(__file__).parent


@pytest.fixture
def env(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("scanpydoc.rtd_github_links.github_base_url", ".")
    monkeypatch.setattr("scanpydoc.rtd_github_links.project_dir", HERE)


def test_as_function(env):
    assert github_url("scanpydoc.rtd_github_links") == "./scanpydoc/rtd_github_links.py"
    assert (
        github_url("scanpydoc.rtd_github_links.github_url")
        == "./scanpydoc/rtd_github_links.py#L101-L121"
    )
