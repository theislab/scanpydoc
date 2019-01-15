# -*- coding: future-fstrings -*-
import pkgutil
from functools import partial
from importlib import import_module

from sphinx.testing.fixtures import make_app, test_params
from sphinx.testing.path import path as STP

import scanpydoc


def test_all_get_installed(monkeypatch, make_app, tmp_path):
    setups_seen = set()
    setups_called = {}
    for finder, mod_name, _ in pkgutil.walk_packages(
        scanpydoc.__path__, f"{scanpydoc.__name__}."
    ):
        mod = import_module(mod_name)
        setups_seen.add(mod_name)
        monkeypatch.setattr(mod, "setup", partial(setups_called.__setitem__, mod_name))

    (tmp_path / "conf.py").write_text("")
    app = make_app(srcdir=STP(tmp_path))
    scanpydoc.setup(app)

    assert setups_called.keys() == setups_seen
    for mod_name, app2 in setups_called.items():
        assert app is app2
