# -*- coding: future-fstrings -*-
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from scanpydoc.rtd_github_links import github_url, _get_linenos

HERE = Path(__file__).parent


@pytest.fixture
def env(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("scanpydoc.rtd_github_links.github_base_url", ".")
    monkeypatch.setattr("scanpydoc.rtd_github_links.project_dir", HERE)


def test_as_function(env):
    assert github_url("scanpydoc.rtd_github_links") == "./scanpydoc/rtd_github_links.py"
    s, e = _get_linenos(github_url)
    assert (
        github_url("scanpydoc.rtd_github_links.github_url")
        == f"./scanpydoc/rtd_github_links.py#L{s}-L{e}"
    )
