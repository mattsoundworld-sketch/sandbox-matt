const STORAGE_KEY = "html-canvas-state-v1";

const NOTE_WIDTH = 210;
const NOTE_HEIGHT = 160;

const state = {
  canvasTitle: "Notes Canvas",
  notes: [],
  selectedNoteId: null,
  layout: {
    mode: "none",
    columns: 3,
    rows: 2,
    showTitles: true,
    titles: {},
  },
};

const els = {
  canvas: document.getElementById("canvas"),
  addNote: document.getElementById("addNote"),
  openLayout: document.getElementById("openLayout"),
  editSectionTitles: document.getElementById("editSectionTitles"),
  editCanvasTitle: document.getElementById("editCanvasTitle"),
  clearAll: document.getElementById("clearAll"),
  noteDialog: document.getElementById("noteDialog"),
  noteDialogForm: document.getElementById("noteDialogForm"),
  cancelNoteDialog: document.getElementById("cancelNoteDialog"),
  newNoteTitle: document.getElementById("newNoteTitle"),
  noteColor: document.getElementById("noteColor"),
  newNoteText: document.getElementById("newNoteText"),
  canvasTitleDialog: document.getElementById("canvasTitleDialog"),
  canvasTitleDialogForm: document.getElementById("canvasTitleDialogForm"),
  cancelCanvasTitleDialog: document.getElementById("cancelCanvasTitleDialog"),
  canvasTitleInput: document.getElementById("canvasTitleInput"),
  sectionTitlesDialog: document.getElementById("sectionTitlesDialog"),
  sectionTitlesDialogForm: document.getElementById("sectionTitlesDialogForm"),
  cancelSectionTitlesDialog: document.getElementById("cancelSectionTitlesDialog"),
  sectionTitlesFields: document.getElementById("sectionTitlesFields"),
  layoutDialog: document.getElementById("layoutDialog"),
  layoutDialogForm: document.getElementById("layoutDialogForm"),
  cancelLayoutDialog: document.getElementById("cancelLayoutDialog"),
  layoutMode: document.getElementById("layoutMode"),
  columnCount: document.getElementById("columnCount"),
  rowCount: document.getElementById("rowCount"),
  showTitles: document.getElementById("showTitles"),
  clearLayout: document.getElementById("clearLayout"),
  noteTemplate: document.getElementById("noteTemplate"),
};

let drag = null;

function uid() {
  return `${Date.now()}-${Math.floor(Math.random() * 10000)}`;
}

function applySelectionStyles() {
  const noteEls = Array.from(els.canvas.querySelectorAll(".note"));
  noteEls.forEach((el) => {
    const id = el.dataset.noteId;
    if (id === state.selectedNoteId) {
      el.classList.add("selected");
    } else {
      el.classList.remove("selected");
    }
  });
}

function setSelectedNote(id) {
  state.selectedNoteId = id;
  applySelectionStyles();
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function load() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return;
  }

  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed.notes)) {
      state.notes = parsed.notes.map((note) => ({
        ...note,
        title: note.title || "",
        text: note.text || "",
      }));
    }
    if (typeof parsed.canvasTitle === "string" && parsed.canvasTitle.trim()) {
      state.canvasTitle = parsed.canvasTitle;
    }
    if (parsed.layout) {
      state.layout = {
        ...state.layout,
        ...parsed.layout,
        titles: parsed.layout.titles || {},
      };
    }
  } catch {
    localStorage.removeItem(STORAGE_KEY);
  }
}

function renderCanvasTitle() {
  els.editCanvasTitle.textContent = state.canvasTitle || "Notes Canvas";
}

function updateLayoutControls() {
  els.layoutMode.value = state.layout.mode;
  els.columnCount.value = state.layout.columns;
  els.rowCount.value = state.layout.rows;
  els.showTitles.checked = state.layout.showTitles;

  const mode = state.layout.mode;
  els.columnCount.disabled = mode === "rows" || mode === "none";
  els.rowCount.disabled = mode === "columns" || mode === "none";
}

function sectionTitle(mode, row, col) {
  const key = `${row}-${col}`;
  const custom = state.layout.titles?.[key];
  if (custom && custom.trim()) {
    return custom;
  }
  if (mode === "columns") {
    return `Column ${col + 1}`;
  }
  if (mode === "rows") {
    return `Row ${row + 1}`;
  }
  if (mode === "grid") {
    return `R${row + 1} C${col + 1}`;
  }
  return "";
}

function renderLayoutOverlay() {
  const existing = els.canvas.querySelector(".layout-overlay");
  if (existing) {
    existing.remove();
  }

  if (state.layout.mode === "none") {
    return;
  }

  const overlay = document.createElement("div");
  overlay.className = "layout-overlay";

  const mode = state.layout.mode;
  const columns = mode === "rows" ? 1 : state.layout.columns;
  const rows = mode === "columns" ? 1 : state.layout.rows;

  const colSize = 100 / columns;
  const rowSize = 100 / rows;

  for (let r = 0; r < rows; r += 1) {
    for (let c = 0; c < columns; c += 1) {
      const cell = document.createElement("div");
      cell.className = "layout-cell";
      cell.style.left = `${c * colSize}%`;
      cell.style.top = `${r * rowSize}%`;
      cell.style.width = `${colSize}%`;
      cell.style.height = `${rowSize}%`;

      if (state.layout.showTitles) {
        const title = document.createElement("div");
        title.className = "layout-title";
        title.textContent = sectionTitle(mode, r, c);
        cell.appendChild(title);
      }

      overlay.appendChild(cell);
    }
  }

  els.canvas.appendChild(overlay);
}

function addNote() {
  const rect = els.canvas.getBoundingClientRect();
  const note = {
    id: uid(),
    x: 20 + (state.notes.length % 6) * 24,
    y: 20 + (state.notes.length % 6) * 24,
    color: els.noteColor.value,
    title: (els.newNoteTitle.value || "").trim(),
    text: (els.newNoteText.value || "").trim(),
  };

  note.x = clamp(note.x, 0, rect.width - NOTE_WIDTH);
  note.y = clamp(note.y, 0, rect.height - NOTE_HEIGHT);

  state.notes.push(note);
  state.selectedNoteId = note.id;
  persist();
  renderNotes();
}

function openNoteDialog() {
  els.newNoteTitle.value = "";
  els.newNoteText.value = "";
  els.noteDialog.showModal();
}

function closeNoteDialog() {
  if (els.noteDialog.open) {
    els.noteDialog.close();
  }
}

function openCanvasTitleDialog() {
  els.canvasTitleInput.value = state.canvasTitle;
  els.canvasTitleDialog.showModal();
}

function closeCanvasTitleDialog() {
  if (els.canvasTitleDialog.open) {
    els.canvasTitleDialog.close();
  }
}

function deleteNote(id) {
  state.notes = state.notes.filter((note) => note.id !== id);
  if (state.selectedNoteId === id) {
    state.selectedNoteId = null;
  }
  persist();
  renderNotes();
}

function onNotePointerDown(e, noteId) {
  if (e.target.classList.contains("note-content") || e.target.classList.contains("note-delete")) {
    return;
  }

  const note = state.notes.find((item) => item.id === noteId);
  if (!note) {
    return;
  }

  const rect = els.canvas.getBoundingClientRect();
  setSelectedNote(noteId);

  drag = {
    id: noteId,
    startX: e.clientX,
    startY: e.clientY,
    originX: note.x,
    originY: note.y,
    canvasRect: rect,
  };

}

function onPointerMove(e) {
  if (!drag) {
    return;
  }

  const note = state.notes.find((item) => item.id === drag.id);
  if (!note) {
    return;
  }

  const dx = e.clientX - drag.startX;
  const dy = e.clientY - drag.startY;

  note.x = clamp(drag.originX + dx, 0, drag.canvasRect.width - NOTE_WIDTH);
  note.y = clamp(drag.originY + dy, 0, drag.canvasRect.height - NOTE_HEIGHT);

  const noteEl = els.canvas.querySelector(`[data-note-id="${note.id}"]`);
  if (noteEl) {
    noteEl.style.left = `${note.x}px`;
    noteEl.style.top = `${note.y}px`;
  }
}

function onPointerUp() {
  if (!drag) {
    return;
  }
  drag = null;
  persist();
}

function renderNotes() {
  const oldNotes = Array.from(els.canvas.querySelectorAll(".note"));
  oldNotes.forEach((el) => el.remove());

  state.notes.forEach((note) => {
    const fragment = els.noteTemplate.content.cloneNode(true);
    const noteEl = fragment.querySelector(".note");
    const titleEl = fragment.querySelector(".note-title");
    const textEl = fragment.querySelector(".note-content");
    const deleteEl = fragment.querySelector(".note-delete");

    noteEl.dataset.noteId = note.id;
    noteEl.style.left = `${note.x}px`;
    noteEl.style.top = `${note.y}px`;
    noteEl.style.background = note.color;

    if (note.id === state.selectedNoteId) {
      noteEl.classList.add("selected");
    }

    titleEl.value = note.title || "";
    textEl.value = note.text;

    titleEl.addEventListener("focus", () => {
      setSelectedNote(note.id);
    });

    titleEl.addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      setSelectedNote(note.id);
    });

    titleEl.addEventListener("click", (e) => {
      e.stopPropagation();
      setSelectedNote(note.id);
    });

    titleEl.addEventListener("input", () => {
      note.title = titleEl.value;
      persist();
    });

    textEl.addEventListener("focus", () => {
      setSelectedNote(note.id);
    });

    textEl.addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      setSelectedNote(note.id);
    });

    textEl.addEventListener("click", (e) => {
      e.stopPropagation();
      setSelectedNote(note.id);
    });

    textEl.addEventListener("input", () => {
      note.text = textEl.value;
      persist();
    });

    deleteEl.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteNote(note.id);
    });

    noteEl.addEventListener("pointerdown", (e) => onNotePointerDown(e, note.id));

    noteEl.addEventListener("click", () => {
      setSelectedNote(note.id);
    });

    els.canvas.appendChild(fragment);
  });
}

function openSectionTitlesDialog() {
  if (state.layout.mode === "none") {
    window.alert("Set a layout first before editing section titles.");
    return;
  }

  const mode = state.layout.mode;
  const columns = mode === "rows" ? 1 : state.layout.columns;
  const rows = mode === "columns" ? 1 : state.layout.rows;

  els.sectionTitlesFields.innerHTML = "";

  for (let r = 0; r < rows; r += 1) {
    for (let c = 0; c < columns; c += 1) {
      const key = `${r}-${c}`;
      const wrapper = document.createElement("div");
      const label = document.createElement("label");
      const input = document.createElement("input");

      label.textContent = sectionTitle(mode, r, c);
      input.type = "text";
      input.maxLength = 80;
      input.value = state.layout.titles?.[key] || "";
      input.dataset.sectionKey = key;

      wrapper.appendChild(label);
      wrapper.appendChild(input);
      els.sectionTitlesFields.appendChild(wrapper);
    }
  }

  els.sectionTitlesDialog.showModal();
}

function closeSectionTitlesDialog() {
  if (els.sectionTitlesDialog.open) {
    els.sectionTitlesDialog.close();
  }
}

function saveSectionTitlesFromDialog() {
  const inputs = Array.from(els.sectionTitlesFields.querySelectorAll("input[data-section-key]"));
  const nextTitles = {};

  inputs.forEach((input) => {
    const key = input.dataset.sectionKey;
    const value = (input.value || "").trim();
    if (key && value) {
      nextTitles[key] = value;
    }
  });

  state.layout.titles = nextTitles;
  persist();
  renderLayoutOverlay();
}

function applyLayoutFromControls() {
  const mode = els.layoutMode.value;
  const columns = clamp(Number(els.columnCount.value) || 1, 1, 8);
  const rows = clamp(Number(els.rowCount.value) || 1, 1, 8);

  state.layout = {
    mode,
    columns,
    rows,
    showTitles: els.showTitles.checked,
  };

  updateLayoutControls();
  renderLayoutOverlay();
  persist();
}

function openLayoutDialog() {
  updateLayoutControls();
  els.layoutDialog.showModal();
}

function closeLayoutDialog() {
  if (els.layoutDialog.open) {
    els.layoutDialog.close();
  }
}

function clearLayout() {
  state.layout.mode = "none";
  state.layout.titles = {};
  updateLayoutControls();
  renderLayoutOverlay();
  persist();
}

function clearAllState() {
  if (!window.confirm("Clear all notes and layout state from local storage?")) {
    return;
  }

  state.notes = [];
  state.selectedNoteId = null;
  state.layout = {
    mode: "none",
    columns: 3,
    rows: 2,
    showTitles: true,
    titles: {},
  };
  state.canvasTitle = "Notes Canvas";

  localStorage.removeItem(STORAGE_KEY);
  renderCanvasTitle();
  updateLayoutControls();
  renderLayoutOverlay();
  renderNotes();
}

function attachEvents() {
  els.addNote.addEventListener("click", openNoteDialog);
  els.noteDialogForm.addEventListener("submit", (e) => {
    e.preventDefault();
    addNote();
    closeNoteDialog();
  });
  els.cancelNoteDialog.addEventListener("click", closeNoteDialog);

  els.editCanvasTitle.addEventListener("click", openCanvasTitleDialog);
  els.canvasTitleDialogForm.addEventListener("submit", (e) => {
    e.preventDefault();
    state.canvasTitle = (els.canvasTitleInput.value || "").trim() || "Notes Canvas";
    renderCanvasTitle();
    persist();
    closeCanvasTitleDialog();
  });
  els.cancelCanvasTitleDialog.addEventListener("click", closeCanvasTitleDialog);

  els.openLayout.addEventListener("click", openLayoutDialog);
  els.layoutDialogForm.addEventListener("submit", (e) => {
    e.preventDefault();
    applyLayoutFromControls();
    closeLayoutDialog();
  });
  els.cancelLayoutDialog.addEventListener("click", closeLayoutDialog);

  els.editSectionTitles.addEventListener("click", openSectionTitlesDialog);
  els.sectionTitlesDialogForm.addEventListener("submit", (e) => {
    e.preventDefault();
    saveSectionTitlesFromDialog();
    closeSectionTitlesDialog();
  });
  els.cancelSectionTitlesDialog.addEventListener("click", closeSectionTitlesDialog);

  els.clearAll.addEventListener("click", clearAllState);
  els.clearLayout.addEventListener("click", clearLayout);
  els.layoutMode.addEventListener("change", () => {
    state.layout.mode = els.layoutMode.value;
    updateLayoutControls();
  });

  document.addEventListener("pointermove", onPointerMove);
  document.addEventListener("pointerup", onPointerUp);

  els.canvas.addEventListener("click", (e) => {
    if (e.target === els.canvas || e.target.classList.contains("layout-overlay") || e.target.classList.contains("layout-cell")) {
      setSelectedNote(null);
    }
  });

  window.addEventListener("resize", () => {
    const rect = els.canvas.getBoundingClientRect();
    state.notes.forEach((note) => {
      note.x = clamp(note.x, 0, rect.width - NOTE_WIDTH);
      note.y = clamp(note.y, 0, rect.height - NOTE_HEIGHT);
    });
    persist();
    renderNotes();
    renderLayoutOverlay();
  });
}

function init() {
  load();
  renderCanvasTitle();
  updateLayoutControls();
  renderLayoutOverlay();
  renderNotes();
  attachEvents();
}

init();
