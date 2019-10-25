import pkgutil
from functools import partial
from importlib import import_module

import scanpydoc


def test_all_get_installed(monkeypatch, make_app_setup):
    setups_seen = set()
    setups_called = {}
    for finder, mod_name, _ in pkgutil.walk_packages(
        scanpydoc.__path__, f"{scanpydoc.__name__}."
    ):
        mod = import_module(mod_name)
        if not hasattr(mod, "setup"):
            continue
        setups_seen.add(mod_name)
        monkeypatch.setattr(mod, "setup", partial(setups_called.__setitem__, mod_name))

    app = make_app_setup()
    app.setup_extension("scanpydoc")

    assert setups_called.keys() == setups_seen
    for mod_name, app2 in setups_called.items():
        assert app is app2
