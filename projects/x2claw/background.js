// X2Claw background service worker.
// Performs the webhook POST so the popup can close mid-send without killing
// the request. Results come back via sendResponse + a desktop notification.

const TIMEOUT_MS = 15000;

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type !== "x2claw/send") return; // not ours: ignore
  handleSend(msg.payload, msg.webhookUrl).then(sendResponse);
  return true; // keep the message channel open for the async reply
});

async function handleSend(payload, webhookOverride) {
  const stored = await chrome.storage.local.get(["webhookUrl", "hookToken"]);
  const webhook = webhookOverride || stored.webhookUrl;
  const hookToken = stored.hookToken || "";
  if (!webhook) return fail("No webhook URL configured. Open X2Claw options and set one.");
  let parsed;
  try { parsed = new URL(webhook); }
  catch { return fail("Webhook URL is not a valid URL."); }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:")
    return fail("Webhook URL must start with http:// or https://");

  const headers = {
    "Content-Type": "application/json",
    "Idempotency-Key": crypto.randomUUID(),
  };
  if (hookToken) headers["Authorization"] = `Bearer ${hookToken}`;

  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
    const res = await fetch(webhook, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
    clearTimeout(timer);
    const body = (await res.text()).slice(0, 300);
    if (res.ok) {
      notify(`Sent to ${payload.agent || "agent"}`, `Delivered (${res.status}).`);
      return { ok: true, status: res.status, body };
    }
    return fail(`Webhook answered ${res.status}: ${body || "(no body)"}`);
  } catch (err) {
    const reason = err?.name === "AbortError" ? "timed out" : `failed: ${err?.message || err}`;
    return fail(
      `Webhook ${reason}. If this keeps happening, re-save Options to grant the extension access to that host.`
    );
  }
}

function fail(message) {
  notify("X2Claw send failed", message);
  return { ok: false, error: message };
}

function notify(title, message) {
  try {
    chrome.notifications.create(`x2claw-${Date.now()}`, {
      type: "basic",
      iconUrl: "icon128.png",
      title,
      message,
    });
  } catch { /* notifications unavailable: popup still shows the result */ }
}
