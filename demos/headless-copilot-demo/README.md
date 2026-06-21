# Headless Copilot 365 Demo

This demo automates a headless Copilot for Microsoft 365 chat call.

## Recommendation

Use **Edge** (`--browser edge`). It is more reliable than Firefox for Microsoft 365 authentication and Copilot UI behavior.

## What It Does

- Reads prompt text from `Prompt.txt`
- Uses a persistent profile folder (`.copilot365-profile`) to reuse auth state
- Opens Copilot chat at `https://m365.cloud.microsoft/chat`
- If not signed in, shows a popup and opens a visible browser window for manual login
- If Playwright headed launch is blocked, it falls back to launching system Edge with the same profile directory
- Returns to headless mode, submits the prompt, monitors the DOM for the assistant response
- Verifies the prompt was posted by detecting a user-message echo before waiting for assistant output
- If generation is interrupted, attempts to click Continue automatically
- Strips common UI wrapper text (`You said`, `Copilot said`, `Stopped generating`) from captured output
- Writes output to `Results.md`

## Setup

From this folder:

```powershell
pip install -r requirements.txt
playwright install
```

## Run

```powershell
python copilot365_headless.py --browser edge --timeout-seconds 120
```

Stable command used successfully in this environment:

```powershell
python copilot365_headless.py --browser edge --timeout-seconds 120 --auth-attempts 3
```

Optional arguments:

- `--url` (default: `https://m365.cloud.microsoft/chat`)
- `--prompt-file` (default: `Prompt.txt`)
- `--results-file` (default: `Results.md`)
- `--profile-dir` (default: `.copilot365-profile`)
- `--browser edge|firefox` (default: `edge`)
- `--timeout-seconds` (default: `120`)
- `--log-file` (default: `run.log`)
- `--auth-attempts` (default: `2`)
- `--log-max-kb` (default: `512`)
- `--quiet` (hide live log echo; still writes `run.log`)
- `--min-response-chars` (default: `120`)
- `--stable-seconds` (default: `8`)

## Notes

- First run may require manual sign-in.
- During login, the browser window opens first. Complete sign-in and keep it open, then click OK so the script can verify chat readiness.
- Keep `.copilot365-profile` for persistent auth.
- If Copilot UI changes significantly, selectors in `copilot365_headless.py` may need adjustment.
- Check `run.log` for detailed execution steps if a run times out.
- If `run.log` reports no user-message echo after submit, the page likely changed send controls/selectors and needs a selector update.

For long or complex prompts, increase timeout and tighten completion behavior:

```powershell
python copilot365_headless.py --browser edge --timeout-seconds 180 --auth-attempts 3 --min-response-chars 300 --stable-seconds 10
```
