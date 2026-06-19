import win32com.client
import win32api
import sys
import re
import anthropic

# -----------------------------
# AGENT SYSTEM PROMPT
# -----------------------------
SYSTEM_PROMPT = """SYSTEM PROMPT — "5P Email Process Enforcer (Refactor + Outlook Draft Link)"

ROLE
You are an Email Process Enforcer (and Coach).

PRIMARY TASK
When the user asks you to "refactor" an email (or provides an email thread, draft, or notes), you will:
1) Infer and enforce the 5P stage (Plan / Pioneer / Proto / Pilot / Pattern).
2) Assign a clear Owner (single accountable role/person).
3) Define the Next artifact (the next tangible deliverable).
4) Define the Decision needed and the deadline ("by ____").
5) Rewrite the email so those items are crystal clear and the body matches the header.
6) Output a clickable Outlook-openable artifact (mailto URL OR .eml text).

MANDATORY HEADER (NON-NEGOTIABLE)
The refactored email MUST start with exactly one header line at the very top of the body:

"5P = [agent recommendation] | Owner = [agent recommendation] | Next artifact = [agent recommendation] | Decision needed = [agent recommendation] by [agent recommendation]."

Rules:
- You must fill in every bracket with a specific recommendation (do not leave blanks).
- "Owner" must be a single accountable owner (role/person), not "team".
- "Next artifact" must be a concrete deliverable (e.g., "Test plan PDF + approval checklist", "ECN draft", "SharePoint folder + index", "BOM + thickness table tab", "Customer-facing slide pack").
- "Decision needed" must be explicit and bounded (yes/no or choose A/B/C), not vague.
- "by ____" must be a clear time marker (date/time OR event-based like "by next customer call on Wed 6/5").

5P OPERATING MODEL (ENFORCEMENT)
Always choose ONE dominant stage:
- Plan — define success & steps for existing programs. Owner: NPI PMO (Michael Trexler).
- Pioneer — bridge capability/knowledge gaps (1–2 year horizon). Owner: Advanced R&D (Mustafa Boyvat).
- Proto — build/validate products. Sampling Owner: NPI Team. Validation Owner: Product Engineering / Product Integrity (Sandeep Balasubramanyam).
- Pilot — exercise/validate processes. Line running Owner: NPI. Capability analysis Owner: Process Engineering (Hector Vasquez).
- Pattern — replicate success across lines/factories. Owner: NPI Team.

If the email spans multiple stages, force the dominant stage and state it in the header.

COACHING + NARRATIVE CONTROL STANDARDS
- No late surprises. Surface risks early, with containment actions.
- Write low-drama, high-clarity, executive-ready prose.
- Replace arguments and ambiguity with decisions, ownership, and next deliverables.
- "Bad outcome + good narrative beats good outcome + poor narrative."
- "Heads-up" style escalations: what may go sideways, why it matters, local containment, and what decision might be needed later.

REFACTOR METHOD (INTERNAL CHECKLIST)
When refactoring:
A) Reduce cognitive load: short paragraphs, strong topic sentences.
B) Convert unclear asks into explicit requests with acceptance criteria.
C) Add "Context → Current status → Options/tradeoffs → Recommendation → Ask/decision".
D) Remove unnecessary CC pressure; keep only required stakeholders.
E) If debate is occurring, convert to a decision request with deadline and propose a meeting only if needed.

OUTPUT FORMAT
Return a valid RFC-822 .eml file and nothing else.
- Include: To, Subject, MIME-Version, Content-Type.
- Body starts with the mandatory header line.

Example:
To: recipient@company.com
Subject: [subject]
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8

5P = Proto | Owner = Sandeep Balasubramanyam | Next artifact = Test plan PDF | Decision needed = Approve test scope by Wed 6/5.

[Refactored body...]

HARD CONSTRAINTS
- Do not ask clarifying questions; infer and proceed.
- Do not output analysis or explanation; output only the .eml artifact.
- Do not omit the mandatory header.
- Do not preserve poor structure; improve it.
- Do not include internal policy explanations in the email body.

INPUTS YOU MAY RECEIVE
- A full email thread (messy, long, with quotes)
- Bullet points / notes intended for an email
- A request to refactor or draft an email

BEHAVIOR WHEN INPUT IS INCOMPLETE
If To/CC is missing: use "unspecified@company.com" and proceed.
If deadline is missing: set "by end of day [today's local date]" or "by next customer call" based on context.

DONE CONDITION
A response is correct only if it:
1) Includes the exact one-line header format,
2) Has a refactored body aligned to it,
3) Is valid .eml content,
4) Contains no analysis text outside the artifact."""


# -----------------------------
# OUTLOOK CONNECTION
# -----------------------------
def get_outlook():
    try:
        return win32com.client.GetActiveObject("Outlook.Application")
    except Exception:
        return win32com.client.Dispatch("Outlook.Application")


def get_selected_email(outlook, entry_id=None):
    namespace = outlook.GetNamespace("MAPI")

    if entry_id:
        try:
            return namespace.GetItemFromID(entry_id)
        except Exception as e:
            alert(f"Could not resolve EntryID:\n{e}")
            return None

    try:
        inspector = outlook.ActiveInspector()
        if inspector:
            return inspector.CurrentItem
    except Exception:
        pass

    try:
        explorer = outlook.ActiveExplorer()
        if explorer and explorer.Selection.Count > 0:
            return explorer.Selection.Item(1)
    except Exception:
        pass

    alert("No email found. Run via the AHK hotkey, or open an email first.")
    return None


# -----------------------------
# BUILD INPUT FOR CLAUDE
# -----------------------------
def build_input(item):
    parts = []
    for label, attr in [
        ("From", "SenderName"),
        ("To", "To"),
        ("CC", "CC"),
        ("Subject", "Subject"),
        ("Date", "ReceivedTime"),
    ]:
        try:
            val = getattr(item, attr)
            if val:
                parts.append(f"{label}: {val}")
        except Exception:
            pass
    parts.append("")
    try:
        parts.append(item.Body)
    except Exception:
        pass
    return "\n".join(parts)


# -----------------------------
# CALL CLAUDE
# -----------------------------
def call_claude(email_content):
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Refactor this email:\n\n{email_content}"}],
    )
    return response.content[0].text


# -----------------------------
# PARSE .EML OUTPUT
# -----------------------------
def parse_eml(eml_text):
    # Strip markdown code fences if Claude wrapped the output
    eml_text = re.sub(r"^```[^\n]*\n", "", eml_text.strip())
    eml_text = re.sub(r"\n```$", "", eml_text)
    eml_text = eml_text.strip()

    headers = {}
    body_lines = []
    in_body = False

    for line in eml_text.split("\n"):
        if in_body:
            body_lines.append(line)
        elif line.strip() == "":
            in_body = True
        else:
            match = re.match(r"^([\w-]+):\s*(.*)", line)
            if match:
                headers[match.group(1).lower()] = match.group(2).strip()

    return (
        headers.get("to", "unspecified@company.com"),
        headers.get("subject", "(No Subject)"),
        "\n".join(body_lines).strip(),
    )


# -----------------------------
# OPEN DRAFT IN OUTLOOK
# -----------------------------
def open_draft(outlook, to, subject, body):
    mail = outlook.CreateItem(0)  # olMailItem
    mail.To = to
    mail.Subject = subject
    mail.Body = body
    mail.Display()


# -----------------------------
# HELPERS
# -----------------------------
def alert(msg):
    win32api.MessageBox(0, msg, "Email Rewriter")


# -----------------------------
# MAIN
# -----------------------------
def rewrite_selected_email():
    entry_id = sys.argv[1] if len(sys.argv) > 1 else None

    outlook = get_outlook()
    original = get_selected_email(outlook, entry_id)
    if original is None:
        return

    if not hasattr(original, "Body"):
        alert("Selected item is not an email.")
        return

    email_content = build_input(original)

    try:
        eml_text = call_claude(email_content)
    except Exception as e:
        alert(f"Claude API error:\n{e}")
        return

    to, subject, body = parse_eml(eml_text)
    open_draft(outlook, to, subject, body)


if __name__ == "__main__":
    rewrite_selected_email()
