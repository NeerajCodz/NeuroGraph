# Setup and Quickstart

## 1. Prerequisites

- Go 1.25+
- Running NeuroGraph backend service
- Optional MCP API key if using API key MCP mode

## 2. Build

Preferred scripted builds write artifacts to `cli/build/output` only.

PowerShell:

```powershell
Set-Location E:\codz\Projects\NeuroGraph\cli
.\builds\build.ps1 -Target current
```

Shell:

```bash
cd /path/to/NeuroGraph/cli
sh ./builds/build.sh current
```

Note for WSL users:

- `build.sh` runs inside Linux userspace and requires `go` installed in WSL.
- If Go is only installed on Windows, use `build.ps1` instead.

Build all cross-platform targets:

```powershell
.\builds\build.ps1 -Target all
```

```bash
sh ./builds/build.sh all
```

Clean build artifacts:

```powershell
.\builds\build.ps1 -Target clean
```

```bash
sh ./builds/build.sh clean
```

From repository root:

```powershell
Set-Location E:\codz\Projects\NeuroGraph\cli
go build ./cmd/neurograph
```

Direct `go build` without `-o` may produce binaries in `cli/`. Prefer scripts above to keep artifacts in `build/output`.

## 3. Basic usage

Show help:

```powershell
.\neurograph.exe --help
```

Show runtime status:

```powershell
.\neurograph.exe status
```

## 4. Authentication

Register:

```powershell
.\neurograph.exe auth register --email user@example.com --password "your-password" --full-name "User Name"
```

Login:

```powershell
.\neurograph.exe auth login --email user@example.com --password "your-password"
```

Current user:

```powershell
.\neurograph.exe auth me
```

Refresh token:

```powershell
.\neurograph.exe auth refresh
```

Logout:

```powershell
.\neurograph.exe auth logout
```

## 5. Configure backend and defaults

Set backend URL:

```powershell
.\neurograph.exe config set backend_url http://localhost:8000/api/v1
```

Set MCP URL:

```powershell
.\neurograph.exe config set mcp_url http://localhost:8000/api/v1/mcp
```

Set default layer:

```powershell
.\neurograph.exe config set layer workspace
```

Set default workspace:

```powershell
.\neurograph.exe config set workspace_id 00000000-0000-0000-0000-000000000000
```

Set default provider/model:

```powershell
.\neurograph.exe config set provider gemini
.\neurograph.exe config set model gemini-2.0-flash
```

Show config:

```powershell
.\neurograph.exe config show
```

## 6. Quick aliases

Quick chat:

```powershell
.\neurograph.exe ask "Summarize my project status"
```

Quick memory store:

```powershell
.\neurograph.exe remember "Project kickoff meeting is every Monday"
```

Quick memory recall:

```powershell
.\neurograph.exe recall "When is kickoff meeting?"
```

## 7. MCP usage

List tools (JWT auth):

```powershell
.\neurograph.exe mcp tools
```

Invoke tool via JWT:

```powershell
.\neurograph.exe mcp invoke --tool neurograph_recall --query "roadmap" --max-results 5
```

Set MCP API key and invoke via key:

```powershell
.\neurograph.exe config set mcp_api_key your-key
.\neurograph.exe mcp invoke-api-key --tool neurograph_status
```

## 8. Global MCP mode (`--mcp`)

Use the global `--mcp` flag to route supported high-level commands through MCP tools while keeping normal command UX.

Examples:

```powershell
.\neurograph.exe --mcp ask "Summarize workspace updates" --workspace-id 00000000-0000-0000-0000-000000000000 --layer workspace
.\neurograph.exe --mcp memory remember "Alice prefers async updates" --layer personal
.\neurograph.exe --mcp memory recall "What does Alice prefer?" --limit 5
.\neurograph.exe --mcp memory search "roadmap decisions" --limit 10
.\neurograph.exe --mcp chat send "Draft sprint plan" --workspace-id 00000000-0000-0000-0000-000000000000 --layer workspace
```
