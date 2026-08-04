"""Small, dependency-free reference implementation for research-agent release gates.

This module deliberately does not call a model, execute experiments, fetch papers, or publish
anything. It makes two necessary boundaries explicit: classify untrusted incoming sources before
they influence a workflow, and gate candidate outputs before any release action is considered.
"""
from __future__ import annotations

import html
import re
from typing import Any


ALLOWED_TOPICS = {"agent-safety", "faithfulness", "misalignment", "interpretability"}
RELEVANT_TERMS = {
    "agent",
    "alignment",
    "audit",
    "deception",
    "faithfulness",
    "injection",
    "interpretability",
    "misalignment",
    "safety",
    "sycophancy",
    "tool-using",
}
LOCAL_HOME_PREFIX = "/" + "Users/"
FILE_URI_PREFIX = "file:" + "//"
FORBIDDEN_OUTPUT = re.compile(
    re.escape(LOCAL_HOME_PREFIX)
    + "|"
    + re.escape(FILE_URI_PREFIX)
    + r"|~/.claude|@[\w.-]+\.[a-z]{2,}|"
    r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}",
    re.IGNORECASE,
)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _is_primary_public_source(record: dict[str, Any]) -> bool:
    url = _safe_text(record.get("url"))
    return url.startswith(("https://arxiv.org/abs/", "https://openreview.net/"))


def _is_relevant(record: dict[str, Any]) -> bool:
    topic = _safe_text(record.get("topic")).lower()
    title = _safe_text(record.get("title")).lower()
    return topic in ALLOWED_TOPICS and any(term in title for term in RELEVANT_TERMS)


def classify_sources(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Allow only relevant public primary sources; retain the reason for every quarantine."""
    eligible, quarantined = [], []
    for position, record in enumerate(records):
        normalized = {
            "id": _safe_text(record.get("id")) or f"source-{position + 1}",
            "topic": _safe_text(record.get("topic")).lower(),
            "title": _safe_text(record.get("title")),
            "url": _safe_text(record.get("url")),
        }
        if not _is_primary_public_source(normalized):
            normalized["reason"] = "source is not an approved public primary URL"
            quarantined.append(normalized)
        elif not _is_relevant(normalized):
            normalized["reason"] = "source is outside the configured research mission"
            quarantined.append(normalized)
        else:
            eligible.append(normalized)
    return {
        "verdict": "ALLOW" if eligible else "NO_RESEARCH_INPUT",
        "eligible_sources": eligible,
        "quarantined_sources": quarantined,
    }


def guard_public_output(candidate: dict[str, Any] | None) -> dict[str, Any]:
    """Apply release preconditions without performing a release action."""
    if candidate is None:
        return {
            "verdict": "NOT_APPLICABLE",
            "findings": [],
            "policy": "No candidate exists; no external publication action is permitted.",
        }
    findings = []
    if _safe_text(candidate.get("evaluation_verdict")).upper() != "PASS":
        findings.append("independent evaluation is not PASS")
    if _safe_text(candidate.get("critic_verdict")).upper() != "KEEP":
        findings.append("independent critic is not KEEP")
    if not _safe_text(candidate.get("reproduce_command")):
        findings.append("missing reproduce command")
    if not _safe_text(candidate.get("claim_boundary")):
        findings.append("missing claim boundary")
    if FORBIDDEN_OUTPUT.search(str(candidate)):
        findings.append("candidate contains a local path or personal identifier")
    return {
        "verdict": "PASS" if not findings else "BLOCK",
        "findings": findings,
        "policy": "This check never publishes, uploads, or submits a candidate.",
    }


def _display(value: Any) -> str:
    return html.escape(FORBIDDEN_OUTPUT.sub("[redacted]", _safe_text(value)))


def render_dashboard(classification: dict[str, Any], release: dict[str, Any]) -> str:
    """Render a standalone, privacy-redacted status page with no network dependencies."""
    eligible = classification.get("eligible_sources", [])
    quarantined = classification.get("quarantined_sources", [])
    findings = release.get("findings", [])
    rows = "".join(
        "<tr><td>Allowed</td><td>{}</td><td>{}</td></tr>".format(
            _display(item.get("title")), _display(item.get("url"))
        )
        for item in eligible
    ) or "<tr><td colspan=\"3\">No approved source.</td></tr>"
    blocked = "<br>".join(_display(item) for item in findings) or "No release findings."
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Research Agent Gate Kit</title><style>
:root{{--ink:#17212b;--muted:#5f6b76;--line:#d7dde3;--bg:#f7f9fb;--panel:#fff;--good:#107c41;--warn:#9b5d00}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif}}main{{max-width:1080px;margin:auto;padding:32px 24px 48px}}header{{border-bottom:1px solid var(--line);padding-bottom:18px}}h1{{margin:0;font-size:26px;letter-spacing:0}}p{{color:var(--muted)}}.metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin:24px 0;border:1px solid var(--line);border-radius:8px;background:var(--panel)}}.metric{{padding:15px;border-right:1px solid var(--line)}}.metric:last-child{{border:0}}.label{{display:block;color:var(--muted);font-size:12px}}.value{{display:block;font-size:21px;font-weight:700;margin-top:5px}}section{{border:1px solid var(--line);border-radius:8px;background:var(--panel);overflow:hidden}}h2{{font-size:16px;margin:0;padding:14px 16px;border-bottom:1px solid var(--line)}}table{{border-collapse:collapse;width:100%}}th,td{{padding:12px 16px;text-align:left;vertical-align:top;overflow-wrap:anywhere;border-bottom:1px solid var(--line)}}th{{font-size:12px;color:var(--muted)}}.note{{padding:14px 16px;color:var(--muted)}}@media(max-width:700px){{main{{padding:20px 14px}}.metrics{{grid-template-columns:repeat(2,minmax(0,1fr))}}.metric:nth-child(2){{border-right:0}}.metric{{border-bottom:1px solid var(--line)}}.metric:nth-last-child(-n+2){{border-bottom:0}}}}</style></head>
<body><main><header><h1>Research Agent Gate Kit</h1><p>Local-only provenance and release checks. No model call or publication action is performed.</p></header>
<div class="metrics"><div class="metric"><span class="label">Input verdict</span><span class="value">{_display(classification.get('verdict'))}</span></div><div class="metric"><span class="label">Approved sources</span><span class="value">{len(eligible)}</span></div><div class="metric"><span class="label">Quarantined</span><span class="value">{len(quarantined)}</span></div><div class="metric"><span class="label">Release verdict</span><span class="value">{_display(release.get('verdict'))}</span></div></div>
<section><h2>Approved Research Inputs</h2><table><thead><tr><th>Status</th><th>Source</th><th>Primary URL</th></tr></thead><tbody>{rows}</tbody></table></section>
<section style="margin-top:16px"><h2>Release Gate</h2><div class="note">{blocked}</div></section></main></body></html>"""
