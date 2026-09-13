const state = {
  dataset: null,
  filtered: null,
  selectedGroup: null,
  charts: {},
  refreshTimer: null,
};

document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;
  if (page === "login") {
    initLogin();
    return;
  }
  initDashboard();
});

function initLogin() {
  const form = document.getElementById("login-form");
  const errorNode = document.getElementById("login-error");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hide(errorNode);

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) {
        const payload = await safeJson(response);
        throw new Error(payload.detail || "Falha no login.");
      }
      window.location.href = "/";
    } catch (error) {
      errorNode.textContent = error.message || "Falha no login.";
      show(errorNode);
    }
  });
}

function initDashboard() {
  bindDashboardEvents();
  loadDashboardData();
}

function bindDashboardEvents() {
  document.getElementById("logout-button").addEventListener("click", logout);
  document.getElementById("export-csv").addEventListener("click", () => {
    window.location.href = "/api/export/csv";
  });
  document.getElementById("period-filter").addEventListener("change", handleFilterChange);
  document.getElementById("group-filter").addEventListener("change", handleFilterChange);
  document.getElementById("model-filter").addEventListener("change", handleFilterChange);
  document.getElementById("custom-start").addEventListener("change", applyFiltersAndRender);
  document.getElementById("custom-end").addEventListener("change", applyFiltersAndRender);
  document.getElementById("auto-refresh-toggle").addEventListener("change", configureAutoRefresh);
  document.getElementById("refresh-interval").addEventListener("change", configureAutoRefresh);
  document.getElementById("close-modal").addEventListener("click", closeModal);
  document.getElementById("group-modal").addEventListener("click", (event) => {
    if (event.target.dataset.closeModal === "true") {
      closeModal();
    }
  });
  document.getElementById("block-group").addEventListener("click", () => runGroupAction("block"));
  document.getElementById("unblock-group").addEventListener("click", () => runGroupAction("unblock"));
  document.getElementById("regenerate-key").addEventListener("click", regenerateKey);
  document.getElementById("budget-form").addEventListener("submit", updateBudget);
}

async function loadDashboardData() {
  try {
    const response = await fetch("/api/groups", { credentials: "same-origin" });
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      const payload = await safeJson(response);
      throw new Error(payload.detail || "Não foi possível carregar o dashboard.");
    }

    state.dataset = await response.json();
    populateGroupFilter(state.dataset.groups);
    applyFiltersAndRender();
    configureAutoRefresh();
  } catch (error) {
    renderAlerts([], error.message || "Erro ao carregar dados.");
  }
}

function handleFilterChange() {
  const isCustom = document.getElementById("period-filter").value === "custom";
  document.getElementById("custom-date-range").classList.toggle("hidden", !isCustom);
  applyFiltersAndRender();
}

function applyFiltersAndRender() {
  if (!state.dataset) {
    return;
  }
  state.filtered = buildFilteredView();
  renderStats();
  renderAlerts(state.filtered.alerts);
  renderGroupsTable();
  renderCharts();
  renderLastUpdated(state.dataset.generated_at);
}

function buildFilteredView() {
  const period = document.getElementById("period-filter").value;
  const selectedGroup = document.getElementById("group-filter").value;
  const selectedModel = document.getElementById("model-filter").value;
  const now = new Date();

  let startDate = null;
  let endDate = now;

  if (period === "1h") startDate = new Date(now.getTime() - 60 * 60 * 1000);
  if (period === "today") startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  if (period === "24h") startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  if (period === "7d") startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  if (period === "30d") startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  if (period === "custom") {
    startDate = parseInputDate(document.getElementById("custom-start").value);
    endDate = parseInputDate(document.getElementById("custom-end").value) || now;
  }

  const calls = state.dataset.calls.filter((call) => {
    const callDate = new Date(call.timestamp);
    const matchesGroup = selectedGroup === "all" || call.group === selectedGroup;
    const matchesModel = selectedModel === "all" || call.model === selectedModel;
    const matchesStart = !startDate || callDate >= startDate;
    const matchesEnd = !endDate || callDate <= endDate;
    return matchesGroup && matchesModel && matchesStart && matchesEnd;
  });

  const visibleGroups = state.dataset.groups.filter((group) => selectedGroup === "all" || group.group === selectedGroup);
  const alerts = state.dataset.alerts.filter((alert) => selectedGroup === "all" || alert.group === selectedGroup);

  return { calls, visibleGroups, alerts, selectedModel };
}

function populateGroupFilter(groups) {
  const select = document.getElementById("group-filter");
  const current = select.value;
  select.innerHTML = '<option value="all">Todos</option>';
  groups.forEach((group) => {
    const option = document.createElement("option");
    option.value = group.group;
    option.textContent = group.group;
    select.appendChild(option);
  });
  select.value = Array.from(select.options).some((option) => option.value === current) ? current : "all";
}

function renderStats() {
  const totalRequests = state.filtered.calls.length;
  const totalTokens = state.filtered.calls.reduce((sum, call) => sum + call.total_tokens, 0);
  const totalCost = state.filtered.calls.reduce((sum, call) => sum + call.cost, 0);
  const activeGroups = state.filtered.visibleGroups.filter((group) => !group.blocked).length;

  document.getElementById("stat-requests").textContent = formatNumber(totalRequests);
  document.getElementById("stat-tokens").textContent = formatCompactNumber(totalTokens);
  document.getElementById("stat-cost").textContent = formatUsd(totalCost);
  document.getElementById("stat-groups").textContent = `${activeGroups} / ${state.filtered.visibleGroups.length}`;
}

function renderAlerts(alerts, fallbackMessage = "") {
  const container = document.getElementById("alerts-container");
  if (fallbackMessage) {
    clearNode(container);
    const item = document.createElement("div");
    item.className = "alert-item alert-critical";
    item.textContent = fallbackMessage;
    container.appendChild(item);
    return;
  }
  if (!alerts.length) {
    clearNode(container);
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Nenhum alerta para os filtros atuais.";
    container.appendChild(empty);
    return;
  }
  clearNode(container);
  alerts.forEach((alert) => {
    const item = document.createElement("div");
    item.className = `alert-item alert-${alert.severity}`;
    const strong = document.createElement("strong");
    strong.textContent = alert.group;
    item.appendChild(strong);
    item.append(` — ${alert.message}`);
    container.appendChild(item);
  });
}

function renderGroupsTable() {
  const tbody = document.getElementById("groups-table-body");
  const groupedCalls = aggregateCallsByGroup(state.filtered.calls);
  clearNode(tbody);

  if (!state.filtered.visibleGroups.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 11;
    cell.className = "empty-state";
    cell.textContent = "Sem grupos para os filtros atuais.";
    row.appendChild(cell);
    tbody.appendChild(row);
    return;
  }

  state.filtered.visibleGroups.forEach((group) => {
    const callSummary = groupedCalls[group.group] || emptySummary();
    const usage = Number(group.budget_used_pct || 0);
    const progressTone = getProgressTone(usage);
    const progressWidth = Math.min(usage, 100);
    const row = document.createElement("tr");

    const groupCell = document.createElement("td");
    const link = document.createElement("a");
    link.href = "#";
    link.className = "group-link";
    link.dataset.group = group.group;
    link.textContent = group.group;
    groupCell.appendChild(link);
    row.appendChild(groupCell);

    [
      formatNumber(callSummary.requests),
      formatNumber(callSummary.input_tokens),
      formatNumber(callSummary.output_tokens),
      formatNumber(callSummary.total_tokens),
      formatUsd(callSummary.cost),
      group.budget == null ? "-" : formatUsd(group.budget),
      group.budget_remaining == null ? "-" : formatUsd(group.budget_remaining),
    ].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    });

    const usageCell = document.createElement("td");
    const progressCell = document.createElement("div");
    progressCell.className = "progress-cell";
    const track = document.createElement("div");
    track.className = "progress-track";
    const bar = document.createElement("div");
    bar.className = `progress-bar progress-${progressTone}`;
    bar.style.width = `${progressWidth}%`;
    track.appendChild(bar);
    const label = document.createElement("span");
    label.textContent = `${usage.toFixed(1)}%`;
    progressCell.append(track, label);
    usageCell.appendChild(progressCell);
    row.appendChild(usageCell);

    const lastCalledCell = document.createElement("td");
    lastCalledCell.textContent = formatDate(callSummary.last_called_at || group.last_called_at);
    row.appendChild(lastCalledCell);

    const statusCell = document.createElement("td");
    statusCell.appendChild(createStatusPill(group.status));
    row.appendChild(statusCell);

    tbody.appendChild(row);
  });

  tbody.querySelectorAll("[data-group]").forEach((node) => {
    node.addEventListener("click", (event) => {
      event.preventDefault();
      openGroupModal(node.dataset.group);
    });
  });
}

function renderStatusPill(status) {
  return `<span class="status-pill"><span class="status-dot tone-${status.tone}"></span>${status.label}</span>`;
}

function createStatusPill(status) {
  const pill = document.createElement("span");
  pill.className = "status-pill";
  const dot = document.createElement("span");
  dot.className = `status-dot tone-${status.tone}`;
  pill.append(dot, status.label);
  return pill;
}

function renderCharts() {
  const calls = state.filtered.calls;
  const costByGroup = aggregateMetricByGroup(calls, "cost");
  const tokensByGroup = aggregateMetricByGroup(calls, "total_tokens");
  const timeline = aggregateTimeline(calls);
  const models = aggregateModels(calls);

  upsertChart("cost-chart", "bar", {
    labels: Object.keys(costByGroup),
    datasets: [{ label: "Custo (US$)", data: Object.values(costByGroup), backgroundColor: "#e6007e" }],
  });
  upsertChart("tokens-chart", "bar", {
    labels: Object.keys(tokensByGroup),
    datasets: [{ label: "Tokens", data: Object.values(tokensByGroup), backgroundColor: "#7c4dff" }],
  });
  upsertChart("timeline-chart", "line", {
    labels: timeline.labels,
    datasets: [{ label: "Custo (US$)", data: timeline.costs, borderColor: "#e6007e", backgroundColor: "rgba(230, 0, 126, 0.18)", fill: true, tension: 0.25 }],
  });
  upsertChart("model-chart", "doughnut", {
    labels: Object.keys(models),
    datasets: [{ data: Object.values(models), backgroundColor: ["#e6007e", "#7c4dff", "#00c853", "#ffd600"] }],
  });
}

function upsertChart(id, type, data) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  if (state.charts[id]) {
    state.charts[id].data = data;
    state.charts[id].update();
    return;
  }
  state.charts[id] = new Chart(ctx, {
    type,
    data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#fff" } },
      },
      scales: type === "doughnut" ? {} : {
        x: { ticks: { color: "#888" }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#888" }, grid: { color: "rgba(255,255,255,0.05)" } },
      },
    },
  });
}

async function openGroupModal(groupName) {
  state.selectedGroup = groupName;
  try {
    const response = await fetch(`/api/groups/${groupName}`, { credentials: "same-origin" });
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      const payload = await safeJson(response);
      throw new Error(payload.detail || "Falha ao carregar detalhes do grupo.");
    }

    const detail = await response.json();
    fillGroupModal(detail);
    show(document.getElementById("group-modal"));
  } catch (error) {
    window.alert(error.message || "Falha ao carregar detalhes do grupo.");
  }
}

function fillGroupModal(detail) {
  document.getElementById("modal-group-name").textContent = detail.group;
  document.getElementById("budget-input").value = detail.budget || "";
  hide(document.getElementById("regenerated-key-box"));

  renderDetailList("budget-details", [
    ["Budget", detail.budget == null ? "-" : formatUsd(detail.budget)],
    ["Budget restante", detail.budget_remaining == null ? "-" : formatUsd(detail.budget_remaining)],
    ["% utilizado", `${Number(detail.budget_used_pct || 0).toFixed(1)}%`],
    ["Status", detail.status.label],
    ["RPM limit", detail.rpm_limit || "-"],
    ["TPM limit", detail.tpm_limit || "-"],
  ]);
  renderDetailList("usage-details", [
    ["Requests", formatNumber(detail.requests)],
    ["Input tokens", formatNumber(detail.input_tokens)],
    ["Output tokens", formatNumber(detail.output_tokens)],
    ["Total tokens", formatNumber(detail.total_tokens)],
    ["Custo atual", formatUsd(detail.current_spend)],
    ["Última chamada", formatDate(detail.last_called_at)],
  ]);

  const modalCallsBody = document.getElementById("recent-calls-body");
  clearNode(modalCallsBody);
  if (!(detail.recent_calls || []).length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 8;
    cell.className = "empty-state";
    cell.textContent = "Sem chamadas recentes.";
    row.appendChild(cell);
    modalCallsBody.appendChild(row);
  } else {
    (detail.recent_calls || []).forEach((call) => {
      const row = document.createElement("tr");
      [
        formatDate(call.timestamp),
        call.model,
        formatNumber(call.input_tokens),
        formatNumber(call.output_tokens),
        formatNumber(call.total_tokens),
        formatUsd(call.cost),
        call.latency_ms ? `${call.latency_ms.toFixed(0)} ms` : "-",
        call.http_status || "-",
      ].forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      });
      modalCallsBody.appendChild(row);
    });
  }

  const modelData = {};
  (detail.model_distribution || []).forEach((entry) => {
    modelData[entry.model] = entry.requests;
  });
  upsertChart("modal-model-chart", "doughnut", {
    labels: Object.keys(modelData),
    datasets: [{ data: Object.values(modelData), backgroundColor: ["#e6007e", "#7c4dff", "#00c853", "#ffd600"] }],
  });
}

function renderDetailList(id, rows) {
  const node = document.getElementById(id);
  clearNode(node);
  rows.forEach(([term, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    node.append(dt, dd);
  });
}

function closeModal() {
  hide(document.getElementById("group-modal"));
}

async function runGroupAction(action) {
  if (!state.selectedGroup) return;
  try {
    const response = await fetch(`/api/groups/${state.selectedGroup}/${action}`, {
      method: "POST",
      credentials: "same-origin",
    });
    if (!response.ok) {
      const payload = await safeJson(response);
      throw new Error(payload.detail || "Falha ao executar ação.");
    }
    await loadDashboardData();
    await openGroupModal(state.selectedGroup);
  } catch (error) {
    window.alert(error.message || "Falha ao executar ação.");
  }
}

async function updateBudget(event) {
  event.preventDefault();
  if (!state.selectedGroup) return;
  const maxBudget = Number(document.getElementById("budget-input").value);
  if (Number.isNaN(maxBudget) || maxBudget < 0) {
    window.alert("Informe um budget válido.");
    return;
  }
  try {
    const response = await fetch(`/api/groups/${state.selectedGroup}/budget`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ max_budget: maxBudget }),
    });
    if (!response.ok) {
      const payload = await safeJson(response);
      throw new Error(payload.detail || "Falha ao atualizar budget.");
    }
    await loadDashboardData();
    await openGroupModal(state.selectedGroup);
  } catch (error) {
    window.alert(error.message || "Falha ao atualizar budget.");
  }
}

async function regenerateKey() {
  if (!state.selectedGroup) return;
  const confirmed = window.confirm(`Regenerar a chave de ${state.selectedGroup}? A chave anterior deixará de ser usada.`);
  if (!confirmed) return;
  try {
    const response = await fetch(`/api/groups/${state.selectedGroup}/regenerate-key`, {
      method: "POST",
      credentials: "same-origin",
    });
    if (!response.ok) {
      const payload = await safeJson(response);
      throw new Error(payload.detail || "Falha ao regenerar chave.");
    }
    const payload = await response.json();
    const box = document.getElementById("regenerated-key-box");
    clearNode(box);
    const title = document.createElement("strong");
    title.textContent = "Chave virtual atualizada:";
    const lineBreak = document.createElement("br");
    const text = document.createTextNode(payload.masked_key || payload.message || "Gerada com sucesso.");
    box.append(title, lineBreak, text);
    show(box);
    await loadDashboardData();
  } catch (error) {
    window.alert(error.message || "Falha ao regenerar chave.");
  }
}

async function logout() {
  await fetch("/api/logout", { method: "POST", credentials: "same-origin" });
  window.location.href = "/login";
}

function configureAutoRefresh() {
  if (state.refreshTimer) {
    window.clearInterval(state.refreshTimer);
    state.refreshTimer = null;
  }
  const enabled = document.getElementById("auto-refresh-toggle").checked;
  const interval = document.getElementById("refresh-interval").value;
  if (!enabled || interval === "manual") {
    return;
  }
  state.refreshTimer = window.setInterval(loadDashboardData, Number(interval));
}

function aggregateCallsByGroup(calls) {
  return calls.reduce((accumulator, call) => {
    const current = accumulator[call.group] || emptySummary();
    current.requests += 1;
    current.input_tokens += call.input_tokens;
    current.output_tokens += call.output_tokens;
    current.total_tokens += call.total_tokens;
    current.cost += call.cost;
    current.last_called_at = current.last_called_at && current.last_called_at > call.timestamp ? current.last_called_at : call.timestamp;
    accumulator[call.group] = current;
    return accumulator;
  }, {});
}

function aggregateMetricByGroup(calls, metric) {
  const values = {};
  calls.forEach((call) => {
    values[call.group] = (values[call.group] || 0) + call[metric];
  });
  return values;
}

function aggregateTimeline(calls) {
  const buckets = {};
  const useHourly = shouldUseHourlyBuckets();
  calls.forEach((call) => {
    const date = new Date(call.timestamp);
    const key = useHourly ? `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:00`
      : `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
    buckets[key] = (buckets[key] || 0) + call.cost;
  });
  const labels = Object.keys(buckets).sort();
  return { labels, costs: labels.map((label) => round(buckets[label])) };
}

function aggregateModels(calls) {
  return calls.reduce((accumulator, call) => {
    accumulator[call.model] = (accumulator[call.model] || 0) + 1;
    return accumulator;
  }, {});
}

function shouldUseHourlyBuckets() {
  const period = document.getElementById("period-filter").value;
  return ["1h", "today", "24h"].includes(period);
}

function parseInputDate(value) {
  return value ? new Date(value) : null;
}

function emptySummary() {
  return { requests: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, cost: 0, last_called_at: null };
}

function getProgressTone(usage) {
  if (usage >= 100) return "danger";
  if (usage >= 85) return "warning-high";
  if (usage >= 70) return "warning";
  return "success";
}

function formatCompactNumber(value) {
  const amount = Number(value || 0);
  if (amount >= 1_000_000_000) {
    return `${trimCompact(amount / 1_000_000_000)}B`;
  }
  if (amount >= 1_000_000) {
    return `${trimCompact(amount / 1_000_000)}M`;
  }
  if (amount >= 1_000) {
    return `${trimCompact(amount / 1_000)}K`;
  }
  return formatNumber(amount);
}

function formatUsd(value) {
  return `US$ ${Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatNumber(value) {
  return new Intl.NumberFormat("pt-BR").format(value || 0);
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function renderLastUpdated(value) {
  document.getElementById("last-updated").textContent = `Atualizado em ${formatDate(value)}`;
}

function safeJson(response) {
  return response.json().catch(() => ({}));
}

function show(node) {
  node.classList.remove("hidden");
}

function hide(node) {
  node.classList.add("hidden");
}

function round(value) {
  return Math.round(value * 100) / 100;
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function trimCompact(value) {
  return Number(value).toFixed(1).replace(/\.0$/, "");
}

function clearNode(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}
