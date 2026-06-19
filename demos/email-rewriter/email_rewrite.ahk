; Email Rewriter — Ctrl+Alt+R
; Grabs the EntryID from Outlook's current selection BEFORE launching Python,
; so the script never loses track of which email you had highlighted.

^!r::
    try {
        olApp := ComObjActive("Outlook.Application")
    } catch {
        MsgBox, Could not connect to Outlook. Make sure Classic Outlook is open and neither it nor AHK is running as administrator.
        return
    }

    entryID := ""

    try {
        inspector := olApp.ActiveInspector()
        if (inspector != "")
            entryID := inspector.CurrentItem.EntryID
    }

    if (entryID = "") {
        try {
            exp := olApp.Explorers.Count > 0 ? olApp.Explorers.Item(1) : ""
            if (exp != "" && exp.Selection.Count > 0)
                entryID := exp.Selection.Item(1).EntryID
        }
    }

    if (entryID = "") {
        MsgBox, No email selected. Highlight an email and try again.
        return
    }

    scriptPath := A_ScriptDir . "\email_rewrite.py"
    Run, pythonw "%scriptPath%" "%entryID%",, Hide
return
