#!/usr/bin/env python3
"""Temp inbox — mail.tm primary, guerrillamail fallback."""

from __future__ import annotations

import html
import json
import random
import re
import string
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

MAILTM = "https://api.mail.tm"
MAILGW = "https://api.mail.gw"
GUERRILLA = "https://api.guerrillamail.com/ajax.php"
ONESEC = "https://www.1secmail.com/api/v1/"


@dataclass
class Inbox:
    address: str
    password: str
    token: str
    provider: str = "mail.tm"


def _req(method: str, url: str, data: dict | None = None, headers: dict | None = None) -> dict | list:
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    if data is not None:
        hdrs["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def _members(data: dict | list) -> list[dict]:
    if isinstance(data, list):
        return data
    return data.get("hydra:member", [])


# --- mail.tm ---

def _mailtm_domain() -> str:
    data = _req("GET", f"{MAILTM}/domains")
    members = _members(data)
    if not members:
        raise RuntimeError("No mail.tm domains")
    return members[0]["domain"]


def _mailgw_domain() -> str:
    data = _req("GET", f"{MAILGW}/domains")
    members = _members(data)
    if not members:
        raise RuntimeError("No mail.gw domains")
    return members[0]["domain"]


def _create_mailgw(prefix: str) -> Inbox:
    dom = _mailgw_domain()
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    address = f"{prefix}{suffix}@{dom}"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    _req("POST", f"{MAILGW}/accounts", {"address": address, "password": password})
    token_data = _req("POST", f"{MAILGW}/token", {"address": address, "password": password})
    return Inbox(address=address, password=password, token=token_data["token"], provider="mail.gw")


def _create_1secmail(prefix: str) -> Inbox:
    with urllib.request.urlopen(f"{ONESEC}?action=genRandomMailbox&count=1") as resp:
        boxes = json.loads(resp.read())
    address = boxes[0]
    login, domain = address.split("@")
    return Inbox(address=address, password="", token=f"{login}|{domain}", provider="1secmail")


def _list_1secmail(inbox: Inbox) -> list[dict]:
    login, domain = inbox.token.split("|", 1)
    url = f"{ONESEC}?action=getMessages&login={login}&domain={domain}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


def _read_1secmail(inbox: Inbox, msg_id: str) -> dict:
    login, domain = inbox.token.split("|", 1)
    url = f"{ONESEC}?action=readMessage&login={urllib.parse.quote(login)}&domain={urllib.parse.quote(domain)}&id={msg_id}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    return {
        "from": {"address": data.get("from", "")},
        "subject": data.get("subject", ""),
        "text": data.get("textBody", "") or "",
        "html": data.get("body", "") or "",
    }


def _create_mailtm(prefix: str) -> Inbox:
    dom = _mailtm_domain()
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    address = f"{prefix}{suffix}@{dom}"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    _req("POST", f"{MAILTM}/accounts", {"address": address, "password": password})
    token_data = _req("POST", f"{MAILTM}/token", {"address": address, "password": password})
    return Inbox(address=address, password=password, token=token_data["token"], provider="mail.tm")


def _list_mailtm(inbox: Inbox) -> list[dict]:
    data = _req("GET", f"{MAILTM}/messages", headers={"Authorization": f"Bearer {inbox.token}"})
    return _members(data)


def _read_mailtm(inbox: Inbox, msg_id: str) -> dict:
    return _req("GET", f"{MAILTM}/messages/{msg_id}", headers={"Authorization": f"Bearer {inbox.token}"})


# --- guerrillamail ---

@dataclass
class _Guerrilla:
    address: str
    sid: str


def _create_guerrilla(prefix: str) -> Inbox:
    user = prefix + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    params = urllib.parse.urlencode(
        {"f": "set_email_user", "email_user": user, "lang": "en", "ip": "127.0.0.1", "agent": "seller-tools/1.0"}
    )
    req = urllib.request.Request(f"{GUERRILLA}?{params}")
    with urllib.request.urlopen(req) as resp:
        cookies = resp.headers.get_all("Set-Cookie") or []
        sid = ""
        for c in cookies:
            if "PHPSESSID=" in c:
                sid = c.split("PHPSESSID=")[1].split(";")[0]
        data = json.loads(resp.read())
    address = data["email_addr"]
    return Inbox(address=address, password="", token=sid, provider="guerrillamail")


def _list_guerrilla(inbox: Inbox) -> list[dict]:
    params = urllib.parse.urlencode({"f": "check_email", "seq": 0, "ip": "127.0.0.1", "agent": "seller-tools/1.0"})
    req = urllib.request.Request(f"{GUERRILLA}?{params}", headers={"Cookie": f"PHPSESSID={inbox.token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data.get("list", [])


def _read_guerrilla(inbox: Inbox, msg_id: str) -> dict:
    params = urllib.parse.urlencode(
        {"f": "fetch_email", "email_id": msg_id, "ip": "127.0.0.1", "agent": "seller-tools/1.0"}
    )
    req = urllib.request.Request(f"{GUERRILLA}?{params}", headers={"Cookie": f"PHPSESSID={inbox.token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    body = html.unescape(data.get("mail_body", "") or "")
    return {
        "from": {"address": data.get("mail_from", "")},
        "subject": html.unescape(data.get("mail_subject", "")),
        "text": body,
        "html": body,
    }


# --- public API ---

def create_inbox(prefix: str = "sellertools", provider: str = "auto") -> Inbox:
    errors: list[str] = []
    order = ["mail.gw", "mail.tm", "1secmail", "guerrillamail"] if provider == "auto" else [provider]
    for prov in order:
        for attempt in range(3):
            try:
                if prov == "guerrillamail":
                    return _create_guerrilla(prefix)
                if prov == "mail.tm":
                    return _create_mailtm(prefix)
                if prov == "mail.gw":
                    return _create_mailgw(prefix)
                if prov == "1secmail":
                    return _create_1secmail(prefix)
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    time.sleep(10 * (attempt + 1))
                    continue
                errors.append(f"{prov}: {e}")
                break
        if provider != "auto":
            raise RuntimeError(errors[-1] if errors else prov)
    raise RuntimeError("All temp mail providers failed: " + "; ".join(errors))


def list_messages(inbox: Inbox) -> list[dict]:
    if inbox.provider == "guerrillamail":
        return _list_guerrilla(inbox)
    if inbox.provider == "1secmail":
        return _list_1secmail(inbox)
    if inbox.provider == "mail.gw":
        data = _req("GET", f"{MAILGW}/messages", headers={"Authorization": f"Bearer {inbox.token}"})
        return _members(data)
    return _list_mailtm(inbox)


def read_message(inbox: Inbox, msg_id: str) -> dict:
    if inbox.provider == "guerrillamail":
        return _read_guerrilla(inbox, msg_id)
    if inbox.provider == "1secmail":
        return _read_1secmail(inbox, msg_id)
    if inbox.provider == "mail.gw":
        return _req("GET", f"{MAILGW}/messages/{msg_id}", headers={"Authorization": f"Bearer {inbox.token}"})
    return _read_mailtm(inbox, msg_id)


def _msg_id(msg: dict, provider: str) -> str:
    if provider in ("mail.tm", "mail.gw"):
        return msg.get("id", "")
    if provider == "1secmail":
        return str(msg.get("id", ""))
    return str(msg.get("mail_id", ""))


def wait_for_code(
    inbox: Inbox,
    *,
    digits: int = 6,
    timeout: int = 180,
    interval: int = 5,
) -> str | None:
    seen: set[str] = set()
    deadline = time.time() + timeout
    pattern = re.compile(rf"\b(\d{{{digits}}})\b")
    while time.time() < deadline:
        for msg in list_messages(inbox):
            mid = _msg_id(msg, inbox.provider)
            if not mid or mid in seen:
                continue
            seen.add(mid)
            full = read_message(inbox, mid)
            text = full.get("text") or ""
            html_body = full.get("html") or ""
            if isinstance(text, list):
                text = " ".join(str(x) for x in text)
            if isinstance(html_body, list):
                html_body = " ".join(str(x) for x in html_body)
            body = html.unescape(str(text) + str(html_body))
            m = pattern.search(body)
            if m:
                return m.group(1)
        time.sleep(interval)
    return None


def wait_for_link(
    inbox: Inbox,
    *,
    sender_contains: str = "",
    timeout: int = 180,
    interval: int = 5,
) -> str | None:
    seen: set[str] = set()
    deadline = time.time() + timeout
    while time.time() < deadline:
        for msg in list_messages(inbox):
            mid = _msg_id(msg, inbox.provider)
            if not mid or mid in seen:
                continue
            seen.add(mid)
            full = read_message(inbox, mid)
            from_addr = (full.get("from") or {}).get("address", "") if isinstance(full.get("from"), dict) else str(full.get("from", ""))
            if sender_contains and sender_contains.lower() not in from_addr.lower():
                continue
            text = full.get("text") or ""
            html_body = full.get("html") or ""
            if isinstance(text, list):
                text = " ".join(str(x) for x in text)
            if isinstance(html_body, list):
                html_body = " ".join(str(x) for x in html_body)
            body = str(text) + str(html_body)
            links = re.findall(r"https?://[^\s\"'<>]+", body)
            for link in links:
                clean = html.unescape(link.rstrip(").,;]"))
                if "unsubscribe" not in clean.lower():
                    return clean
        time.sleep(interval)
    return None


if __name__ == "__main__":
    for prov in ("guerrillamail", "mail.tm"):
        try:
            box = create_inbox(provider=prov)
            print(json.dumps({"provider": box.provider, "address": box.address, "password": box.password}, indent=2))
            break
        except Exception as e:
            print(f"{prov} failed: {e}", file=__import__("sys").stderr)