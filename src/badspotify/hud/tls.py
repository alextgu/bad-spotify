"""A self-signed certificate, so a phone will turn its camera on.

Browsers only expose `getUserMedia` in a secure context: HTTPS, or localhost.
A phone reaching this machine over wifi is neither, so the companion app at
`/phone` gets a blocked camera and no obvious reason why. That is the single
most likely thing to eat an hour before a demo.

The fix that needs no download, no account and no internet is to serve HTTPS
with a certificate generated here. The phone will warn once -- it is signed by
nobody -- and after "proceed anyway" the page is a secure context and the
camera works. The alternative, a tunnel, is better for showing someone
remotely and worse on a conference wifi that may not let you out.

The certificate names the machine's LAN IP in subjectAltName. Without that,
modern browsers reject it before offering the override, and the warning page
becomes a dead end rather than a speed bump.
"""
from __future__ import annotations

import datetime as _dt
import ipaddress
from pathlib import Path

from ..log import notice as print  # stdout is reserved for data

#Beside the token cache, and gitignored for the same reason: generated, local,
#and meaningless to anyone else.
CERT_DIR = Path(__file__).resolve().parents[3] / ".tls"
CERT = CERT_DIR / "hud-cert.pem"
KEY = CERT_DIR / "hud-key.pem"


def ensure_cert(lan_ip: str) -> tuple[str, str]:
    """Return (cert_path, key_path), generating them if needed."""
    if CERT.exists() and KEY.exists() and _covers(lan_ip):
        return str(CERT), str(KEY)

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NAME_OID := NameOID.COMMON_NAME, lan_ip)])

    alt: list[x509.GeneralName] = [x509.DNSName("localhost")]
    for addr in {lan_ip, "127.0.0.1"}:
        try:
            alt.append(x509.IPAddress(ipaddress.ip_address(addr)))
        except ValueError:
            alt.append(x509.DNSName(addr))

    now = _dt.datetime.now(_dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - _dt.timedelta(minutes=5))
        .not_valid_after(now + _dt.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName(alt), critical=False)
        .sign(key, hashes.SHA256())
    )

    CERT_DIR.mkdir(parents=True, exist_ok=True)
    KEY.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()))
    CERT.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print(f"[hud] generated a self-signed certificate for {lan_ip} "
          f"-> {CERT_DIR.name}/")
    return str(CERT), str(KEY)


def _covers(lan_ip: str) -> bool:
    """Does the existing certificate still name this address?

    The laptop's IP changes with the network, and a certificate for
    yesterday's wifi fails in a way that looks like the code is broken.
    """
    try:
        from cryptography import x509

        cert = x509.load_pem_x509_certificate(CERT.read_bytes())
        san = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName).value
        names = {str(v) for v in san.get_values_for_type(x509.IPAddress)}
        names |= set(san.get_values_for_type(x509.DNSName))
        expired = cert.not_valid_after_utc < _dt.datetime.now(_dt.timezone.utc)
        return lan_ip in names and not expired
    except Exception:
        return False
