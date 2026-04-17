# GitHub Issues API Reference

Quick reference for the API patterns used by this agent. For full docs: https://docs.github.com/en/rest/issues

---

## Authentication

All requests require:
```
Authorization: Bearer {GH_TOKEN}
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

Token scopes needed:
- `public_repo` — read/write issues on public repos
- `repo` — read/write issues on private repos

---

## Key Endpoints

### List open issues
```
GET /repos/{owner}/{repo}/issues?state=open&per_page=100&page=1
```
- Returns issues **and pull requests** — filter PRs by checking `"pull_request" not in item`
- Paginate: increment `page` until response length < `per_page`

### List comments on an issue
```
GET /repos/{owner}/{repo}/issues/{issue_number}/comments?per_page=100&page=1
```
- Only needed if `issue["comments"] > 0`

### Post a comment
```
POST /repos/{owner}/{repo}/issues/{issue_number}/comments
{"body": "your markdown comment"}
```
- Returns 201 on success

### Close an issue
```
PATCH /repos/{owner}/{repo}/issues/{issue_number}
{"state": "closed"}
```
- Returns 200 with updated issue object

### Check rate limit
```
GET /rate_limit
```
Response includes:
```json
{
  "rate": {
    "limit": 5000,
    "remaining": 4823,
    "reset": 1713398400
  }
}
```

---

## Pagination Pattern

```python
def get_all_pages(url, headers, params=None):
    params = dict(params or {})
    params["per_page"] = 100
    results = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results
```

---

## Rate Limits

- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour (never use unauthenticated)
- Rate limit headers on every response:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset` (Unix timestamp)

---

## Issue Object Fields Used

| Field | Type | Notes |
|---|---|---|
| `number` | int | Issue number — used in filenames and API calls |
| `title` | string | Used in filename slug |
| `state` | string | `open` or `closed` |
| `labels` | array | Each has `name` field |
| `created_at` | ISO 8601 | Creation timestamp |
| `updated_at` | ISO 8601 | Last update timestamp |
| `user.login` | string | Issue author |
| `html_url` | string | Browser URL for the issue |
| `body` | string | Issue description (may be null) |
| `comments` | int | Comment count — use to skip comment fetch when 0 |
| `pull_request` | object | Present only on PRs — use to filter them out |

## Comment Object Fields Used

| Field | Type | Notes |
|---|---|---|
| `user.login` | string | Commenter |
| `created_at` | ISO 8601 | Comment timestamp |
| `body` | string | Comment text (may be null) |
