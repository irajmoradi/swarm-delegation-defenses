"""Notification sinks. Toy: sinks are in-memory lists; nothing leaves the process."""
from urllib.parse import urlparse

SENT = []


def host_allowed(url, config):
    return urlparse(url).hostname in config["egress_allowlist"]


def send(url, payload, config):
    if not host_allowed(url, config):
        raise PermissionError(f"egress to {url} not allowed")
    SENT.append({"url": url, "payload": payload})
    return True


def notify_alerts(alerts, config, url="https://alerts.internal.example/hook"):
    for alert in alerts:
        send(url, alert, config)
    return len(alerts)
