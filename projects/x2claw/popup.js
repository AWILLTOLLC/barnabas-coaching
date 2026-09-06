// X2Claw popup: reads the active tab, extracts tweet text from the page DOM,
// and hands the payload to the background service worker for delivery.

const $ = (id) => document.getElementById(id);

const STATUS_RE = /^https?:\/\/(?:www\.)?(?:x|twitter)\.com\/(?:i\/web\/status\/|([A-Za-z0-9_]{1,20})\/status\/)(\d+)/;
const PREVIEW_LEN = 280;

const post = { url: "", text: "", author: "", onPost: false };

init();

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const tabUrl = tab?.url ?? "";
  $("url").textContent = tabUrl || "(no URL)";
  const m = tabUrl.match(STATUS_RE);
  if (!m) {
    $("nopost").classList.remove("hidden");
    return;
  }

  post.onPost = true;
  post.url = tabUrl.split("?")[0]; // strip tracking params
  post.author = m[1] ? "@" + m[1] : ""; // prefer the handle from the URL
  $("form").classList.remove("hidden");

  // Pull tweet text from the page DOM. activeTab (granted by clicking the
  // toolbar icon) lets us inject into this one tab on demand.
  try {
    const [res] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractTweetData,
    });
    const data = res?.result ?? {};
    if (!post.author) post.author = data.author || "";
    post.text = data.text || "";
  } catch { /* restricted page: URL-only send still works */ }

  if (post.text) {
    $("preview").classList.remove("empty");
    $("preview").textContent =
      post.text.length > PREVIEW_LEN
        ? post.text.slice(0, PREVIEW_LEN) + `… (+${post.text.length - PREVIEW_LEN} chars, full text sent)`
        : post.text;
  } else {
    $("preview").textContent = "Couldn't read tweet text from the page. The URL will still be sent.";
  }
  $("author").textContent = post.author;

  await loadAgents();
  $("send").addEventListener("click", send);
}

// Injected into the page. On a status page the first article is the main tweet;
// its tweetText precedes any quoted tweet's text in document order.
function extractTweetData() {
  const art = document.querySelector('article[data-testid="tweet"]');
  const textEl = art && art.querySelector('[data-testid="tweetText"]');
  let author = "";
  const nameEl = art && art.querySelector('[data-testid="User-Name"]');
  if (nameEl) {
    const m = nameEl.textContent.match(/@([A-Za-z0-9_]{1,20})/);
    if (m) author = "@" + m[1];
  }
  return { text: textEl ? textEl.innerText.trim() : "", author };
}

async function loadAgents() {
  const { agents = DEFAULT_AGENTS, lastAgent = "" } =
    await chrome.storage.local.get(["agents", "lastAgent"]);
  const sel = $("agent");
  for (const a of agents) {
    const opt = document.createElement("option");
    opt.value = a.slug;
    opt.textContent = a.name;
    sel.appendChild(opt);
  }
  if (lastAgent && agents.some((a) => a.slug === lastAgent)) sel.value = lastAgent;
  sel.addEventListener("change", () => chrome.storage.local.set({ lastAgent: sel.value }));
}

async function send() {
  const agent = $("agent").value;
  if (!agent) return setStatus("No agents configured. Add some in Options.", "err");

  const { promptPrefix = "" } = await chrome.storage.local.get("promptPrefix");
  const payload = {
    url: post.url,
    text: post.text,
    author: post.author,
    agent,
    prompt_prefix: promptPrefix,
  };

  $("send").disabled = true;
  setStatus("Sending…");
  let resp;
  try {
    resp = await chrome.runtime.sendMessage({ type: "x2claw/send", payload });
  } catch (err) {
    resp = { ok: false, error: err?.message || String(err) };
  }
  $("send").disabled = false;

  if (resp?.ok) setStatus(`Sent to ${agent} ✓`, "ok");
  else setStatus(resp?.error || "Send failed.", "err");
}

function setStatus(text, kind = "") {
  const el = $("status");
  el.textContent = text;
  el.className = kind;
}
