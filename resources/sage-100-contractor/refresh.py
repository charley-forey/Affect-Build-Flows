"""Scrape the Sage 100 Contractor WebHelp (MadCap Flare) -> markdown, and
convert the docs.sage.com PDF guides -> markdown.

    python refresh.py [outdir]        # defaults to this file's directory

Topic list comes from the help system's own Data/Toc_Chunk*.js + Data/Alias.js,
so it is the complete published set, not a link crawl.

Converter core (Node/Tree/inline/block/table) is lifted from
../outbuild/api/refresh.py -- same job, different site.
"""

import concurrent.futures
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

# 20_5 is the newest version on the WebHelp host (checked 19_7..28_1; 20_6+ 404).
# docs.sage.com carries the newer versions but 403s everything except the PDFs.
BASE = "http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5"
HELP_VERSION = "20.5"

# PDFs worth having as text. docs.sage.com serves these but blocks its HTML help.
PDFS = {
    "database-and-company-administration-2025-v27.2": "https://docs.sage.com/docs/en/customer/100contractor/27_2US/open/DatabaseAndCompanyAdministrationGuide.pdf",
    "database-and-company-administration-2024-v26.1": "https://docs.sage.com/docs/en/customer/100contractor/26_1CA/open/DatabaseAndCompanyAdministrationGuide.pdf",
    "database-and-company-administration-2022-v24.1": "https://docs.sage.com/docs/en/customer/100contractor/24_1US/open/DatabaseAndCompanyAdministrationGuide.pdf",
    "sage-100-contractor-and-your-business-2026.1": "https://docs.sage.com/docs/en/customer/100contractor/2026_1US/open/Sage100ContractorandYourBusiness.pdf",
    "user-guide-2021-sql-v23.1": "https://docs.sage.com/docs/en/customer/100contractor/23_1US/open/UserGuide.pdf",
}

VOID = {"br", "img", "hr", "meta", "input", "link", "col"}
SKIP = {"script", "style", "svg", "path", "button", "nav", "head", "title"}
BLOCKS = {"table", "ul", "ol", "pre", "div", "blockquote"}
# MadCap emits its own namespaced tags; HTMLParser lowercases them.
CONTAINERS = {
    "div", "section", "header", "article", "details", "li", "body",
    "madcap:dropdown", "madcap:dropdownbody", "madcap:conditionaltext",
    "madcap:snippetblock", "tbody", "thead", "colgroup", "form",
}
BR = "\x00"  # marks a real <br>, so source-formatting newlines can be collapsed


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

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].kids.append(Node(tag, attrs))

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


def relink(href, depth):
    """Rewrite a topic href so it works inside the repo."""
    if not href or href.startswith(("http://", "https://", "mailto:", "javascript:")):
        return href
    if href.startswith("#"):
        return ""  # in-page MadCap anchors; the target name is meaningless in md
    url, _, frag = href.partition("#")
    if url.lower().endswith((".htm", ".html")):
        return re.sub(r"\.html?$", ".md", url, flags=re.I)
    if url.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        # Images stay on the help host rather than being vendored.
        return urllib.parse.urljoin(f"{BASE}/Content/{'x/' * depth}", url)
    return href


def inline(n, depth):
    """Render inline content to markdown."""
    if isinstance(n, str):
        return n.replace("​", "")
    t = n.tag
    if t in SKIP or "MCBreadcrumbs" in cls(n):
        return ""
    if t == "br":
        return BR
    if t == "img":
        src = relink(n.attrs.get("src", ""), depth)
        return f"![{n.attrs.get('alt', '')}]({src})"
    inner = "".join(inline(k, depth) for k in n.kids)
    if t == "code":
        return f"`{inner.strip()}`" if inner.strip() else ""
    if t in ("strong", "b"):
        return f"**{inner.strip()}**" if inner.strip() else ""
    if t in ("em", "i"):
        return f"*{inner.strip()}*" if inner.strip() else ""
    if t == "del":
        return f"~~{inner}~~"
    if t == "span" and "font-weight: bold" in n.attrs.get("style", ""):
        return f"**{inner.strip()}**" if inner.strip() else ""
    if t == "a":
        href = relink(n.attrs.get("href", ""), depth)
        inner = inner.strip()
        if not inner:
            return ""  # bare <a name="kanchor..."> bookmarks
        return f"[{inner}]({href})" if href else inner
    return inner


def squash(s, br=" "):
    """Collapse source-formatting whitespace; <br> becomes `br`."""
    parts = [re.sub(r"\s+", " ", p).strip() for p in s.split(BR)]
    return br.join(p for p in parts if p).strip()


def walk(n):
    for k in n.kids:
        yield k
        if isinstance(k, Node):
            yield from walk(k)


def table(n, depth):
    rows = []
    for tr in [x for x in walk(n) if isinstance(x, Node) and x.tag == "tr"]:
        cells = [
            squash(inline(c, depth), "<br>").replace("|", "\\|")
            for c in tr.kids
            if isinstance(c, Node) and c.tag in ("td", "th")
        ]
        if cells:
            rows.append(cells)
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def block(n, depth, nest=0):
    """Render a block-level node to markdown chunks."""
    if isinstance(n, str):
        s = squash(n)
        return [s] if s else []
    t = n.tag
    if t in SKIP or "MCBreadcrumbs" in cls(n):
        return []
    if t == "pre":
        return ["```\n" + text(n).strip("\n") + "\n```"]
    if t == "table":
        return [table(n, depth)]
    if re.fullmatch(r"h[1-6]", t):
        s = squash(inline(n, depth))
        return ["#" * int(t[1]) + " " + s] if s else []
    if t == "madcap:dropdownhead":
        s = squash(inline(n, depth)).replace("**", "")
        return [f"**{s}**"] if s else []
    if t == "p":
        # Flare serves invalid <p><table>...</p>; recurse rather than flatten.
        if any(isinstance(k, Node) and k.tag in BLOCKS for k in n.kids):
            return [x for k in n.kids for x in block(k, depth, nest)]
        s = squash(inline(n, depth), "  \n")
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
                    inline(k, depth)
                    for k in li.kids
                    if isinstance(k, str) or k.tag not in BLOCKS
                ),
                "  \n",
            )
            if lead:
                parts.append(lead)
            for k in li.kids:
                if isinstance(k, Node) and k.tag in BLOCKS:
                    parts.extend(block(k, depth, nest + 1))
            body = "\n\n".join(p for p in parts if p)
            ind = " " * len(marker)
            out.append(marker + body.replace("\n", "\n" + ind))
        return ["\n".join(out)] if out else []
    if t == "blockquote":
        inner = "\n\n".join(x for k in n.kids for x in block(k, depth, nest + 1))
        return ["\n".join("> " + l for l in inner.split("\n"))] if inner else []
    if t in CONTAINERS:
        return [x for k in n.kids for x in block(k, depth, nest)]
    s = squash(inline(n, depth))
    return [s] if s else []


def convert(page_html, depth):
    m = re.search(r"<body[^>]*>(.*?)</body>", page_html, re.S | re.I)
    if not m:
        return None
    p = Tree()
    p.feed(m.group(1))
    chunks = [c for k in p.root.kids for c in block(k, depth)]
    md = "\n\n".join(c for c in chunks if c.strip())
    # Identical "More resources" / Sage University footer on all ~2000 topics.
    md = re.split(r"\n#+ More resources\b", md)[0]
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def fetch(url, binary=False, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            break
        except urllib.error.HTTPError:
            raise  # a real 404 will not improve with retrying
        except Exception:
            # The help host drops a handful of connections per full crawl.
            if attempt == tries - 1:
                raise
            time.sleep(1 + attempt)
    if binary:
        return data
    # Topics declare utf-8 but ship cp1252 bytes (en-dashes, curly quotes).
    try:
        return data.decode("utf8")
    except UnicodeDecodeError:
        return data.decode("cp1252", "replace")


def topic_paths():
    """Every published topic, from the help system's own index files."""
    blob = ""
    for i in range(64):
        try:
            blob += fetch(f"{BASE}/Data/Toc_Chunk{i}.js")
        except Exception:
            break
    blob += fetch(f"{BASE}/Data/Alias.js")
    pat = r"(?:/)?(?:Content/)?((?:[A-Za-z0-9_\-]+/)+[A-Za-z0-9_%\-.()',&+]+\.htm)"
    paths = {p for p in re.findall(pat, blob) if not p.startswith("Resources/")}
    return sorted(paths)


def title_of(md, path):
    m = re.search(r"^#+ (.+)$", md, re.M)
    if m:
        return m.group(1).strip()
    return urllib.parse.unquote(os.path.basename(path)[:-4]).replace("_", " ")


def grab(path, outdir):
    # Paths arrive both percent-encoded (from the TOC) and decoded (from disk on the
    # dangling-link pass); normalize so both produce the same URL and the same file.
    path = urllib.parse.unquote(path)
    url = f"{BASE}/Content/{urllib.parse.quote(path, safe='/')}"
    try:
        md = convert(fetch(url), path.count("/"))
    except Exception as e:
        return path, None, f"FAIL {path}: {e}"
    if not md:
        return path, None, f"EMPTY {path}"
    dest = os.path.join(outdir, "help", urllib.parse.unquote(path)[:-4] + ".md")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf8", newline="\n") as f:
        f.write(f"<!-- Source: {url} (Sage 100 Contractor help v{HELP_VERSION}) -->\n\n{md}\n")
    return path, title_of(md, path), None


def pdf_to_md(name, url, outdir):
    dest_dir = os.path.join(outdir, "guides")
    os.makedirs(dest_dir, exist_ok=True)
    pdf = os.path.join(dest_dir, name + ".pdf")
    with open(pdf, "wb") as f:
        f.write(fetch(url, binary=True))
    txt = subprocess.run(
        ["pdftotext", "-layout", "-nopgbrk", pdf, "-"],
        capture_output=True, text=True, encoding="utf8", errors="replace",
    ).stdout
    os.remove(pdf)  # the markdown is what we version; the PDF is 1-4 MB of binary
    txt = re.sub(r"\n{4,}", "\n\n\n", txt).strip()
    dest = os.path.join(dest_dir, name + ".md")
    with open(dest, "w", encoding="utf8", newline="\n") as f:
        f.write(f"<!-- Source: {url} -->\n\n```\n{txt}\n```\n")
    return dest, len(txt)


def dangling(outdir):
    """Topic paths that written pages link to but which aren't on disk yet."""
    root = os.path.join(outdir, "help")
    out = set()
    for dirpath, _, names in os.walk(root):
        for name in names:
            if not name.endswith(".md") or name == "INDEX.md":
                continue
            src = os.path.join(dirpath, name)
            with open(src, encoding="utf8") as f:
                body = f.read()
            for target in re.findall(r"\]\(([^)]+\.md)\)", body):
                target = urllib.parse.unquote(target)
                dest = os.path.normpath(os.path.join(dirpath, target))
                if os.path.exists(dest):
                    continue
                rel = os.path.relpath(dest, root).replace(os.sep, "/")
                if not rel.startswith(".."):
                    out.add(rel[:-3] + ".htm")
    return out


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    paths = topic_paths()
    print(f"{len(paths)} topics")

    index, failures, done = [], [], set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        # Sage's TOC omits some topics that other topics link to. Fetch the indexed
        # set, then chase dangling cross-links until the corpus closes over itself.
        for rnd in range(6):
            todo = [p for p in paths if p not in done]
            if not todo:
                break
            done |= set(todo)
            print(f"round {rnd + 1}: {len(todo)} topics")
            for i, (path, title, err) in enumerate(ex.map(lambda p: grab(p, outdir), todo), 1):
                (failures if err else index).append(err or (path, title))
                if i % 400 == 0:
                    print(f"  {i}/{len(todo)}")
            paths = sorted(dangling(outdir) - done)
            failures = [f for f in failures if isinstance(f, str)]
    print(f"help: {len(index)} written, {len(failures)} skipped")
    for f in failures[:20]:
        print("  " + f)

    for name, url in PDFS.items():
        try:
            dest, n = pdf_to_md(name, url, outdir)
            print(f"pdf: {dest} ({n} chars)")
        except Exception as e:
            print(f"pdf FAIL {name}: {e}")

    write_index(outdir, index)


def write_index(outdir, index):
    """help/INDEX.md -- every topic, grouped by section, so an agent can grep one file."""
    groups = {}
    for path, title in sorted(index):
        p = urllib.parse.unquote(path)
        groups.setdefault(p.split("/")[0], []).append((p, title))
    lines = [
        f"# Sage 100 Contractor help — topic index (v{HELP_VERSION})",
        "",
        f"{len(index)} topics scraped from `{BASE}`. Regenerate with `python refresh.py`.",
        "",
    ]
    for section in sorted(groups):
        lines.append(f"## {section.replace('_', ' ')}")
        lines.append("")
        for p, title in groups[section]:
            rel = p[:-4] + ".md"
            lines.append(f"- [{title}]({urllib.parse.quote(rel)})")
        lines.append("")
    dest = os.path.join(outdir, "help", "INDEX.md")
    with open(dest, "w", encoding="utf8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"index: {dest} ({len(index)} entries)")


if __name__ == "__main__":
    main()
