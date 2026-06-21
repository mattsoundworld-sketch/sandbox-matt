from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import BrowserContext, Error, Page, TimeoutError, sync_playwright


DEFAULT_URL = "https://m365.cloud.microsoft/chat"
DEFAULT_PROMPT_FILE = "Prompt.txt"
DEFAULT_RESULTS_FILE = "Results.md"
DEFAULT_PROFILE_DIR = ".copilot365-profile"
DEFAULT_LOG_FILE = "run.log"
DEFAULT_AUTH_ATTEMPTS = 2
DEFAULT_LOG_MAX_KB = 512
DEFAULT_MIN_RESPONSE_CHARS = 120
DEFAULT_STABLE_SECONDS = 8

LOG_ECHO_TO_STDOUT = True

# Broad selectors are intentional because Copilot web UI can change often.
COMPOSER_SELECTORS = [
    "textarea",
    "[contenteditable='true'][role='textbox']",
    "[contenteditable='true']",
]

STRICT_COMPOSER_SELECTORS = [
    "textarea[aria-label*='copilot' i]",
    "textarea[placeholder*='copilot' i]",
    "textarea[placeholder*='ask' i]",
    "[contenteditable='true'][aria-label*='copilot' i]",
    "[contenteditable='true'][aria-label*='ask' i]",
    "[role='textbox'][aria-label*='copilot' i]",
    "[role='textbox'][aria-label*='ask' i]",
    "[data-testid*='composer' i]",
]

AUTH_INDICATOR_SELECTORS = [
    "input[name='loginfmt']",
    "input[type='email']",
    "input[type='password']",
    "input[name='passwd']",
    "button:has-text('Sign in')",
    "text=Sign in to your account",
]

MESSAGE_SELECTORS = [
    "[data-testid*='assistant']",
    "[data-testid*='response']",
    "[data-testid*='message']",
    "[data-author-role='assistant']",
    "[data-message-author-role='assistant']",
    "[data-author='assistant']",
    ".assistant",
    "main article",
    "main [role='article']",
    "main .markdown",
    "main .prose",
    "article",
]

USER_MESSAGE_SELECTORS = [
    "[data-testid*='user']",
    "[data-author-role='user']",
    "[data-message-author-role='user']",
    "[data-author='user']",
    "[data-author='me']",
]

SEND_BUTTON_SELECTORS = [
    "button[aria-label*='send' i]",
    "button[aria-label*='submit' i]",
    "button[data-testid*='send' i]",
    "button[data-testid*='submit' i]",
    "button:has-text('Send')",
    "button:has-text('Submit')",
    "button[type='submit']",
    "[role='button'][aria-label*='send' i]",
]

STOP_BUTTON_SELECTORS = [
    "button[aria-label*='stop' i]",
    "button:has-text('Stop generating')",
    "button:has-text('Stop')",
    "[role='button'][aria-label*='stop' i]",
]

GENERATION_ACTIVE_SELECTORS = [
    "[aria-busy='true']",
    "text=Thinking",
    "text=Generating",
    "text=Working on it",
    "text=Drafting",
]

CONTINUE_BUTTON_SELECTORS = [
    "button:has-text('Continue generating')",
    "button:has-text('Continue')",
    "button:has-text('Keep generating')",
    "[role='button']:has-text('Continue generating')",
]

INTERRUPTION_MARKER_SELECTORS = [
    "text=Stopped generating",
    "button:has-text('Regenerate')",
]


def debug_log(log_file: Path, message: str) -> None:
    timestamp = dt.datetime.now().astimezone().isoformat()
    line = f"[{timestamp}] {message}"
    if LOG_ECHO_TO_STDOUT:
        print(line)
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def prepare_log_file(log_file: Path, max_kb: int) -> None:
    max_bytes = max(1, max_kb) * 1024
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if log_file.exists() and log_file.stat().st_size > max_bytes:
            rotated = log_file.with_name(log_file.name + ".1")
            if rotated.exists():
                rotated.unlink()
            log_file.replace(rotated)
        if not log_file.exists():
            log_file.write_text("", encoding="utf-8")
    except Exception:
        # Logging should never block automation.
        pass


def show_auth_popup(message: str) -> None:
    """Display a basic auth prompt box; fallback to console if tkinter is unavailable."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Copilot 365 Authentication Required", message)
        root.destroy()
    except Exception:
        print("\n[AUTH REQUIRED]", file=sys.stderr)
        print(message, file=sys.stderr)


def find_edge_executable() -> str | None:
    candidates = [
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
    ]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Microsoft/Edge/Application/msedge.exe")

    for path in candidates:
        if path.exists():
            return str(path)
    return None


def launch_system_browser_for_login(profile_dir: Path, url: str, browser: str) -> None:
    if browser != "edge":
        raise RuntimeError("System-browser fallback is currently supported for Edge only.")

    edge_exe = find_edge_executable()
    if not edge_exe:
        raise RuntimeError("Could not find msedge.exe on this machine.")

    subprocess.Popen(
        [
            edge_exe,
            f"--user-data-dir={profile_dir}",
            "--new-window",
            url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def first_visible(page: Page, selectors: list[str], timeout_ms: int = 5000):
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if locator.is_visible(timeout=250):
                    return selector, locator
            except Error:
                continue
        time.sleep(0.2)
    return None, None


def is_likely_chat_input(locator) -> bool:
    try:
        meta = locator.evaluate(
            """
            el => {
                const rect = el.getBoundingClientRect();
                return {
                    ariaLabel: (el.getAttribute('aria-label') || '').toLowerCase(),
                    placeholder: (el.getAttribute('placeholder') || '').toLowerCase(),
                    dataTestId: (el.getAttribute('data-testid') || '').toLowerCase(),
                    className: (el.getAttribute('class') || '').toLowerCase(),
                    id: (el.getAttribute('id') || '').toLowerCase(),
                    width: rect.width,
                    height: rect.height,
                };
            }
            """
        )
    except Error:
        return False

    text_blob = " ".join(
        [
            str(meta.get("ariaLabel", "")),
            str(meta.get("placeholder", "")),
            str(meta.get("dataTestId", "")),
            str(meta.get("className", "")),
            str(meta.get("id", "")),
        ]
    )

    good_terms = ["copilot", "ask", "chat", "message", "prompt", "composer"]
    bad_terms = ["search", "filter", "address", "find"]

    has_good = any(term in text_blob for term in good_terms)
    has_bad = any(term in text_blob for term in bad_terms)
    width = float(meta.get("width", 0) or 0)
    height = float(meta.get("height", 0) or 0)

    if has_good:
        return True

    # Fallback heuristic for unlabeled chat-like inputs near normal composer size.
    if not has_bad and width >= 260 and height >= 24:
        return True

    return False


def find_chat_composer(page: Page, timeout_ms: int = 8000):
    deadline = time.time() + (timeout_ms / 1000)
    selector_sets = [STRICT_COMPOSER_SELECTORS, COMPOSER_SELECTORS]

    while time.time() < deadline:
        for selectors in selector_sets:
            for selector in selectors:
                locator = page.locator(selector)
                try:
                    count = min(locator.count(), 8)
                except Error:
                    continue
                for i in range(count):
                    candidate = locator.nth(i)
                    try:
                        if not candidate.is_visible(timeout=150):
                            continue
                    except Error:
                        continue
                    if is_likely_chat_input(candidate):
                        return selector, candidate
        time.sleep(0.25)

    return None, None


def page_needs_auth(page: Page) -> bool:
    url = (page.url or "").lower()
    if "login.microsoftonline.com" in url or "signin" in url:
        return True

    for selector in AUTH_INDICATOR_SELECTORS:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=200):
                return True
        except Error:
            continue

    return False


def wait_until_chat_ready(page: Page, timeout_seconds: int = 300):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not page_needs_auth(page):
            selector, composer = find_chat_composer(page, timeout_ms=1200)
            if composer is not None:
                return selector, composer
        time.sleep(1)
    return None, None


def settle_auth_state(page: Page, seconds: int = 10) -> None:
    """Allow transient login redirects to settle before evaluating auth state."""
    deadline = time.time() + max(1, seconds)
    while time.time() < deadline:
        try:
            current = (page.url or "").lower()
        except Exception:
            break
        if "login.microsoftonline.com" not in current:
            break
        time.sleep(0.5)


def snapshot_messages(page: Page) -> list[str]:
    texts: list[str] = []
    for selector in MESSAGE_SELECTORS:
        locator = page.locator(selector)
        try:
            count = locator.count()
        except Error:
            continue
        if count == 0:
            continue
        for i in range(count):
            try:
                text = (locator.nth(i).inner_text(timeout=800) or "").strip()
            except Error:
                text = ""
            if text:
                texts.append(text)
        if texts:
            return texts
    return texts


# Fallback selectors used when first-class author metadata is not present.
def snapshot_user_messages(page: Page) -> list[str]:
    texts: list[str] = []
    for selector in USER_MESSAGE_SELECTORS:
        locator = page.locator(selector)
        try:
            count = locator.count()
        except Error:
            continue
        if count == 0:
            continue
        for i in range(count):
            try:
                text = (locator.nth(i).inner_text(timeout=500) or "").strip()
            except Error:
                text = ""
            if text:
                texts.append(text)
        if texts:
            return texts
    return texts


def click_send_button(page: Page) -> bool:
    if is_generation_active(page) or is_stop_button_present(page):
        return False

    for selector in SEND_BUTTON_SELECTORS:
        locator = page.locator(selector)
        try:
            count = min(locator.count(), 5)
        except Error:
            continue
        for i in range(count):
            button = locator.nth(i)
            try:
                if not button.is_visible(timeout=100):
                    continue
                if not button.is_enabled(timeout=100):
                    continue
                metadata = ""
                try:
                    metadata = (
                        button.get_attribute("aria-label")
                        or button.get_attribute("data-testid")
                        or button.inner_text(timeout=80)
                        or ""
                    ).lower()
                except Error:
                    metadata = ""
                if "stop" in metadata or "cancel" in metadata:
                    continue
                button.click(timeout=1000)
                return True
            except Error:
                continue
    return False


def is_stop_button_present(page: Page) -> bool:
    for selector in STOP_BUTTON_SELECTORS:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=80):
                return True
        except Error:
            continue
    return False


def click_send_near_composer(composer) -> bool:
    try:
        return bool(
            composer.evaluate(
                """
                (el) => {
                    const roots = [];
                    let node = el;
                    for (let i = 0; i < 6 && node; i++) {
                        roots.push(node);
                        node = node.parentElement;
                    }

                    const isClickable = (btn) => {
                        if (!btn) return false;
                        const style = window.getComputedStyle(btn);
                        if (style.visibility === 'hidden' || style.display === 'none') return false;
                        if (btn.disabled) return false;
                        const rect = btn.getBoundingClientRect();
                        return rect.width > 4 && rect.height > 4;
                    };

                    const score = (btn) => {
                        const text = [
                            btn.getAttribute('aria-label') || '',
                            btn.getAttribute('data-testid') || '',
                            btn.textContent || '',
                            btn.getAttribute('class') || '',
                        ].join(' ').toLowerCase();
                        let s = 0;
                        if (text.includes('send')) s += 5;
                        if (text.includes('submit')) s += 4;
                        if (text.includes('arrow')) s += 1;
                        if (btn.getAttribute('type') === 'submit') s += 3;
                        return s;
                    };

                    let best = null;
                    let bestScore = -1;
                    for (const root of roots) {
                        const buttons = root.querySelectorAll('button, [role="button"]');
                        for (const btn of buttons) {
                            if (!isClickable(btn)) continue;
                            const s = score(btn);
                            if (s > bestScore) {
                                best = btn;
                                bestScore = s;
                            }
                        }
                        if (best && bestScore >= 3) break;
                    }

                    if (!best) return false;
                    best.click();
                    return true;
                }
                """
            )
        )
    except Exception:
        return False


def wait_for_user_message_post(page: Page, baseline_count: int, timeout_seconds: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout_seconds:
        posted = snapshot_user_messages(page)
        if len(posted) > baseline_count:
            return True
        time.sleep(0.5)
    return False


def composer_text_length(composer) -> int:
    try:
        return int(
            composer.evaluate(
                """
                el => {
                    const tag = (el.tagName || '').toLowerCase();
                    if (tag === 'textarea' || tag === 'input') {
                        return (el.value || '').trim().length;
                    }
                    return (el.innerText || el.textContent || '').trim().length;
                }
                """
            )
        )
    except Exception:
        return 0


def wait_for_composer_nonempty(composer, timeout_seconds: int = 6) -> bool:
    start = time.time()
    while time.time() - start < timeout_seconds:
        if composer_text_length(composer) > 0:
            return True
        time.sleep(0.2)
    return False


def wait_for_composer_cleared(composer, timeout_seconds: int = 8) -> bool:
    start = time.time()
    while time.time() - start < timeout_seconds:
        if composer_text_length(composer) == 0:
            return True
        time.sleep(0.2)
    return False


def set_prompt_text(page: Page, prompt: str, composer, composer_selector: str) -> str:
    try:
        tag_name = composer.evaluate("el => el.tagName.toLowerCase()")
    except Error:
        tag_name = ""

    if tag_name == "textarea":
        composer.fill(prompt)
        try:
            composer.press("Enter")
            return "enter"
        except Error:
            if click_send_button(page):
                return "send-button"
            raise

    composer.click()
    # For contenteditable composers, keyboard typing is more reliable than fill().
    try:
        composer.press("Control+A")
        composer.press("Delete")
    except Error:
        pass

    try:
        page.keyboard.type(prompt, delay=5)
    except Error:
        pass

    try:
        composer.fill(prompt)
    except Error:
        page.evaluate(
            """
            (args) => {
                const [selector, value] = args;
                const el = document.querySelector(selector);
                if (!el) return;
                el.focus();
                el.textContent = value;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }
            """,
            [composer_selector, prompt],
        )

    if not wait_for_composer_nonempty(composer, timeout_seconds=6):
        raise TimeoutError("Composer did not accept prompt text.")

    submit_methods = [
        ("enter", lambda: composer.press("Enter")),
        ("ctrl-enter", lambda: composer.press("Control+Enter")),
        ("shift-enter", lambda: composer.press("Shift+Enter")),
        ("send-button", lambda: click_send_button(page)),
        ("send-near-composer", lambda: click_send_near_composer(composer)),
    ]

    for method_name, method_call in submit_methods:
        try:
            result = method_call()
            if result is False:
                continue
            if wait_for_composer_cleared(composer, timeout_seconds=4):
                return method_name
        except Error:
            continue

    # Return best-effort method name even if composer does not clear in this UI.
    return "enter"


def snapshot_fallback_blocks(page: Page) -> list[str]:
    selectors = [
        "main p",
        "main li",
        "main pre",
        "main div",
    ]
    blocks: list[str] = []
    for selector in selectors:
        locator = page.locator(selector)
        try:
            count = min(locator.count(), 200)
        except Error:
            continue
        for i in range(count):
            try:
                text = (locator.nth(i).inner_text(timeout=120) or "").strip()
            except Error:
                text = ""
            if len(text) >= 80:
                blocks.append(text)
        if blocks:
            return blocks
    return blocks


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def is_prompt_echo(candidate: str, prompt_text: str) -> bool:
    cand = normalize_text(candidate)
    prompt = normalize_text(prompt_text)
    if not cand:
        return True

    if cand.startswith("you said:") or cand.startswith("you asked:") or cand.startswith("prompt:"):
        return True

    if not prompt:
        return False

    # Reject direct restatements of the prompt or near-identical wrappers around it.
    if cand == prompt:
        return True
    if prompt in cand and len(cand) <= len(prompt) + 180:
        return True

    return False


def sanitize_captured_response(text: str, prompt_text: str) -> str:
    lines = [line.strip() for line in (text or "").splitlines()]
    out: list[str] = []
    prompt_norm = normalize_text(prompt_text)

    capture_started = False
    for line in lines:
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue

        low = line.lower()

        if "stopped generating" in low or low == "regenerate":
            break
        if low == "today":
            continue
        if low == "copilot":
            continue
        if low.startswith("you said:") or low.startswith("you asked:"):
            continue
        if low.startswith("copilot said:"):
            capture_started = True
            continue
        if low.startswith("reasoning completed in"):
            continue

        if prompt_norm and normalize_text(line) == prompt_norm:
            continue

        out.append(line)

    cleaned = "\n".join(out).strip()
    if cleaned:
        return cleaned

    # Fallback to trimmed raw text when sanitization over-prunes.
    return (text or "").strip()


def is_generation_active(page: Page) -> bool:
    for selector in GENERATION_ACTIVE_SELECTORS:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=80):
                return True
        except Error:
            continue
    return False


def best_candidate_from_page(
    page: Page,
    baseline: list[str],
    fallback_baseline: list[str],
    prompt_text: str,
) -> str:
    best = ""

    messages = snapshot_messages(page)
    if messages:
        baseline_last = baseline[-1] if baseline else ""
        for msg in messages:
            text = (msg or "").strip()
            if not text:
                continue
            if is_prompt_echo(text, prompt_text):
                continue
            if baseline_last and text == baseline_last:
                continue
            if len(text) > len(best):
                best = text

    fallback_blocks = snapshot_fallback_blocks(page)
    if len(fallback_blocks) > len(fallback_baseline):
        for block in fallback_blocks[len(fallback_baseline) :]:
            text = (block or "").strip()
            if is_prompt_echo(text, prompt_text):
                continue
            if len(text) > len(best):
                best = text

    return best


def generation_interrupted(page: Page) -> bool:
    for selector in INTERRUPTION_MARKER_SELECTORS:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=80):
                return True
        except Error:
            continue
    return False


def try_continue_generation(page: Page, log_file: Path) -> bool:
    for selector in CONTINUE_BUTTON_SELECTORS:
        locator = page.locator(selector)
        try:
            count = min(locator.count(), 3)
        except Error:
            continue
        for i in range(count):
            button = locator.nth(i)
            try:
                if not button.is_visible(timeout=100):
                    continue
                if not button.is_enabled(timeout=100):
                    continue
                button.click(timeout=1200)
                debug_log(log_file, f"Clicked continue control: {selector}")
                return True
            except Error:
                continue

    debug_log(log_file, "Generation interruption detected, but no continue control was clickable.")
    return False


def wait_for_new_response(
    page: Page,
    baseline: list[str],
    timeout_seconds: int,
    min_response_chars: int,
    stable_seconds: int,
    prompt_text: str,
    log_file: Path,
) -> str:
    start = time.time()
    fallback_baseline = snapshot_fallback_blocks(page)
    best_seen = ""
    current_observed = ""
    last_change_time = time.time()
    poll_seconds = 1.5
    continue_attempts = 0
    max_continue_attempts = 3

    while time.time() - start < timeout_seconds:
        candidate_raw = best_candidate_from_page(
            page,
            baseline=baseline,
            fallback_baseline=fallback_baseline,
            prompt_text=prompt_text,
        )
        candidate = sanitize_captured_response(candidate_raw, prompt_text)
        if candidate and len(candidate) > len(best_seen):
            best_seen = candidate
            debug_log(log_file, f"Response length grew to {len(best_seen)} characters")

        if candidate != current_observed:
            current_observed = candidate
            last_change_time = time.time()

        stable_for = time.time() - last_change_time
        generation_active = is_generation_active(page)
        stop_visible = is_stop_button_present(page)

        if generation_interrupted(page) and continue_attempts < max_continue_attempts:
            continue_attempts += 1
            debug_log(log_file, f"Interruption detected; continue attempt {continue_attempts}/{max_continue_attempts}")
            if try_continue_generation(page, log_file):
                last_change_time = time.time()
                time.sleep(1.5)
                continue

        if best_seen and stable_for >= stable_seconds:
            # Preferred graceful completion: response stabilized and no explicit stop control remains.
            if not stop_visible and (len(best_seen) >= min_response_chars):
                debug_log(log_file, "Returning due to stable response with no stop control visible.")
                return best_seen.strip()

            # Fallback graceful completion when generation indicators are noisy/sticky.
            prolonged_stable = max(stable_seconds * 3, 30)
            if stable_for >= prolonged_stable:
                debug_log(log_file, "Returning due to prolonged stable response (indicator likely stale).")
                return best_seen.strip()

            # If clearly idle and stable, return even for short-but-complete answers.
            if not generation_active and not stop_visible and (time.time() - start) >= (timeout_seconds / 3):
                debug_log(log_file, "Returning due to idle stable response.")
                return best_seen.strip()

        time.sleep(poll_seconds)

    if best_seen:
        debug_log(log_file, f"Timed out, returning best response seen ({len(best_seen)} chars)")
        return best_seen.strip()

    raise TimeoutError(f"Timed out waiting for Copilot response after {timeout_seconds} seconds.")


def open_context(
    profile_dir: Path,
    headless: bool,
    browser: str,
    timeout_ms: int,
    pw,
) -> BrowserContext:
    launch_args = {
        "headless": headless,
        "args": ["--disable-blink-features=AutomationControlled"],
        "viewport": {"width": 1440, "height": 900},
    }

    if browser == "edge":
        launch_args["channel"] = "msedge"

    context = pw.chromium.launch_persistent_context(str(profile_dir), **launch_args)
    context.set_default_timeout(timeout_ms)
    return context


def open_context_with_retry(
    profile_dir: Path,
    headless: bool,
    browser: str,
    timeout_ms: int,
    pw,
    log_file: Path,
    attempts: int = 3,
) -> BrowserContext:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            debug_log(
                log_file,
                f"Opening {'headless' if headless else 'headed'} context (attempt {attempt}/{attempts})",
            )
            return open_context(
                profile_dir=profile_dir,
                headless=headless,
                browser=browser,
                timeout_ms=timeout_ms,
                pw=pw,
            )
        except Exception as ex:
            last_error = ex
            debug_log(log_file, f"Context open failed on attempt {attempt}: {ex}")
            if attempt < attempts:
                show_auth_popup(
                    "Browser profile is still in use.\n\n"
                    "Please close any visible Edge windows opened for this run, then click OK to retry."
                )

    assert last_error is not None
    raise last_error


def ensure_authenticated(
    page: Page,
    profile_dir: Path,
    browser: str,
    timeout_ms: int,
    url: str,
    pw,
    log_file: Path,
) -> None:
    needs_auth = page_needs_auth(page)
    _, composer = find_chat_composer(page, timeout_ms=12000)

    debug_log(log_file, f"Initial URL: {page.url}")
    debug_log(log_file, f"Auth indicators detected: {needs_auth}")
    debug_log(log_file, f"Composer detected before auth flow: {composer is not None}")

    if composer is not None and not needs_auth:
        return

    debug_log(log_file, "Authentication required. Starting system Edge sign-in flow.")

    page.context.close()
    # Manual login path is intentionally explicit to keep auth deterministic.
    try:
        login_context = open_context_with_retry(
            profile_dir=profile_dir,
            headless=False,
            browser=browser,
            timeout_ms=timeout_ms,
            pw=pw,
            log_file=log_file,
            attempts=2,
        )
        login_page = login_context.pages[0] if login_context.pages else login_context.new_page()
        login_page.goto(url, wait_until="domcontentloaded")
        login_page.bring_to_front()
        debug_log(log_file, f"Launched headed Edge for sign-in: {login_page.url}")

        authenticated = False
        for prompt_try in range(1, 4):
            show_auth_popup(
                "Sign-in is required. A browser window is already open using your persistent profile.\n\n"
                "Complete sign-in in that window and keep it open, then click OK to verify."
            )

            # User may have closed the window; recreate if needed.
            if login_context.pages:
                login_page = login_context.pages[0]
            else:
                login_page = login_context.new_page()
                login_page.goto(url, wait_until="domcontentloaded")
                login_page.bring_to_front()

            selector, login_composer = wait_until_chat_ready(login_page, timeout_seconds=45)
            if login_composer is not None:
                debug_log(log_file, f"Authentication verified in headed window using selector: {selector}")
                authenticated = True
                break

            debug_log(log_file, f"Auth not verified after prompt attempt {prompt_try}/3")

        try:
            login_context.close()
        except Exception:
            pass

        if not authenticated:
            raise TimeoutError("Authentication could not be verified in headed login flow.")
    except Exception as ex:
        debug_log(log_file, f"Headed login path failed, falling back to system Edge: {ex}")
        launch_system_browser_for_login(profile_dir=profile_dir, url=url, browser=browser)
        debug_log(log_file, "Launched system Edge for sign-in.")
        show_auth_popup(
            "Sign-in is required. An Edge window is already open using your persistent profile.\n\n"
            "1) Complete sign-in\n"
            "2) Confirm Copilot chat is visible\n"
            "3) Leave the window open\n"
            "4) Click OK to continue"
        )


def write_results(results_file: Path, prompt: str, response: str, url: str, browser: str) -> None:
    timestamp = dt.datetime.now().astimezone().isoformat()
    output = (
        f"# Copilot 365 Result\n\n"
        f"- Timestamp: {timestamp}\n"
        f"- URL: {url}\n"
        f"- Browser: {browser}\n\n"
        "## Prompt\n\n"
        f"```text\n{prompt.strip()}\n```\n\n"
        "## Response\n\n"
        f"{response.strip()}\n"
    )
    results_file.write_text(output, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a headless Copilot 365 chat prompt and save response to Results.md"
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Copilot 365 chat URL")
    parser.add_argument(
        "--prompt-file",
        default=DEFAULT_PROMPT_FILE,
        help="Path to Prompt.txt containing the prompt text",
    )
    parser.add_argument(
        "--results-file",
        default=DEFAULT_RESULTS_FILE,
        help="Path to output markdown file for response",
    )
    parser.add_argument(
        "--profile-dir",
        default=DEFAULT_PROFILE_DIR,
        help="Persistent browser profile directory to reuse authentication",
    )
    parser.add_argument(
        "--browser",
        choices=["edge", "firefox"],
        default="edge",
        help="Browser mode. Edge is recommended for Microsoft 365 compatibility.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Seconds to wait for Copilot response before failing",
    )
    parser.add_argument(
        "--log-file",
        default=DEFAULT_LOG_FILE,
        help="Path to run log file",
    )
    parser.add_argument(
        "--auth-attempts",
        type=int,
        default=DEFAULT_AUTH_ATTEMPTS,
        help="How many auth-check cycles to run before failing",
    )
    parser.add_argument(
        "--log-max-kb",
        type=int,
        default=DEFAULT_LOG_MAX_KB,
        help="Rotate run.log when it exceeds this size in KB",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress log echo to stdout while still writing to run.log",
    )
    parser.add_argument(
        "--min-response-chars",
        type=int,
        default=DEFAULT_MIN_RESPONSE_CHARS,
        help="Minimum response length before considering completion (best-effort)",
    )
    parser.add_argument(
        "--stable-seconds",
        type=int,
        default=DEFAULT_STABLE_SECONDS,
        help="Seconds with no response change before considering completion",
    )
    return parser.parse_args()


def main() -> int:
    # CORE: Parse CLI options that define runtime behavior (URLs, files, timeouts, retry knobs).
    args = parse_args()

    # CORE: Configure whether debug logs are echoed to stdout for this run.
    # BACKUP / SAFETY: Even in quiet mode, logs still go to run.log for post-run diagnostics.
    global LOG_ECHO_TO_STDOUT
    LOG_ECHO_TO_STDOUT = not args.quiet

    # CORE: Resolve all runtime paths relative to this script so calls are stable from any CWD.
    script_dir = Path(__file__).resolve().parent
    prompt_file = (script_dir / args.prompt_file).resolve()
    results_file = (script_dir / args.results_file).resolve()
    profile_dir = (script_dir / args.profile_dir).resolve()
    log_file = (script_dir / args.log_file).resolve()

    # CORE: Ensure persistent profile directory exists to preserve auth/session state across runs.
    profile_dir.mkdir(parents=True, exist_ok=True)

    # BACKUP / SAFETY: Prepare/rotate logs to avoid unbounded growth and keep latest run visible.
    prepare_log_file(log_file, max_kb=args.log_max_kb)
    debug_log(log_file, "----- New run started -----")

    # CORE: Validate prompt input file before launching browser automation.
    # BACKUP / SAFETY: Fail fast with explicit messages to avoid ambiguous browser-side failures.
    if not prompt_file.exists():
        print(f"Prompt file not found: {prompt_file}", file=sys.stderr)
        return 1

    # CORE: Read prompt fresh on each run so edits to Prompt.txt are picked up immediately.
    prompt_text = prompt_file.read_text(encoding="utf-8").strip()

    # BACKUP / SAFETY: Prevent empty submissions that can produce undefined UI behavior.
    if not prompt_text:
        print("Prompt file is empty.", file=sys.stderr)
        return 1

    # CORE: Normalize runtime tuning inputs for downstream wait and completion logic.
    # BACKUP / SAFETY: Clamp to sane minimums to avoid invalid/degenerate waits.
    timeout_ms = max(1000, args.timeout_seconds * 1000)
    auth_attempts = max(1, args.auth_attempts)
    min_response_chars = max(1, args.min_response_chars)
    stable_seconds = max(2, args.stable_seconds)

    # CORE: Start a single Playwright session for this run and perform auth + prompt/response workflow.
    with sync_playwright() as pw:
        context: BrowserContext | None = None

        # CORE: Auth cycle loop. Each cycle tries to reach authenticated chat and execute one prompt.
        # BACKUP / SAFETY: Multiple cycles recover from transient auth redirects/session glitches.
        for auth_try in range(1, auth_attempts + 1):
            context = open_context_with_retry(
                profile_dir=profile_dir,
                headless=True,
                browser=args.browser,
                timeout_ms=timeout_ms,
                pw=pw,
                log_file=log_file,
            )
            try:
                # CORE: Navigate to chat and allow redirect/auth state to settle before checks.
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(args.url, wait_until="domcontentloaded")
                settle_auth_state(page, seconds=10)
                debug_log(log_file, f"Loaded URL in headless mode (auth cycle {auth_try}/{auth_attempts}): {page.url}")

                # CORE: If auth is still required, trigger the manual verification flow.
                # BACKUP / SAFETY: Re-enter next auth cycle after verification attempt.
                if page_needs_auth(page):
                    debug_log(log_file, "Auth indicators present, initiating manual sign-in flow.")
                    ensure_authenticated(
                        page=page,
                        profile_dir=profile_dir,
                        browser=args.browser,
                        timeout_ms=timeout_ms,
                        url=args.url,
                        pw=pw,
                        log_file=log_file,
                    )
                    context = None
                    continue

                # CORE: Discover the active chat composer for prompt entry.
                # BACKUP / SAFETY: Hard-fail with explicit error if the chat input cannot be found.
                composer_selector, composer = find_chat_composer(page, timeout_ms=18000)
                if composer is None:
                    debug_log(log_file, "Composer not found on authenticated page.")
                    raise TimeoutError("Could not find Copilot prompt input on page.")

                debug_log(log_file, f"Composer found using selector: {composer_selector}")

                # CORE: Capture pre-submit baselines to detect new user/assistant content after submit.
                baseline = snapshot_messages(page)
                baseline_user = snapshot_user_messages(page)
                debug_log(log_file, f"Baseline assistant/message candidates: {len(baseline)}")
                debug_log(log_file, f"Baseline user-message candidates: {len(baseline_user)}")

                # CORE: Submit the prompt via the detected composer.
                # BACKUP / SAFETY: Internal submit helper uses multiple methods (enter/button heuristics).
                submit_method = set_prompt_text(page, prompt_text, composer, composer_selector)
                debug_log(log_file, f"Prompt submitted using: {submit_method}")

                # CORE: Prefer explicit user-echo confirmation that the prompt posted to the thread.
                user_echo_detected = wait_for_user_message_post(
                    page, baseline_count=len(baseline_user), timeout_seconds=15
                )
                if not user_echo_detected:
                    # BACKUP / SAFETY: If echo is missing, infer submit state from generation/stop/composer signals
                    # and only retry a click when it is safe (to avoid accidentally pressing Stop generating).
                    generation_started = is_generation_active(page) or is_stop_button_present(page)
                    composer_has_text = composer_text_length(composer) > 0
                    if generation_started:
                        debug_log(
                            log_file,
                            "User echo not detected, but generation appears active; not retrying submit click.",
                        )
                    elif not composer_has_text:
                        debug_log(
                            log_file,
                            "User echo not detected, but composer is empty; treating submit as sent.",
                        )
                    else:
                        debug_log(log_file, "User message echo not detected after submit; retrying via send-button click.")
                        if click_send_button(page):
                            user_echo_detected = wait_for_user_message_post(
                                page, baseline_count=len(baseline_user), timeout_seconds=15
                            )
                        else:
                            debug_log(
                                log_file,
                                "Safe send retry not available; continuing to assistant response wait.",
                            )

                # CORE: Record whether user-echo proof was seen. Missing echo is tolerated in some UI variants.
                if user_echo_detected:
                    debug_log(log_file, "User message echo detected.")
                else:
                    debug_log(
                        log_file,
                        "User message echo still not detected; waiting for assistant response as fallback.",
                    )

                # CORE: Monitor and collect assistant output until graceful completion rules are met.
                # BACKUP / SAFETY: Response watcher includes interruption handling, sanitization, and timeout fallback.
                response = wait_for_new_response(
                    page,
                    baseline,
                    timeout_seconds=args.timeout_seconds,
                    min_response_chars=min_response_chars,
                    stable_seconds=stable_seconds,
                    prompt_text=prompt_text,
                    log_file=log_file,
                )

                # CORE: Persist normalized run artifact for downstream use.
                write_results(results_file, prompt_text, response, args.url, args.browser)
                debug_log(log_file, f"Response captured with {len(response)} characters")

                # CORE: Successful run exit.
                print(f"Saved response to: {results_file}")
                return 0
            finally:
                # BACKUP / SAFETY: Always close context created in this cycle to release profile/driver resources.
                if context is not None:
                    context.close()

        # BACKUP / SAFETY: If all auth cycles are exhausted, fail with explicit remediation guidance.
        raise TimeoutError(
            "Authentication is still required after manual sign-in attempts. "
            "Check run.log and confirm login completes in the opened Edge window."
        )


if __name__ == "__main__":
    sys.exit(main())
