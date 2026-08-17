# 签证查阅

用中文说明美国常见签证。H-2 季节工查询是其中一项工具：把美国劳工部 [SeasonalJobs](https://seasonaljobs.dol.gov/) 的 H-2A / H-2B 公开岗位做成中文查阅页。

- 不向求职者收费
- 不代办签证、不代招
- 使用劳工部公开数据，但未经劳工部认可或认证

## 本地预览

```bash
cd /workspace/h2info
python3 -m http.server 8080
```

打开 http://127.0.0.1:8080

季节工页是 `h2.html`（地址 `/h2`）。不要直接双击它，浏览器会拦 `jobs.json`。

## 更新数据

劳工部数据源每天美东午夜更新：

- H-2A 岗位单：`https://api.seasonaljobs.dol.gov/datahub-search/sjCaseData/zip/jo/YYYY-MM-DD`
- H-2B 申请：`https://api.seasonaljobs.dol.gov/datahub-search/sjCaseData/zip/h2b/YYYY-MM-DD`

用仓库里的生成脚本重新抽出 `jobs.json` 即可。
