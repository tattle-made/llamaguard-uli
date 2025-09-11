# Content Moderation API

Base URL: `https://safety.tattle.co.in/`
Version: `0.0.1`

---

## Overview
This API flags abusive/harmful text content using a 3-step flow:
- Check against Tattle's slur list (moderate if matched)
- Check with Llama Guard model (moderate if unsafe)
- Check against a use case specific flagged list.

Responses are shaped consistently with a `meta` object, a `should_moderate` flag, a `reason` enum, and an HTTP `status_code` echoed in the body.

---

### Endpoints

#### 2) POST `/moderate`
- **Description**: Runs the content moderation flow on the provided text.
- **Request Body**:
```json
{
  "text": "string"
}
```

- **Response Body (Success/Handled Error)**:
```json
{
  "meta": {
    "response_time": 12.34,
    "flagged_words": ["string"]
  },
  "should_moderate": true || false,
  "reason": "safe | tattle_slur_list | llama_guard | flag_list",
  "status_code": 200
}
```

Below we explain the Input and Output structures in detail
---

### Request Schema

- **`text`** (string, required): Raw text to be evaluated. Empty or whitespace-only strings are treated as invalid input.

Example:
```json
{
  "text": "I think this message is fine."
}
```

---

### Response Schema

- **`meta`** (object, always present)
  - **`response_time`** (number): Time in milliseconds taken to process the request.
  - **`flagged_words`** (array of strings): Words that matched either the slur list or the flagged list (depending on the branch taken). Empty if none.

- **`should_moderate`** (boolean):
  - `true` → Content should be moderated/blocked.
  - `false` → Content is safe to allow.

- **`reason`** (enum string): One of the following values describing why the decision was made.
  - `tattle_slur_list` → Matched with Tattle's slur list. Text should be moderated.
  - `llama_guard` → Llama Guard model classified as unsafe. Text should be moderated.
  - `flag_list` → Matched with use-case specific flagged list of terms/words . This flag's indicates Human review is needed.
  - `safe` → Content assessed as safe.

- **`status_code`** (integer): Mirrors the HTTP status code. Common values:
  - `200`: Successful evaluation (including safe or moderate outcomes).
  - `400`: Bad input (e.g., empty/whitespace-only `text`).
  - `500`: Internal server error.

---

### Status Codes

- **200 OK**: Request processed successfully. `status_code` in body is `200`.
- **400 Bad Request**: Input was invalid (e.g., empty `text`). `status_code` in body is `400`.
- **500 Internal Server Error**: An unexpected error occurred. `status_code` in body is `500`.

---

### Examples

#### A) Slur matched (HTTP 200, moderate)
Request:
```bash
curl -X POST \
  http://localhost:8000/moderate \
  -H 'Content-Type: application/json' \
  -d '{"text": "contains badword"}'
```

Response 200:
```json
{
  "meta": {
    "response_time": 3.21,
    "flagged_words": ["badword"]
  },
  "should_moderate": true,
  "reason": "tattle_slur_list",
  "status_code": 200
}
```

#### B) Llama Guard unsafe (HTTP 200, moderate)
Request:
```bash
curl -X POST \
  http://localhost:8000/moderate \
  -H 'Content-Type: application/json' \
  -d '{"text": "some unsafe content"}'
```

Response 200:
```json
{
  "meta": {
    "response_time": 45.67,
    "flagged_words": []
  },
  "should_moderate": true,
  "reason": "llama_guard",
  "status_code": 200
}
```

#### C) Use-case specific Flagged list match (HTTP 200, safe)
Request:
```bash
curl -X POST \
  http://localhost:8000/moderate \
  -H 'Content-Type: application/json' \
  -d '{"text": "contains whitelist term"}'
```

Response 200:
```json
{
  "meta": {
    "response_time": 7.89,
    "flagged_words": ["whitelist"]
  },
  "should_moderate": false,
  "reason": "flag_list",
  "status_code": 200
}
```

#### D) Safe content (HTTP 200, safe)
Request:
```bash
curl -X POST \
  http://localhost:8000/moderate \
  -H 'Content-Type: application/json' \
  -d '{"text": "Hello there!"}'
```

Response 200:
```json
{
  "meta": {
    "response_time": 2.34,
    "flagged_words": []
  },
  "should_moderate": false,
  "reason": "safe",
  "status_code": 200
}
```

#### E) Empty input (HTTP 400)
Request:
```bash
curl -X POST \
  http://localhost:8000/moderate \
  -H 'Content-Type: application/json' \
  -d '{"text": "   "}'
```

Response 400:
```json
{
  "meta": {
    "response_time": 0.12,
    "flagged_words": []
  },
  "should_moderate": false,
  "reason": null,
  "status_code": 400
}
```

---

### Notes
- Word list files are read from `assets/slur-list.txt` and `assets/flagged-list.txt` if present.
- When Llama Guard is unavailable, the model check is skipped and processing continues based on lists.
- `response_time` is returned in milliseconds as a floating-point number.
