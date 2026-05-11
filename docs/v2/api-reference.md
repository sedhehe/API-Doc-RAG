# NexAPI Reference — v2

NexAPI is a REST API for managing users, teams, and notifications.
All endpoints are served over HTTPS. Base URL: `https://api.nexapi.io/v2`

---

## Authentication

NexAPI uses Bearer token authentication. Every request must include a valid API key in the Authorization header.

Tokens are scoped to a workspace and can be created from the dashboard under **Settings → API Keys**. Tokens do not expire by default but can be revoked manually.

### Bearer Token

Include your API key in every request using the `Authorization` header. Requests without a valid token will receive a `401 Unauthorized` response.

| Header        | Value                        | Required |
|---------------|------------------------------|----------|
| Authorization | Bearer YOUR_API_KEY          | yes      |
| Content-Type  | application/json             | yes      |

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

response = requests.get("https://api.nexapi.io/v2/users", headers=headers)
```

### API Key Scopes

Each API key can be assigned one or more scopes that limit what it can access.

| Scope          | Description                          |
|----------------|--------------------------------------|
| users:read     | Read user data                       |
| users:write    | Create and update users              |
| teams:read     | Read team data                       |
| teams:write    | Create and update teams              |
| notify:send    | Send notifications                   |

```python
# Example: scoped key for read-only user access
headers = {
    "Authorization": "Bearer READ_ONLY_KEY",
}
response = requests.get("https://api.nexapi.io/v2/users", headers=headers)
```

---

## Users

The Users API allows you to create, retrieve, update, and delete user accounts within your workspace.

### List Users

Returns a paginated list of users in your workspace. Results are sorted by `created_at` in descending order by default.

| Parameter | Type    | Required | Description                          |
|-----------|---------|----------|--------------------------------------|
| limit     | integer | no       | Number of results per page (max 100, default 20) |
| offset    | integer | no       | Number of results to skip (default 0) |
| sort      | string  | no       | Field to sort by: `created_at`, `email`, `name` |
| order     | string  | no       | Sort direction: `asc` or `desc`      |

```python
response = requests.get(
    "https://api.nexapi.io/v2/users",
    headers=headers,
    params={"limit": 20, "offset": 0, "sort": "created_at", "order": "desc"}
)

# Response
{
    "data": [...],
    "pagination": {
        "total": 143,
        "limit": 20,
        "offset": 0,
        "has_more": true
    }
}
```

### Get User

Returns a single user by their unique ID.

| Parameter | Type   | Required | Description       |
|-----------|--------|----------|-------------------|
| user_id   | string | yes      | The user's unique ID (path parameter) |

```python
response = requests.get(
    "https://api.nexapi.io/v2/users/usr_abc123",
    headers=headers
)

# Response
{
    "id": "usr_abc123",
    "email": "jane@example.com",
    "name": "Jane Doe",
    "role": "member",
    "created_at": "2024-03-15T10:00:00Z",
    "updated_at": "2024-11-01T08:30:00Z"
}
```

### Create User

Creates a new user in your workspace. The email address must be unique across the workspace.

| Parameter    | Type   | Required | Description                              |
|--------------|--------|----------|------------------------------------------|
| email        | string | yes      | User's email address (must be unique)    |
| name         | string | yes      | User's full name                         |
| role         | string | no       | Role: `admin`, `member`, `viewer` (default: `member`) |
| metadata     | object | no       | Arbitrary key-value pairs (max 10 keys)  |

```python
response = requests.post(
    "https://api.nexapi.io/v2/users",
    headers=headers,
    json={
        "email": "jane@example.com",
        "name": "Jane Doe",
        "role": "member",
        "metadata": {"department": "engineering"}
    }
)
```

### Update User

Updates an existing user. Only fields provided in the request body are updated — this is a partial update (PATCH semantics).

| Parameter | Type   | Required | Description                        |
|-----------|--------|----------|------------------------------------|
| user_id   | string | yes      | The user's unique ID (path param)  |
| name      | string | no       | Updated full name                  |
| role      | string | no       | Updated role                       |
| metadata  | object | no       | Replaces entire metadata object    |

```python
response = requests.patch(
    "https://api.nexapi.io/v2/users/usr_abc123",
    headers=headers,
    json={"role": "admin"}
)
```

### Delete User

Permanently deletes a user from your workspace. This action cannot be undone. The user's data is removed within 30 days.

| Parameter | Type   | Required | Description                       |
|-----------|--------|----------|-----------------------------------|
| user_id   | string | yes      | The user's unique ID (path param) |

```python
response = requests.delete(
    "https://api.nexapi.io/v2/users/usr_abc123",
    headers=headers
)
# Returns 204 No Content on success
```

---

## Teams

Teams allow you to group users and manage permissions at the team level. A user can belong to multiple teams.

### List Teams

Returns all teams in your workspace.

| Parameter | Type    | Required | Description                    |
|-----------|---------|----------|--------------------------------|
| limit     | integer | no       | Results per page (default 20)  |
| offset    | integer | no       | Results to skip (default 0)    |

```python
response = requests.get(
    "https://api.nexapi.io/v2/teams",
    headers=headers
)
```

### Create Team

Creates a new team. Team names must be unique within a workspace.

| Parameter   | Type   | Required | Description                         |
|-------------|--------|----------|-------------------------------------|
| name        | string | yes      | Team name (must be unique)          |
| description | string | no       | Optional team description           |

```python
response = requests.post(
    "https://api.nexapi.io/v2/teams",
    headers=headers,
    json={"name": "Engineering", "description": "Product engineers"}
)
```

### Add Team Member

Adds an existing user to a team.

| Parameter | Type   | Required | Description                         |
|-----------|--------|----------|-------------------------------------|
| team_id   | string | yes      | Team ID (path parameter)            |
| user_id   | string | yes      | User ID to add                      |
| role      | string | no       | Team role: `lead` or `member` (default: `member`) |

```python
response = requests.post(
    "https://api.nexapi.io/v2/teams/tm_xyz789/members",
    headers=headers,
    json={"user_id": "usr_abc123", "role": "lead"}
)
```

---

## Notifications

The Notifications API lets you send messages to users or teams via email, SMS, or in-app channels.

### Send Notification

Sends a notification to one or more recipients. Requires the `notify:send` scope.

| Parameter  | Type          | Required | Description                                      |
|------------|---------------|----------|--------------------------------------------------|
| to         | array[string] | yes      | List of user IDs or team IDs                     |
| channel    | string        | yes      | Delivery channel: `email`, `sms`, `in_app`       |
| subject    | string        | yes (email) | Email subject line                            |
| body       | string        | yes      | Message body (plain text or HTML for email)      |
| priority   | string        | no       | `normal` or `high` (default: `normal`)           |
| schedule_at| string        | no       | ISO 8601 datetime to schedule delivery           |

```python
response = requests.post(
    "https://api.nexapi.io/v2/notifications",
    headers=headers,
    json={
        "to": ["usr_abc123", "tm_xyz789"],
        "channel": "email",
        "subject": "Your report is ready",
        "body": "Hello, your weekly report has been generated.",
        "priority": "high"
    }
)
```

### Get Notification Status

Returns the delivery status of a previously sent notification.

| Parameter       | Type   | Required | Description                         |
|-----------------|--------|----------|-------------------------------------|
| notification_id | string | yes      | Notification ID (path parameter)    |

```python
response = requests.get(
    "https://api.nexapi.io/v2/notifications/ntf_def456",
    headers=headers
)

# Response
{
    "id": "ntf_def456",
    "status": "delivered",
    "delivered_at": "2024-11-01T09:05:00Z",
    "recipients": {
        "total": 2,
        "delivered": 2,
        "failed": 0
    }
}
```

---

## Pagination

All list endpoints in NexAPI use offset-based pagination. Use `limit` and `offset` parameters to navigate through results.

### How Pagination Works

Every list response includes a `pagination` object:

| Field    | Type    | Description                                  |
|----------|---------|----------------------------------------------|
| total    | integer | Total number of records matching your query  |
| limit    | integer | Number of records returned in this response  |
| offset   | integer | Number of records skipped                    |
| has_more | boolean | Whether more records exist after this page   |

```python
# Fetch all users by paginating
offset = 0
limit = 50
all_users = []

while True:
    response = requests.get(
        "https://api.nexapi.io/v2/users",
        headers=headers,
        params={"limit": limit, "offset": offset}
    )
    data = response.json()
    all_users.extend(data["data"])

    if not data["pagination"]["has_more"]:
        break

    offset += limit
```

---

## Rate Limits

NexAPI enforces rate limits per API key to ensure fair usage across all customers.

### Default Limits

| Endpoint Group   | Limit              |
|------------------|--------------------|
| Users (read)     | 300 requests/min   |
| Users (write)    | 60 requests/min    |
| Teams            | 100 requests/min   |
| Notifications    | 30 requests/min    |
| Global           | 500 requests/min   |

### Rate Limit Headers

Every response includes headers showing your current usage:

| Header                  | Description                              |
|-------------------------|------------------------------------------|
| X-RateLimit-Limit       | Maximum requests allowed per window      |
| X-RateLimit-Remaining   | Requests remaining in current window     |
| X-RateLimit-Reset       | Unix timestamp when the window resets    |

```python
response = requests.get("https://api.nexapi.io/v2/users", headers=headers)

print(response.headers["X-RateLimit-Remaining"])  # e.g. "297"
print(response.headers["X-RateLimit-Reset"])       # e.g. "1730448060"
```

### Handling 429 Errors

When you exceed the rate limit, the API returns a `429 Too Many Requests` response. Use the `Retry-After` header to know when to retry.

```python
if response.status_code == 429:
    retry_after = int(response.headers["Retry-After"])
    time.sleep(retry_after)
    response = requests.get(url, headers=headers)
```

---

## Errors

NexAPI uses standard HTTP status codes. All error responses include a JSON body with a machine-readable `code` and a human-readable `message`.

### Error Response Format

```json
{
    "error": {
        "code": "validation_error",
        "message": "The email field is required.",
        "field": "email"
    }
}
```

### HTTP Status Codes

| Code | Name                  | Description                                              |
|------|-----------------------|----------------------------------------------------------|
| 200  | OK                    | Request succeeded                                        |
| 201  | Created               | Resource created successfully                            |
| 204  | No Content            | Request succeeded, no body returned (e.g. DELETE)        |
| 400  | Bad Request           | Invalid parameters or missing required fields            |
| 401  | Unauthorized          | Missing or invalid API key                               |
| 403  | Forbidden             | Valid key but insufficient scope                         |
| 404  | Not Found             | Resource does not exist                                  |
| 409  | Conflict              | Resource already exists (e.g. duplicate email)           |
| 429  | Too Many Requests     | Rate limit exceeded                                      |
| 500  | Internal Server Error | Something went wrong on NexAPI's side                    |

### Common Error Codes

| Error Code          | HTTP Status | Cause                                      |
|---------------------|-------------|--------------------------------------------|
| invalid_token       | 401         | API key is missing, malformed, or revoked  |
| insufficient_scope  | 403         | API key lacks required scope               |
| not_found           | 404         | The requested resource does not exist      |
| duplicate_email     | 409         | A user with this email already exists      |
| validation_error    | 400         | One or more fields failed validation       |
| rate_limit_exceeded | 429         | Too many requests, slow down               |
