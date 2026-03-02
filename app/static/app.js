const state = {
  galleries: [],
  briefing: null,
};

const elements = {
  healthBadge: document.getElementById("healthBadge"),
  refreshAllBtn: document.getElementById("refreshAllBtn"),
  sourceType: document.getElementById("sourceType"),
  sourceKey: document.getElementById("sourceKey"),
  displayName: document.getElementById("displayName"),
  galleryForm: document.getElementById("galleryForm"),
  galleriesList: document.getElementById("galleriesList"),
  collectBtn: document.getElementById("collectBtn"),
  rebuildBtn: document.getElementById("rebuildBtn"),
  windowHours: document.getElementById("windowHours"),
  fetchLimit: document.getElementById("fetchLimit"),
  opsResult: document.getElementById("opsResult"),
  briefingBtn: document.getElementById("briefingBtn"),
  briefWindowFilter: document.getElementById("briefWindowFilter"),
  briefLimitFilter: document.getElementById("briefLimitFilter"),
  topicGrid: document.getElementById("topicGrid"),
  topicPosts: document.getElementById("topicPosts"),
  trendGalleryFilter: document.getElementById("trendGalleryFilter"),
  trendHours: document.getElementById("trendHours"),
  trendBtn: document.getElementById("trendBtn"),
  trendChart: document.getElementById("trendChart"),
  apiKeyInput: document.getElementById("apiKeyInput"),
  topicCardTemplate: document.getElementById("topicCardTemplate"),
};

function getApiKey() {
  return elements.apiKeyInput.value.trim();
}

function selectedBoardIds() {
  return [...document.querySelectorAll('input[name="boardSelection"]:checked')].map((node) =>
    parseInt(node.value, 10),
  );
}

function headers(includeJson = false, includeApiKey = false) {
  const result = {};
  if (includeJson) result["Content-Type"] = "application/json";
  if (includeApiKey) {
    const key = getApiKey();
    if (key) result["X-API-Key"] = key;
  }
  return result;
}

async function apiGet(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`GET ${path} failed: ${response.status}`);
  return response.json();
}

async function apiPost(path, body = null, includeApiKey = false) {
  const response = await fetch(path, {
    method: "POST",
    headers: headers(Boolean(body), includeApiKey),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`POST ${path} failed: ${response.status} ${text}`);
  }
  return response.json();
}

function message(text, isError = false) {
  elements.opsResult.textContent = text;
  elements.opsResult.style.color = isError ? "#7f1d1d" : "";
}

function setHealth(ok) {
  elements.healthBadge.className = `badge ${ok ? "ok" : "fail"}`;
  elements.healthBadge.textContent = ok ? "API Healthy" : "API Down";
}

function renderSourceOptions(sources) {
  elements.sourceType.innerHTML = "";
  for (const source of sources) {
    const option = document.createElement("option");
    option.value = source;
    option.textContent = source;
    elements.sourceType.appendChild(option);
  }
}

function renderGalleries() {
  elements.galleriesList.innerHTML = "";
  elements.trendGalleryFilter.innerHTML = '<option value="">Select</option>';

  if (!state.galleries.length) {
    elements.galleriesList.innerHTML = '<p class="trend-empty">No boards registered yet.</p>';
    return;
  }

  for (const gallery of state.galleries) {
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <label class="board-row">
        <input type="checkbox" name="boardSelection" value="${gallery.id}" checked />
        <div>
          <p class="board-title">${gallery.display_name}</p>
          <p class="board-meta">${gallery.source_type} / ${gallery.source_key}</p>
        </div>
      </label>
    `;
    elements.galleriesList.appendChild(item);

    const option = document.createElement("option");
    option.value = String(gallery.id);
    option.textContent = gallery.display_name;
    elements.trendGalleryFilter.appendChild(option);
  }
}

function trendClass(trend) {
  if (trend === "up") return "up";
  if (trend === "down") return "down";
  return "stable";
}

function renderTopics(topics) {
  elements.topicGrid.innerHTML = "";
  if (!topics.length) {
    elements.topicGrid.innerHTML = '<p class="trend-empty">No topics. Run collect, then generate briefing.</p>';
    return;
  }

  for (const topic of topics) {
    const node = elements.topicCardTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector("h4").textContent = topic.title;

    const pill = node.querySelector(".trend-pill");
    pill.classList.add(trendClass(topic.trend));
    pill.textContent = topic.trend.toUpperCase();

    node.querySelector(".topic-summary").textContent = topic.summary;
    node.querySelector(".topic-meta").textContent =
      `score ${topic.score.toFixed(3)} | confidence ${topic.confidence.toFixed(2)} | boards ${topic.gallery_names.join(", ")}`;

    const keywords = node.querySelector(".topic-keywords");
    for (const word of topic.keywords || []) {
      const tag = document.createElement("span");
      tag.className = "keyword";
      tag.textContent = word;
      keywords.appendChild(tag);
    }

    node.addEventListener("click", () => renderTopicPosts(topic.posts || []));
    elements.topicGrid.appendChild(node);
  }
}

function renderTopicPosts(posts) {
  elements.topicPosts.innerHTML = "";
  if (!posts.length) {
    elements.topicPosts.innerHTML = '<p class="trend-empty">No evidence posts for this topic.</p>';
    return;
  }

  for (const post of posts) {
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <a class="post-link" href="${post.url}" target="_blank" rel="noreferrer">${post.title}</a>
      <p>${post.gallery_name} | ${new Date(post.published_at).toLocaleString()}</p>
      <p>up ${post.upvote_count} / comments ${post.comment_count} / views ${post.view_count}</p>
    `;
    elements.topicPosts.appendChild(item);
  }
}

function renderTrendChart(items) {
  if (!items.length) {
    elements.trendChart.innerHTML = '<p class="trend-empty">No trend data in this window.</p>';
    return;
  }
  const width = 600;
  const height = 160;
  const pad = 24;
  const maxValue = Math.max(...items.map((item) => item.count), 1);
  const points = items.map((item, idx) => {
    const x = pad + (idx * (width - pad * 2)) / Math.max(items.length - 1, 1);
    const y = height - pad - (item.count / maxValue) * (height - pad * 2);
    return { x, y, label: item.bucket, count: item.count };
  });

  const path = points.map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const circles = points
    .map(
      (p) =>
        `<circle cx="${p.x}" cy="${p.y}" r="2.8" fill="#005a70"><title>${p.label}: ${p.count}</title></circle>`,
    )
    .join("");

  elements.trendChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" class="sparkline" preserveAspectRatio="none">
      <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="rgba(23,34,45,0.25)" />
      <path d="${path}" fill="none" stroke="#005a70" stroke-width="2.5" stroke-linecap="round" />
      ${circles}
    </svg>
  `;
}

async function loadHealth() {
  try {
    await apiGet("/health");
    setHealth(true);
  } catch (_) {
    setHealth(false);
  }
}

async function loadSources() {
  const sources = await apiGet("/galleries/sources");
  renderSourceOptions(sources);
}

async function loadGalleries() {
  state.galleries = await apiGet("/galleries");
  renderGalleries();
}

async function loadBriefing() {
  const ids = selectedBoardIds();
  if (!ids.length) {
    message("Select at least one board to generate briefing.", true);
    return;
  }

  const query = new URLSearchParams();
  for (const id of ids) query.append("gallery_ids", String(id));
  query.set("window_hours", elements.briefWindowFilter.value || "24");
  query.set("limit", elements.briefLimitFilter.value || "20");

  state.briefing = await apiGet(`/briefing?${query.toString()}`);
  renderTopics(state.briefing.topics || []);
  renderTopicPosts([]);
}

async function runCollect() {
  const limit = parseInt(elements.fetchLimit.value || "100", 10);
  const result = await apiPost(`/ops/collect?limit=${limit}`, null, true);
  message(`Collect done: ${JSON.stringify(result)}`);
}

async function runRebuild() {
  const windowHours = parseInt(elements.windowHours.value || "24", 10);
  const result = await apiPost(`/ops/topics/rebuild?window_hours=${windowHours}`, null, true);
  message(`Rebuild done: run_id ${result.run_id}`);
}

async function loadTrend() {
  const galleryId = elements.trendGalleryFilter.value;
  if (!galleryId) {
    elements.trendChart.innerHTML = '<p class="trend-empty">Choose one board first.</p>';
    return;
  }
  const hours = elements.trendHours.value || "24";
  const trend = await apiGet(`/topics/trend?gallery_id=${encodeURIComponent(galleryId)}&hours=${hours}`);
  renderTrendChart(trend);
}

async function refreshAll() {
  try {
    await Promise.all([loadHealth(), loadSources(), loadGalleries()]);
  } catch (error) {
    message(error.message, true);
  }
}

function bindEvents() {
  elements.galleryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await apiPost("/galleries", {
        source_type: elements.sourceType.value,
        source_key: elements.sourceKey.value.trim(),
        display_name: elements.displayName.value.trim(),
        enabled: true,
      });
      elements.sourceKey.value = "";
      elements.displayName.value = "";
      await loadGalleries();
      message("Board added.");
    } catch (error) {
      message(error.message, true);
    }
  });

  elements.collectBtn.addEventListener("click", async () => {
    try {
      await runCollect();
    } catch (error) {
      message(error.message, true);
    }
  });

  elements.rebuildBtn.addEventListener("click", async () => {
    try {
      await runRebuild();
    } catch (error) {
      message(error.message, true);
    }
  });

  elements.briefingBtn.addEventListener("click", async () => {
    try {
      await loadBriefing();
    } catch (error) {
      message(error.message, true);
    }
  });

  elements.trendBtn.addEventListener("click", async () => {
    try {
      await loadTrend();
    } catch (error) {
      message(error.message, true);
    }
  });

  elements.refreshAllBtn.addEventListener("click", refreshAll);
}

async function init() {
  bindEvents();
  await refreshAll();
  elements.topicGrid.innerHTML =
    '<p class="trend-empty">Select boards and click "Generate Briefing".</p>';
  elements.trendChart.innerHTML = '<p class="trend-empty">Choose a board and load trend.</p>';
}

init();

