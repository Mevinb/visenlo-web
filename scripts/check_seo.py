#!/usr/bin/env python3
"""Check the static site's crawlable SEO contract with Python's standard library.

Default: filesystem checks only, no network and no dependencies.
--live: also check the configured production domain after deployment.
This validates implementation details, not Google indexing, rankings or eligibility.
"""
from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://reactor-web-seven.vercel.app/"
VERIFICATION = "0732bed172a36bf8"


class Page(HTMLParser):
    def __init__(self, path, source=None):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.source = path.read_text(encoding="utf-8") if source is None else source
        self.tags, self.headings, self.schemas = [], [], []
        self.title, self._title = "", False
        self._heading, self._json, self._json_text = None, False, ""
        self.feed(self.source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.tags.append((tag, values))
        if tag == "title":
            self._title = True
        if re.fullmatch(r"h[1-6]", tag):
            self._heading = [tag, ""]
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json, self._json_text = True, ""

    handle_startendtag = handle_starttag

    def handle_data(self, text):
        if self._title:
            self.title += text
        if self._heading is not None:
            self._heading[1] += text
        if self._json:
            self._json_text += text

    def handle_endtag(self, tag):
        if tag == "title":
            self._title = False
        if self._heading is not None and tag == self._heading[0]:
            self.headings.append((tag, " ".join(self._heading[1].split())))
            self._heading = None
        if tag == "script" and self._json:
            self.schemas.append(json.loads(self._json_text))
            self._json = False

    def meta(self, key):
        return [a.get("content", "") for tag, a in self.tags if tag == "meta"
                and (a.get("name") == key or a.get("property") == key)]

    def links(self, rel):
        return [a.get("href", "") for tag, a in self.tags if tag == "link" and rel in a.get("rel", "").split()]

    @property
    def ids(self):
        return [a["id"] for _, a in self.tags if a.get("id")]

    @property
    def indexable(self):
        return not any("noindex" in value.lower() for value in self.meta("robots"))


def local_file(url):
    path = unquote(urlsplit(url).path).lstrip("/") or "index.html"
    candidate = (ROOT / path).resolve()
    if not candidate.is_relative_to(ROOT):
        return None
    return candidate / "index.html" if candidate.is_dir() else candidate


def schema_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def fetch(url, follow_redirects=True):
    request = Request(url, headers={"User-Agent": "Visenlo-SEO-check/1.0"})
    try:
        with (urlopen(request, timeout=20) if follow_redirects else build_opener(NoRedirect()).open(request, timeout=20)) as response:
            return response.status, response.headers, response.read(), response.url
    except HTTPError as response:
        return response.code, response.headers, response.read(), response.url


def run(live=False):
    failures = []
    count = 0

    def check(condition, message):
        nonlocal count
        count += 1
        if not condition:
            failures.append(message)
            print("FAIL:", message)

    pages = {}
    for path in ROOT.glob("*.html"):
        if path.name.startswith("google"):
            continue  # Google's verification token is not a content page.
        try:
            pages[path] = Page(path)
        except (ValueError, OSError) as error:
            check(False, f"{path.name}: parse HTML/JSON-LD: {error}")
    indexable = {p: page for p, page in pages.items() if page.indexable}
    check(bool(indexable), "At least one indexable content page exists")
    titles, descriptions, canonical_urls = [], [], []
    all_nodes = [node for page in pages.values() for data in page.schemas for node in schema_nodes(data)]
    defined_ids = {node["@id"] for node in all_nodes if "@id" in node and "@type" in node}
    robot = RobotFileParser()
    robot.parse((ROOT / "robots.txt").read_text().splitlines())
    check(ORIGIN + "sitemap.xml" in (robot.site_maps() or []), "robots.txt declares the canonical sitemap")

    for path, page in pages.items():
        relative = path.relative_to(ROOT).as_posix()
        page_url = urljoin(ORIGIN, "" if relative == "index.html" else relative)
        ids = page.ids
        check(len(ids) == len(set(ids)), f"{relative}: duplicate HTML IDs")
        check(len([h for h in page.headings if h[0] == "h1"]) == 1, f"{relative}: one meaningful H1")
        check(any(tag == "html" and a.get("lang") == "en" for tag, a in page.tags), f"{relative}: declared document language")
        check(bool(page.meta("viewport")), f"{relative}: mobile viewport declaration")
        if page.indexable:
            check(bool(page.title.strip()), f"{relative}: nonempty title")
            check(len(page.meta("description")) == 1 and bool(page.meta("description")[0]), f"{relative}: one nonempty meta description")
            check(page.links("canonical") == [page_url], f"{relative}: exactly one self-referencing HTTPS canonical")
            check(page.meta("og:url") == [page_url], f"{relative}: Open Graph URL equals canonical")
            check(page.meta("og:title") == [page.title], f"{relative}: Open Graph title matches page title")
            check(page.meta("twitter:title") == [page.title], f"{relative}: social title matches page title")
            check(page.meta("og:description") == page.meta("description"), f"{relative}: Open Graph description matches page")
            check(page.meta("twitter:description") == page.meta("description"), f"{relative}: Twitter description matches page")
            check(page.meta("twitter:card") == ["summary_large_image"], f"{relative}: large social card declared")
            check(bool(page.meta("og:image:alt")) and bool(page.meta("twitter:image:alt")), f"{relative}: descriptive social image alternatives")
            check(page.meta("google-site-verification") == [VERIFICATION], f"{relative}: original Google verification retained")
            check(robot.can_fetch("Googlebot", page_url), f"{relative}: content crawl permitted")
            check(bool(page.schemas), f"{relative}: parseable JSON-LD")
            check(bool(page.links("icon")), f"{relative}: favicon present")
            for data in page.schemas:
                check(data.get("@context") == "https://schema.org", f"{relative}: Schema.org JSON-LD context")
            for node in (n for data in page.schemas for n in schema_nodes(data)):
                check(node.get("@type") != "SearchAction", f"{relative}: no invented site-search action")
                check(not any(k in node for k in ("aggregateRating", "review")), f"{relative}: no fabricated ratings/reviews")
                if "@id" in node and "@type" not in node:
                    check(node["@id"] in defined_ids, f"{relative}: structured data reference resolves: {node['@id']}")
            for image_url in page.meta("og:image"):
                image_path = local_file(image_url)
                check(urlsplit(image_url).netloc == urlsplit(ORIGIN).netloc and bool(image_path and image_path.is_file()), f"{relative}: social image exists on canonical origin")
                if image_path and image_path.is_file() and image_path.suffix == ".png":
                    data = image_path.read_bytes()
                    check(data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", data[16:24]) == (1200, 630), f"{relative}: social image is really 1200×630")
            titles.append(page.title)
            descriptions.extend(page.meta("description"))
            canonical_urls.append(page_url)
        else:
            check(path.name == "404.html", f"{relative}: unexpected content page excluded from indexing")

        for tag, attrs in page.tags:
            if tag == "img":
                check("alt" in attrs, f"{relative}: image alternative text declared")
                check(bool(attrs.get("width") and attrs.get("height")), f"{relative}: image dimensions reserve layout space")
            references = []
            if tag == "a":
                check(bool(attrs.get("href")) and attrs.get("href") != "#"
                      and not attrs.get("href", "").lower().startswith("javascript:"),
                      f"{relative}: navigation has a meaningful destination")
            if attrs.get("srcset"):
                references.extend(candidate.strip().split()[0] for candidate in attrs["srcset"].split(",") if candidate.strip())
            if attrs.get("src"):
                references.append(attrs["src"])
            if tag in ("a", "link") and attrs.get("href"):
                references.append(attrs["href"])
            for reference in references:
                target = urljoin(page_url, reference)
                parts = urlsplit(target)
                if parts.netloc != urlsplit(ORIGIN).netloc or parts.scheme not in ("http", "https"):
                    continue
                target_path = local_file(target)
                check(bool(target_path and target_path.is_file()), f"{relative}: linked local resource exists: {reference}")
                if target_path and target_path in pages and parts.fragment:
                    check(unquote(parts.fragment) in pages[target_path].ids, f"{relative}: local anchor resolves: {reference}")

    check(len(titles) == len(set(titles)), "Indexable page titles are unique")
    check(len(descriptions) == len(set(descriptions)), "Indexable descriptions are unique")
    for path in ROOT.glob("*.css"):
        for match in re.finditer(r"url\(\s*['\"]?([^)'\"\s]+)", path.read_text()):
            reference = match.group(1)
            if not reference.startswith(("data:", "http:", "https:", "#")):
                check((path.parent / reference).is_file(), f"{path.name}: CSS asset exists: {reference}")
    sitemap = ET.parse(ROOT / "sitemap.xml")
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [node.text for node in sitemap.findall("s:url/s:loc", ns)]
    check(set(locations) == set(canonical_urls) and len(locations) == len(set(locations)), "Sitemap lists exactly the canonical content pages, without duplicates or fragments")
    for modified in sitemap.findall("s:url/s:lastmod", ns):
        try:
            check(date.fromisoformat(modified.text) <= date.today(), "Sitemap modification date is real and not in the future")
        except (ValueError, TypeError):
            check(False, "Sitemap lastmod must be a valid date")
    for node in sitemap.iter():
        check(node.tag.split("}")[-1] not in ("priority", "changefreq"), "Sitemap avoids ignored priority/changefreq signals")
    check(zipfile.is_zipfile(ROOT / "downloads/Visenlo.zip"), "Download is an actual ZIP archive")
    config = json.loads((ROOT / "vercel.json").read_text())
    check(config.get("framework", "absent") is None and config.get("outputDirectory") == "." and config.get("buildCommand") == "", "Vercel explicitly serves this static folder without a build")
    check(any(r.get("source") == "/index.html" and r.get("destination") == "/" and r.get("permanent") is True for r in config.get("redirects", [])), "Vercel redirects duplicate /index.html to / permanently")
    download_headers = {h["key"].lower(): h["value"] for rule in config.get("headers", []) if rule.get("source") == "/downloads/Visenlo.zip" for h in rule.get("headers", [])}
    check(download_headers.get("x-robots-tag") == "noindex" and "attachment" in download_headers.get("content-disposition", ""), "Download is configured as an attachment, excluded from search results")
    for source in ("/assets/:path*", "/styles.css", "/site.js"):
        cache_headers = {h["key"].lower(): h["value"] for rule in config.get("headers", []) if rule.get("source") == source for h in rule.get("headers", [])}
        value = cache_headers.get("cache-control", "")
        check("max-age=3600" in value and "must-revalidate" in value and "immutable" not in value,
              f"Vercel {source}: bounded caching for assets without hashed filenames")

    if live:
        for url in canonical_urls + [ORIGIN + "robots.txt", ORIGIN + "sitemap.xml"]:
            try:
                status, headers, content, final = fetch(url)
                check(status == 200, f"Live {url} returns 200 (got {status}; {headers.get('x-vercel-error', '')})")
                check(final == url, f"Live canonical URL has no unexpected redirect: {url}")
                check("noindex" not in headers.get("X-Robots-Tag", "").lower(), f"Live {url} has no index-blocking header")
                if status == 200:
                    local = local_file(url)
                    check(bool(local and content == local.read_bytes()), f"Live {url} serves the current local content")
                    if local in indexable:
                        deployed_page = Page(local, source=content.decode("utf-8"))
                        check(deployed_page.links("canonical") == [url],
                              f"Live {url} canonical points to its actual production URL")
            except (OSError, URLError) as error:
                check(False, f"Live {url}: {error}")
        try:
            status, headers, _, _ = fetch(ORIGIN + "index.html", follow_redirects=False)
            check(status == 308 and urljoin(ORIGIN, headers.get("Location", "")) == ORIGIN,
                  "Live /index.html redirects to / with HTTP308")
            status, headers, content, _ = fetch(ORIGIN + "downloads/Visenlo.zip")
            check(status == 200 and content == (ROOT / "downloads/Visenlo.zip").read_bytes(),
                  "Live source ZIP is current and downloadable")
            check("attachment" in headers.get("Content-Disposition", "")
                  and "noindex" in headers.get("X-Robots-Tag", ""),
                  "Live ZIP attachment and noindex headers are applied")
            for asset in ("styles.css", "site.js", "assets/space-grotesk.woff2"):
                status, headers, _, _ = fetch(ORIGIN + asset)
                value = headers.get("Cache-Control", "")
                check(status == 200 and "max-age=3600" in value and "immutable" not in value,
                      f"Live {asset}: intended bounded cache policy is applied")
            check(fetch(ORIGIN + "definitely-not-a-visenlo-page")[0] == 404, "Live unknown routes return HTTP404, not a soft404")
        except (OSError, URLError) as error:
            check(False, f"Live redirect/download/404 check: {error}")

    print(f"\n{count-len(failures)}/{count} checks passed across {len(indexable)} indexable pages.")
    print("Checks do not establish Google indexing, rich results, Core Web Vitals, or search rank.")
    if not live:
        print("Run with --live after deployment to verify production responses and current content.")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="also check the public production domain (network required)")
    sys.exit(run(parser.parse_args().live))
