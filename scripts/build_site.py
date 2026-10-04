#!/usr/bin/env python3
"""Build the Signalbox reading station into ``build/site``.

The station is a static projection. Article authority stays with the canonical
Markdown under ``docs/`` and the root README siblings; this builder only
renders that source into a reading shell and attaches synthetic replay
receipts computed by the canonical ``scripts.replay`` implementation.

Nothing here contacts a network, a router, or a deployment. ``build/site`` is
ignored generated output and is never treated as deployment evidence.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from markdown_it import MarkdownIt

from scripts.repository_paths import RepositoryPathError, resolve_repository_path

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
ASSET_DIR = SITE_DIR / "assets"
OUT_DIR = ROOT / "build" / "site"

REPO_URL = "https://github.com/IndelibleVivi/signalbox-routing"
MERMAID_VERSION = "11.4.1"
MERMAID_JS = (
    f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.esm.min.mjs"
)

# Fonts are the kit's typewriter/monospace pair, loaded from Google Fonts with
# system fallbacks. This is the only third-party font request; see site/README.
FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Special+Elite&family=IBM+Plex+Mono:wght@400;500&display=swap');"
)

# Assets copied byte-for-byte from the supplied design kit. The values are a
# content-identity check, not a license grant; see site/README.md.
SUPPLIED_ASSETS = {
    "receiving-room.webp": "ce34c1acc22e362e486957c2b5b5d5d6ec800b7872448f27afc52bccead47745",
    "tape-s-mark.webp": "e040ec46429fafc295416170b8e0c364ba2f10189b16fdf3891c97bea77dd06e",
    "courier-note.webp": "728f68b914418e675ff9ebf233141af5212340658ec5467468dae45c9ecead0c",
}

# Necessary agent/reference sources rendered for the workbench and reference
# shelf. Human navigation still owns the main reading paths. The bilingual
# human pairs come from ``contracts/docs-pairs.json`` so this list cannot
# silently diverge from the registered documentation contract.
REFERENCE_DOCS = [
    ("signalbox.agent.surface", "docs/agent/README.md", "Agent Surface"),
    ("signalbox.agent.workflow", "docs/agent/workflow.md", "Agent Workflow"),
    ("signalbox.agent.implementation-reference", "docs/agent/implementation-reference.md", "Implementation Reference"),
    ("signalbox.agent.tailnet-vps-implementation-reference", "docs/agent/tailnet-vps-implementation-reference.md", "Tailnet/VPS Implementation Reference"),
    ("signalbox.agent.acceptance-matrix", "docs/agent/acceptance-matrix.md", "Acceptance Matrix"),
    ("signalbox.agent.patch-protocol", "docs/agent/patch-protocol.md", "Patch Protocol"),
    ("signalbox.reference.glossary", "docs/reference/glossary.md", "Glossary"),
    ("signalbox.reference.health-and-observability", "docs/reference/health-and-observability.md", "Health and Observability"),
    ("signalbox.reference.failure-catalog", "docs/reference/failure-catalog.md", "Failure Catalog"),
    ("signalbox.specification", "docs/specification.md", "Specification"),
    ("signalbox.programme-plan", "docs/programme-plan.md", "Programme Plan"),
    ("signalbox.current-state", "docs/current-state.md", "Current State"),
    ("signalbox.examples.mintie", "examples/mintie/README.md", "Mintie Reference"),
    ("signalbox.examples.scenarios", "examples/scenarios/README.md", "Synthetic Scenarios"),
    ("signalbox.schemas", "schemas/README.md", "JSON Schemas"),
]

# The station's own guide is rendered as a page so its links resolve locally.
SITE_README = "site/README.md"

# Kit index copy rendered as the interactive workbench receipt. The label is
# authored shell text; the numbers come from scripts.replay at build time.
SCENARIO_LABELS = {
    "canonical-direct-overlap": (
        "集合重叠时的选路",
        "canonical private ingress 与 DIRECT 集合重叠时，哪条路由先胜出。",
    ),
    "domain-versus-ip-only": (
        "域名与仅 IP 连接",
        "同一个应用的 domain 请求与 IP-only 连接，不保证走同一条路由。",
    ),
    "router-probe-versus-lan": (
        "路由器探测与 LAN 覆盖",
        "绕过 LAN 的一段探测，不能代表整条路径。",
    ),
    "awake-versus-sleeping": (
        "清醒与休眠的客户端",
        "同一 upstream 下，只有客户端侧交互不同。",
    ),
    "new-report-old-observations": (
        "新报告，旧观测",
        "报告结构通过，但观测年龄超过 profile 上限。",
    ),
    "pointer-changes-before-decision": (
        "decision 前指针已变",
        "旧 identity 不能授权新的 current generation。",
    ),
    "older-attempt-finishes-last": (
        "先开始的 attempt 后完成",
        "晚完成的旧 attempt 只归档，current 仍归新 generation。",
    ),
    "restart-continuity-unknown": (
        "重启后连续性未知",
        "无法确认 epoch/sequence continuity 时保留 guard。",
    ),
}

EXPLICIT_ANCHOR = re.compile(r"^<a\s+id=\"([^\"]+)\"\s*></a>\s*$")


def load_pairs() -> list[tuple[str, str, str]]:
    """Read the bilingual documentation registry from the owning contract."""
    document = json.loads((ROOT / "contracts/docs-pairs.json").read_text(encoding="utf-8"))
    return [(pair["doc_id"], pair["zh-CN"], pair["en"]) for pair in document["pairs"]]


def source_identity() -> dict[str, str]:
    """Describe the actual Git HEAD and whether the worktree content is exact.

    Worktree changes mean HEAD is not the content being built, so the
    manifest records a dirty-worktree state instead of pretending the commit
    hash describes the rendered bytes.
    """
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    commit = head.stdout.decode().strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    worktree_changes = [
        line for line in status.stdout.decode().splitlines()
        if line.strip()
    ]
    return {
        "commit": commit,
        "state": "dirty-worktree" if worktree_changes else "exact-head",
        "source_root": f"{REPO_URL}/blob/{commit}",
    }


def slug(text: str) -> str:
    """GitHub-flavoured slug for a heading without an explicit anchor."""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff\- ]+", "", text)
    text = re.sub(r"\s+", "-", text)
    return text


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    block = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


def extract_leading_comment(text: str) -> tuple[dict[str, str], str]:
    """Parse leading ``<!-- key: value -->`` comment blocks (root README)."""
    meta: dict[str, str] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        match = re.fullmatch(r"<!--\s*(.*?)\s*-->", line)
        if not match:
            break
        content = match.group(1)
        if ":" in content:
            key, _, value = content.partition(":")
            meta[key.strip()] = value.strip()
        index += 1
    return meta, "\n".join(lines[index:])


def first_heading(body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return re.sub(r"<[^>]+>", "", line[2:]).strip()
    return ""


@dataclass
class RenderedArticle:
    doc_id: str
    lang: str
    source: str
    title: str
    html: str
    headings: list[tuple[str, str, str]] = field(default_factory=list)


def make_renderer() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    md.enable("table")
    return md


def render_markdown(body: str, md: MarkdownIt) -> tuple[str, list[tuple[str, str, str]]]:
    """Render Markdown, keeping fence languages and explicit anchors."""
    tokens = md.parse(body)
    headings: list[tuple[str, str, str]] = []

    # Attach one id per heading. A preceding standalone ``<a id>`` anchor block
    # transfers its id to the owning heading and is removed, so the explicit
    # stable anchor survives without a duplicate id node. Repeated automatic
    # slugs get a numeric suffix, matching GitHub's duplicate-heading behavior.
    pending_anchor: str | None = None
    drop_inline: set[int] = set()
    drop_block: set[int] = set()
    used: dict[str, int] = {}

    def unique(anchor: str) -> str:
        seen = used.get(anchor, 0)
        used[anchor] = seen + 1
        return anchor if seen == 0 else f"{anchor}-{seen}"

    for index, token in enumerate(tokens):
        if token.type == "inline":
            match = EXPLICIT_ANCHOR.match(token.content.strip())
            if match and all(child.type == "html_inline" for child in token.children or []):
                pending_anchor = match.group(1)
                drop_inline.add(index)
                # Also drop the wrapping paragraph so no empty <p> remains.
                if index > 0 and tokens[index - 1].type == "paragraph_open":
                    drop_block.add(index - 1)
                if index + 1 < len(tokens) and tokens[index + 1].type == "paragraph_close":
                    drop_block.add(index + 1)
                continue
        if token.type == "heading_open":
            inline = tokens[index + 1]
            text = inline.content
            if pending_anchor:
                anchor = pending_anchor
                used[anchor] = used.get(anchor, 0) + 1
            else:
                anchor = unique(slug(text))
            headings.append((token.tag, text, anchor))
            token.attrSet("id", anchor)
            pending_anchor = None
        elif token.type not in ("paragraph_open", "paragraph_close"):
            pending_anchor = None

    # Mark Mermaid fences so the shell can render a readable fallback and the
    # browser can progressively enhance them.
    for token in tokens:
        if token.type == "fence" and token.info.strip().split()[0:1] == ["mermaid"]:
            token.attrJoin("class", "sbx-mermaid-source")

    kept = [
        token for index, token in enumerate(tokens)
        if index not in drop_inline and index not in drop_block
    ]
    rendered = md.renderer.render(kept, md.options, {})
    # Local horizontal scroll for wide tables so the reading column never
    # overflows the page on narrow screens.
    rendered = rendered.replace("<table>", '<div class="sx-table-scroll"><table>')
    rendered = rendered.replace("</table>", "</table></div>")
    return rendered, headings


def build_articles() -> dict[str, RenderedArticle]:
    md = make_renderer()
    articles: dict[str, RenderedArticle] = {}

    def add(source: str, lang: str, doc_id: str) -> None:
        raw = (ROOT / source).read_text(encoding="utf-8")
        if source in {"README.md", "README.zh-CN.md"}:
            _meta, body = extract_leading_comment(raw)
        else:
            _meta, body = split_front_matter(raw)
        title = first_heading(body) or source
        rendered, headings = render_markdown(body, md)
        articles[source] = RenderedArticle(
            doc_id=doc_id, lang=lang, source=source, title=title,
            html=rendered, headings=headings,
        )

    for doc_id, zh, en in load_pairs():
        add(zh, "zh-CN", doc_id)
        add(en, "en", doc_id)
    for doc_id, source, _title in REFERENCE_DOCS:
        lang = "zh-CN" if ".zh-CN." in source else "en"
        add(source, lang, doc_id)
    add(SITE_README, "zh-CN", "signalbox.site")
    return articles


def compute_scenarios() -> list[dict[str, object]]:
    from scripts.replay import replay_case

    cases = json.loads((ROOT / "examples/scenarios/cases.json").read_text(encoding="utf-8"))
    receipts: list[dict[str, object]] = []
    for case in cases:
        actual = replay_case(case)
        expected = case["expected"]
        matched = all(actual.get(key) == value for key, value in expected.items())
        label, blurb = SCENARIO_LABELS.get(case["id"], (case["id"], ""))
        receipts.append(
            {
                "id": case["id"],
                "kind": case["kind"],
                "label": label,
                "blurb": blurb,
                "expected": expected,
                "actual": actual,
                "passed": matched,
            }
        )
    return receipts


def build_manifest(articles: dict[str, RenderedArticle], identity: dict[str, str]) -> dict[str, object]:
    pages = [
        {
            "source": source,
            "output": source[:-3] + ".html",
            "doc_id": article.doc_id,
            "lang": article.lang,
            "title": article.title,
        }
        for source, article in sorted(articles.items())
    ]
    return {
        "generator": "scripts/build_site.py",
        "source_identity": identity,
        "repo_url": REPO_URL,
        "mermaid": {"version": MERMAID_VERSION, "url": MERMAID_JS},
        "fonts": {"import_url": FONT_IMPORT, "families": ["Special Elite", "IBM Plex Mono"]},
        "supplied_assets": [
            {"path": f"site/assets/{name}", "sha256": digest}
            for name, digest in SUPPLIED_ASSETS.items()
        ],
        "pages": pages,
    }


DOC_TITLES = {
    "signalbox.readme": ("通信札记", "Signalbox"),
    "signalbox.human.start-here": ("起步", "Start here"),
    "signalbox.human.architecture": ("架构图解", "Architecture"),
    "signalbox.human.basic-router-guide": ("基础手册", "Basic router guide"),
    "signalbox.human.routing-dns-fail-closed": ("路由与 DNS", "Routing and DNS"),
    "signalbox.human.tailnet-vps-private-ingress": ("私有入口", "Private ingress"),
    "signalbox.human.worked-cases": ("案例", "Worked cases"),
}


@dataclass
class PageSpec:
    source: str
    out_rel: str
    lang: str
    base: str
    doc_id: str
    is_human: bool
    counterpart: str | None = None
    template: str = "article"


def _output_rel(source: str) -> str:
    path = source[:-3] + ".html"
    # Mirror the repository path, preserving the README siblings' basenames.
    return path


def rewrite_links(
    body: str, spec: PageSpec, generated: set[str], source_root: str
) -> str:
    """Rewrite repository-relative links for the generated build tree.

    Every contained Markdown link routes through the shared
    ``resolve_repository_path`` containment contract with the source file's
    directory as base and ``allow_parent=True``. A target that resolves to a
    generated page becomes a local page link (with its ``#anchor``); an actual
    contained file that is not a page becomes an exact public GitHub source
    link. Absolute paths, backslashes, path escape and symlink escape are
    rejected before a link is emitted.
    """
    source_dir = (ROOT / spec.source).parent

    def resolve_target(raw: str) -> str:
        clean = raw.strip().strip("<>")
        if not clean:
            return raw
        parts = urlsplit(clean)
        if parts.scheme in ("http", "https", "mailto"):
            return clean
        if clean.startswith("#"):
            return clean
        if "\\" in clean:
            raise RepositoryPathError(f"link must use POSIX syntax: {raw}")
        path, _, anchor = clean.partition("#")
        if not path:
            return "#" + anchor if anchor else raw
        try:
            resolved = resolve_repository_path(
                ROOT, path, base=source_dir, expected_kind="any", allow_parent=True
            )
        except RepositoryPathError as exc:
            raise RepositoryPathError(f"link is not repository-contained: {raw} ({exc})") from exc
        repo_path = resolved.relative_to(ROOT.resolve()).as_posix()
        if repo_path in generated:
            target = spec.base + _output_rel(repo_path)
        else:
            target = f"{source_root}/{repo_path}"
        return target + (f"#{anchor}" if anchor else "")

    def repl(match: re.Match[str]) -> str:
        prefix, target, suffix = match.group(1), match.group(2), match.group(3)
        return f"{prefix}{resolve_target(target)}{suffix}"

    # Match Markdown links produced by the renderer: href="...".
    return re.sub(r'(href=")([^"]+)(")', repl, body)


def build_toc(article: RenderedArticle) -> str:
    items = []
    for tag, text, anchor in article.headings:
        level = "h3" if tag == "h3" else "h2"
        if tag == "h1":
            continue
        plain = re.sub(r"<[^>]+>", "", text)
        plain = re.sub(r"`([^`]+)`", r"\1", plain).strip()
        items.append(
            f'            <a href="#{anchor}" data-level="{level}">{html.escape(plain)}</a>'
        )
    return "\n".join(items) if items else "            <span class=\"sx-small sx-muted\">本篇没有小节标题。</span>"


def counterpart_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for _doc_id, zh, en in load_pairs():
        mapping[zh] = en
        mapping[en] = zh
    return mapping


def build_pages(articles: dict[str, RenderedArticle]) -> list[PageSpec]:
    pairs = counterpart_map()
    specs: list[PageSpec] = []
    for source, article in articles.items():
        out_rel = _output_rel(source)
        depth = out_rel.count("/")
        base = "../" * depth
        is_human = source in pairs
        counterpart = pairs.get(source)
        specs.append(
            PageSpec(
                source=source,
                out_rel=out_rel,
                lang=article.lang,
                base=base,
                doc_id=article.doc_id,
                is_human=is_human,
                counterpart=counterpart,
                template="note" if source == SITE_README else "article",
            )
        )
    return specs


def _scenario_buttons(scenarios: list[dict[str, object]]) -> tuple[str, str]:
    buttons = []
    for index, item in enumerate(scenarios):
        pressed = "true" if index == 0 else "false"
        buttons.append(
            f'          <li><button type="button" data-scenario-button aria-pressed="{pressed}">'
            f'<span class="sx-mono sx-small">{html.escape(str(item["id"]))}</span><br>'
            f'{html.escape(str(item["label"]))}</button></li>'
        )
    data = json.dumps(scenarios, ensure_ascii=False, sort_keys=True)
    data = data.replace("</", "<\\/")
    return "\n".join(buttons), data


def build() -> int:
    if not (ROOT / "contracts").is_dir():
        raise SystemExit("run from the repository root; contracts/ not found")

    articles = build_articles()
    scenarios = compute_scenarios()
    specs = build_pages(articles)
    generated = set(articles)
    pairs = counterpart_map()
    identity = source_identity()
    source_root = identity["source_root"]

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    (OUT_DIR / "assets").mkdir()

    # Copy supplied assets byte-for-byte and verify their content identity.
    for name, digest in SUPPLIED_ASSETS.items():
        src = ASSET_DIR / name
        actual = hashlib.sha256(src.read_bytes()).hexdigest()
        if actual != digest:
            raise SystemExit(f"supplied asset {name} hash changed: {actual}")
        shutil.copy2(src, OUT_DIR / "assets" / name)
    for extra in ("site.css", "site.js"):
        shutil.copy2(ASSET_DIR / extra, OUT_DIR / "assets" / extra)

    shell = (SITE_DIR / "shell.html").read_text(encoding="utf-8")
    home_tpl = (SITE_DIR / "home.html").read_text(encoding="utf-8")
    article_tpl = (SITE_DIR / "article.html").read_text(encoding="utf-8")
    note_tpl = (SITE_DIR / "note.html").read_text(encoding="utf-8")

    def render_shell(content: str, base: str, lang: str, title: str) -> str:
        return (
            shell.replace("{{BASE}}", base)
            .replace("{{LANG}}", lang)
            .replace("{{TITLE}}", title)
            .replace("{{CONTENT}}", content)
        )

    # Home page.
    buttons, scenario_json = _scenario_buttons(scenarios)
    home_body = home_tpl.replace("{{BASE}}", "").replace("{{SCENARIO_BUTTONS}}", buttons)
    home_body += (
        f'\n    <script type="application/json" data-scenario-data>{scenario_json}</script>'
    )
    (OUT_DIR / "index.html").write_text(
        render_shell(home_body, "", "zh-CN", "Signalbox — 通信札记"), encoding="utf-8"
    )

    # Reading pages.
    for spec in specs:
        article = articles[spec.source]
        body = rewrite_links(article.html, spec, generated, source_root)
        if spec.template == "note":
            content = note_tpl.replace("{{NOTE_BODY}}", body).replace("{{BASE}}", spec.base)
            (OUT_DIR / spec.out_rel).parent.mkdir(parents=True, exist_ok=True)
            (OUT_DIR / spec.out_rel).write_text(
                render_shell(content, spec.base, article.lang, "阅读站说明 — Signalbox"),
                encoding="utf-8",
            )
            continue
        if spec.counterpart:
            other = pairs[spec.source]
            href = spec.base + _output_rel(other)
            other_article = articles[other]
            label = "English" if spec.lang == "zh-CN" else "简体中文"
            lang_links = f'<a href="{href}" hreflang="{other_article.lang}">{label}</a>'
        else:
            lang_links = '<span class="sx-small sx-muted">本篇暂无对照语言。</span>'
        toc = build_toc(article)
        if spec.is_human:
            zh_title, en_title = DOC_TITLES.get(spec.doc_id, (article.title, article.title))
            reader_label = "READER / " + ("简体中文" if spec.lang == "zh-CN" else "ENGLISH")
            article_label = en_title.upper()
            title_suffix = zh_title if spec.lang == "zh-CN" else en_title
        else:
            reader_label = "REFERENCE / " + article.lang.upper()
            article_label = spec.doc_id
            title_suffix = article.title

        content = (
            article_tpl.replace("{{READER_LABEL}}", reader_label)
            .replace("{{ARTICLE_LABEL}}", html.escape(article_label))
            .replace("{{ARTICLE_TITLE}}", html.escape(article.title))
            .replace("{{TOC}}", toc)
            .replace("{{LANG_LINKS}}", lang_links)
            .replace("{{SOURCE_PATH}}", html.escape(spec.source))
            .replace("{{SOURCE_LINK}}", f"{source_root}/{spec.source}")
            .replace("{{SOURCE_NOTICE}}", (
                "当前预览含未提交修改；source 链接查看 HEAD snapshot。"
                if identity["state"] == "dirty-worktree" else ""
            ))
            .replace("{{ARTICLE_BODY}}", body)
        )
        content = content.replace("{{BASE}}", spec.base)
        page_title = f"{title_suffix} — Signalbox"
        out_path = OUT_DIR / spec.out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            render_shell(content, spec.base, article.lang, page_title), encoding="utf-8"
        )

    manifest = build_manifest(articles, identity)
    manifest["identity_note"] = (
        "HEAD is the checkout commit; state=dirty-worktree means the worktree has "
        "changes and the commit hash does not describe the rendered bytes."
    )
    manifest["scenarios"] = [
        {"id": item["id"], "passed": item["passed"], "kind": item["kind"]}
        for item in scenarios
    ]
    (OUT_DIR / "build-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    try:
        where = OUT_DIR.relative_to(ROOT)
    except ValueError:
        where = OUT_DIR
    print(
        f"signalbox site build: {len(specs)} reading pages, 1 home, "
        f"{len(scenarios)} synthetic scenario receipts -> {where}"
    )
    return 0


def serve(port: int) -> int:
    """Serve the built site on loopback only. No deployment, no remote bind."""
    import functools
    import http.server
    import socketserver

    if not (OUT_DIR / "index.html").is_file():
        build()
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(OUT_DIR)
    )

    class Server(socketserver.TCPServer):
        allow_reuse_address = True

    # Loopback only: bind the hostname that resolves to the local interface.
    host = "localhost"
    with Server((host, port), handler) as httpd:
        print(f"signalbox site preview: http://{host}:{port}/ (loopback only, Ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nsignalbox site preview: stopped")
    return 0


def check() -> int:
    """Rebuild into a scratch directory and confirm it matches ``build/site``.

    Determinism matters because the whole tree is generated from canonical
    Markdown at build time; a stable rebuild means no hidden state and no
    hand-edited output. Hosted CI separately asserts the worktree is unchanged.
    """
    global OUT_DIR
    import tempfile

    canonical = OUT_DIR
    build()  # produce the canonical build/site first
    with tempfile.TemporaryDirectory() as tmp:
        OUT_DIR = Path(tmp) / "site"
        build()
        scratch = OUT_DIR
        problems: list[str] = []
        canonical_files = {
            p.relative_to(canonical) for p in canonical.rglob("*") if p.is_file()
        }
        scratch_files = {
            p.relative_to(scratch) for p in scratch.rglob("*") if p.is_file()
        }
        for missing in sorted(scratch_files - canonical_files):
            problems.append(f"build/site is missing generated file {missing}")
        for extra in sorted(canonical_files - scratch_files):
            problems.append(f"build/site has unexpected file {extra}")
        for rel in sorted(canonical_files & scratch_files):
            if (canonical / rel).read_bytes() != (scratch / rel).read_bytes():
                problems.append(f"build/site differs from a fresh build: {rel}")
    OUT_DIR = canonical

    if problems:
        print("signalbox site check: FAIL", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print("signalbox site check: PASS (build output is deterministic)")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="rebuild and verify deterministic output")
    parser.add_argument("--serve", action="store_true", help="serve build/site on loopback only")
    parser.add_argument("--port", type=int, default=8765, help="loopback preview port (default 8765)")
    args = parser.parse_args(argv)
    if args.serve:
        return serve(args.port)
    if args.check:
        return check()
    return build()


if __name__ == "__main__":
    raise SystemExit(main())
