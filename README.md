# 签证政策

对照官网，整理各国现有签证 / 移民政策，并记录规则变更。

美国签证种类说明和 H-2 季节工查询仍是站点里的工具。H-2 数据来自美国劳工部 [SeasonalJobs](https://seasonaljobs.dol.gov/)，未经劳工部认可或认证。

- 不向读者收费
- 不代办签证、不代招
- 只认官网，不认中介和自媒体

线上：https://h2-chaxun.pages.dev

## 本地预览

```bash
python3 -m http.server 8080
```

打开 http://127.0.0.1:8080

季节工页是 `h2.html`（地址 `/h2`）。政策变更轨迹是 `gengxin.html`（地址 `/gengxin`），数据在 `zhengce-rizhi.json`。

## 更新 H-2 数据

劳工部数据源每天美东午夜更新：

- H-2A 岗位单：`https://api.seasonaljobs.dol.gov/datahub-search/sjCaseData/zip/jo/YYYY-MM-DD`
- H-2B 申请：`https://api.seasonaljobs.dol.gov/datahub-search/sjCaseData/zip/h2b/YYYY-MM-DD`
