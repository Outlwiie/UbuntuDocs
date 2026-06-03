const API = "http://127.0.0.1:8000";

const uploadZone = document.getElementById("uploadZone");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");
const docList = document.getElementById("docList");
const messages = document.getElementById("messages");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");

// ── Boot ───────────────────────────────────────────────────────────────────────

loadDocuments();

// ── Upload ─────────────────────────────────────────────────────────────────────

uploadZone.addEventListener("click", () => fileInput.click());

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("dragover");
});

uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
  if (!file.name.endsWith(".pdf")) {
    setStatus("Only PDF files are supported.", "error");
    return;
  }

  setStatus("Uploading...");

  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch(`${API}/upload`, { method: "POST", body: form });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "Upload failed.");

    setStatus(`✓ ${data.chunks} chunks ingested`);
    loadDocuments();

    // clear status after 3s
    setTimeout(() => setStatus(""), 3000);
  } catch (err) {
    setStatus(`✗ ${err.message}`, "error");
  }

  fileInput.value = "";
}

function setStatus(msg, type = "ok") {
  uploadStatus.textContent = msg;
  uploadStatus.style.color = type === "error" ? "#e07070" : "var(--gold)";
}

// ── Documents list ─────────────────────────────────────────────────────────────

async function loadDocuments() {
  try {
    const res = await fetch(`${API}/documents`);
    const docs = await res.json();

    docList.innerHTML = "";

    if (docs.length === 0) {
      docList.innerHTML = '<li class="doc-empty">No documents yet</li>';
      return;
    }

    docs.forEach((doc) => {
      const li = document.createElement("li");
      li.className = "doc-item";
      li.innerHTML = `
        <span class="doc-name" title="${doc.filename}">${doc.filename}</span>
        <span class="doc-chunks">${doc.chunks}c</span>
        <button class="doc-delete" title="Remove" data-id="${doc.document_id}">×</button>
      `;
      li.querySelector(".doc-delete").addEventListener("click", () =>
        deleteDoc(doc.document_id),
      );
      docList.appendChild(li);
    });
  } catch {
    docList.innerHTML = '<li class="doc-empty">Could not load documents</li>';
  }
}

async function deleteDoc(id) {
  try {
    await fetch(`${API}/documents/${id}`, { method: "DELETE" });
    loadDocuments();
  } catch {
    alert("Failed to delete document.");
  }
}

// ── Chat ───────────────────────────────────────────────────────────────────────

sendBtn.addEventListener("click", sendQuestion);

questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendQuestion();
  }
});

// Auto-grow textarea
questionInput.addEventListener("input", () => {
  questionInput.style.height = "auto";
  questionInput.style.height = questionInput.scrollHeight + "px";
});

async function sendQuestion() {
  const question = questionInput.value.trim();
  if (!question) return;

  // Clear welcome screen on first message
  const welcome = document.querySelector(".welcome");
  if (welcome) welcome.remove();

  // Show user message
  appendMessage("user", question);
  questionInput.value = "";
  questionInput.style.height = "auto";
  sendBtn.disabled = true;

  // Show thinking indicator
  const thinkingId = appendThinking();

  try {
    const res = await fetch(`${API}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();
    removeThinking(thinkingId);

    if (!res.ok) throw new Error(data.detail || "Query failed.");

    appendMessage("assistant", data.answer, data.sources);
  } catch (err) {
    removeThinking(thinkingId);
    appendMessage("assistant", `Error: ${err.message}`);
  }

  sendBtn.disabled = false;
  scrollToBottom();
}

function appendMessage(role, text, sources = []) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;

  const sourcesHTML = sources.length
    ? `<div class="msg-sources">${sources.map((s) => `<span class="source-tag">📄 ${s}</span>`).join("")}</div>`
    : "";

  div.innerHTML = `
    <div class="msg-label">${role === "user" ? "You" : "UbuntuDocs"}</div>
    <div class="msg-bubble">${escapeHtml(text)}</div>
    ${sourcesHTML}
  `;

  messages.appendChild(div);
  scrollToBottom();
}

function appendThinking() {
  const id = "thinking-" + Date.now();
  const div = document.createElement("div");
  div.className = "msg assistant thinking";
  div.id = id;
  div.innerHTML = `
    <div class="msg-label">UbuntuDocs</div>
    <div class="msg-bubble">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
  `;
  messages.appendChild(div);
  scrollToBottom();
  return id;
}

function removeThinking(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br/>");
}
