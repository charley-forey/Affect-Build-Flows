"""Scrape pp-docs.outbuild.com (Docusaurus, server-rendered) -> markdown files."""
import html
import os
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

BASE = "https://pp-docs.outbuild.com"
OUT = sys.argv[1]

VOID = {"br", "img", "hr", "meta", "input", "link"}
SKIP = {"script", "style", "svg", "path", "button", "nav"}
BLOCKS = {"table", "ul", "ol", "pre", "details", "blockquote", "div"}


class Node:
    def __init__(self, tag, attrs=None):
        self.tag, self.attrs, self.kids = tag, dict(attrs or []), []


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].kids.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].kids.append(data)


def cls(n):
    return n.attrs.get("class", "")


def text(n):
    """Raw text, <br> -> newline. Used for code blocks."""
    if isinstance(n, str):
        return n
    if n.tag == "br":
        return "\n"
    if n.tag in SKIP:
        return ""
    return "".join(text(k) for k in n.kids)


def badge(src):
    m = re.search(r"/badge/([^?]+)", src)
    if not m:
        return ""
    parts = urllib.parse.unquote(m.group(1)).split("-")
    return f"`{parts[1]}`" if len(parts) > 1 else f"`{parts[0]}`"


def absurl(u):
    return urllib.parse.urljoin(BASE, u) if u.startswith("/") else u


def inline(n):
    """Render inline content to markdown."""
    if isinstance(n, str):
        return n.replace("​", "")
    t = n.tag
    if t in SKIP or "hash-link" in cls(n):
        return ""
    if t == "br":
        return BR
    if t == "img":
        src = n.attrs.get("src", "")
        if "img.shields.io" in src:
            return badge(src)
        return f"![{n.attrs.get('alt', '')}]({absurl(src)})"
    inner = "".join(inline(k) for k in n.kids)
    if t == "code":
        return f"`{inner.strip()}`" if inner.strip() else ""
    if t in ("strong", "b"):
        return f"**{inner.strip()}**" if inner.strip() else ""
    if t in ("em", "i"):
        return f"*{inner.strip()}*" if inner.strip() else ""
    if t == "del":
        return f"~~{inner}~~"
    if t == "a":
        href = n.attrs.get("href", "")
        inner = inner.strip()
        return f"[{inner}]({absurl(href)})" if href and inner else inner
    return inner


BR = "\x00"  # marks a real <br>, so source-formatting newlines can be collapsed


def squash(s, br=" "):
    """Collapse source-formatting whitespace; <br> becomes `br`."""
    parts = [re.sub(r"\s+", " ", p).strip() for p in s.split(BR)]
    return br.join(p for p in parts if p).strip()


def codeblock(n):
    lang = ""
    m = re.search(r"language-(\w+)", cls(n))
    if m:
        lang = m.group(1)
    title = ""
    body = ""
    for d in walk(n):
        if isinstance(d, Node):
            if "codeBlockTitle" in cls(d) and not title:
                title = squash(text(d))
            if d.tag == "code" and not body:
                body = text(d)
    body = body.replace("​", "").strip("\n")
    head = f"{lang} title=\"{title}\"" if title else lang
    return f"```{head}\n{body}\n```"


def walk(n):
    for k in n.kids:
        yield k
        if isinstance(k, Node):
            yield from walk(k)


def table(n):
    rows = []
    for tr in [x for x in walk(n) if isinstance(x, Node) and x.tag == "tr"]:
        cells = [
            squash(inline(c), "<br>").replace("|", "\\|")
            for c in tr.kids
            if isinstance(c, Node) and c.tag in ("td", "th")
        ]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def block(n, depth=0):
    """Render a block-level node to markdown chunks."""
    if isinstance(n, str):
        s = squash(n)
        return [s] if s else []
    t = n.tag
    if t in SKIP or "breadcrumbs" in cls(n) or "tocCollapsible" in cls(n):
        return []
    if "codeBlockContainer" in cls(n) or (t == "pre" and depth == 0):
        return [codeblock(n)]
    if t == "table":
        return [table(n)]
    if re.fullmatch(r"h[1-6]", t):
        return ["#" * int(t[1]) + " " + squash(inline(n))]
    if t == "p":
        # The site serves invalid <p><table>…</p>; recurse rather than flatten.
        if any(isinstance(k, Node) and k.tag in BLOCKS for k in n.kids):
            return [x for k in n.kids for x in block(k, depth)]
        s = squash(inline(n), "  \n")
        return [s] if s else []
    if t == "hr":
        return ["---"]
    if t in ("ul", "ol"):
        out, i = [], 1
        for li in [k for k in n.kids if isinstance(k, Node) and k.tag == "li"]:
            marker = "- " if t == "ul" else f"{i}. "
            i += 1
            parts = []
            lead = squash(
                "".join(
                    inline(k)
                    for k in li.kids
                    if isinstance(k, str)
                    or k.tag not in ("ul", "ol", "table", "pre", "div")
                ),
                "  \n",
            )
            if lead:
                parts.append(lead)
            for k in li.kids:
                if isinstance(k, Node) and k.tag in ("ul", "ol", "table", "div", "pre"):
                    parts.extend(block(k, depth + 1))
            body = "\n\n".join(p for p in parts if p)
            ind = " " * len(marker)
            out.append(marker + body.replace("\n", "\n" + ind))
        return ["\n".join(out)]
    if t == "blockquote":
        inner = "\n\n".join(x for k in n.kids for x in block(k, depth + 1))
        return ["\n".join("> " + l for l in inner.split("\n"))] if inner else []
    if t == "summary":
        s = squash(inline(n)).replace("**", "")  # avoid nesting bold inside bold
        return [f"**{s}**"] if s else []
    if t in ("div", "section", "header", "article", "details", "li"):
        return [x for k in n.kids for x in block(k, depth)]
    s = squash(inline(n))
    return [s] if s else []


def convert(page_html):
    m = re.search(
        r'<div class="theme-doc-markdown markdown">(.*?)(?=<footer|</article>)',
        page_html,
        re.S,
    )
    if not m:
        return None
    p = Tree()
    p.feed(m.group(1))
    chunks = [c for k in p.root.kids for c in block(k)]
    md = "\n\n".join(c for c in chunks if c.strip())
    return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf8")


def slug(url):
    path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    path = path.replace("/docs/", "").strip("/") or "index"
    return path.replace(" ", "-") + ".md"


def main():
    sm = fetch(BASE + "/sitemap.xml")
    urls = re.findall(r"<loc>([^<]+)</loc>", sm)
    for u in urls:
        try:
            page = fetch(u)
        except Exception as e:
            print(f"FAIL {u}: {e}")
            continue
        md = convert(page)
        if md is None:
            print(f"SKIP (no doc content) {u}")
            continue
        dest = os.path.join(OUT, slug(u))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf8", newline="\n") as f:
            f.write(f"<!-- Source: {u} -->\n\n{md}")
        print(f"OK {dest} ({len(md)} chars)")


if __name__ == "__main__":
    main()
