"""The self-signed certificate that makes a phone turn its camera on.

Browsers only expose `getUserMedia` in a secure context -- HTTPS or localhost
-- so the companion app at `/phone` gets a blocked camera over wifi and no
obvious reason why. This is the thing that unblocks it without a download, an
account, or an internet connection.

The details tested here are the ones that decide whether the phone shows a
warning you can click past or a dead end.
"""
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

pytest.importorskip("cryptography")
from cryptography import x509                              # noqa: E402

from badspotify.hud import tls                             # noqa: E402


@pytest.fixture(autouse=True)
def temp_cert_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(tls, "CERT_DIR", tmp_path)
    monkeypatch.setattr(tls, "CERT", tmp_path / "hud-cert.pem")
    monkeypatch.setattr(tls, "KEY", tmp_path / "hud-key.pem")


def load():
    return x509.load_pem_x509_certificate(tls.CERT.read_bytes())


def san(cert):
    ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
    return ({str(v) for v in ext.value.get_values_for_type(x509.IPAddress)}
            | set(ext.value.get_values_for_type(x509.DNSName)))


def test_it_writes_a_usable_pair():
    cert_path, key_path = tls.ensure_cert("192.168.1.50")
    assert Path(cert_path).exists() and Path(key_path).exists()
    assert "BEGIN" in Path(key_path).read_text()


def test_the_lan_address_is_in_subject_alt_name():
    """The detail that decides whether the phone offers "proceed anyway".
    Without the IP in SAN, browsers reject the certificate outright and the
    warning page is a dead end rather than one tap."""
    tls.ensure_cert("192.168.1.50")
    names = san(load())
    assert "192.168.1.50" in names
    assert "127.0.0.1" in names
    assert "localhost" in names


def test_a_second_call_reuses_the_same_certificate():
    """Regenerating on every run would mean re-accepting the phone's warning
    on every run, which is exactly the friction this is meant to remove."""
    tls.ensure_cert("192.168.1.50")
    first = load().serial_number
    tls.ensure_cert("192.168.1.50")
    assert load().serial_number == first


def test_moving_to_another_network_regenerates_it():
    """The laptop's address changes with the wifi, and a certificate for
    yesterday's network fails in a way that looks like broken code."""
    tls.ensure_cert("192.168.1.50")
    first = load().serial_number
    tls.ensure_cert("10.0.0.7")
    assert load().serial_number != first
    assert "10.0.0.7" in san(load())


def test_it_is_valid_now_and_not_forever():
    tls.ensure_cert("192.168.1.50")
    cert = load()
    now = _dt.datetime.now(_dt.timezone.utc)
    assert cert.not_valid_before_utc <= now < cert.not_valid_after_utc
    assert (cert.not_valid_after_utc - now).days <= 366


def test_a_hostname_instead_of_an_ip_still_works():
    """`_lan_address` falls back to a name when the routing trick fails, and
    that must not crash certificate generation."""
    tls.ensure_cert("my-laptop.local")
    assert "my-laptop.local" in san(load())
