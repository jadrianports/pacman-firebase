import importlib
import sys


def test_release_module_imports_and_has_cli():
    # release.py must import without side effects and expose main() + an arg parser.
    mod = importlib.import_module("release")
    assert hasattr(mod, "main")
    assert hasattr(mod, "build_parser")
    p = mod.build_parser()
    ns = p.parse_args(["--init"])
    assert ns.init is True
