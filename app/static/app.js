const state = {
  galleries: [],
  topics: [],
  selectedTopicId: null,
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
  topicGrid: document.getElementById("topicGrid"),
  topicPosts: document.getElementById("topicPosts"),
  topicGalleryFilter: document.getElementById("topicGalleryFilter"),
  topicWindowFilter: document.getElementById("topicWindowFilter"),
  topicLimitFilter: document.getElementById("topicLimitFilter"),
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

function buildHeaders(includeJson = false, includeApiKey = false) {
  const headers = {};
  if (includeJson) {
    headers["Content-Type"] = "application/json";
  }
  if (includeApiKey) {
    const apiKey = getApiKey();
    if (apiKey) {
      headers["X-API-Key"] = apiKey;
    }
  }
  return headers;
}

async function apiGet(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return res.json();
}

async function apiPost(path, payload = null, includeApiKey = false) {
  const opts = {
    method: "POST",
    headers: buildHeaders(Boolean(payload), includeApiKey),
  };
  if (payload) {
    opts.body = JSON.stringify(payload);
  }
  const res = await fetch(path, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} failed: ${res.status} ${text}`);
  }
  return res.json();
}

function setOpsMessage(text, isError = false) {
  elements.opsResult.textContent = text;
  elements.opsResult.style.color = isError ? "#7f1d1d" : "";
}

function renderHealth(ok) {
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
  if (!state.galleries.length) {
    elements.galleriesList.innerHTML = '<p class="trend-empty">등록된 소스가 없습니다.</p>';
    return;
  }

  for (const gallery of state.galleries) {
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <h5>${gallery.display_name}</h5>
      <p>${gallery.source_type} / ${gallery.source_key}</p>
      <p>ID: ${gallery.id}</p>
    `;
    elements.galleriesList.appendChild(item);
  }

  const topicFilter = elements.topicGalleryFilter;
  const trendFilter = elements.trendGalleryFilter;
  topicFilter.innerHTML = '<option value="">All</option>';
  trendFilter.innerHTML = '<option value="">Select</option>';
  for (const gallery of state.galleries) {
    const optionA = document.createElement("option");
    optionA.value = String(gallery.id);
    optionA.textContent = gallery.display_name;
    topicFilter.appendChild(optionA);

    const optionB = document.createElement("option");
    optionB.value = String(gallery.id);
    optionB.textContent = gallery.display_name;
    trendFilter.appendChild(optionB);
  }
}

function trendPillClass(trend) {
  if (trend === "up") return "up";
  if (trend === "down") return "down";
  return "stable";
}

function renderTopics() {
  elements.topicGrid.innerHTML = "";
  if (!state.topics.length) {
    elements.topicGrid.innerHTML = '<p class="trend-empty">토픽이 없습니다. Collect/Rebuild를 먼저 실행해보세요.</p>';
    return;
  }

  for (const topic of state.topics) {
    const node = elements.topicCardTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector("h4").textContent = topic.title;
    const pill = node.querySelector(".trend-pill");
    pill.classList.add(trendPillClass(topic.trend));
    pill.textContent = topic.trend.toUpperCase();
    node.querySelector(".topic-summary").textContent = topic.summary;
    node.querySelector(".topic-meta").textContent =
      `score ${topic.score.toFixed(3)} | confidence ${topic.confidence.toFixed(2)} | gallery ${topic.gallery_id}`;

    const keywords = node.querySelector(".topic-keywords");
    for (const word of topic.keywords || []) {
      const k = document.createElement("span");
      k.className = "keyword";
      k.textContent = word;
      keywords.appendChild(k);
    }

    node.addEventListener("click", () => {
      state.selectedTopicId = topic.id;
      loadTopicPosts(topic.id);
    });

    elements.topicGrid.appendChild(node);
  }
}

function renderTopicPosts(posts) {
  elements.topicPosts.innerHTML = "";
  if (!posts.length) {
    elements.topicPosts.innerHTML = '<p class="trend-empty">대표 글이 없습니다.</p>';
    return;
  }
  for (const post of posts) {
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <a class="post-link" href="${post.url}" target="_blank" rel="noreferrer">${post.rank}. ${post.title}</a>
      <p>${new Date(post.published_at).toLocaleString()}</p>
      <p>up ${post.upvote_count} / comments ${post.comment_count} / views ${post.view_count}</p>
    `;
    elements.topicPosts.appendChild(item);
  }
}

function renderTrendChart(items) {
  if (!items.length) {
    elements.trendChart.innerHTML = '<p class="trend-empty">트렌드 데이터가 없습니다.</p>';
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
  const last = points[points.length - 1];

  elements.trendChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" class="sparkline" preserveAspectRatio="none">
      <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="rgba(23,34,45,0.25)" />
      <path d="${path}" fill="none" stroke="#005a70" stroke-width="2.5" stroke-linecap="round" />
      ${circles}
      <text x="${last.x - 6}" y="${last.y - 9}" font-size="10" fill="#005a70">${last.count}</text>
    </svg>
  `;
}

async function loadSources() {
  const sources = await apiGet("/galleries/sources");
  renderSourceOptions(sources);
}

async function loadGalleries() {
  state.galleries = await apiGet("/galleries");
  renderGalleries();
}

async function loadTopics() {
  const q = new URLSearchParams();
  if (elements.topicGalleryFilter.value) {
    q.set("gallery_id", elements.topicGalleryFilter.value);
  }
  q.set("window_hours", elements.topicWindowFilter.value || "24");
  q.set("limit", elements.topicLimitFilter.value || "50");
  state.topics = await apiGet(`/topics?${q.toString()}`);
  renderTopics();
}

async function loadTopicPosts(topicId) {
  const posts = await apiGet(`/topic/${topicId}/posts`);
  renderTopicPosts(posts);
}

async function loadTrend() {
  const galleryId = elements.trendGalleryFilter.value;
  if (!galleryId) {
    elements.trendChart.innerHTML = '<p class="trend-empty">먼저 Gallery를 선택해주세요.</p>';
    return;
  }
  const hours = elements.trendHours.value || "24";
  const trend = await apiGet(`/topics/trend?gallery_id=${encodeURIComponent(galleryId)}&hours=${hours}`);
  renderTrendChart(trend);
}

async function refreshAll() {
  try {
    await Promise.all([loadHealth(), loadSources(), loadGalleries()]);
    await loadTopics();
    if (state.selectedTopicId) {
      await loadTopicPosts(state.selectedTopicId);
    }
  } catch (err) {
    setOpsMessage(err.message, true);
  }
}

async function loadHealth() {
  try {
    await apiGet("/health");
    renderHealth(true);
  } catch (_) {
    renderHealth(false);
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
      setOpsMessage("Source added.");
      await loadGalleries();
    } catch (err) {
      setOpsMessage(err.message, true);
    }
  });

  elements.collectBtn.addEventListener("click", async () => {
    try {
      const limit = parseInt(elements.fetchLimit.value || "100", 10);
      const result = await apiPost(`/ops/collect?limit=${limit}`, null, true);
      setOpsMessage(`Collect complete: ${JSON.stringify(result)}`);
      await loadTopics();
    } catch (err) {
      setOpsMessage(err.message, true);
    }
  });

  elements.rebuildBtn.addEventListener("click", async () => {
    try {
      const hours = parseInt(elements.windowHours.value || "24", 10);
      const result = await apiPost(`/ops/topics/rebuild?window_hours=${hours}`, null, true);
      setOpsMessage(`Rebuild complete: run_id ${result.run_id}`);
      await loadTopics();
    } catch (err) {
      setOpsMessage(err.message, true);
    }
  });

  elements.topicGalleryFilter.addEventListener("change", loadTopics);
  elements.topicWindowFilter.addEventListener("change", loadTopics);
  elements.topicLimitFilter.addEventListener("change", loadTopics);
  elements.trendBtn.addEventListener("click", loadTrend);
  elements.refreshAllBtn.addEventListener("click", refreshAll);
}

async function init() {
  bindEvents();
  await refreshAll();
  elements.trendChart.innerHTML = '<p class="trend-empty">Gallery를 고르고 Load를 눌러주세요.</p>';
}

init();

