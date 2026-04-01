# Testing and Validation

## 1. Added tests

### 1.1 `internal/api/client_test.go`

Covers:

- Auth header inclusion for authenticated requests
- API error extraction from backend `detail`
- Delete handling with empty response body
- Login form encoding behavior (`username` and `password`)
- Refresh behavior without auth header
- MCP invoke (JWT) and MCP invoke (API key) header behavior

### 1.2 `internal/config/config_test.go`

Covers:

- Default config values
- Load/save/reset with explicit config path
- Config path override behavior (`NEUROGRAPH_CONFIG`)
- Token set/clear/login-state behavior
- Invalid JSON load error handling

## 2. Executed validation commands

Executed during implementation:

```powershell
Set-Location E:\codz\Projects\NeuroGraph\cli
gofmt -w .
go test ./internal/api -count=1
go build ./cmd/neurograph
go run ./cmd/neurograph --help
```

Results:

- `go test ./internal/api -count=1` passed
- `go build ./cmd/neurograph` passed
- command tree rendered correctly in help output

## 3. Environment-specific issue for full test sweep

In this environment, full package execution of `go test ./...` is blocked by OS Application Control when executing generated test binaries for `internal/config`:

- Error observed: policy blocked execution of generated `config.test.exe`

This is an environment execution policy issue, not a compile/type issue in CLI source.

## 4. How to validate fully on a local machine

Run from `cli/`:

```powershell
go mod tidy
gofmt -w .
go test ./...
go build ./cmd/neurograph
```

Optional smoke tests:

```powershell
.\neurograph.exe --help
.\neurograph.exe status
.\neurograph.exe config show
```

If backend is running:

```powershell
.\neurograph.exe auth login --email user@example.com --password "..."
.\neurograph.exe auth me
.\neurograph.exe models providers
.\neurograph.exe mcp tools
```
