const STORAGE_KEY = "chat-garden-state-v1";

const defaultState = () => ({
  messages: [],
  seeds: [],
  metrics: {
    totalMessages: 0,
    userMessages: 0,
    gardenMessages: 0,
    seedUses: 0,
    lastInteraction: null,
    seedMatchReplies: 0,
    fallbackReplies: 0,
  },
  streak: {
    days: 0,
    lastTended: null,
  },
});

const state = loadState();

const ui = {
  feed: document.getElementById("message-feed"),
  composer: document.getElementById("composer"),
  messageInput: document.getElementById("message-input"),
  creativity: document.getElementById("creativity"),
  clearBtn: document.getElementById("clear-convo"),
  exportBtn: document.getElementById("export-data"),
  seedForm: document.getElementById("seed-form"),
  seedPrompt: document.getElementById("seed-prompt"),
  seedResponse: document.getElementById("seed-response"),
  seedTags: document.getElementById("seed-tags"),
  seedList: document.getElementById("seed-list"),
  metrics: document.getElementById("metrics"),
  heroSeeds: document.getElementById("seed-count"),
  heroStreak: document.getElementById("streak-count"),
  heroLastTended: document.getElementById("last-tended"),
};

bootstrap();

function bootstrap() {
  ensureSystemIntro();
  renderAll();
  wireEvents();
}

function wireEvents() {
  ui.composer.addEventListener("submit", (event) => {
    event.preventDefault();
    const content = ui.messageInput.value.trim();
    if (!content) return;

    const creativity = Number(ui.creativity.value);
    addMessage("user", content, { creativity });
    const reply = synthesizeResponse(content, creativity);
    addMessage("garden", reply.text, reply.meta);
    ui.messageInput.value = "";
    ui.messageInput.focus();
    renderAll();
    saveState();
  });

  ui.seedForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const prompt = ui.seedPrompt.value.trim();
    const response = ui.seedResponse.value.trim();
    if (!prompt || !response) return;

    const tags = ui.seedTags.value
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    const seed = {
      id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
      prompt,
      response,
      tags,
      createdAt: new Date().toISOString(),
      uses: 0,
    };

    state.seeds.unshift(seed);
    ui.seedForm.reset();
    refreshMetrics();
    renderAll();
    saveState();
  });

  ui.clearBtn.addEventListener("click", () => {
    if (state.messages.length <= 1) return;
    if (!confirm("Clear the conversation history?")) return;
    state.messages = state.messages.filter((msg) => msg.role === "system");
    state.metrics.totalMessages = state.messages.length;
    state.metrics.userMessages = 0;
    state.metrics.gardenMessages = 0;
    state.metrics.seedUses = 0;
    refreshMetrics();
    renderAll();
    saveState();
  });

  ui.exportBtn.addEventListener("click", () => {
    const payload = {
      generatedAt: new Date().toISOString(),
      state,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `chat-garden-export-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  });
}

function ensureSystemIntro() {
  if (!state.messages.length) {
    addMessage("system", "Welcome caretaker. Plant knowledge seeds and the garden will weave replies from what you teach.");
  }
}

function addMessage(role, content, meta = {}) {
  const createdAt = new Date().toISOString();
  state.messages.push({ role, content, createdAt, meta });
  state.metrics.totalMessages = state.messages.length;
  if (role === "user") state.metrics.userMessages += 1;
  if (role === "garden") state.metrics.gardenMessages += 1;
  if (meta.usedSeedId) state.metrics.seedUses += 1;
  state.metrics.lastInteraction = createdAt;
  state.streak.lastTended = createdAt;
  refreshStreak();
}

function synthesizeResponse(content, creativity) {
  const tokens = tokenize(content);
  const match = findBestSeed(tokens);
  const creativityFactor = creativity / 100;
  const tone = creativityFactor > 0.6 ? "imaginative" : creativityFactor > 0.3 ? "reflective" : "grounded";

  if (match) {
    match.seed.uses += 1;
    const blended = blendSeedResponse(match.seed.response, content, creativityFactor);
    return {
      text: blended,
      meta: {
        strategy: "seed-match",
        usedSeedId: match.seed.id,
        similarity: match.score.toFixed(2),
        tone,
      },
    };
  }

  const fallback = [
    "I am still sprouting context. Plant a seed in the ledger so I may answer with more depth next time.",
    "The garden is listening. Offer a prompt-response seed to teach me how to reply with your tone.",
    "No matching stories yet. Add a knowledge seed and I'll weave it into future replies.",
  ];

  const offset = Math.min(fallback.length - 1, Math.floor(creativityFactor * fallback.length));

  return {
    text: fallback[offset],
    meta: {
      strategy: "fallback",
      tone,
    },
  };
}

function tokenize(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .split(/\s+/)
    .filter(Boolean);
}

function findBestSeed(tokens) {
  if (!state.seeds.length || !tokens.length) return null;
  let best = null;

  for (const seed of state.seeds) {
    const seedTokens = tokenize(seed.prompt + " " + seed.response);
    const score = jaccardSimilarity(tokens, seedTokens);
    if (!best || score > best.score) {
      best = { seed, score };
    }
  }

  if (!best || best.score === 0) return null;
  return best;
}

function jaccardSimilarity(aTokens, bTokens) {
  const a = new Set(aTokens);
  const b = new Set(bTokens);
  const intersection = [...a].filter((token) => b.has(token)).length;
  const union = new Set([...a, ...b]).size;
  return union === 0 ? 0 : intersection / union;
}

function blendSeedResponse(seedResponse, prompt, creativityFactor) {
  if (creativityFactor < 0.25) return seedResponse;
  const reflections = [
    "I'm weaving your latest prompt into the memory lattice.",
    "The ledger glows with this addition—context deepens.",
    "Your care nourishes the dataset; my replies grow steadier.",
  ];
  const reflection = reflections[Math.floor(creativityFactor * reflections.length) % reflections.length];
  return `${seedResponse}\n\n<small>${reflection}</small>`;
}

function renderAll() {
  renderMessages();
  renderMetrics();
  renderSeeds();
  renderHero();
}

function renderMessages() {
  ui.feed.innerHTML = "";
  const template = document.getElementById("message-template");
  state.messages.forEach((message) => {
    const node = template.content.cloneNode(true);
    const article = node.querySelector(".message");
    article.classList.add(message.role);

    const avatar = node.querySelector("[data-role]");
    avatar.textContent = message.role === "garden" ? "🌱" : message.role === "system" ? "✴" : "🙂";

    node.querySelector("[data-author]").textContent =
      message.role === "garden" ? "Garden" : message.role === "system" ? "System" : "Caretaker";
    node.querySelector("[data-timestamp]").textContent = formatRelativeTime(message.createdAt);
    node.querySelector("[data-content]").innerHTML = sanitize(message.content);

    const footer = node.querySelector("[data-footer]");
    footer.innerHTML = buildFooter(message.meta, message.role);

    ui.feed.appendChild(node);
  });
  ui.feed.scrollTop = ui.feed.scrollHeight;
}

function sanitize(value) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(value, "text/html");
  return doc.body.innerHTML;
}

function buildFooter(meta = {}, role) {
  if (!meta) return "";
  const chips = [];
  if (meta.strategy) chips.push(`Strategy: ${meta.strategy}`);
  if (meta.tone) chips.push(`Tone: ${meta.tone}`);
  if (meta.creativity !== undefined && role === "user")
    chips.push(`Creativity: ${meta.creativity}`);
  if (meta.similarity) chips.push(`Similarity: ${meta.similarity}`);
  return chips.map((chip) => `<span>${chip}</span>`).join(" ");
}

function renderMetrics() {
  refreshMetrics();
  const mapping = {
    "total-messages": state.metrics.totalMessages,
    "user-messages": state.metrics.userMessages,
    "garden-messages": state.metrics.gardenMessages,
    "avg-seed-usage": state.seeds.length ? (state.metrics.seedUses / state.seeds.length).toFixed(2) : "0",
    "last-interaction": state.metrics.lastInteraction ? formatAbsoluteTime(state.metrics.lastInteraction) : "—",
    "seed-match-replies": state.metrics.seedMatchReplies,
    "fallback-replies": state.metrics.fallbackReplies,
    "seed-reuse-rate": state.metrics.gardenMessages
      ? `${Math.round((state.metrics.seedMatchReplies / state.metrics.gardenMessages) * 100)}%`
      : "0%",
  };

  Object.entries(mapping).forEach(([dataAttr, value]) => {
    const node = ui.metrics.querySelector(`[data-stat="${dataAttr}"]`);
    if (node) node.textContent = value;
  });
}

function renderSeeds() {
  ui.seedList.innerHTML = "";
  if (!state.seeds.length) {
    const empty = document.createElement("li");
    empty.textContent = "No seeds planted yet. Start by storing a prompt and response.";
    empty.className = "seed-card";
    ui.seedList.appendChild(empty);
    return;
  }

  state.seeds.slice(0, 6).forEach((seed) => {
    const item = document.createElement("li");
    item.className = "seed-card";

    const meta = document.createElement("div");
    meta.className = "seed-card__meta";
    meta.innerHTML = `<span>${formatAbsoluteTime(seed.createdAt)}</span><span>${seed.uses} uses</span>`;
    item.appendChild(meta);

    const prompt = document.createElement("p");
    prompt.className = "seed-card__prompt";
    prompt.textContent = seed.prompt;
    item.appendChild(prompt);

    const response = document.createElement("p");
    response.className = "seed-card__response";
    response.textContent = seed.response;
    item.appendChild(response);

    if (seed.tags.length) {
      const tags = document.createElement("div");
      tags.className = "seed-card__tags";
      seed.tags.forEach((tag) => {
        const chip = document.createElement("span");
        chip.textContent = tag;
        tags.appendChild(chip);
      });
      item.appendChild(tags);
    }

    ui.seedList.appendChild(item);
  });
}

function renderHero() {
  ui.heroSeeds.textContent = state.seeds.length;
  ui.heroLastTended.textContent = state.streak.lastTended
    ? formatAbsoluteTime(state.streak.lastTended)
    : "—";
  ui.heroStreak.textContent = `${state.streak.days} day${state.streak.days === 1 ? "" : "s"}`;
}

function refreshMetrics() {
  state.metrics.totalMessages = state.messages.length;
  state.metrics.userMessages = state.messages.filter((m) => m.role === "user").length;
  state.metrics.gardenMessages = state.messages.filter((m) => m.role === "garden").length;
  state.metrics.seedUses = state.seeds.reduce((acc, seed) => acc + seed.uses, 0);
  const gardenMessages = state.messages.filter((m) => m.role === "garden");
  state.metrics.seedMatchReplies = gardenMessages.filter((m) => m.meta?.strategy === "seed-match").length;
  state.metrics.fallbackReplies = gardenMessages.filter((m) => m.meta?.strategy === "fallback").length;
  state.metrics.lastInteraction = state.messages.length
    ? state.messages[state.messages.length - 1].createdAt
    : null;
}

function refreshStreak() {
  if (!state.streak.lastTended) {
    state.streak.days = 0;
    return;
  }
  const last = new Date(state.streak.lastTended);
  const now = new Date();
  const diff = Math.floor((now - last) / (1000 * 60 * 60 * 24));
  state.streak.days = diff >= 0 ? diff + 1 : 0;
}

function formatRelativeTime(iso) {
  if (!iso) return "just now";
  const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
  const date = new Date(iso);
  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.round(diffMs / 60000);
  if (Math.abs(diffMinutes) < 60) return formatter.format(-diffMinutes, "minute");
  const diffHours = Math.round(diffMinutes / 60);
  if (Math.abs(diffHours) < 24) return formatter.format(-diffHours, "hour");
  const diffDays = Math.round(diffHours / 24);
  return formatter.format(-diffDays, "day");
}

function formatAbsoluteTime(iso) {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);
    return {
      ...defaultState(),
      ...parsed,
      metrics: { ...defaultState().metrics, ...parsed.metrics },
      streak: { ...defaultState().streak, ...parsed.streak },
    };
  } catch (error) {
    console.warn("Unable to load saved state", error);
    return defaultState();
  }
}

function saveState() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        messages: state.messages,
        seeds: state.seeds,
        metrics: state.metrics,
        streak: state.streak,
      })
    );
  } catch (error) {
    console.warn("Unable to persist state", error);
  }
}
