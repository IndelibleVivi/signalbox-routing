"""Behavior-focused tests for the generated Signalbox reading station.

These tests build the site once into a temporary directory and assert that
generated pages come from canonical Markdown, that internal links/anchors and
language counterparts resolve, that replay receipts match the canonical
implementation, and that the source/build boundary holds. They deliberately do
not mirror every CSS rule.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import build_site
from scripts.build_site import (
    POSTCARDS_SCHEMA,
    POSTCARDS_SOURCE,
    REFERENCE_DOCS,
    SITE_README,
    SUPPLIED_ASSETS,
    load_postcards,
    load_pairs,
)
from scripts.repository_paths import RepositoryPathError

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'href="([^"]+)"')


class SiteBuildMixin:
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._orig_out = build_site.OUT_DIR
        build_site.OUT_DIR = Path(cls._tmp.name) / "site"
        build_site.build()
        cls.out = build_site.OUT_DIR
        cls.articles = build_site.build_articles()

    @classmethod
    def tearDownClass(cls):
        build_site.OUT_DIR = cls._orig_out
        cls._tmp.cleanup()

    def read(self, rel: str) -> str:
        return (self.out / rel).read_text(encoding="utf-8")

class BuildContentTests(SiteBuildMixin, unittest.TestCase):
    def test_every_registered_human_pair_and_reference_renders_a_page(self):
        pairs = load_pairs()
        self.assertEqual(len(pairs), 10)
        for _doc_id, zh, en in pairs:
            for source in (zh, en):
                self.assertTrue(
                    (self.out / (source[:-3] + ".html")).is_file(),
                    f"missing page for {source}",
                )
        for _doc_id, source, _title in REFERENCE_DOCS:
            self.assertTrue(
                (self.out / (source[:-3] + ".html")).is_file(),
                f"missing page for {source}",
            )
        self.assertTrue((self.out / (SITE_README[:-3] + ".html")).is_file())

    def test_page_set_uses_the_registered_pair_contract(self):
        pair = load_pairs()[1]
        registered = [("signalbox.test-registered-pair", pair[1], pair[2])]
        with mock.patch.object(build_site, "load_pairs", return_value=registered):
            articles = build_site.build_articles()
        for source in pair[1:]:
            self.assertEqual(articles[source].doc_id, "signalbox.test-registered-pair")

    def test_pages_render_live_canonical_markdown_not_stale_copy(self):
        source = "docs/human/40-tailnet-vps-private-ingress.zh-CN.md"
        text = (ROOT / source).read_text(encoding="utf-8")
        heading = next(line[2:].strip() for line in text.splitlines() if line.startswith("# "))
        page = self.read("docs/human/40-tailnet-vps-private-ingress.zh-CN.html")
        self.assertIn(heading.split()[0], page)
        # The explicit anchor that precedes the source heading is honored, and
        # the article body is the freshly rendered source, not the kit copy.
        self.assertIn('id="canonical-origin"', page)
        self.assertIn(
            "由 <span class=\"sx-mono\">" + source + "</span> 生成",
            page,
        )

    def test_top_heading_appears_once_without_a_duplicate_template_title(self):
        page = self.read("docs/human/40-tailnet-vps-private-ingress.zh-CN.html")
        self.assertEqual(page.count("<h1"), 1)

    def test_front_matter_is_stripped(self):
        page = self.read("docs/human/00-start-here.zh-CN.html")
        self.assertNotIn("doc_id:", page)
        self.assertNotIn("contract_revision:", page)

    def test_table_and_fence_structures_survive(self):
        table_page = self.read("docs/human/30-routing-dns-and-fail-closed.zh-CN.html")
        self.assertIn("sx-table-scroll", table_page)
        self.assertIn("<table>", table_page)
        fence_page = self.read("docs/human/00-start-here.zh-CN.html")
        self.assertIn("<pre><code", fence_page)

    def test_mermaid_source_is_preserved_as_readable_fallback(self):
        page = self.read("docs/human/10-architecture.zh-CN.html")
        self.assertIn("sbx-mermaid-source", page)
        self.assertIn("flowchart", page)

    def test_code_copy_is_progressive_and_mermaid_source_stays_untouched(self):
        js = (ROOT / "site/assets/site.js").read_text(encoding="utf-8")
        self.assertIn('root.querySelectorAll(".sx-content pre")', js)
        self.assertIn('code.classList.contains("sbx-mermaid-source")', js)
        self.assertIn("navigator.clipboard.writeText(code.textContent)", js)
        self.assertIn('const language = (languageClass ? languageClass.slice("language-".length) : "code")', js)
        css = (ROOT / "site/assets/site.css").read_text(encoding="utf-8")
        self.assertIn(".sx-content .sx-copy-button { min-height: 44px;", css)
        self.assertIn(".sx-content .sx-copy-button:focus-visible", css)
        page = self.read("docs/agent/workflow.html")
        self.assertNotIn("sx-copy-button", page)
        self.assertIn("<pre><code", page)


class HeadingIdTests(SiteBuildMixin, unittest.TestCase):
    def test_no_page_has_a_duplicate_id(self):
        offenders = {}
        for page in self.out.rglob("*.html"):
            ids = re.findall(r'id="([^"]+)"', page.read_text(encoding="utf-8"))
            dups = [i for i, count in Counter(ids).items() if count > 1]
            if dups:
                offenders[str(page.relative_to(self.out))] = dups
        self.assertEqual(offenders, {}, f"duplicate ids: {offenders}")

    def test_explicit_anchor_moves_to_the_owning_heading(self):
        page = self.read("docs/human/40-tailnet-vps-private-ingress.zh-CN.html")
        # The standalone anchor node is gone; the id lives on the heading.
        self.assertNotIn('<p><a id="canonical-origin"></a></p>', page)
        self.assertEqual(page.count('id="canonical-origin"'), 1)

    def test_repeated_automatic_headings_get_unique_ids(self):
        md = build_site.make_renderer()
        _html, headings = build_site.render_markdown(
            "# Same\n\n## Repeat\n\n## Repeat\n\ntext\n", md
        )
        anchors = [anchor for _tag, _text, anchor in headings]
        self.assertEqual(len(anchors), len(set(anchors)), anchors)
        self.assertIn("repeat", anchors)
        self.assertIn("repeat-1", anchors)


class LinkResolutionTests(SiteBuildMixin, unittest.TestCase):
    def test_all_internal_links_and_same_page_anchors_resolve(self):
        root = self.out.resolve()
        missing = []
        for page in root.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            for href in LINK.findall(text):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                if href.startswith("#"):
                    anchor = href[1:]
                    if anchor and f'id="{anchor}"' not in text:
                        missing.append(f"{page.relative_to(root)} -> same-page #{anchor}")
                    continue
                target, _, anchor = href.partition("#")
                resolved = (page.parent / target).resolve()
                if not resolved.exists():
                    missing.append(f"{page.relative_to(root)} -> {href}")
                    continue
                if anchor and f'id="{anchor}"' not in resolved.read_text(encoding="utf-8"):
                    missing.append(f"{page.relative_to(root)} -> missing #{anchor}")
        self.assertEqual(missing, [], f"broken links/anchors: {missing[:10]}")

    def test_station_guide_link_resolves_to_a_generated_page(self):
        # The root README's station-guide link must not become a stale snapshot.
        for page in ("README.zh-CN.html", "README.html"):
            self.assertIn("site/README.html", LINK.findall(self.read(page)))

    def test_containment_contract_rejects_escaping_links(self):
        spec = build_site.PageSpec(
            source="docs/human/40-tailnet-vps-private-ingress.zh-CN.md",
            out_rel="x.html", lang="zh-CN", base="../../", doc_id="d", is_human=True,
        )
        generated = set(build_site.build_articles())
        for bad in ("../../../etc/passwd", "/etc/passwd", "C:\\x", "foo\\bar.md",
                    "../../../../outside.md"):
            with self.assertRaises(RepositoryPathError, msg=bad):
                build_site.rewrite_links(
                    f'<a href="{bad}">x</a>', spec, generated, "https://x/y"
                )

    def test_contained_non_page_target_becomes_exact_source_link(self):
        spec = build_site.PageSpec(
            source="docs/agent/README.md", out_rel="docs/agent/README.html",
            lang="en", base="../../", doc_id="d", is_human=False,
        )
        generated = set(build_site.build_articles())
        identity = build_site.source_identity()
        out = build_site.rewrite_links(
            '<a href="../../contracts/catalog.json">c</a>', spec, generated,
            identity["source_root"],
        )
        self.assertIn(f'{identity["source_root"]}/contracts/catalog.json', out)

    def test_contracts_schemas_scripts_link_to_exact_github_source(self):
        hrefs = LINK.findall(self.read("docs/agent/README.html"))
        identity = build_site.source_identity()
        self.assertTrue(
            any("contracts/catalog.json" in h and identity["source_root"] in h for h in hrefs),
            "expected an exact public GitHub link for a contract",
        )

    def test_no_absolute_machine_paths_in_output(self):
        for page in self.out.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("Volumes/", text, page.name)
            self.assertNotIn("/Users/", text, page.name)
            self.assertNotIn("file://", text, page.name)

    def test_language_counterparts_link_both_ways(self):
        case = "docs/human/10-architecture"
        self.assertIn(case + ".en.html", self.read(case + ".zh-CN.html"))
        self.assertIn(case + ".zh-CN.html", self.read(case + ".en.html"))


class ScenarioReceiptTests(SiteBuildMixin, unittest.TestCase):
    def _scenario_data(self):
        home = self.read("index.html")
        match = re.search(
            r'<script type="application/json" data-scenario-data>(.*?)</script>',
            home,
            re.S,
        )
        self.assertIsNotNone(match)
        return json.loads(match.group(1))

    def test_receipts_match_canonical_replay_and_expected_values(self):
        from scripts.replay import replay_case

        cases = json.loads((ROOT / "examples/scenarios/cases.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in self._scenario_data()}
        self.assertEqual(len(by_id), len(cases))
        for case in cases:
            receipt = by_id[case["id"]]
            expected_match = all(
                receipt["actual"].get(key) == value
                for key, value in case["expected"].items()
            )
            self.assertTrue(receipt["passed"], case["id"])
            self.assertEqual(receipt["passed"], expected_match)
            self.assertEqual(receipt["actual"], replay_case(case))

    def test_workbench_distinguishes_match_from_verdict(self):
        js = (ROOT / "site/assets/site.js").read_text(encoding="utf-8")
        self.assertIn("expected judgment matched", js)
        self.assertIn("不是 live health", self.read("index.html"))
        stale = next(
            item for item in self._scenario_data()
            if item["id"] == "new-report-old-observations"
        )
        self.assertEqual(stale["actual"]["effective_outcome"], "unknown")
        self.assertTrue(stale["passed"])

    def test_maxwell_quote_is_not_duplicated_in_caption(self):
        markup = (ROOT / "site/home.html").read_text(encoding="utf-8")
        script = (ROOT / "site/assets/site.js").read_text(encoding="utf-8")
        quote = "And all its circuits close in thee."
        # The quote lives once in the JS note cycle and nowhere in the static
        # markup; the visible source line carries only author/source.
        self.assertEqual(script.count(quote), 1)
        self.assertEqual(markup.count(quote), 0)
        self.assertIn("J. C. Maxwell", markup)

    def test_font_import_and_fallbacks_present(self):
        css = (ROOT / "site/assets/site.css").read_text(encoding="utf-8")
        self.assertIn("fonts.googleapis.com", css)
        self.assertIn("Special+Elite", css)
        self.assertIn("IBM+Plex+Mono", css)


class PostcardBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._orig_out = build_site.OUT_DIR
        build_site.OUT_DIR = Path(cls._tmp.name) / "site"
        build_site.build()
        cls.out = build_site.OUT_DIR
        cls.postcards = load_postcards()
        cls.home = (cls.out / "index.html").read_text(encoding="utf-8")
        match = re.search(
            r'<script type="application/json" data-postcard-data>(.*?)</script>',
            cls.home,
            re.S,
        )
        assert match, "postcard scene data is missing"
        cls.scene = json.loads(match.group(1))

    @classmethod
    def tearDownClass(cls):
        build_site.OUT_DIR = cls._orig_out
        cls._tmp.cleanup()

    def read(self, rel: str) -> str:
        return (self.out / rel).read_text(encoding="utf-8")

    def test_authored_postcards_are_in_catalog_and_scene_is_not_drifted(self):
        source = json.loads((ROOT / POSTCARDS_SOURCE).read_text(encoding="utf-8"))
        self.assertEqual(self.scene["targets"], source["targets"])
        self.assertEqual(self.scene["conditions"], source["conditions"])
        self.assertEqual(self.scene["journeys"], source["journeys"])
        catalog = json.loads((ROOT / "contracts/catalog.json").read_text(encoding="utf-8"))
        entry = next(
            item for item in catalog["entries"]
            if item["schema_id"] == "signalbox.postcard-journeys/v1"
        )
        self.assertEqual(entry["owner"], POSTCARDS_SOURCE)
        self.assertEqual(entry["schema_path"], POSTCARDS_SCHEMA)

    def test_only_applicable_combinations_and_permission_truth_are_offered(self):
        source = load_postcards()
        conditions = {item["id"]: item for item in source["conditions"]}
        journeys = {
            (item["target_ref"], item["condition_ref"]): item
            for item in source["journeys"]
        }
        self.assertEqual(len(journeys), 7)
        self.assertNotIn(("tailnet-host", "missing-return-route"), journeys)
        self.assertIn(("nas-source-preserving", "missing-return-route"), journeys)
        for target, condition in journeys:
            self.assertIn(target, conditions[condition]["targets"])
        for (target, condition), journey in journeys.items():
            if condition == "access-denied":
                self.assertEqual(journey["outcome"], "stopped")
                self.assertNotIn("RLY", [step["stamp"] for step in journey["steps"]])
            if condition == "missing-return-route":
                self.assertEqual(target, "nas-source-preserving")
                self.assertIn("source-preserving", " ".join(
                    step["detail"] for step in journey["steps"]
                ))
                self.assertEqual(journey["outcome"], "stopped")
            if condition == "direct-udp-blocked":
                self.assertIn("RLY", [step["stamp"] for step in journey["steps"]])
                self.assertNotIn("direct", journey["result"].lower())
                self.assertIn("DIRECT", journey["caveat"])

    def test_ambiguous_or_unselectable_records_fail_the_build(self):
        source = load_postcards()
        mutations = [
            ("duplicate target", lambda data: data["targets"].append(data["targets"][0])),
            ("unknown target", lambda data: data["conditions"][0]["targets"].append("unknown")),
            ("selection key", lambda data: data["journeys"][0].update(id="wrong-key")),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                data = json.loads(json.dumps(source))
                mutate(data)
                fixture = Path(directory) / "journeys.json"
                fixture.write_text(json.dumps(data), encoding="utf-8")
                with mock.patch.object(build_site, "POSTCARDS_SOURCE", str(fixture)):
                    with self.assertRaisesRegex(ValueError, label):
                        load_postcards()

    def test_article_links_are_generated_anchors_and_old_selected_guide_survives(self):
        self.assertIn("docs/human/60-travel-router.zh-CN.html", self.home)
        self.assertIn("docs/human/40-tailnet-vps-private-ingress.zh-CN.html", self.home)
        self.assertRegex(self.home, r'<a href="index\.html#sx-postcards">本期</a>')
        for journey in self.scene["journeys"]:
            article = journey["article"]
            target = article["source"][:-3] + ".html"
            page = self.read(target)
            self.assertIn(f'id="{article["anchor"]}"', page)
            self.assertIn(f"{target}#{article['anchor']}", self.home)

    def test_articles_keep_practical_paths_limits_and_attributed_sources(self):
        expectations = {
            "60-travel-router": (
                "SNAT",
                "source-preserving",
                "return route",
                "https://tailscale.com/docs/features/subnet-routers/4via6-subnets",
                "https://github.com/IndelibleVivi/infra-field-guide/blob/main/docs/07-network-and-proxies.md",
            ),
            "70-peer-relay": (
                "1.86",
                "DERP",
                "Internet exit",
                "https://tailscale.com/docs/features/peer-relay",
                "https://github.com/IndelibleVivi/infra-field-guide/blob/main/docs/09-private-access.md",
            ),
            "80-mesh-and-openwrt": (
                "Traffic-and-DNS",
                "OpenWrt",
                "https://developers.cloudflare.com/mesh/concepts/",
                "https://raw.githubusercontent.com/openwrt/packages/master/net/tailscale/Makefile",
            ),
        }
        for stem, required in expectations.items():
            for language in ("zh-CN", "en"):
                source = (ROOT / f"docs/human/{stem}.{language}.md").read_text(
                    encoding="utf-8"
                )
                for text in required:
                    self.assertIn(text, source, f"{stem}.{language}: {text}")
                if stem == "80-mesh-and-openwrt":
                    native_support_clause = (
                        "没有把 OpenWrt 列为官方支持"
                        if language == "zh-CN" else "does not list OpenWrt"
                    )
                    self.assertIn(native_support_clause, source)
                self.assertIn("contract_revision: 6", source)
                self.assertIn("2026-10-22", source)
        for language in ("zh-CN", "en"):
            source = (ROOT / f"docs/human/80-mesh-and-openwrt.{language}.md").read_text(
                encoding="utf-8"
            )
            self.assertNotRegex(
                source,
                r'CONNECTOR -->\|inbound service path\| PUBLIC',
                "Tunnel arrows must distinguish the inbound service path from the outbound connector",
            )

    def test_fallback_has_every_authored_case_and_reset_controls(self):
        self.assertIn("直接阅读七封教学信", self.home)
        self.assertNotIn("<noscript>", self.home)
        self.assertIn('data-postcard-reset', self.home)
        self.assertIn('data-postcard-next', self.home)
        for journey in self.scene["journeys"]:
            self.assertEqual(
                self.home.count(f'data-postcard-case="{journey["id"]}"'),
                1,
                journey["id"],
            )
            self.assertIn(journey["result"], self.home)
        self.assertIn('data-postcard-enhanced', self.home)
        self.assertIn('aria-live="polite"', self.home)


POSTCARD_JS_HARNESS = r"""
const fs = require("fs");
const source = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const mk = (o = {}) => {
  const el = {
    _a: { ...o }, textContent: o.textContent ?? "", hidden: !!o.hidden, disabled: false,
    dataset: { ...(o.dataset || {}) }, className: "", innerHTML: "", href: "",
    classList: Object.assign([], { contains: () => false }), L: {},
    children: [], parentNode: null,
    setAttribute(k, v) { this._a[k] = String(v); },
    getAttribute(k) { return this._a[k] ?? null; },
    hasAttribute(k) { return k in this._a; },
    addEventListener(e, f) { (this.L[e] ||= []).push(f); },
    dispatch(e, x = {}) { (this.L[e] || []).forEach((f) => f(x)); },
    focus() { document.activeElement = el; }, insertAdjacentElement() {}, closest() { return null; },
    querySelector() { return null; }, querySelectorAll() { return []; },
  };
  el.append = (...nodes) => { el.children.push(...nodes); nodes.forEach((node) => { node.parentNode = el; }); };
  el.replaceWith = (replacement) => { replacement.parentNode = el.parentNode; el.parentNode = null; };
  return el;
};
const button = (selector, value, pressed = "false") => {
  const el = mk({ textContent: value });
  el.dataset[selector] = value;
  el._a["aria-pressed"] = pressed;
  return el;
};
const targetButtons = source.targets.map((item) => button("postcardTarget", item.id));
const conditionButtons = source.conditions.map((item) => button("postcardCondition", item.id));
const fallbackCases = source.journeys.map((item) => {
  const el = mk();
  el.dataset.target = item.target_ref;
  el.dataset.condition = item.condition_ref;
  return el;
});
const data = mk({ textContent: JSON.stringify(source) });
const enhanced = mk();
enhanced.querySelector = (s) => s === "[data-postcard-target]" ? targetButtons[0] : null;
const targetGroup = mk(), conditionGroup = mk(), nextButton = mk(), resetButton = mk();
const articleLink = mk(), stage = mk(), route = mk(), result = mk();
const targetLabel = mk(), conditionLabel = mk(), availability = mk();
const progress = mk(), seal = mk();
const section = mk();
section.querySelector = (s) => ({
  "[data-postcard-enhanced]": enhanced, "[data-postcard-targets]": targetGroup,
  "[data-postcard-conditions]": conditionGroup, "[data-postcard-next]": nextButton,
  "[data-postcard-reset]": resetButton, "[data-postcard-article]": articleLink,
  "[data-postcard-stage]": stage, "[data-postcard-route]": route,
  "[data-postcard-result]": result, "[data-postcard-target-label]": targetLabel,
  "[data-postcard-condition-label]": conditionLabel,
  "[data-postcard-availability]": availability,
  "[data-postcard-progress]": progress, "[data-postcard-seal]": seal,
}[s] || null);
section.querySelectorAll = (s) => ({
  "[data-postcard-target]": targetButtons,
  "[data-postcard-condition]": conditionButtons,
  "[data-postcard-case]": fallbackCases,
}[s] || []);
const root = mk();
root.querySelector = (s) => ({
  "[data-postcard-data]": data, "#sx-postcards": section,
}[s] || null);
root.querySelectorAll = () => [];
global.document = {
  getElementById: () => root, activeElement: null,
  createElement: () => mk(), createRange: () => ({ selectNodeContents() {} }),
};
global.window = {
  getSelection: () => null,
  matchMedia: () => ({ matches: false, addEventListener() {} }),
};
Object.defineProperty(globalThis, "navigator", { configurable: true, value: {} });
global.HTMLScriptElement = { prototype: {} };
eval(fs.readFileSync(process.argv[2], "utf8"));

const byId = (items, selector, id) => items.find((item) => item.dataset[selector] === id);
const pressed = (items, selector) => items.filter((item) =>
  item.getAttribute("aria-pressed") === "true"
).map((item) => item.dataset[selector]);
const missing = byId(conditionButtons, "postcardCondition", "missing-return-route");
const initialOk = enhanced.dataset.ready === "true"
  && section.dataset.ready === "true" && missing.disabled
  && stage.dataset.outcome === "ready" && /READY TO POST/.test(result.innerHTML)
  && /0 \/ 2/.test(progress.textContent) && !route.innerHTML.includes('aria-current="step"');
let allSteps = true, terminalTruth = true, replay = true, reset = true;
for (const journey of source.journeys) {
  byId(targetButtons, "postcardTarget", journey.target_ref).dispatch("click");
  byId(conditionButtons, "postcardCondition", journey.condition_ref).dispatch("click");
  allSteps &&= stage.dataset.outcome === "ready";
  for (let i = 0; i < journey.steps.length; i += 1) {
    nextButton.dispatch("click");
    allSteps &&= result.innerHTML.includes(journey.steps[i].label)
      && progress.textContent.endsWith((i + 1) + " / " + journey.steps.length)
      && (i === journey.steps.length - 1 || stage.dataset.outcome === "transit");
  }
  terminalTruth &&= stage.dataset.outcome === journey.outcome
    && result.innerHTML.includes(journey.result) && !nextButton.disabled
    && nextButton.textContent.includes(journey.outcome === "delivered" ? "信已送达" : "信暂存这里");
  nextButton.dispatch("click");
  replay &&= result.innerHTML.includes(journey.steps[0].label)
    && stage.dataset.outcome === "transit";
  resetButton.dispatch("click");
  reset &&= stage.dataset.outcome === "ready" && /READY TO POST/.test(result.innerHTML)
    && document.activeElement === nextButton;
}
byId(targetButtons, "postcardTarget", "nas-source-preserving").dispatch("click");
missing.dispatch("click");
byId(targetButtons, "postcardTarget", "tailnet-host").dispatch("click");
const unavailableResets = missing.disabled
  && pressed(conditionButtons, "postcardCondition")[0] === "normal"
  && stage.dataset.outcome === "ready";
console.log(JSON.stringify({
  initialOk, allSteps, terminalTruth, replay, reset, unavailableResets,
  allFallbacksReadable: fallbackCases.every((item) => !item.hidden),
}));
"""

class IdentityTests(SiteBuildMixin, unittest.TestCase):
    def test_manifest_uses_actual_head_and_labels_dirty_state(self):
        identity = build_site.source_identity()
        manifest = json.loads(self.read("build-manifest.json"))
        self.assertEqual(manifest["source_identity"]["commit"], identity["commit"])
        self.assertIn(identity["state"], {"exact-head", "dirty-worktree"})
        self.assertIn(identity["commit"], manifest["source_identity"]["source_root"])

class AssetBoundaryTests(SiteBuildMixin, unittest.TestCase):
    def test_supplied_assets_copied_byte_for_byte(self):
        for name, digest in SUPPLIED_ASSETS.items():
            source = (ROOT / "site/assets" / name).read_bytes()
            built = (self.out / "assets" / name).read_bytes()
            self.assertEqual(built, source, name)
            self.assertEqual(hashlib.sha256(built).hexdigest(), digest, name)

    def test_build_output_is_ignored_and_source_is_not_build(self):
        self.assertIn("build/", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "site/shell.html").is_file())
        self.assertFalse((ROOT / "site/index.html").exists())
        for source in self.articles:
            self.assertFalse(
                (ROOT / source).with_suffix(".html").exists(),
                f"generated HTML must not sit next to source {source}",
            )

    def test_only_expected_media_in_authored_asset_dir(self):
        media = {p.name for p in (ROOT / "site/assets").iterdir()}
        self.assertEqual(
            media,
            {"receiving-room.webp", "tape-s-mark.webp", "courier-note.webp",
             "site.css", "site.js"},
        )


JS_HARNESS = r"""
const fs = require("fs");
const mk = (o = {}) => {
  const el = {
    _a: { ...o }, textContent: o.textContent ?? "", hidden: !!o.hidden, dataset: {},
    classList: Object.assign([], { contains: () => false }), L: {},
    children: [], parentNode: null,
    setAttribute(k, v) { this._a[k] = String(v); },
    getAttribute(k) { return this._a[k] ?? null; },
    hasAttribute(k) { return k in this._a; },
    addEventListener(e, f) { (this.L[e] ||= []).push(f); },
    dispatch(e, x = {}) { (this.L[e] || []).forEach((f) => f(x)); },
    focus() {}, insertAdjacentElement() {},
    closest() { return { insertAdjacentElement() {} }; },
    querySelector() { return null; }, querySelectorAll() { return []; },
  };
  el.append = (...nodes) => {
    el.children.push(...nodes);
    nodes.forEach((node) => { node.parentNode = el; });
  };
  el.replaceWith = (replacement) => {
    for (let ancestor = el.parentNode; ancestor; ancestor = ancestor.parentNode) {
      if (ancestor === replacement) {
        throw new TypeError(
          "Failed to execute 'replaceWith' on 'Element': " +
          "The new child element contains the parent."
        );
      }
    }
    if (el.parentNode) {
      const index = el.parentNode.children.indexOf(el);
      if (index >= 0) el.parentNode.children.splice(index, 1, replacement);
    }
    replacement.parentNode = el.parentNode;
    el.parentNode = null;
  };
  return el;
};
const keyOut = mk(), decoded = mk(), secret = mk({ hidden: true });
const keyUp = mk(), keyDown = mk(), closeBtn = mk();
const dialog = mk();
dialog.querySelector = (s) => ({
  "[data-key-value]": keyOut, "[data-decoded]": decoded,
  "[data-secret-note]": secret, "[data-key-up]": keyUp, "[data-key-down]": keyDown,
}[s] || null);
const catNote = mk(), catSrc = mk({ hidden: true }), catBtn = mk();
const callsign = mk({ textContent: "... .. --. -. .- .-.. -... --- -..-" });
const csBtn = mk({ textContent: "译出呼号" });
const data = mk({ textContent: JSON.stringify([
  { id: "x", label: "X", blurb: "", passed: true, expected: { a: 1 }, actual: { a: 1 } },
]) });
const receipt = mk();
const copiedCode = mk({ textContent: "make verify PYTHON=.venv/bin/python\n中文 “quoted” path\\n" });
const copiedPre = mk();
copiedPre.querySelector = () => copiedCode;
const selectedRanges = [];
const selection = {
  removeAllRanges() { selectedRanges.length = 0; },
  addRange(range) { selectedRanges.push(range); },
};
let clipboardText = null;
let clipboardFails = false;
let clipboardGate = false;
let clipboardCalls = 0;
let clipboardResolvers = [];
const root = mk();
root.querySelector = (s) => ({
  "[data-scenario-data]": data, "[data-receipt]": receipt, "dialog.sx-dispatch": dialog,
  "[data-cat-note]": catNote, "[data-cat-source]": catSrc,
  "[data-callsign]": callsign, "[data-callsign-button]": csBtn,
  "[data-close-dispatch]": closeBtn, "[data-cat-button]": catBtn,
}[s] || null);
root.querySelectorAll = (s) => ({
  "[data-scenario-button]": [mk()], ".sx-content pre": [copiedPre],
  "code.sbx-mermaid-source": [],
}[s] || []);
global.document = { getElementById: () => root, activeElement: null };
const created = [];
global.document.createElement = (tag) => {
  const node = mk();
  node.tagName = tag;
  created.push(node);
  return node;
};
global.document.createRange = () => ({ selectNodeContents(node) { this.node = node; } });
global.window = { getSelection: () => selection, matchMedia: () => ({ matches: false, addEventListener() {} }) };
Object.defineProperty(globalThis, "navigator", { configurable: true, value: {
  clipboard: { writeText: async (text) => {
    clipboardCalls += 1;
    if (clipboardFails) throw new Error("blocked");
    clipboardText = text;
    if (clipboardGate) await new Promise((resolve) => { clipboardResolvers.push(resolve); });
  } },
} });
global.HTMLScriptElement = { prototype: { noModule: true } };
eval(fs.readFileSync(process.argv[2], "utf8"));
keyUp.dispatch("click"); keyUp.dispatch("click"); keyUp.dispatch("click");
const solvedOk = keyOut.textContent === "03" && decoded.textContent === "STILL GROWING"
  && secret.hidden === false && dialog.dataset.solved === "true";
for (let i = 0; i < 23; i++) keyUp.dispatch("click");
const wrapOk = keyOut.textContent === "00" && decoded.textContent === "VWLOO JURZLQJ";
keyDown.dispatch("click");
const downOk = keyOut.textContent === "25";
csBtn.dispatch("click");
const morseOk = callsign.textContent === "S I G N A L B O X" && csBtn.textContent === "折回电码";
csBtn.dispatch("click");
const morseBack = callsign.textContent.startsWith("... ..");
catBtn.dispatch("click"); catBtn.dispatch("click"); catBtn.dispatch("click");
const catOk = catNote.textContent === "And all its circuits close in thee." && catSrc.hidden === false;
const receiptOk = /EXPECTED/.test(receipt.innerHTML);
const copyButton = created.find((node) => node.className === "sx-copy-button");
const copyHint = created.find((node) => node.className === "sx-copy-hint");
const copyFigure = created.find((node) => node.className === "sx-code-block");
const copySetupOk = copiedPre.parentNode === copyFigure && copyFigure.children[1] === copiedPre
  && copyButton.getAttribute("aria-label") === "复制代码"
  && copyHint.hidden === true;
// The adapter has no browser event return value; let the clipboard promise
// settle before inspecting the button state.
copyButton.dispatch("click");
setImmediate(async () => {
  const copySuccessOk = clipboardText === copiedCode.textContent
    && copyButton.textContent === "已复制" && copyButton.dataset.state === "success";
  clipboardFails = true;
  await copyButton.dispatch("click");
  const copyFailureOk = copyButton.textContent === "重试复制"
    && copyButton.dataset.state === "failure" && copyHint.hidden === false
    && selectedRanges[0].node === copiedCode;
  // Rapid activation while one clipboard write is unresolved is ignored.
  clipboardFails = false;
  clipboardGate = true;
  clipboardResolvers = [];
  const callsBeforeRapid = clipboardCalls;
  copyButton.dispatch("click");
  copyButton.dispatch("click");
  const rapidCallsOnce = clipboardCalls === callsBeforeRapid + 1;
  clipboardResolvers.shift()();
  clipboardGate = false;
  await new Promise((resolve) => setTimeout(resolve, 0));
  const copyPendingOk = copyButton.textContent === "已复制"
    && copyButton.dataset.state === "success";
  console.log(JSON.stringify({
    solvedOk, wrapOk, downOk, morseOk, morseBack, catOk, receiptOk,
    copySetupOk, copySuccessOk, copyFailureOk, rapidCallsOnce, copyPendingOk,
  }));
});
"""


class InteractionLogicTests(unittest.TestCase):
    """Exercise the shipped site.js logic in Node when it is available.

    This verifies cipher wrap, the solved note, the Morse toggle, the cat quote
    cycle, and the scenario receipt render. It uses a minimal DOM adapter and
    does not execute browser layout.
    """

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_station_interactions(self):
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as handle:
            handle.write(JS_HARNESS)
            harness = handle.name
        try:
            result = subprocess.run(
                ["node", harness, str(ROOT / "site/assets/site.js")],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
        finally:
            Path(harness).unlink(missing_ok=True)
        outcome = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(all(outcome.values()), outcome)

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_postcard_selection_progression_stop_and_reset(self):
        source = json.dumps(load_postcards(), ensure_ascii=False)
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as handle:
            handle.write(POSTCARD_JS_HARNESS)
            harness = handle.name
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write(source)
            scene = handle.name
        try:
            result = subprocess.run(
                [
                    "node", harness, str(ROOT / "site/assets/site.js"), scene,
                ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            if result.returncode:
                self.fail(f"postcard harness failed:\n{result.stderr}")
        finally:
            Path(harness).unlink(missing_ok=True)
            Path(scene).unlink(missing_ok=True)
        outcome = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(all(outcome.values()), outcome)


if __name__ == "__main__":
    unittest.main()
