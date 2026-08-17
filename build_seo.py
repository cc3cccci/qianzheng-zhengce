#!/usr/bin/env python3
"""Pre-render crawlable Chinese job HTML for Baidu / Bing / 360."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TODAY = "2026-08-14"
SITE = "https://h2-chaxun.pages.dev"
DESC = (
    "免费查阅美国劳工部公开的 H-2A 农业和 H-2B 非农季节工岗位，"
    "中文翻译职位、工资、开工日和雇主联系方式。非官方，不收费，不代办签证。"
)

CSS = """
    :root {
      --bg: #f6f3ee;
      --card: #fffdf8;
      --ink: #1f1b16;
      --muted: #5c564c;
      --line: #e4ddd2;
      --a: #1f5c45;
      --a2: #163d2e;
      --warn: #8a3b12;
      --warnbg: #f8e8d8;
      --h2a: #1f5c45;
      --h2b: #2c4a7c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font: 16px/1.6 "Source Han Sans SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }
    header, main, footer, .banner, .crumbs, .subnav {
      max-width: 42rem;
      margin-left: auto;
      margin-right: auto;
    }
    .topnav { border-bottom: 1px solid var(--line); background: var(--bg); }
    .topnav-inner {
      max-width: 42rem; margin: 0 auto; padding: 4px 20px;
      display: flex; flex-wrap: wrap; align-items: center; gap: 4px 18px;
    }
    .nav-brand {
      color: var(--a); font-weight: 600; letter-spacing: .12em; font-size: .78rem;
      text-decoration: none; min-height: 44px; display: inline-flex; align-items: center;
    }
    .nav-links { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 6px; }
    .nav-links a {
      min-height: 44px; display: inline-flex; align-items: center; padding: 0 10px;
      border-radius: 8px; text-decoration: none; color: var(--a); font-size: .95rem;
    }
    header { padding: 28px 20px 8px; }
    .crumbs { padding: 0 20px; color: var(--muted); font-size: .9rem; }
    .crumbs a { text-decoration: none; }
    .subnav { padding: 0 20px 8px; font-size: .95rem; }
    .subnav a { margin-right: 14px; }
    h1 { font-size: 1.6rem; margin: 0 0 6px; letter-spacing: .02em; }
    .sub { color: var(--muted); margin: 0; }
    .banner {
      margin-top: 16px;
      margin-bottom: 16px;
      padding: 12px 16px;
      background: var(--warnbg);
      color: var(--warn);
      border-radius: 10px;
    }
    main { padding: 8px 20px 64px; }
    h2 { font-size: 1.15rem; margin: 28px 0 10px; }
    .cards { display: grid; gap: 10px; }
    @media (min-width: 720px) { .cards.three { grid-template-columns: 1fr 1fr 1fr; } }
    .note, .job {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px 16px;
    }
    .note strong { display: block; margin-bottom: 4px; }
    .job { margin-bottom: 10px; }
    .job h3 { margin: 0 0 4px; font-size: 1.05rem; }
    .meta { color: var(--muted); font-size: .92rem; }
    .tag {
      display: inline-block;
      font-size: .75rem;
      padding: 1px 7px;
      border-radius: 999px;
      color: #fff;
      vertical-align: middle;
      margin-right: 6px;
    }
    .tag.a { background: var(--h2a); }
    .tag.b { background: var(--h2b); }
    a { color: var(--a); }
    a:hover { color: var(--a2); }
    .duties { margin: 8px 0 0; color: var(--muted); font-size: .92rem; }
    .contact { margin-top: 8px; font-size: .92rem; }
    footer {
      padding: 0 20px 40px;
      color: var(--muted);
      font-size: .88rem;
    }
    .count { color: var(--muted); margin: 0 0 12px; }
    dl { margin: 0; }
    dt {
      font-weight: 600;
      margin-top: 14px;
    }
    dd {
      margin: 2px 0 0;
      color: var(--muted);
      font-size: .95rem;
    }
    @media (min-width: 900px) {
      header, main, footer, .banner, .crumbs, .subnav, .topnav-inner {
        max-width: 70rem;
      }
    }
"""

CARDS = """
    <div class="cards three">
      <div class="note"><strong>H-2A 农业</strong>没有人数上限。农场、农机、畜牧。雇主通常要提供免费住房。</div>
      <div class="note"><strong>H-2B 非农</strong>每年法定 66,000 个名额。厨师、酒店、园林、建筑。住房多半要自己付钱。</div>
      <div class="note"><strong>开工日 / 收工日</strong>就是这份合同的起止。错过开工日不会自动改期，最多是雇主还缺人时把你补进去，干到收工日。</div>
    </div>
"""

BANNER = (
    "任何人向你收“办签费、名额费、介绍费”，都是违法的。"
    "H-2 必须由美国雇主申请，你不能自己递件。岗位原文以劳工部网站为准。"
)

NAV = (
    '<nav class="topnav" aria-label="站点导航">'
    '<div class="topnav-inner">'
    '<a class="nav-brand" href="/">签证政策</a>'
    '<div class="nav-links">'
    '<a href="/#guojia">国家</a>'
    '<a href="/gengxin">政策更新</a>'
    "</div></div></nav>"
)

CRUMBS = (
    '<p class="crumbs">'
    '<a href="/">签证政策</a> / '
    '<a href="/meiguo">美国</a> / '
    "%s</p>"
)

SUBNAV = (
    '<p class="subnav">'
    '<a href="/gangwei">全部岗位</a>'
    '<a href="/h2a">H-2A 农业</a>'
    '<a href="/h2b">H-2B 非农</a>'
    "</p>"
)

FOOTER = """
  <footer>
    <p>本站使用美国劳工部 SeasonalJobs 公开数据，但未经劳工部认可或认证。请到原文页联系雇主：<a href="https://seasonaljobs.dol.gov/">seasonaljobs.dol.gov</a>。</p>
    <p>本站不代招、不收费、不保证签证。中国籍申请人能否获签，由使领馆决定。</p>
  </footer>
"""


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def is_active(job: dict) -> bool:
    end = (job.get("end") or "").strip()
    return (not end) or end >= TODAY


def loc_of(job: dict) -> str:
    return ", ".join(p for p in (job.get("city") or "", job.get("state") or "") if p)


def excerpt(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def job_article(job: dict, with_duties: bool = True) -> str:
    tag = "a" if job.get("type") == "H-2A" else "b"
    loc = loc_of(job)
    parts_top = [job.get("title_en") or "", job.get("employer") or "", loc]
    top = " · ".join(p for p in parts_top if p)
    start = job.get("start") or "未标明"
    end = job.get("end") or "未标明"
    wage = job.get("wage") or ""
    mid = f"开工 {start} · 收工 {end}"
    if wage:
        mid += f" · {wage}"
    duties_html = ""
    if with_duties:
        dut = excerpt(job.get("duties") or "")
        if dut:
            duties_html = f'<p class="duties">{esc(dut)}</p>'
    url = job.get("url") or "https://seasonaljobs.dol.gov/"
    return (
        f'<article class="job">\n'
        f'  <h3><span class="tag {tag}">{esc(job.get("type"))}</span>{esc(job.get("title_zh"))}</h3>\n'
        f'  <div class="meta">{esc(top)}</div>\n'
        f'  <div class="meta">{esc(mid)}</div>\n'
        f"  {duties_html}\n"
        f'  <div class="contact"><a href="{esc(url)}" target="_blank" rel="noopener">看劳工部原文</a></div>\n'
        f"</article>"
    )


def page_head(title: str, description: str, canonical: str, extra: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{esc(canonical)}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:site_name" content="签证政策">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta name="twitter:card" content="summary">
  {extra}
  <style>{CSS}
  </style>
</head>
"""


def wrap_page(title: str, description: str, path: str, body: str, crumb: str) -> str:
    return (
        page_head(title, description, f"{SITE}/{path.lstrip('/')}")
        + "<body>\n"
        + f"  {NAV}\n"
        + f"  {CRUMBS % esc(crumb)}\n"
        + "  <header>\n"
        + f"    <h1>{esc(crumb)}</h1>\n"
        + f'    <p class="sub">{esc(description)}</p>\n'
        + "  </header>\n"
        + f"  {SUBNAV}\n"
        + f'  <div class="banner">{esc(BANNER)}</div>\n'
        + f"  <main>\n{body}\n  </main>\n"
        + FOOTER
        + "</body>\n</html>\n"
    )


def inject_list(index_html: str, snippet: str) -> str:
    """Replace #list contents using depth matching so inner </div> is safe."""
    start_mark = "<!--seo-jobs-->"
    end_mark = "<!--/seo-jobs-->"
    block = f'<div id="list">{start_mark}\n{snippet}\n    {end_mark}</div>'
    needle = '<div id="list">'
    i = index_html.find(needle)
    if i < 0:
        raise SystemExit('could not find <div id="list"> in index.html')
    pos = i + len(needle)
    depth = 1
    while pos < len(index_html):
        nxt_open = index_html.find("<div", pos)
        nxt_close = index_html.find("</div>", pos)
        if nxt_close < 0:
            raise SystemExit("unclosed #list div")
        if nxt_open != -1 and nxt_open < nxt_close:
            depth += 1
            pos = nxt_open + 4
            continue
        depth -= 1
        if depth == 0:
            end = nxt_close + len("</div>")
            return index_html[:i] + block + index_html[end:]
        pos = nxt_close + 6
    raise SystemExit("unclosed #list div")


def load_jobs() -> tuple[str, list[dict]]:
    data = json.loads((ROOT / "jobs.json").read_text(encoding="utf-8"))
    jobs = [j for j in (data.get("jobs") or []) if is_active(j)]
    return data.get("updated") or TODAY, jobs


def write_gangwei(jobs: list[dict]) -> int:
    items = []
    for j in jobs:
        loc = loc_of(j)
        line = " · ".join(
            p
            for p in (
                j.get("type") or "",
                j.get("employer") or "",
                loc,
                f"{j.get('start') or '未标明'}–{j.get('end') or '未标明'}",
                j.get("wage") or "",
            )
            if p
        )
        url = j.get("url") or "https://seasonaljobs.dol.gov/"
        items.append(
            f"      <dt>{esc(j.get('title_zh'))}</dt>\n"
            f"      <dd>{esc(line)} · <a href=\"{esc(url)}\" target=\"_blank\" rel=\"noopener\">劳工部原文</a></dd>"
        )
    body = (
        "    <h2>全部可查岗位</h2>\n"
        f'    <p class="count">共 {len(jobs)} 条（收工日 {TODAY} 及以后，或未标明收工日）。完整列表供搜索引擎收录。</p>\n'
        "    <dl>\n"
        + "\n".join(items)
        + "\n    </dl>"
    )
    html_out = wrap_page(
        "全部 H-2A H-2B 岗位列表｜签证政策",
        "美国劳工部公开的 H-2A / H-2B 季节工岗位完整中文列表：职位、雇主、地点、工期和工资。非官方，不收费，不代办签证。",
        "gangwei.html",
        body,
        "全部岗位",
    )
    (ROOT / "gangwei.html").write_text(html_out, encoding="utf-8")
    return len(jobs)


def write_type_page(jobs: list[dict], visa: str, filename: str, title: str, lead: str) -> int:
    matched = [j for j in jobs if j.get("type") == visa][:60]
    articles = "\n".join(job_article(j) for j in matched)
    heading = "H-2A 农业季节工" if visa == "H-2A" else "H-2B 非农季节工"
    body = (
        f"    <h2>先看懂再找工</h2>\n{CARDS}\n"
        f"    <h2>{heading}</h2>\n"
        f'    <p class="count">{esc(lead)}下列为前 {len(matched)} 条仍有效岗位。</p>\n'
        f"    {articles}"
    )
    crumb = "H-2A 农业" if visa == "H-2A" else "H-2B 非农"
    html_out = wrap_page(title, DESC, filename, body, crumb)
    (ROOT / filename).write_text(html_out, encoding="utf-8")
    return len(matched)


def main() -> None:
    updated, jobs = load_jobs()
    n_all = write_gangwei(jobs)
    n_a = write_type_page(
        jobs,
        "H-2A",
        "h2a.html",
        "H-2A 农业季节工岗位｜签证政策",
        "H-2A 没有人数上限。农场、农机、畜牧。雇主通常要提供免费住房。",
    )
    n_b = write_type_page(
        jobs,
        "H-2B",
        "h2b.html",
        "H-2B 非农季节工岗位｜签证政策",
        "H-2B 每年法定 66,000 个名额。厨师、酒店、园林、建筑。住房多半要自己付钱。",
    )
    print(f"updated={updated}")
    print(f"gangwei.html jobs={n_all}")
    print(f"h2a.html articles={n_a}")
    print(f"h2b.html articles={n_b}")


if __name__ == "__main__":
    main()
