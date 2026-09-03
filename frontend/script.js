/**
 * script.js — AI Research Assistant Agent Frontend Logic
 * =========================================================
 * This file handles ALL the interactivity of the frontend:
 *
 * 1. Sending queries to the backend API
 * 2. Updating the workflow dashboard in real-time
 * 3. Rendering the final Markdown answer
 * 4. Loading and displaying history
 * 5. Theme toggle (dark / light mode)
 * 6. Helper utilities (toasts, copy, etc.)
 *
 * HOW THE FRONTEND TALKS TO THE BACKEND:
 *   We use the Fetch API to send HTTP requests to the FastAPI backend.
 *   When the user clicks "Run Agent", we POST the query to /api/agent/run.
 *   The backend runs the agent and returns a JSON response.
 *   We then parse that JSON and update the UI.
 */

// ============================================================
// CONFIGURATION
// ============================================================

/**
 * Backend API URL.
 * - In development: http://localhost:8000
 * - In production: replace with your Render/Railway URL
 *   e.g. https://my-agent-backend.onrender.com
 */
const API_BASE_URL = "http://localhost:8000";

// ============================================================
// STATE
// ============================================================

// Stores the last full AgentResponse from the API
let lastResponse = null;

// Tracks whether the agent is currently running
let isRunning = false;

// ============================================================
// PAGE INITIALIZATION
// ============================================================

/**
 * Runs when the page finishes loading.
 * Sets up event listeners and loads initial data.
 */
document.addEventListener("DOMContentLoaded", () => {
  // Load the query history from the backend
  loadHistory();

  // Set up character counter for the query input
  const queryInput = document.getElementById("queryInput");
  queryInput.addEventListener("input", updateCharCount);

  // Allow pressing Ctrl+Enter (or Cmd+Enter on Mac) to submit
  queryInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      runAgent();
    }
  });

  // Set up example query buttons
  document.querySelectorAll(".example-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      queryInput.value = query;
      updateCharCount();
      queryInput.focus();
    });
  });

  // Apply saved theme preference from localStorage
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);
});

// ============================================================
// CHARACTER COUNTER
// ============================================================

function updateCharCount() {
  const input = document.getElementById("queryInput");
  const counter = document.getElementById("charCount");
  const len = input.value.length;
  counter.textContent = `${len} / 1000`;

  // Turn red if approaching limit
  counter.style.color = len > 900
    ? "var(--error)"
    : len > 700
      ? "var(--warning)"
      : "var(--text-muted)";
}

// ============================================================
// THEME TOGGLE
// ============================================================

/**
 * Toggle between dark and light mode.
 * Saves preference to localStorage so it persists on reload.
 */
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const icon = document.querySelector(".theme-icon");
  if (icon) icon.textContent = theme === "dark" ? "🌙" : "☀️";
}

// Wire up the theme toggle button
document.getElementById("themeToggle")?.addEventListener("click", toggleTheme);

// ============================================================
// MAIN AGENT RUNNER
// ============================================================

/**
 * Main function called when the user clicks "Run Agent".
 *
 * Flow:
 * 1. Validate the input
 * 2. Show the loading state
 * 3. POST to /api/agent/run
 * 4. Animate the workflow steps
 * 5. Display the final answer
 */
async function runAgent() {
  // Prevent running multiple times simultaneously
  if (isRunning) return;

  const queryInput = document.getElementById("queryInput");
  const query = queryInput.value.trim();

  // Validate input
  if (!query) {
    showToast("Please enter a question first.", "error");
    queryInput.focus();
    return;
  }
  if (query.length < 3) {
    showToast("Question is too short. Please be more specific.", "error");
    return;
  }

  // ── Set running state ──
  isRunning = true;
  lastResponse = null;

  // Update UI to running state
  setStatus("running", "Agent is thinking...");
  disableRunButton(true);
  hideAllSections();
  showWorkflowSection();
  resetWorkflowSteps();
  showLoadingOverlay("Sending query to agent...");

  // Simulate the first two steps starting immediately (UX feedback)
  simulateEarlySteps();

  try {
    // ── Call the Backend API ──
    const response = await fetch(`${API_BASE_URL}/api/agent/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query,
        session_id: generateSessionId(),
      }),
    });

    // Hide loading overlay once we have a response
    hideLoadingOverlay();

    // Handle HTTP errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMsg = errorData.detail || `Server error: ${response.status}`;
      throw new Error(errorMsg);
    }

    // Parse the JSON response
    const data = await response.json();
    lastResponse = data;

    // ── Update the UI with the response ──
    await displayAgentResponse(data);

    // Refresh history to show this new query
    loadHistory();

    setStatus("done", `Done in ${data.processing_time || "?"}`);

  } catch (error) {
    hideLoadingOverlay();
    console.error("Agent error:", error);

    // Update step statuses to show something went wrong
    markAllPendingStepsFailed();

    // Show error section
    showErrorSection(error.message);
    setStatus("error", "Error");

    showToast(`Error: ${error.message}`, "error");
  } finally {
    isRunning = false;
    disableRunButton(false);
  }
}

// ============================================================
// SIMULATED EARLY STEPS (Visual Feedback)
// ============================================================

/**
 * While the API call is happening, we animate the first two steps
 * to give the user immediate visual feedback that something is happening.
 * The real step data from the API will update them when it arrives.
 */
function simulateEarlySteps() {
  // Step 1 starts immediately
  setTimeout(() => {
    updateWorkflowStep(0, {
      step_name: "Understanding & Planning",
      status: "in_progress",
      summary: "Analyzing your question and planning research steps...",
    });
    updateLoadingText("Planning research steps...");
  }, 300);

  // Step 2 starts after a delay
  setTimeout(() => {
    updateWorkflowStep(0, {
      step_name: "Understanding & Planning",
      status: "in_progress",
      summary: "Creating a step-by-step research plan...",
    });
    updateLoadingText("Selecting tools and executing tasks...");
  }, 2000);

  setTimeout(() => {
    updateLoadingText("Gathering information from tools...");
  }, 4000);

  setTimeout(() => {
    updateLoadingText("Reviewing gathered information...");
  }, 8000);

  setTimeout(() => {
    updateLoadingText("Generating your structured answer...");
  }, 12000);
}

// ============================================================
// DISPLAY AGENT RESPONSE
// ============================================================

/**
 * Takes the full API response and updates all UI sections.
 *
 * @param {Object} data - The AgentResponse object from the API
 */
async function displayAgentResponse(data) {
  // ── 1. Update workflow step cards ──
  if (data.steps && data.steps.length > 0) {
    // Map backend steps to our 7 UI step cards
    displayWorkflowSteps(data.steps);
  } else {
    // If no step data, mark all as completed
    markAllStepsCompleted();
  }

  // Small delay so the user sees the steps animate in
  await sleep(400);

  // ── 2. Show the research plan ──
  if (data.plan && data.plan.length > 0) {
    displayPlan(data.plan);
  }

  // ── 3. Show tools used ──
  if (data.tools_used && data.tools_used.length > 0) {
    displayToolsUsed(data.tools_used);
  }

  // ── 4. Show processing time ──
  if (data.processing_time) {
    const timeEl = document.getElementById("processingTime");
    timeEl.textContent = `⚡ Completed in ${data.processing_time}`;
    timeEl.style.display = "block";
  }

  await sleep(300);

  // ── 5. Show final answer ──
  if (data.final_answer) {
    displayFinalAnswer(data.final_answer, data.reflection);
  }
}

// ============================================================
// WORKFLOW STEPS UI
// ============================================================

/**
 * Maps the backend agent steps to the 7 UI workflow cards.
 *
 * The backend returns 4 steps (planner, executor, reflector, generator).
 * We distribute them across our 7 visual cards.
 */
function displayWorkflowSteps(steps) {
  // Our 7 UI step IDs
  const stepIds = [
    "step-understanding",
    "step-planning",
    "step-tools",
    "step-executing",
    "step-observing",
    "step-reflection",
    "step-answer",
  ];

  // Map each backend step to a UI card
  // Backend step 1 (Planner) → Cards 0+1
  // Backend step 2 (Executor) → Cards 2+3+4
  // Backend step 3 (Reflection) → Card 5
  // Backend step 4 (Generator) → Card 6
  const mappings = [
    { backendIndex: 0, uiSummary: "Analyzed your question and understood the goal." },
    { backendIndex: 0, uiSummary: null }, // Will use backend summary
    { backendIndex: 1, uiSummary: "Selected the most appropriate tools for this query." },
    { backendIndex: 1, uiSummary: null },
    { backendIndex: 1, uiSummary: "Collected and reviewed all tool outputs." },
    { backendIndex: 2, uiSummary: null },
    { backendIndex: 3, uiSummary: null },
  ];

  mappings.forEach((mapping, uiIndex) => {
    const backendStep = steps[mapping.backendIndex];
    if (!backendStep) return;

    const stepEl = document.getElementById(stepIds[uiIndex]);
    if (!stepEl) return;

    const summary = mapping.uiSummary || backendStep.summary || "";
    const duration = uiIndex === mappings.length - 1 ? backendStep.duration : null;

    // Animate each step with a stagger delay
    setTimeout(() => {
      updateStepElement(stepEl, backendStep.status, summary, duration);
    }, uiIndex * 180);
  });
}

/**
 * Update a single workflow step card's appearance.
 */
function updateStepElement(stepEl, status, summary, duration) {
  // Remove old status classes
  stepEl.classList.remove(
    "status-pending",
    "status-in_progress",
    "status-completed",
    "status-failed"
  );
  stepEl.classList.add(`status-${status}`);

  // Update the status badge
  const badge = stepEl.querySelector(".step-status-badge");
  if (badge) {
    badge.className = `step-status-badge ${status}`;
    const labels = {
      pending: "Pending",
      in_progress: "Running...",
      completed: "✓ Done",
      failed: "✗ Failed",
    };
    badge.textContent = labels[status] || status;
  }

  // Update the summary text
  if (summary) {
    const summaryEl = stepEl.querySelector(".step-summary");
    if (summaryEl) summaryEl.textContent = summary;
  }

  // Update duration
  if (duration) {
    const durEl = stepEl.querySelector(".step-duration");
    if (durEl) durEl.textContent = `⏱ ${duration}`;
  }
}

/**
 * Update a step by index (0-6) — used during simulation.
 */
function updateWorkflowStep(index, stepData) {
  const stepIds = [
    "step-understanding", "step-planning", "step-tools",
    "step-executing", "step-observing", "step-reflection", "step-answer"
  ];
  const stepEl = document.getElementById(stepIds[index]);
  if (!stepEl) return;
  updateStepElement(stepEl, stepData.status, stepData.summary, stepData.duration);
}

function resetWorkflowSteps() {
  const allSteps = document.querySelectorAll(".workflow-step");
  allSteps.forEach((step) => {
    step.className = "workflow-step";
    const badge = step.querySelector(".step-status-badge");
    if (badge) { badge.className = "step-status-badge pending"; badge.textContent = "Pending"; }
    const durEl = step.querySelector(".step-duration");
    if (durEl) durEl.textContent = "";
  });

  // Hide plan and tools cards
  const planCard = document.getElementById("planCard");
  const toolsCard = document.getElementById("toolsCard");
  if (planCard) planCard.style.display = "none";
  if (toolsCard) toolsCard.style.display = "none";
}

function markAllStepsCompleted() {
  const allSteps = document.querySelectorAll(".workflow-step");
  allSteps.forEach((step, i) => {
    setTimeout(() => {
      updateStepElement(step, "completed", null, null);
    }, i * 120);
  });
}

function markAllPendingStepsFailed() {
  document.querySelectorAll(".workflow-step").forEach((step) => {
    if (!step.classList.contains("status-completed")) {
      updateStepElement(step, "failed", "An error occurred.", null);
    }
  });
}

// ============================================================
// PLAN DISPLAY
// ============================================================

function displayPlan(plan) {
  const planCard = document.getElementById("planCard");
  const planList = document.getElementById("planList");
  planList.innerHTML = "";

  plan.forEach((step) => {
    const li = document.createElement("li");
    li.className = `plan-item ${step.completed ? "done" : ""}`;
    li.innerHTML = `
      ${step.description}
      ${step.tool_suggested ? `<span class="tool-tag">${step.tool_suggested}</span>` : ""}
    `;
    planList.appendChild(li);
  });

  planCard.style.display = "block";
}

// ============================================================
// TOOLS DISPLAY
// ============================================================

function displayToolsUsed(toolsUsed) {
  const toolsCard = document.getElementById("toolsCard");
  const toolsList = document.getElementById("toolsList");
  toolsList.innerHTML = "";

  // Group by tool name and count success/fail
  const toolMap = {};
  toolsUsed.forEach((t) => {
    if (!toolMap[t.tool_name]) {
      toolMap[t.tool_name] = { count: 0, success: true };
    }
    toolMap[t.tool_name].count++;
    if (!t.success) toolMap[t.tool_name].success = false;
  });

  // Tool icons
  const icons = {
    Calculator: "🔢",
    WikipediaSearch: "🔍",
    DateTime: "📅",
    TextSummarizer: "📝",
  };

  Object.entries(toolMap).forEach(([name, info]) => {
    const chip = document.createElement("div");
    chip.className = `tool-chip ${info.success ? "success" : "failed"}`;
    chip.innerHTML = `
      <span>${icons[name] || "🔧"}</span>
      <span>${name}</span>
      ${info.count > 1 ? `<span style="opacity:0.6">×${info.count}</span>` : ""}
    `;
    toolsList.appendChild(chip);
  });

  toolsCard.style.display = "block";
}

// ============================================================
// FINAL ANSWER DISPLAY
// ============================================================

/**
 * Render the final answer and reflection.
 * Uses marked.js to convert Markdown → HTML.
 */
function displayFinalAnswer(markdownText, reflection) {
  const answerSection = document.getElementById("answerSection");
  const answerContent = document.getElementById("answerContent");
  const reflectionCard = document.getElementById("reflectionCard");
  const reflectionText = document.getElementById("reflectionText");

  // Show reflection if available
  if (reflection && reflection.trim()) {
    reflectionText.textContent = reflection;
    reflectionCard.style.display = "flex";
  } else {
    reflectionCard.style.display = "none";
  }

  // Convert Markdown to HTML using marked.js
  // marked.parse() handles headings, bold, lists, code blocks, etc.
  try {
    answerContent.innerHTML = marked.parse(markdownText);
  } catch {
    // Fallback: display as plain text if Markdown parsing fails
    answerContent.textContent = markdownText;
  }

  // Show the answer section with animation
  answerSection.style.display = "block";

  // Smooth scroll to the answer
  setTimeout(() => {
    answerSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 200);
}

// ============================================================
// HISTORY
// ============================================================

/**
 * Fetch history from GET /api/history and render it.
 */
async function loadHistory() {
  const historyGrid = document.getElementById("historyGrid");

  try {
    const response = await fetch(`${API_BASE_URL}/api/history?limit=9`);
    if (!response.ok) throw new Error("Failed to load history");

    const data = await response.json();

    if (!data.history || data.history.length === 0) {
      historyGrid.innerHTML = `
        <div class="history-empty">
          <span class="empty-icon">📭</span>
          <p>No queries yet. Run your first agent above!</p>
        </div>`;
      return;
    }

    // Render history cards
    historyGrid.innerHTML = data.history
      .map((item) => createHistoryCard(item))
      .join("");

  } catch (error) {
    // Silently fail — history is a bonus feature, not critical
    console.warn("Could not load history:", error.message);
  }
}

/**
 * Build the HTML for a single history card.
 */
function createHistoryCard(item) {
  // Format the timestamp to a readable format
  const time = formatTimestamp(item.timestamp);

  // Build the tool tags
  const toolTags = (item.tools_used || [])
    .map((t) => `<span class="history-tool-tag">${t}</span>`)
    .join("");

  // Escape HTML in the query to prevent XSS
  const safeQuery = escapeHtml(item.query);
  const safePreview = escapeHtml(item.answer_preview || "");

  return `
    <div class="history-card" onclick="fillQueryFromHistory(${JSON.stringify(item.query).replace(/"/g, '&quot;')})">
      <div class="history-query">${safeQuery}</div>
      <div class="history-preview">${safePreview}</div>
      <div class="history-meta">
        <div class="history-tools">${toolTags || '<span class="history-tool-tag">No tools</span>'}</div>
        <div style="display:flex; gap:0.5rem; align-items:center;">
          ${item.processing_time ? `<span class="history-duration">⚡ ${item.processing_time}</span>` : ""}
          <span class="history-time">${time}</span>
        </div>
      </div>
    </div>`;
}

/**
 * Click a history card to fill the query input with that query.
 */
function fillQueryFromHistory(query) {
  const queryInput = document.getElementById("queryInput");
  queryInput.value = query;
  updateCharCount();
  queryInput.focus();
  // Scroll to input
  queryInput.scrollIntoView({ behavior: "smooth", block: "center" });
  showToast("Query loaded. Click 'Run Agent' to run it again.", "success");
}

// ============================================================
// UI HELPERS
// ============================================================

function showWorkflowSection() {
  document.getElementById("workflowSection").style.display = "block";
}

function hideAllSections() {
  document.getElementById("answerSection").style.display = "none";
  document.getElementById("errorSection").style.display = "none";
  document.getElementById("workflowSection").style.display = "none";
  document.getElementById("processingTime").style.display = "none";
}

function showErrorSection(message) {
  const section = document.getElementById("errorSection");
  const msgEl = document.getElementById("errorMessage");
  msgEl.textContent = message;
  section.style.display = "block";
}

function disableRunButton(disabled) {
  const btn = document.getElementById("runBtn");
  btn.disabled = disabled;
  btn.querySelector(".btn-text").textContent = disabled ? "Running..." : "Run Agent";
  btn.querySelector(".btn-icon").textContent = disabled ? "⏳" : "▶";
}

function setStatus(state, text) {
  const dot = document.querySelector(".status-dot");
  const label = document.querySelector(".status-text");
  dot.className = `status-dot ${state}`;
  label.textContent = text;
}

function showLoadingOverlay(text) {
  const overlay = document.getElementById("loadingOverlay");
  document.getElementById("loadingText").textContent = text;
  overlay.style.display = "flex";
}

function hideLoadingOverlay() {
  document.getElementById("loadingOverlay").style.display = "none";
}

function updateLoadingText(text) {
  const el = document.getElementById("loadingText");
  if (el) el.textContent = text;
}

/**
 * Reset the UI to start a new query.
 */
function newQuery() {
  hideAllSections();
  setStatus("idle", "Ready");
  const input = document.getElementById("queryInput");
  input.value = "";
  updateCharCount();
  input.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Copy the final answer text to clipboard.
 */
async function copyAnswer() {
  if (!lastResponse?.final_answer) {
    showToast("No answer to copy.", "error");
    return;
  }
  try {
    await navigator.clipboard.writeText(lastResponse.final_answer);
    showToast("Answer copied to clipboard!", "success");
  } catch {
    showToast("Could not copy. Try selecting the text manually.", "error");
  }
}

/**
 * Show a brief toast notification at the bottom-right.
 */
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

/**
 * Format an ISO timestamp to a human-readable string.
 * e.g. "2024-01-15T10:30:00" → "Jan 15, 10:30 AM"
 */
function formatTimestamp(isoString) {
  if (!isoString) return "Unknown time";
  try {
    const date = new Date(isoString);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return isoString;
  }
}

/**
 * Generate a short session ID for grouping related queries.
 */
function generateSessionId() {
  return Math.random().toString(36).substring(2, 10);
}

/**
 * Escape HTML characters to prevent XSS attacks.
 * Always escape user-provided text before inserting into the DOM.
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(text));
  return div.innerHTML;
}

/**
 * Sleep for a given number of milliseconds.
 * Used to create stagger animations.
 */
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
