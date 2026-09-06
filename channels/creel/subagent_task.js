const WebSocket = require('/Users/apollo/.openclaw/extensions/vantage/node_modules/ws');

const TOKEN = 'f717336e074e27d107121780e32dac8dfabd4713fbf0bd7b';
const TASK_ID = 'subagent-fortune-' + Date.now();

// Creative task: Fortune Cookie Wisdom Generator
// Generates 5 fortune cookie messages using word-scramble + reassembly logic
function generateFortunes() {
  const subjects = ['The patient coder', 'A quiet bug', 'Your next deploy', 'The empty loop', 'Midnight commits'];
  const verbs = ['reveals', 'teaches', 'echoes', 'remembers', 'outlasts'];
  const objects = ['what silence cannot', 'the logic you forgot', 'every deleted branch', 'the stack trace of fate', 'three cups of coffee'];
  const endings = ['🥠', '✨', '🔮', '🌙', '⚡'];

  const fortunes = [];
  for (let i = 0; i < 5; i++) {
    fortunes.push(`${subjects[i]} ${verbs[i]} ${objects[i]} ${endings[i]}`);
  }
  return fortunes;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  const ws = new WebSocket('ws://127.0.0.1:18789');
  let connected = false;
  const pending = {};
  let msgId = 1;

  function send(method, params) {
    return new Promise((resolve, reject) => {
      const id = 'r' + (msgId++);
      pending[id] = { resolve, reject };
      const msg = JSON.stringify({ type: 'req', id, method, params });
      console.log(`→ Sending [${id}] ${method}`);
      ws.send(msg);
      setTimeout(() => reject(new Error('Timeout for ' + id)), 15000);
    });
  }

  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    console.log(`← Received type=${msg.type} id=${msg.id || '?'} method=${msg.method || ''}`);

    if (msg.type === 'event' && msg.event === 'connect.challenge') {
      console.log('Challenge received, sending connect...');
      ws.send(JSON.stringify({
        type: 'req', id: 'r0', method: 'connect',
        params: {
          minProtocol: 1, maxProtocol: 5,
          client: { id: 'gateway-client', version: '1.0.0', platform: 'linux', mode: 'backend' },
          caps: [], auth: { token: TOKEN },
          role: 'operator', scopes: ['operator.admin']
        }
      }));
      return;
    }

    if (msg.type === 'res' && msg.id === 'r0') {
      console.log('Connected!', JSON.stringify(msg.result || msg.error));
      connected = true;
      return;
    }

    if (msg.type === 'res' && pending[msg.id]) {
      pending[msg.id].resolve(msg);
      delete pending[msg.id];
    }
  });

  ws.on('error', (err) => console.error('WS error:', err.message));

  // Wait for connection
  await new Promise((resolve) => {
    const check = setInterval(() => {
      if (connected) { clearInterval(check); resolve(); }
    }, 100);
    setTimeout(() => { clearInterval(check); resolve(); }, 10000);
  });

  if (!connected) {
    console.error('Failed to connect!');
    process.exit(1);
  }

  await sleep(2000);

  // Step 1: Register task
  console.log('\n--- Step 1: Register task ---');
  const regRes = await send('vantage.task.register', {
    taskId: TASK_ID,
    channel: 'vantage-oc',
    name: 'Fortune Cookie Wisdom Generator'
  });
  console.log('Register result:', JSON.stringify(regRes.result || regRes.error));

  await sleep(2000);

  // Step 2: Do the work
  console.log('\n--- Step 2: Generating fortunes ---');
  const fortunes = generateFortunes();
  const output = fortunes.map((f, i) => `${i + 1}. ${f}`).join('\n');
  console.log('Generated output:\n' + output);

  await sleep(2000);

  // Step 3: Attach proof
  console.log('\n--- Step 3: Attach proof ---');
  const proofRes = await send('vantage.task.proof', {
    taskId: TASK_ID,
    data: output
  });
  console.log('Proof result:', JSON.stringify(proofRes.result || proofRes.error));

  await sleep(2000);

  // Step 4: Mark complete
  console.log('\n--- Step 4: Mark complete ---');
  const completeRes = await send('vantage.task.complete', {
    taskId: TASK_ID
  });
  console.log('Complete result:', JSON.stringify(completeRes.result || completeRes.error));

  console.log('\n✅ All done!');
  ws.close();
  process.exit(0);
}

run().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
