# Configuration

## 1. Config file location

Resolution order:

1. `NEUROGRAPH_CONFIG` environment variable
2. `%APPDATA%\neurograph\config.json`
3. `~\.neurograph\config.json`

Path command:

```powershell
.\neurograph.exe config path
```

## 2. Config schema

```json
{
  "backend_url": "http://localhost:8000/api/v1",
  "mcp_url": "http://localhost:8000/api/v1/mcp",
  "mcp_api_key": "",
  "auth": {
    "access_token": "",
    "refresh_token": "",
    "expires_at": 0
  },
  "defaults": {
    "layer": "personal",
    "workspace_id": "",
    "provider": "gemini",
    "model": "gemini-2.0-flash"
  }
}
```

## 3. Defaults

- `backend_url`: `http://localhost:8000/api/v1`
- `mcp_url`: `http://localhost:8000/api/v1/mcp`
- default layer: `personal`
- default provider: `gemini`
- default model: `gemini-2.0-flash`

## 4. Config keys supported by CLI

Set:

- `backend_url`, `backend`, `api_url`
- `mcp_url`, `mcp`
- `mcp_api_key`, `mcp_key`
- `layer`, `default_layer`
- `workspace`, `workspace_id`
- `provider`
- `model`

Get:

- same keys as above

## 5. Layer semantics

User-facing values:

- `personal`
- `workspace`
- `global`

Internal/backend mapping:

- For memory/graph: `workspace` becomes `tenant`
- For chat: `workspace` is used as-is

If workspace scope is selected, commands that require workspace context will validate that `workspace_id` is set.

## 6. Token handling

- Tokens are stored under `auth.access_token` and `auth.refresh_token`
- `expires_at` is unix seconds
- `IsLoggedIn()` rules:
  - no access token: not logged in
  - `expires_at == 0`: treated as logged in
  - otherwise current time must be before `expires_at`

## 7. Security notes

- Config file write mode is restricted (`0600`)
- `config show` masks token/key values
- Avoid sharing raw config with secrets in logs or screenshots
