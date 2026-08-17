#!/usr/bin/env python3
"""Rebuild change HTML from zhengce-rizhi.json + countries.json.

One script writes:
- gengxin.html (country chips, shareable ?country=us)
- homepage recent-changes fragment
- per-country change lists
- upcoming-rule bars on US cards
- related-change bars on /qianzheng visa blocks

Daily workflow: prepend to zhengce-rizhi.json, then run this script.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from collections import OrderedDict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://h2-chaxun.pages.dev"
RECENT_N = 8

PAGE_LABELS = {
    "qianzheng#b2": "B-1/B-2 说明",
    "qianzheng#f1": "F-1 说明",
    "qianzheng#m1": "M-1 说明",
    "qianzheng#j1": "J-1 说明",
    "qianzheng#h2a": "H-2A 说明",
    "qianzheng#h2b": "H-2B 说明",
    "qianzheng#h1b": "H-1B 说明",
    "qianzheng#l1": "L-1 说明",
    "qianzheng#h3": "H-3 说明",
    "qianzheng#esta": "ESTA 说明",
    "qianzheng#e1e2": "E-1/E-2 说明",
    "qianzheng#e3": "E-3 说明",
    "qianzheng#tn": "TN 说明",
    "qianzheng#h1b1": "H-1B1 说明",
    "qianzheng#o1": "O-1 说明",
    "qianzheng#p": "P 类说明",
    "qianzheng#r1": "R-1 说明",
    "qianzheng#k1": "K-1 说明",
    "qianzheng#eb": "EB 说明",
    "h2": "季节工查询",
}

SHARED_CSS = """
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
      --chip: #fffdf8;
    }
    * { box-sizing: border-box; }
    html { -webkit-text-size-adjust: 100%; scroll-padding-top: 12px; }
    body {
      margin: 0;
      font: 16px/1.6 "Source Han Sans SC", "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }
    a { color: var(--a); }
    .wrap { max-width: 42rem; margin: 0 auto; padding: 0 18px; }
    .topnav { border-bottom: 1px solid var(--line); background: var(--bg); }
    .topnav-inner {
      max-width: 42rem; margin: 0 auto; padding: 4px 18px;
      display: flex; flex-wrap: wrap; align-items: center; gap: 4px 18px;
    }
    .nav-brand {
      color: var(--a); font-weight: 600; letter-spacing: .12em; font-size: .78rem;
      text-decoration: none; min-height: 44px; display: inline-flex; align-items: center;
    }
    .nav-links { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 6px; }
    .nav-links a, .nav-links .here, .nav-drop > summary {
      min-height: 44px; display: inline-flex; align-items: center; padding: 0 10px;
      border-radius: 8px; text-decoration: none; color: var(--a); font-size: .95rem;
    }
    .nav-links .here { color: var(--muted); font-weight: 600; }
    .nav-drop { position: relative; }
    .nav-drop > summary {
      list-style: none; cursor: pointer; font: inherit;
    }
    .nav-drop > summary::-webkit-details-marker { display: none; }
    .nav-drop[open] > summary { background: #eef6f2; }
    .nav-drop-list {
      position: absolute; left: 0; top: 100%; z-index: 5;
      min-width: 10rem; padding: 6px; margin: 0;
      background: var(--card); border: 1px solid var(--line); border-radius: 12px;
      box-shadow: 0 8px 24px rgba(31, 27, 22, .08);
    }
    .nav-drop-list a, .nav-drop-list .here {
      display: flex; min-height: 44px; align-items: center; padding: 0 12px;
      border-radius: 8px; text-decoration: none; color: var(--a);
    }
    .nav-drop-list .here { color: var(--muted); font-weight: 600; }
    header { padding: 22px 0 8px; }
    .brand {
      display: inline-block; font-size: .78rem; letter-spacing: .12em;
      color: var(--a); font-weight: 600; margin: 0 0 10px;
    }
    h1 { font-size: 1.72rem; line-height: 1.25; margin: 0 0 10px; letter-spacing: .01em; }
    .sub { color: var(--muted); margin: 0 0 14px; }
    .banner {
      margin: 0 0 8px; padding: 12px 14px; background: var(--warnbg);
      color: var(--warn); border-radius: 10px; font-size: .95rem;
    }
    .crumbs { color: var(--muted); font-size: .9rem; margin: 0 0 12px; }
    .crumbs a { text-decoration: none; }
    .checked { color: var(--muted); font-size: .9rem; margin: 0 0 12px; }
    .page-jump { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; }
    .page-jump a {
      min-height: 44px; display: inline-flex; align-items: center; padding: 0 12px;
      border: 1px solid var(--line); border-radius: 999px; background: var(--card);
      text-decoration: none;
    }
    .tools { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 8px; }
    .btn-go, .go {
      display: inline-flex; align-items: center; justify-content: center;
      min-height: 44px; padding: 8px 14px; border-radius: 12px;
      font-weight: 600; text-decoration: none;
    }
    .btn-go {
      background: var(--a); border: 1px solid var(--a); color: #fff;
    }
    .btn-go.ghost {
      background: var(--card); border-color: var(--line); color: var(--a);
    }
    main { padding: 12px 0 48px; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      font: inherit; min-height: 44px; border-radius: 999px;
      border: 1px solid var(--line); background: var(--chip); color: var(--ink);
      padding: 8px 14px; cursor: pointer;
      -webkit-tap-highlight-color: rgba(31, 92, 69, .12);
    }
    .chip.on { background: var(--a); border-color: var(--a); color: #fff; }
    .chip:active { transform: scale(.98); }
    .grid { display: grid; gap: 10px; }
    @media (min-width: 560px) { .grid { grid-template-columns: 1fr 1fr; } }
    .vcard, .ccard, .visa, .note, .item, .slot {
      background: var(--card); border: 1px solid var(--line);
      border-radius: 14px; padding: 14px 16px 12px;
    }
    .ccard h2, .vcard h2, .visa h2 { margin: 0 0 6px; font-size: 1.08rem; line-height: 1.35; }
    .one { margin: 0 0 10px; color: var(--muted); font-size: .95rem; }
    .tag {
      display: inline-block; font-size: .72rem; font-weight: 600;
      padding: 3px 8px; border-radius: 999px; border: 1px solid var(--line);
      color: var(--muted); line-height: 1.4; margin: 0 6px 10px 0;
    }
    .tag.ok { color: var(--a); border-color: #b7d2c6; background: #eef6f2; }
    .tag.no { color: var(--warn); border-color: #e4c4ae; background: var(--warnbg); }
    .code {
      display: inline-block; font-size: .72rem; font-weight: 700; letter-spacing: .04em;
      padding: 2px 8px; border-radius: 999px; background: var(--a); color: #fff;
      vertical-align: middle; margin-right: 6px;
    }
    .code.dim { background: var(--muted); }
    .block { margin: 28px 0 0; }
    .block[hidden], .vcard[hidden] { display: none; }
    .q { margin: 22px 0 0; }
    .q h2, .block h2 { font-size: 1.02rem; margin: 0 0 8px; }
    .changelist { list-style: none; padding: 0; margin: 0; }
    .changelist li {
      background: var(--card); border: 1px solid var(--line); border-radius: 12px;
      padding: 12px 14px; margin: 0 0 8px;
    }
    .changelist .meta { color: var(--muted); font-size: .88rem; }
    .soon, .change-bar {
      margin: 0 0 10px; padding: 8px 10px; background: var(--warnbg);
      color: var(--warn); border-radius: 10px; font-size: .9rem;
    }
    .soon a, .change-bar a { color: var(--warn); font-weight: 600; }
    .day { margin: 0 0 22px; }
    .day h2 { font-size: 1.02rem; margin: 0 0 10px; }
    .item { border-radius: 12px; margin: 0 0 10px; }
    .item h3 { font-size: 1rem; margin: 0 0 6px; }
    .meta { color: var(--muted); font-size: .88rem; margin: 0 0 8px; }
    .item p { margin: 0 0 8px; }
    .item p:last-child { margin-bottom: 0; }
    .affect { font-size: .9rem; }
    .empty { color: var(--muted); }
    .slot { min-height: 5.5rem; color: var(--muted); }
    details.fold {
      background: var(--card); border: 1px solid var(--line);
      border-radius: 12px; padding: 0 14px; margin: 16px 0 0;
    }
    details.fold > summary {
      min-height: 48px; display: flex; align-items: center;
      cursor: pointer; font-weight: 600; list-style: none;
    }
    details.fold > summary::-webkit-details-marker { display: none; }
    details.fold .grid { margin: 0 0 14px; }
    footer { padding: 0 0 40px; color: var(--muted); font-size: .88rem; }
    footer p { margin: 0 0 8px; }
    footer a { word-break: break-all; }
    @media (min-width: 900px) {
      .wrap, .topnav-inner { max-width: 70rem; }
    }
""" + (ROOT / "layout.css").read_text(encoding="utf-8")


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def load_json(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def country_map(countries: list[dict]) -> dict[str, dict]:
    return {c["id"]: c for c in countries}


def entry_id(e: dict) -> str:
    raw = "%s|%s|%s" % (e.get("logged", ""), e.get("country", ""), e.get("title", ""))
    return "c-" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]


def country_of(e: dict, cmap: dict[str, dict]) -> dict:
    cid = e.get("country") or ""
    if cid in cmap:
        return cmap[cid]
    # leftover display names from older logs
    for c in cmap.values():
        if c["name"] == cid:
            return c
    return {"id": cid, "slug": "", "name": cid or "未标国家"}


def effective_or(e: dict) -> str:
    return e.get("effective") or e.get("announced") or e.get("logged") or ""


def page_label(path: str) -> str:
    return PAGE_LABELS.get(path) or path.replace("qianzheng#", "").upper() + " 说明"


def affected_links(e: dict) -> str:
    pages = e.get("site_pages") or []
    if not pages:
        return ""
    bits = []
    for p in pages:
        label = page_label(p)
        href = "/" + p if p.startswith("qianzheng") or p.startswith("h2") else "/" + p
        bits.append('<a href="%s">%s</a>' % (esc(href), esc(label)))
    return '<p class="affect">影响到：%s</p>' % "、".join(bits)


def change_card(e: dict, cmap: dict[str, dict], heading: str = "h3") -> str:
    c = country_of(e, cmap)
    dates = []
    if e.get("announced"):
        dates.append("官网公布 " + e["announced"])
    if e.get("effective"):
        dates.append("生效 " + e["effective"])
    date_line = " · ".join(dates) if dates else ""
    country_html = esc(c["name"])
    if c.get("slug"):
        country_html = '<a href="/%s">%s</a>' % (esc(c["slug"]), esc(c["name"]))
    src = ""
    if e.get("source"):
        src = '<p><a href="%s">%s</a></p>' % (esc(e["source"]), esc(e.get("source_label") or "官网"))
    return (
        '<article class="item" id="%s" data-country="%s">\n'
        "        <%s>%s</%s>\n"
        '        <p class="meta">%s</p>\n'
        "        %s\n"
        "        <p>%s</p>\n"
        "        %s\n"
        "        %s\n"
        "      </article>"
        % (
            esc(entry_id(e)),
            esc(c.get("id") or ""),
            heading,
            esc(e.get("title") or ""),
            heading,
            country_html,
            ('<p class="meta">%s</p>' % esc(date_line)) if date_line else "",
            esc(e.get("what") or ""),
            src,
            affected_links(e),
        )
    )


def recent_items_html(entries: list[dict], cmap: dict[str, dict], n: int = RECENT_N) -> str:
    rows = []
    for e in entries[:n]:
        c = country_of(e, cmap)
        when = effective_or(e)
        country_bit = esc(c["name"])
        if c.get("slug"):
            country_bit = '<a href="/%s">%s</a>' % (esc(c["slug"]), esc(c["name"]))
        title_bit = '<a href="/gengxin#%s">%s</a>' % (esc(entry_id(e)), esc(e.get("title") or ""))
        rows.append(
            "        <li>%s · %s · %s</li>"
            % (country_bit, esc(when), title_bit)
        )
    if not rows:
        return '        <li class="empty">还没有记下的改动。</li>'
    return "\n".join(rows)


def country_list_html(entries: list[dict], cmap: dict[str, dict], country_id: str) -> str:
    matched = [e for e in entries if country_of(e, cmap).get("id") == country_id]
    if not matched:
        return '<p class="empty">还没有记下的改动。</p>'
    items = []
    for e in matched:
        when = effective_or(e)
        items.append(
            "        <li><span class=\"meta\">%s</span> · <a href=\"/gengxin#%s\">%s</a></li>"
            % (esc(when), esc(entry_id(e)), esc(e.get("title") or ""))
        )
    return '<ul class="changelist">\n%s\n      </ul>' % "\n".join(items)


def upcoming_for_page(entries: list[dict], page: str, today: str) -> str:
    bits = []
    for e in entries:
        eff = e.get("effective") or ""
        if not eff or eff <= today:
            continue
        pages = e.get("site_pages") or []
        if page not in pages:
            continue
        bits.append(
            '<p class="soon"><a href="/gengxin#%s">%s 起规则将变</a></p>'
            % (esc(entry_id(e)), esc(eff))
        )
    return "\n".join(bits)


def change_bars_for_page(entries: list[dict], page: str) -> str:
    bits = []
    for e in entries:
        pages = e.get("site_pages") or []
        if page not in pages:
            continue
        when = e.get("effective") or e.get("announced") or ""
        prefix = ("%s 起：" % when) if when else ""
        bits.append(
            '<p class="change-bar"><a href="/gengxin#%s">%s%s</a></p>'
            % (esc(entry_id(e)), esc(prefix), esc(e.get("title") or ""))
        )
    return "\n".join(bits)


def replace_block(text: str, name: str, inner: str) -> str:
    start = "<!--gengxin:%s-->" % name
    end = "<!--/gengxin:%s-->" % name
    if start not in text or end not in text:
        raise SystemExit("missing marker %s" % name)
    pre, rest = text.split(start, 1)
    _, post = rest.split(end, 1)
    body = inner
    if body and not body.startswith("\n"):
        body = "\n" + body
    if body and not body.endswith("\n"):
        body = body + "\n      "
    return pre + start + body + end + post


def replace_all_named(text: str, prefix: str, builder) -> str:
    pattern = re.compile(
        r"<!--gengxin:%s:([^>]+)-->.*?<!--/gengxin:%s:\1-->" % (re.escape(prefix), re.escape(prefix)),
        re.S,
    )

    def repl(m):
        key = m.group(1)
        inner = builder(key) or ""
        if inner and not inner.startswith("\n"):
            inner = "\n" + inner
        if inner and not inner.endswith("\n"):
            inner += "\n      "
        return "<!--gengxin:%s:%s-->%s<!--/gengxin:%s:%s-->" % (prefix, key, inner, prefix, key)

    return pattern.sub(repl, text)


def nav_html(here: str = "", country_id: str = "", countries: list[dict] | None = None) -> str:
    countries = countries or []
    country_here = here in ("home", "country")
    gengxin_here = here == "gengxin"
    country_label = '<span class="here">国家</span>' if country_here and here == "home" else ""
    if not country_label:
        items = []
        for c in countries:
            href = "/%s" % c["slug"]
            if country_id and c["id"] == country_id:
                items.append('<span class="here">%s</span>' % esc(c["name"]))
            else:
                items.append('<a href="%s">%s</a>' % (esc(href), esc(c["name"])))
        items.insert(0, '<a href="/#guojia">国家目录</a>')
        country_label = (
            '<details class="nav-drop">\n'
            '          <summary>国家</summary>\n'
            '          <div class="nav-drop-list">\n'
            "            %s\n"
            "          </div>\n"
            "        </details>" % "\n            ".join(items)
        )
    gengxin = '<span class="here">政策更新</span>' if gengxin_here else '<a href="/gengxin">政策更新</a>'
    return (
        '  <nav class="topnav" aria-label="站点导航">\n'
        '    <div class="topnav-inner">\n'
        '      <a class="nav-brand" href="/">签证政策</a>\n'
        '      <div class="nav-links">\n'
        "        %s\n"
        "        %s\n"
        "      </div>\n"
        "    </div>\n"
        "  </nav>" % (country_label, gengxin)
    )


def write_gengxin(log: dict, countries: list[dict], cmap: dict[str, dict]) -> None:
    entries = log.get("entries") or []
    by_day = OrderedDict()
    for e in entries:
        by_day.setdefault(e["logged"], []).append(e)

    days_html = []
    for day in sorted(by_day.keys(), reverse=True):
        blocks = [change_card(e, cmap) for e in by_day[day]]
        days_html.append(
            '      <section class="day" data-day="%s">\n        <h2>%s 记下</h2>\n      %s\n      </section>'
            % (esc(day), esc(day), "\n      ".join(blocks))
        )

    chips = ['<button type="button" class="chip on" data-country="">全部</button>']
    for c in countries:
        chips.append(
            '<button type="button" class="chip" data-country="%s">%s</button>'
            % (esc(c["id"]), esc(c["name"]))
        )

    title = "签证政策更新记录"
    html_out = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%s</title>
  <meta name="description" content="美加英澳官方签证政策变更轨迹。只记已公布的规则、新表格、名额和排期，附官网链接。">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="%s/gengxin">
  <meta name="theme-color" content="#f6f3ee">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:site_name" content="签证政策">
  <meta property="og:title" content="%s">
  <meta property="og:description" content="美加英澳官方签证政策变更轨迹。只记已公布的规则、新表格、名额和排期。">
  <meta property="og:url" content="%s/gengxin">
  <style>%s
  </style>
  <link rel="stylesheet" href="/layout.css">
</head>
<body>
%s
  <div class="wrap">
    <header>
      <p class="brand">签证政策</p>
      <h1>政策更新记录</h1>
      <p class="sub">工作日对照官网。只记已入规的改动：新规则、新表格、名额、排期。不记讲话和传闻。最新核对 %s。</p>
      <div class="chips" id="country-chips" aria-label="按国家筛选">
        %s
      </div>
    </header>
    <main id="log">
%s
    </main>
    <footer>
      <p>非官方整理，以原文为准。</p>
      <p><a href="/">回国家目录</a></p>
    </footer>
  </div>
  <script>
    (function () {
      var chips = document.getElementById("country-chips");
      if (!chips) return;
      function apply(id) {
        var all = chips.querySelectorAll(".chip");
        var i;
        for (i = 0; i < all.length; i++) {
          var on = (all[i].getAttribute("data-country") || "") === id;
          if (on) all[i].classList.add("on");
          else all[i].classList.remove("on");
        }
        var items = document.querySelectorAll(".item");
        for (i = 0; i < items.length; i++) {
          var c = items[i].getAttribute("data-country") || "";
          items[i].hidden = !!(id && c !== id);
        }
        var days = document.querySelectorAll(".day");
        for (i = 0; i < days.length; i++) {
          var shown = days[i].querySelector(".item:not([hidden])");
          days[i].hidden = !shown;
        }
        var url = new URL(window.location.href);
        if (id) url.searchParams.set("country", id);
        else url.searchParams.delete("country");
        history.replaceState(null, "", url.pathname + url.search + url.hash);
      }
      chips.addEventListener("click", function (e) {
        var btn = e.target.closest ? e.target.closest(".chip") : null;
        if (!btn) return;
        apply(btn.getAttribute("data-country") || "");
      });
      var start = new URLSearchParams(window.location.search).get("country") || "";
      apply(start);
    })();
  </script>
</body>
</html>
""" % (
        title,
        SITE,
        title,
        SITE,
        SHARED_CSS,
        nav_html("gengxin", countries=countries),
        esc(log.get("updated") or ""),
        "\n        ".join(chips),
        "\n".join(days_html) if days_html else '      <p class="empty">还没有记下的改动。</p>',
    )
    (ROOT / "gengxin.html").write_text(html_out, encoding="utf-8")


def write_placeholder(c: dict, countries: list[dict], entries: list[dict], cmap: dict[str, dict]) -> None:
    checked = (
        "本页最后核对 %s" % c["checked"]
        if c.get("checked")
        else "本页最后核对：现有政策尚未核对"
    )
    changes = country_list_html(entries, cmap, c["id"])
    title = "%s签证政策｜现有政策与官方变更" % c["name"]
    html_out = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%s</title>
  <meta name="description" content="%s现有签证政策待补。可先看已记下的官方变更。不收费，不代办。">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="%s/%s">
  <meta name="theme-color" content="#f6f3ee">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:site_name" content="签证政策">
  <meta property="og:title" content="%s">
  <meta property="og:description" content="%s现有签证政策待补。可先看已记下的官方变更。">
  <meta property="og:url" content="%s/%s">
  <style>%s
  </style>
  <link rel="stylesheet" href="/layout.css">
</head>
<body>
%s
  <div class="wrap">
    <header>
      <p class="brand">签证政策</p>
      <h1>%s</h1>
      <p class="sub">%s</p>
      <p class="checked">%s</p>
      <nav class="page-jump" aria-label="本页两块">
        <a href="#xianyou">现有政策</a>
        <a href="#biangeng">最近变更</a>
      </nav>
    </header>
    <main>
      <div class="country-split">
      <section class="block" id="xianyou">
        <h2>现有政策</h2>
        <p class="note">现有政策待补。对照官网的路径卡之后会放在这里，大约 3–6 条。</p>
        <div class="grid" aria-hidden="true">
          <div class="slot">路径卡待补</div>
          <div class="slot">路径卡待补</div>
          <div class="slot">路径卡待补</div>
        </div>
      </section>
      <section class="block" id="biangeng">
        <h2>最近变更</h2>
        %s
        <p><a href="/gengxin?country=%s">在更新记录里只看%s</a></p>
      </section>
      </div>
    </main>
    <footer>
      <p>非官方。现有政策待补。已记下的变更以官网原文为准。不收费，不代办。</p>
      <p><a href="/">回国家目录</a> · <a href="/gengxin">政策更新</a></p>
    </footer>
  </div>
</body>
</html>
""" % (
        esc(title),
        esc(c["name"]),
        SITE,
        esc(c["slug"]),
        esc(title),
        esc(c["name"]),
        SITE,
        esc(c["slug"]),
        SHARED_CSS,
        nav_html("country", c["id"], countries),
        esc(c["name"]),
        esc(c.get("blurb") or "现有政策待补。"),
        esc(checked),
        changes,
        esc(c["id"]),
        esc(c["name"]),
    )
    (ROOT / ("%s.html" % c["slug"])).write_text(html_out, encoding="utf-8")


def patch_marked_pages(entries: list[dict], cmap: dict[str, dict], countries: list[dict], today: str) -> None:
    index = ROOT / "index.html"
    if index.exists():
        text = index.read_text(encoding="utf-8")
        text = replace_block(text, "recent", recent_items_html(entries, cmap))
        index.write_text(text, encoding="utf-8")

    meiguo = ROOT / "meiguo.html"
    if meiguo.exists():
        text = meiguo.read_text(encoding="utf-8")
        us = cmap.get("us") or {}
        checked = (
            "本页最后核对 %s" % us["checked"]
            if us.get("checked")
            else "本页最后核对：现有政策尚未核对"
        )
        text = replace_block(text, "checked", checked)
        text = replace_block(text, "country", country_list_html(entries, cmap, "us"))
        text = replace_all_named(text, "soon", lambda page: upcoming_for_page(entries, page, today))
        meiguo.write_text(text, encoding="utf-8")

    qianzheng = ROOT / "qianzheng.html"
    if qianzheng.exists():
        text = qianzheng.read_text(encoding="utf-8")
        text = replace_all_named(text, "bar", lambda page: change_bars_for_page(entries, page))
        qianzheng.write_text(text, encoding="utf-8")


def main() -> None:
    countries_data = load_json("countries.json")
    countries = countries_data.get("countries") or []
    cmap = country_map(countries)
    log = load_json("zhengce-rizhi.json")
    entries = log.get("entries") or []
    today = date.today().isoformat()

    write_gengxin(log, countries, cmap)
    for c in countries:
        if c.get("status") == "placeholder":
            write_placeholder(c, countries, entries, cmap)
    patch_marked_pages(entries, cmap, countries, today)
    print("wrote gengxin.html", len(entries), "entries; today", today)


if __name__ == "__main__":
    main()
