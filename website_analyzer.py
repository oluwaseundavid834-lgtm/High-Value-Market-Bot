"""Safe public-page fetching and lightweight on-page SEO analysis.

Protects against SSRF by validating every URL and every redirect target,
and by refusing private/loopback/link-local/reserved IPs.
"""

import asyncio
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

MAX_BYTES = 1_000_000
TIMEOUT = 15.0
USER_AGENT = "HighValueMarketBot/1.0 (+https://t.me/)"
BLOCKED_HOSTS = {"localhost", "ip6-localhost", "ip6-loopback"}


class UnsafeURLError(Exception):
    pass


async def _is_safe_url(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Could not parse the URL."
    if parsed.scheme not in ("http", "https"):
        return False, "Only http:// or https:// URLs are allowed."
    host = (parsed.hostname or "").lower()
    if not host or host in BLOCKED_HOSTS:
        return False, "This host is not allowed."
    loop = asyncio.get_event_loop()
    try:
        infos = await loop.run_in_executor(None, socket.getaddrinfo, host, None)
    except Exception:
        return False, "Could not resolve the host."
    for info in infos:
        ip_str = info[4][0]
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
            return False, "This host resolves to a non-public IP address."
    return True, ""


async def fetch_html(url: str) -> tuple[str, str]:
    """Fetch HTML following a limited number of safe redirects."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    safe, reason = await _is_safe_url(url)
    if not safe:
        raise UnsafeURLError(reason)

    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"}
    current = url
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False) as client:
        for _ in range(4):
            resp = await client.get(current, headers=headers)
            if resp.status_code in (301, 302, 303, 307, 308):
                nxt = resp.headers.get("location")
                if not nxt:
                    raise UnsafeURLError("Invalid redirect.")
                nxt = urljoin(current, nxt)
                safe, reason = await _is_safe_url(nxt)
                if not safe:
                    raise UnsafeURLError(f"Unsafe redirect: {reason}")
                current = nxt
                continue
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").lower()
            if "html" not in content_type and "xml" not in content_type:
                raise UnsafeURLError("URL did not return an HTML page.")
            return current, resp.text[:MAX_BYTES]
    raise UnsafeURLError("Too many redirects.")


def analyze_html(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else None

    meta_desc = None
    for tag in soup.find_all("meta"):
        if (tag.get("name") or "").lower() == "description":
            meta_desc = (tag.get("content") or "").strip()
            break

    headings = []
    for h in soup.find_all(re.compile(r"^h[1-6]$", re.IGNORECASE)):
        try:
            level = int(h.name[1])
        except (ValueError, IndexError):
            continue
        text = h.get_text(" ", strip=True)
        if text:
            headings.append((level, text[:200]))

    canonical = None
    for tag in soup.find_all("link"):
        rel = tag.get("rel") or []
        if isinstance(rel, str):
            rel = [rel]
        if "canonical" in [r.lower() for r in rel]:
            canonical = tag.get("href")
            break

    robots_meta = None
    for tag in soup.find_all("meta"):
        if (tag.get("name") or "").lower() == "robots":
            robots_meta = (tag.get("content") or "").strip()
            break

    for s in soup(["script", "style", "noscript"]):
        s.decompose()
    text = soup.get_text(" ", strip=True)
    word_count = len(text.split())

    images = soup.find_all("img")
    images_missing_alt = sum(1 for img in images if not (img.get("alt") or "").strip())

    links = soup.find_all("a", href=True)
    internal = sum(1 for a in links if not a["href"].startswith(("http://", "https://", "mailto:", "tel:", "#", "//")))
    external = len(links) - internal

    h1s = [t for lvl, t in headings if lvl == 1]

    return {
        "url": url,
        "title": title,
        "title_length": len(title) if title else 0,
        "meta_description": meta_desc,
        "meta_description_length": len(meta_desc) if meta_desc else 0,
        "headings": headings[:60],
        "h1_count": len(h1s),
        "h1s": h1s[:5],
        "canonical": canonical,
        "robots_meta": robots_meta,
        "word_count": word_count,
        "images": len(images),
        "images_missing_alt": images_missing_alt,
        "internal_links": internal,
        "external_links": external,
        "text_sample": text[:3000],
    }


def format_audit_summary(data: dict) -> str:
    issues: list[str] = []
    wins: list[str] = []

    if not data["title"]:
        issues.append("❌ Missing <title> tag.")
    elif data["title_length"] < 30 or data["title_length"] > 65:
        issues.append(f"⚠️ Title length is {data['title_length']} chars (ideal 50-60).")
    else:
        wins.append(f"✅ Title present ({data['title_length']} chars).")

    if not data["meta_description"]:
        issues.append("❌ Missing meta description.")
    elif data["meta_description_length"] < 120 or data["meta_description_length"] > 165:
        issues.append(f"⚠️ Meta description length is {data['meta_description_length']} (ideal 140-160).")
    else:
        wins.append(f"✅ Meta description present ({data['meta_description_length']} chars).")

    if data["h1_count"] == 0:
        issues.append("❌ No H1 detected.")
    elif data["h1_count"] > 1:
        issues.append(f"⚠️ Multiple H1s detected ({data['h1_count']}).")
    else:
        wins.append("✅ Exactly one H1 detected.")

    if data["word_count"] < 300:
        issues.append(f"⚠️ Low word count ({data['word_count']}).")
    else:
        wins.append(f"✅ Word count: {data['word_count']}.")

    if data["images_missing_alt"] > 0:
        issues.append(f"⚠️ {data['images_missing_alt']} image(s) without alt text.")

    if not data["canonical"]:
        issues.append("⚠️ No canonical tag detected.")
    else:
        wins.append(f"✅ Canonical: {data['canonical']}")

    if data["robots_meta"] and "noindex" in data["robots_meta"].lower():
        issues.append("🚫 Page is set to noindex.")

    lines = [f"🌐 *Public Page Analysis* — {data['url']}", ""]
    lines.append("*Detected:*")
    lines.append(f"• Title: {data['title'] or '(missing)'}")
    lines.append(f"• Meta description: {(data['meta_description'] or '(missing)')[:160]}")
    lines.append(f"• H1s: {data['h1_count']}")
    lines.append(f"• Word count: {data['word_count']}")
    lines.append(f"• Images: {data['images']} ({data['images_missing_alt']} missing alt)")
    lines.append(f"• Internal / External links: {data['internal_links']} / {data['external_links']}")
    lines.append("")
    if wins:
        lines.append("*Strengths:*")
        lines.extend(wins)
        lines.append("")
    if issues:
        lines.append("*Issues found:*")
        lines.extend(issues)
        lines.append("")
    lines.append("ℹ️ Public page data only — this is not a full Google Search Console audit.")
    return "\n".join(lines)
