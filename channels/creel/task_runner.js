const WebSocket = require('/Users/apollo/.openclaw/extensions/vantage/node_modules/ws');

const TOKEN = 'f717336e074e27d107121780e32dac8dfabd4713fbf0bd7b';
const TASK_ID = 'task-temp-converter-' + Date.now();

// Temperature converter output
const tempConverterOutput = `
=== Temperature Converter ===

function toCelsius(f) { return (f - 32) * 5/9; }
function toFahrenheit(c) { return c * 9/5 + 32; }
function toKelvin(c) { return c + 273.15; }

Sample conversions:
  0°F  → ${((0-32)*5/9).toFixed(2)}°C  → ${((0-32)*5/9 + 273.15).toFixed(2)}K  (Freezing)
  32°F → ${((32-32)*5/9).toFixed(2)}°C  → ${((32-32)*5/9 + 273.15).toFixed(2)}K  (Water freezes)
  72°F → ${((72-32)*5/9).toFixed(2)}°C  → ${((72-32)*5/9 + 273.15).toFixed(2)}K  (Room temp)
  98.6°F → ${((98.6-32)*5/9).toFixed(2)}°C → ${((98.6-32)*5/9 + 273.15).toFixed(2)}K  (Body temp)
  212°F → ${((212-32)*5/9).toFixed(2)}°C → ${((212-32)*5/9 + 273.15).toFixed(2)}K  (Boiling)
  -40°F → ${((-40-32)*5/9).toFixed(2)}°C → ${((-40-32)*5/9 + 273.15).toFixed(2)}K  (F=C crossover)
`;

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function run() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket('ws://127.0.0.1:18789');
    let connected = false;
    let msgQueue = [];
    let pendingResolvers = {};
    let msgIdCounter = 1;

    function sendRpc(method, params) {
      const id = 'rpc-' + (msgIdCounter++);
      return new Promise((res, rej) => {
        pendingResolvers[id] = { res, rej };
        const msg = JSON.stringify({ type: 'req', id, method, params });
        console.log(`→ Sending: ${method} [${id}]`);
        ws.send(msg);
      });
    }

    ws.on('message', (raw) => {
      const msg = JSON.parse(raw.toString());
      console.log(`← Received:`, JSON.stringify(msg).slice(0, 200));

      if (msg.type === 'event' && msg.event === 'connect.challenge') {
        console.log('  Challenge received, sending connect...');
        const connectMsg = JSON.stringify({
          type: 'req', id: 'r1', method: 'connect',
          params: {
            minProtocol: 1, maxProtocol: 5,
            client: { id: 'gateway-client', version: '1.0.0', platform: 'linux', mode: 'backend' },
            caps: [], auth: { token: TOKEN },
            role: 'operator', scopes: ['operator.admin']
          }
        });
        ws.send(connectMsg);
        return;
      }

      if (msg.id === 'r1' && msg.type === 'res') {
        connected = true;
        console.log('  Connected! Starting task flow...');
        doTasks().then(resolve).catch(reject);
        return;
      }

      if (msg.id && pendingResolvers[msg.id]) {
        const { res, rej } = pendingResolvers[msg.id];
        delete pendingResolvers[msg.id];
        if (msg.error) rej(new Error(JSON.stringify(msg.error)));
        else res(msg.result);
      }
    });

    ws.on('error', reject);

    async function doTasks() {
      // 1. Register task
      console.log('\n[1] Registering task...');
      const reg = await sendRpc('vantage.task.register', {
        taskId: TASK_ID,
        channel: 'vantage-oc',
        name: 'Temperature Converter Demo'
      });
      console.log('  Registered:', JSON.stringify(reg));

      await sleep(2000);

      // 2. Attach proof
      console.log('\n[2] Attaching proof...');
      const proof = await sendRpc('vantage.task.proof', {
        taskId: TASK_ID,
        data: tempConverterOutput
      });
      console.log('  Proof attached:', JSON.stringify(proof));

      await sleep(2000);

      // 3. Mark complete
      console.log('\n[3] Marking complete...');
      const done = await sendRpc('vantage.task.complete', {
        taskId: TASK_ID
      });
      console.log('  Complete:', JSON.stringify(done));

      ws.close();
      console.log('\n✓ All three RPCs succeeded!');
      console.log('\nTask output:' + tempConverterOutput);
    }
  });
}

run().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
