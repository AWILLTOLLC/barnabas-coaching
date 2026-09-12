const http = require('http');
const fs = require('fs');
const path = require('path');
const ROOT = __dirname;
const MIME = { '.html':'text/html', '.json':'application/json', '.md':'text/plain', '.js':'text/javascript' };
http.createServer((req, res) => {
  const urlPath = decodeURIComponent(req.url.split('?')[0]);
  let fp = path.join(ROOT, urlPath === '/' ? 'labeler.html' : urlPath);
  if (!fp.startsWith(ROOT)) { res.writeHead(403); return res.end('forbidden'); }
  fs.readFile(fp, (err, buf) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    // allow saving results back
    if (req.method === 'POST' && urlPath === '/results') {
      res.writeHead(200); return res.end('ok');
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(fp)] || 'application/octet-stream' });
    res.end(buf);
  });
}).listen(8787, "100.65.203.16", () => console.log('labeler serving at http://localhost:8787'));
