"""Unit tests for the scheme-aware URL logic in njsPC-HA.

The helpers under test live in ``custom_components/njspc_ha/const.py`` and are
pure (no Home Assistant / aiohttp / socketio imports), so this file runs in a
plain interpreter: ``python3 tests/test_scheme.py``. It is also pytest-compatible
(each ``test_*`` function is a real test), so it can be picked up by an upstream
test runner that does have HA available.

Contract under test (the HTTPS fix):
  * A user may enter ``https://pool.example:443``; the scheme must survive into
    the base URL the integration talks to (config_flow validate + NjsPCHAapi).
  * Plain ``http://`` and bare hosts keep working exactly as before (backward
    compatibility — the default scheme for a bare host / legacy entry is http).
  * CONF_HOST is stored scheme-free so the unique-id / entity-id helpers
    (``CONF_HOST.replace(".", "")``) are never corrupted by a ``://``.
"""

import importlib.util
import os
import sys

# Load const.py by file path instead of importing the package: importing
# `custom_components.njspc_ha` runs its __init__.py, which needs aiohttp /
# socketio / homeassistant (not installed in a bare checkout). const.py
# itself is pure (only stdlib), so this is safe and keeps the tests runnable
# in any interpreter.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONST_PATH = os.path.join(
    _REPO_ROOT, "custom_components", "njspc_ha", "const.py"
)
_SPEC = importlib.util.spec_from_file_location("njspc_ha_const", _CONST_PATH)
const = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(const)

CONF_SCHEME = const.CONF_SCHEME
build_base_url = const.build_base_url
parse_scheme = const.parse_scheme
strip_scheme = const.strip_scheme

HTTPS_POOL = "pool-api.siliconspirit.net"


def test_parse_scheme_https():
    assert parse_scheme(f"https://{HTTPS_POOL}") == "https"


def test_parse_scheme_http():
    assert parse_scheme(f"http://{HTTPS_POOL}") == "http"


def test_parse_scheme_bare_host_defaults_http():
    assert parse_scheme(HTTPS_POOL) == "http"


def test_parse_scheme_case_insensitive():
    assert parse_scheme(f"HTTPS://{HTTPS_POOL}") == "https"


def test_parse_scheme_none_or_blank_is_http():
    assert parse_scheme(None) == "http"
    assert parse_scheme("") == "http"
    assert parse_scheme("   ") == "http"


def test_strip_scheme_removes_https():
    assert strip_scheme(f"https://{HTTPS_POOL}") == HTTPS_POOL


def test_strip_scheme_removes_http():
    assert strip_scheme(f"http://{HTTPS_POOL}") == HTTPS_POOL


def test_strip_scheme_bare_host_unchanged():
    assert strip_scheme(HTTPS_POOL) == HTTPS_POOL


def test_strip_scheme_strips_trailing_slash():
    assert strip_scheme(f"https://{HTTPS_POOL}/") == HTTPS_POOL


def test_strip_scheme_trimmed():
    assert strip_scheme(f"  https://{HTTPS_POOL}  ") == HTTPS_POOL


def test_build_base_url_preserves_explicit_https_scheme():
    # The primary HTTPS fix: bare host + explicit scheme -> https base URL.
    assert (
        build_base_url(HTTPS_POOL, 443, "https")
        == f"https://{HTTPS_POOL}:443"
    )


def test_build_base_url_embedded_scheme_wins_for_legacy_entries():
    # Legacy entries that stored the scheme inside CONF_HOST (no CONF_SCHEME)
    # still resolve correctly; the embedded scheme is the only signal there.
    assert (
        build_base_url(f"https://{HTTPS_POOL}", 443, None)
        == f"https://{HTTPS_POOL}:443"
    )
    assert (
        build_base_url(f"http://{HTTPS_POOL}", 4200, None)
        == f"http://{HTTPS_POOL}:4200"
    )


def test_build_base_url_backward_compat_bare_host_defaults_http():
    # A bare host with no scheme at all stays plain http — matches the
    # historical behavior before the HTTPS fix.
    assert (
        build_base_url(HTTPS_POOL, 4200, None)
        == f"http://{HTTPS_POOL}:4200"
    )


def test_build_base_url_strips_trailing_slash():
    assert (
        build_base_url(f"https://{HTTPS_POOL}/", 443, "https")
        == f"https://{HTTPS_POOL}:443"
    )


def test_build_base_url_case_insensitive_scheme():
    assert (
        build_base_url(f"HTTPS://{HTTPS_POOL}", 443, None)
        == f"https://{HTTPS_POOL}:443"
    )


def test_build_base_url_default_port_when_absent():
    # NjsPCHAapi passes data.get(CONF_PORT, 4200); the helper itself trusts the
    # port it is given, so this asserts the default that __init__.py supplies.
    assert (
        build_base_url(HTTPS_POOL, 4200, None)
        == f"http://{HTTPS_POOL}:4200"
    )


def test_conf_scheme_key_is_plain_string():
    # Stored in entry.data alongside CONF_HOST; must be a simple key.
    assert CONF_SCHEME == "scheme"


def _main() -> int:
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {name}: {exc}")
        else:
            print(f"PASS {name}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_main())
