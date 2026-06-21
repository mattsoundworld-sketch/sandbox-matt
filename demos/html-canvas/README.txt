HTML Notes Canvas Prototype

What this is
- A browser-based note canvas prototype.
- Notes can be added, edited, deleted, and moved around freely.
- Notes use a consistent fixed block size.
- New notes use user-selected color.
- Canvas can be split into columns, rows, or a row/column grid.
- Split sections can show optional titles.
- Entire canvas state persists in browser localStorage.
- Core actions are exposed in a top navigation bar.
- Any action requiring user input opens a popup dialog.
- Canvas title is editable from the nav bar.
- Section titles are editable with a popup editor.
- Notes support title + body, and collapse to about half-height until hover/focus.

Files
- index.html
- styles.css
- app.js

How to run
1. Open index.html in any modern browser.
2. Use the top navigation bar:
  - Canvas title button (left): opens popup to edit canvas title.
  - Add Note: opens popup for note title, color, and optional initial text.
  - Configure Layout: opens popup for mode, counts, and title visibility.
  - Edit Section Titles: opens popup to rename section labels for current layout.
  - Clear Layout: returns to free canvas mode.
  - Clear Canvas State: removes all notes and saved layout.

State persistence
- State key: html-canvas-state-v1
- Stored data includes:
  - Canvas title
  - Notes (position, color, text)
  - Note title
  - Current selected layout mode and split settings
  - Custom section titles

Notes
- Drag notes by clicking/dragging the note card body (not the text area).
- Selected note has a visual outline.
- Notes are compact by default and expand when hovered or focused.
