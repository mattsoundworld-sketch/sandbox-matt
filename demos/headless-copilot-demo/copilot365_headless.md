# Prompt to Generate a Robust Copilot 365 Headless Automation Script

Use this prompt with a coding model to recreate the full functionality.

## Copy/Paste Prompt

You are an expert Python automation engineer. Build a production-ready script that performs a headless call to Copilot for Microsoft 365 chat with robust authentication, response capture, and safety controls.

### Objective
Create a Python script that:
- Opens Copilot 365 chat at https://m365.cloud.microsoft/chat
- Reads prompt content from Prompt.txt on every run
- Submits that prompt in the chat composer
- Monitors DOM output until response completion
- Writes final response to Results.md
- Uses a persistent browser profile folder so authentication is reused across runs
- Handles manual authentication if needed with desktop popup guidance
- Uses extensive resilience against UI changes and interruptions

### Browser Recommendation
- Default browser choice must be Edge (recommended for Microsoft 365 compatibility)
- Provide optional Firefox mode as a secondary option

### Required Files
Implement these files in the same folder:
1. copilot365_headless.py
2. requirements.txt (include playwright)
3. README.md with setup, run instructions, options, and troubleshooting

### Script Requirements
Use Playwright sync API in Python.

#### Input and Output
- Input prompt file: Prompt.txt
- Output file: Results.md
- Log file: run.log
- Persistent profile directory: .copilot365-profile

#### CLI Arguments
Support these arguments:
- --url (default: https://m365.cloud.microsoft/chat)
- --prompt-file (default: Prompt.txt)
- --results-file (default: Results.md)
- --profile-dir (default: .copilot365-profile)
- --browser (choices: edge, firefox; default edge)
- --timeout-seconds (default 120)
- --log-file (default run.log)
- --auth-attempts (default 2 or more)
- --log-max-kb (default 512)
- --quiet (suppress stdout log echo but keep file logging)
- --min-response-chars (best-effort threshold)
- --stable-seconds (stable-output completion threshold)

### Authentication Behavior
Implement reliable authentication handling:
- Detect auth-required state via URL and login controls (login.microsoftonline.com, email/password/sign-in elements)
- If auth is required:
  - Open a headed browser context using the same persistent profile
  - Show a popup instructing user to sign in and keep the window open
  - Verify auth is complete in the headed window by detecting chat composer readiness
  - Retry verification prompts if needed
- If headed verification path fails, fallback to launching system Edge executable with the same profile and prompt user via popup
- Do not proceed until auth is verified or attempts are exhausted

### Safety and Resilience Rules
Implement these safeguards:
- Never use destructive git/system commands
- Retry browser context opening when profile is locked
- Never let logging failures stop script execution
- Rotate run.log when size exceeds threshold
- Avoid false positives from random text inputs by using strict composer detection + heuristics

### Prompt Submission Rules
- Fill or type into the composer reliably (contenteditable and textarea support)
- Use multiple submit methods in order (Enter, Ctrl+Enter, Shift+Enter, send button fallback)
- Detect whether generation started before retry-clicking send
- IMPORTANT: do not click submit retry if button has become stop/cancel state
- Explicitly detect stop-generating controls and avoid clicking them during submit retry logic

### Response Monitoring Rules
- Capture assistant response from robust selector sets with fallback scanning
- Track growth of best response length over time
- Sanitize captured output to remove wrapper UI text (for example: You said, Copilot said, Today, Reasoning completed, Regenerate, Stopped generating)
- Detect interruption markers (Stopped generating, Regenerate)
- Attempt to click Continue generating safely if available
- Use graceful completion logic:
  - Return when response is stable for stable-seconds and stop control is no longer visible
  - Return on prolonged stable state even if indicators are noisy/sticky
  - Return on idle-stable states for shorter responses
  - If timeout is reached but content exists, return best seen content

### Result File Format
Write Results.md in markdown with:
- Title: Copilot 365 Result
- Timestamp
- URL
- Browser
- Prompt section in fenced text block
- Response section with cleaned final answer text

### Logging Requirements
Log each major state transition with timestamps:
- Context launch attempts
- URL loads
- Auth detection and auth flow transitions
- Composer detection
- Submit method used
- User echo detection outcomes
- Response length growth events
- Interruption/continue attempts
- Exact reason for graceful completion or timeout fallback

### Code Quality Requirements
- Keep code in one main script file for operational simplicity
- Add clear comments that label each block as either:
  - CORE
  - BACKUP / SAFETY
- Keep implementation deterministic and maintainable
- Handle exceptions with actionable messages

### Acceptance Criteria
The script is successful when:
1. It reuses authentication via persistent profile across runs
2. It prompts for manual sign-in only when needed
3. It can recover from transient auth/profile lock issues
4. It submits prompt without accidentally triggering stop-generation
5. It captures long responses without premature truncation
6. It exits gracefully when response completion is detected
7. It writes Results.md and run.log for each run
8. It can be re-run repeatedly with updated Prompt.txt content each time

### Setup and Run
README must include:
- pip install -r requirements.txt
- playwright install
- Recommended run command for long prompts
- Troubleshooting guidance for auth loops, interrupted generation, and selector drift

Build this as production-style automation, not a toy demo.