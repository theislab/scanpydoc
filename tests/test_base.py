# -*- coding: future-fstrings -*-
import pkgutil
from functools import partial
from importlib import import_module

import scanpydoc


def test_all_get_installed(monkeypatch, app_no_setup):
    setups_seen = set()
    setups_called = {}
    for finder, mod_name, _ in pkgutil.walk_packages(
        scanpydoc.__path__, f"{scanpydoc.__name__}."
    ):
        mod = import_module(mod_name)
        setups_seen.add(mod_name)
        monkeypatch.setattr(mod, "setup", partial(setups_called.__setitem__, mod_name))

    scanpydoc.setup(app_no_setup)

    assert setups_called.keys() == setups_seen
    for mod_name, app2 in setups_called.items():
        assert app_no_setup is app2
