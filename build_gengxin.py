#!/usr/bin/env python3
"""Rebuild gengxin.html from zhengce-rizhi.json. Newest logged date first."""
import json
from collections import OrderedDict
from pathlib import Path

root = Path(__file__).resolve().parent
log = json.loads((root / "zhengce-rizhi.json").read_text(encoding="utf-8"))

css = """
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
    .nav-links a, .nav-links .here {
      min-height: 44px; display: inline-flex; align-items: center; padding: 0 10px;
      border-radius: 8px; text-decoration: none; color: var(--a); font-size: .95rem;
    }
    .nav-links .here { color: var(--muted); font-weight: 600; }
    header { padding: 22px 0 8px; }
    .brand {
      display: inline-block; font-size: .78rem; letter-spacing: .12em;
      color: var(--a); font-weight: 600; margin: 0 0 10px;
    }
    h1 { font-size: 1.72rem; line-height: 1.25; margin: 0 0 10px; letter-spacing: .01em; }
    .sub { color: var(--muted); margin: 0 0 14px; }
    main { padding: 12px 0 48px; }
    .day { margin: 0 0 22px; }
    .day h2 { font-size: 1.02rem; margin: 0 0 10px; }
    .item {
      background: var(--card); border: 1px solid var(--line); border-radius: 12px;
      padding: 14px 16px; margin: 0 0 10px;
    }
    .item h3 { font-size: 1rem; margin: 0 0 6px; }
    .meta { color: var(--muted); font-size: .88rem; margin: 0 0 8px; }
    .item p { margin: 0 0 8px; }
    .item p:last-child { margin-bottom: 0; }
    footer { border-top: 1px solid var(--line); padding: 18px 0 36px; color: var(--muted); font-size: .88rem; }
    footer p { margin: 0 0 8px; }
    footer a { word-break: break-all; }
"""

by_day = OrderedDict()
for e in log["entries"]:
    by_day.setdefault(e["logged"], []).append(e)

days_html = []
for day in sorted(by_day.keys(), reverse=True):
    items = by_day[day]
    blocks = []
    for e in items:
        dates = []
        if e.get("announced"):
            dates.append("官网公布 " + e["announced"])
        if e.get("effective"):
            dates.append("生效 " + e["effective"])
        meta = " · ".join([e["country"]] + dates)
        src = ""
        if e.get("source"):
            src = '<p><a href="%s">%s</a></p>' % (e["source"], e.get("source_label") or "官网")
        affect = ""
        if e.get("affects"):
            affect = "<p>对站点：%s</p>" % e["affects"]
        blocks.append(
            '      <article class="item">\n'
            "        <h3>%s</h3>\n"
            '        <p class="meta">%s</p>\n'
            "        <p>%s</p>\n"
            "        %s\n"
            "        %s\n"
            "      </article>" % (e["title"], meta, e["what"], affect, src)
        )
    days_html.append(
        '      <section class="day">\n        <h2>%s 记下</h2>\n%s\n      </section>'
        % (day, "\n".join(blocks))
    )

title = "签证政策更新记录"
html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%s</title>
  <meta name="description" content="美加英澳官方签证政策变更轨迹。只记已公布的规则、新表格、名额和排期，附官网链接。">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="https://h2-chaxun.pages.dev/gengxin">
  <meta name="theme-color" content="#f6f3ee">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:site_name" content="签证政策">
  <meta property="og:title" content="%s">
  <meta property="og:description" content="美加英澳官方签证政策变更轨迹。只记已公布的规则、新表格、名额和排期。">
  <meta property="og:url" content="https://h2-chaxun.pages.dev/gengxin">
  <style>%s
  </style>
</head>
<body>
  <nav class="topnav" aria-label="站点导航">
    <div class="topnav-inner">
      <a class="nav-brand" href="/">签证政策</a>
      <div class="nav-links">
        <a href="/">签证种类</a>
        <a href="/h2">查季节工</a>
        <span class="here">政策更新</span>
      </div>
    </div>
  </nav>
  <div class="wrap">
    <header>
      <p class="brand">签证政策</p>
      <h1>政策更新记录</h1>
      <p class="sub">工作日对照官网。只记已入规的改动：新规则、新表格、名额、排期。不记讲话和传闻。最新核对 %s。</p>
    </header>
    <main>
%s
    </main>
    <footer>
      <p>非官方整理，以原文为准。</p>
      <p><a href="/">回签证总览</a> · <a href="/qianzheng">种类说明</a> · <a href="/h2">查季节工</a></p>
    </footer>
  </div>
</body>
</html>
""" % (title, title, css, log["updated"], "\n".join(days_html))

(root / "gengxin.html").write_text(html, encoding="utf-8")
print("wrote gengxin.html", len(log["entries"]), "entries")
