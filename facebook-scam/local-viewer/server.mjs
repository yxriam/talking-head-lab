import http from 'node:http';
import { readFile, readdir, realpath, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const dataRoot = path.join(root, 'data', 'final_accounts');
const types = { image: new Set(['.jpg','.jpeg','.png','.webp','.gif']), video: new Set(['.mp4','.webm','.mov']), audio: new Set(['.mp3','.wav','.m4a','.ogg']), text: new Set(['.txt','.json','.csv','.md']) };
const mime = { '.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.gif':'image/gif','.mp4':'video/mp4','.webm':'video/webm','.mov':'video/quicktime','.mp3':'audio/mpeg','.wav':'audio/wav','.m4a':'audio/mp4','.ogg':'audio/ogg','.txt':'text/plain; charset=utf-8','.json':'application/json; charset=utf-8','.csv':'text/plain; charset=utf-8','.md':'text/plain; charset=utf-8' };

function json(res, status, value) { res.writeHead(status, {'Content-Type':'application/json; charset=utf-8'}); res.end(JSON.stringify(value)); }
function inside(base, target) { const rel = path.relative(base,target); return rel !== '' && !rel.startsWith('..') && !path.isAbsolute(rel); }
async function targets() {
  const entries = JSON.parse((await readFile(path.join(root,'crawler','targets.json'),'utf8')).replace(/^\uFEFF/,''));
  const enabled = new Set(['01_ray_hunt','02_belibisamantha','04_lisa_panetta_official']);
  return entries.filter(t => typeof t.slug === 'string' && enabled.has(t.slug));
}
async function listFiles(slug) {
  const base = await realpath(dataRoot);
  const result = {};
  for (const [kind, extensions] of Object.entries(types)) {
    result[kind] = [];
    const dir = path.join(dataRoot,slug,kind);
    let entries;
    try { if (!inside(base,await realpath(dir))) continue; entries = await readdir(dir,{withFileTypes:true}); }
    catch(error) { if(error.code === 'ENOENT') continue; throw error; }
    for(const entry of entries) {
      if(!entry.isFile() || !extensions.has(path.extname(entry.name).toLowerCase())) continue;
      result[kind].push({name:entry.name,url:'/media/'+[slug,kind,entry.name].map(encodeURIComponent).join('/'),bytes:(await stat(path.join(dir,entry.name))).size});
    }
    result[kind].sort((a,b)=>a.name.localeCompare(b.name));
  }
  return result;
}

const server = http.createServer(async(req,res) => {
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Cache-Control','no-store');
  res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self'; media-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
  try {
    const allowedHosts = [`127.0.0.1:${server.address().port}`,`localhost:${server.address().port}`];
    if(!allowedHosts.includes(req.headers.host)) return json(res,403,{error:'不允许的访问地址'});
    if(req.method !== 'GET' && req.method !== 'HEAD') return json(res,405,{error:'仅支持读取'});
    const url = new URL(req.url,'http://127.0.0.1');
    if(url.pathname === '/api/health') return json(res,200,{app:'facebook-local-results',version:1});
    if(url.pathname === '/') { const html = await readFile(path.join(here,'index.html')); res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}); return res.end(req.method === 'HEAD' ? undefined : html); }
    if(url.pathname === '/api/accounts') {
      return json(res,200,{accounts:(await targets()).map(({slug,name,url})=>({slug,name,url})),mode:'existing-local-results'});
    }
    if(url.pathname.startsWith('/api/account/')) {
      const slug = decodeURIComponent(url.pathname.slice('/api/account/'.length));
      const account = (await targets()).find(t=>t.slug === slug);
      if(!account) return json(res,404,{error:'本地尚未收录该账号'});
      return json(res,200,{slug:account.slug,name:account.name,url:account.url,files:await listFiles(slug),mode:'existing-local-results'});
    }
    if(url.pathname.startsWith('/media/')) {
      const parts = url.pathname.slice(7).split('/').map(decodeURIComponent);
      if(parts.length !== 3 || parts.some(p=>!p || p === '.' || p === '..' || /[\\/\x00]/.test(p))) return json(res,400,{error:'无效文件路径'});
      const [slug,kind,name] = parts;
      if(!(await targets()).some(t=>t.slug === slug) || !types[kind]?.has(path.extname(name).toLowerCase())) return json(res,404,{error:'文件不存在'});
      const base = await realpath(dataRoot);
      const file = await realpath(path.join(dataRoot,...parts));
      if(!inside(base,file)) return json(res,403,{error:'文件不在结果目录中'});
      const info = await stat(file);
      if(!info.isFile()) return json(res,404,{error:'文件不存在'});
      let start = 0, end = info.size-1, status = 200;
      if(req.headers.range) {
        const match = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
        if(!match || (!match[1] && !match[2]) || info.size === 0) { res.setHeader('Content-Range',`bytes */${info.size}`); return json(res,416,{error:'无效读取范围'}); }
        if(!match[1]) start = Math.max(0,info.size-Number(match[2]));
        else { start = Number(match[1]); if(match[2]) end = Math.min(end,Number(match[2])); }
        if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>end||start>=info.size) { res.setHeader('Content-Range',`bytes */${info.size}`); return json(res,416,{error:'无效读取范围'}); }
        status = 206; res.setHeader('Content-Range',`bytes ${start}-${end}/${info.size}`);
      }
      res.writeHead(status,{'Content-Type':mime[path.extname(name).toLowerCase()],'Content-Length':info.size === 0 ? 0 : end-start+1,'Accept-Ranges':'bytes'});
      if(req.method === 'HEAD' || info.size === 0) return res.end();
      const stream = createReadStream(file,{start,end}); stream.on('error',()=>res.destroy()); res.on('close',()=>stream.destroy()); return stream.pipe(res);
    }
    return json(res,404,{error:'页面不存在'});
  } catch(error) { if(res.headersSent) return res.destroy(); json(res,error.code === 'ENOENT' ? 404 : 500,{error:error.code === 'ENOENT' ? '本地文件尚未找到' : '读取失败，请检查本地项目文件'}); }
});
server.on('error',error=>{ console.error(error.code === 'EADDRINUSE' ? 'Port is in use. Close the existing viewer or choose another port.' : error.message); process.exit(1); });
server.listen(Number(process.env.FACEBOOK_VIEWER_PORT || 8765),'127.0.0.1',()=>console.log(`Facebook local results: http://127.0.0.1:${server.address().port}`));
