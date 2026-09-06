// X2Claw options: webhook URL, hook token, prompt prefix, agent list.

const $ = (id) => document.getElementById(id);

init();

async function init() {
  const { webhookUrl = "", hookToken = "", promptPrefix = "", agents = null } =
    await chrome.storage.local.get(["webhookUrl", "hookToken", "promptPrefix", "agents"]);
  $("webhook").value = webhookUrl;
  $("token").value = hookToken;
  $("prefix").value = promptPrefix;
  $("agents").value = agentsToText(agents ?? DEFAULT_AGENTS);
  $("save").addEventListener("click", save);
  $("test").addEventListener("click", test);
}

function agentsToText(agents) {
  return agents
    .map((a) => (a.name && a.name.toLowerCase() !== a.slug ? `${a.name} | ${a.slug}` : a.slug))
    .join("\n");
}

function parseAgents(text) {
  const out = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const [namePart, slugPart] = line.split("|").map((s) => s.trim());
    const slug = (slugPart || namePart).toLowerCase().replace(/[^a-z0-9_-]/g, "");
    if (!slug) continue;
    out.push({ name: namePart || slug, slug });
  }
  return out;
}

async function save() {
  const webhookUrl = $("webhook").value.trim();
  const hookToken = $("token").value.trim();
  const promptPrefix = $("prefix").value;
  const agents = parseAgents($("agents").value);

  if (webhookUrl) {
    try { new URL(webhookUrl); }
    catch { return setStatus("Webhook URL is not a valid URL.", "err"); }
  }
  if (!agents.length) return setStatus("Add at least one agent.", "err");

  await chrome.storage.local.set({ webhookUrl, hookToken, promptPrefix, agents });

  // Ask once for access to the webhook host so the service worker can POST
  // there. Denied access means sends to this host will fail until allowed.
  let granted = true;
  if (webhookUrl) {
    const origin = new URL(webhookUrl).origin + "/*";
    const has = await chrome.permissions.contains({ origins: [origin] });
    granted = has || (await chrome.permissions.request({ origins: [origin] }));
  }
  if (granted) setStatus("Saved ✓", "ok");
  else setStatus("Saved, but host access was denied. Sends to this webhook will fail until you allow it.", "warn");
}

async function test() {
  const webhookUrl = $("webhook").value.trim();
  if (!webhookUrl) return setStatus("Set a webhook URL first.", "err");
  try { new URL(webhookUrl); }
  catch { return setStatus("Webhook URL is not a valid URL.", "err"); }

  $("test").disabled = true;
  setStatus("Pinging webhook…");
  let resp;
  try {
    resp = await chrome.runtime.sendMessage({
      type: "x2claw/send",
      webhookUrl, // test what's in the box, not what's saved
      payload: {
        url: "x2claw://test",
        text: "Test ping from X2Claw options.",
        author: "",
        agent: "test",
        prompt_prefix: $("prefix").value,
      },
    });
  } catch (err) {
    resp = { ok: false, error: err?.message || String(err) };
  }
  $("test").disabled = false;
  if (resp?.ok) setStatus(`Webhook answered ${resp.status} ✓`, "ok");
  else setStatus(resp?.error || "Test failed.", "err");
}

function setStatus(text, kind = "") {
  const el = $("status");
  el.textContent = text;
  el.className = kind;
}
