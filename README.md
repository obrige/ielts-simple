# IELTS Familiarisation Test — Offline Training

## Start

```bash
curl -fsSL https://raw.githubusercontent.com/obrige/gelielts/main/docker-compose.yml | docker compose -f - up -d
```

→ http://localhost:5000

## Admin

Login `admin@ielts.local` → `/admin/tests`

- 试题 CRUD · 答案录入 · JSON 导入导出
- 评分引擎: `exact` | `contains` | `regex` | `manual`
- 完成全部测试后自动出分
