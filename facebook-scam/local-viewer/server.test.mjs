import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { readFile,readdir } from 'node:fs/promises';
import vm from 'node:vm';
import http from 'node:http';

test('local results: three examples, real files, range requests and access boundaries',async()=>{
  const child = spawn(process.execPath,[fileURLToPath(new URL('server.mjs',import.meta.url))],{env:{...process.env,FACEBOOK_VIEWER_PORT:'0'},stdio:['ignore','pipe','pipe']});
  let stderr='';child.stderr.on('data',chunk=>stderr+=chunk);
  try {
    const base = await new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(new Error('Server startup timeout: '+stderr)),10000);
      child.once('error',error=>{clearTimeout(timer);reject(error)});
      child.once('exit',code=>{clearTimeout(timer);reject(new Error('Server exit '+code+': '+stderr))});
      child.stdout.on('data',chunk=>{const match=String(chunk).match(/http:\/\/127\.0\.0\.1:\d+/);if(match){clearTimeout(timer);resolve(match[0])}});
    });
    const html=await (await fetch(base)).text();
    new vm.Script(html.match(/<script>([\s\S]*?)<\/script>/)[1]);
    assert.match(html,/不会访问 Facebook/);
    assert.equal((await fetch(base,{method:'POST'})).status,405);
    const badHostStatus=await new Promise((resolve,reject)=>{const request=http.get(base,{headers:{Host:'untrusted.example'}},response=>{response.resume();resolve(response.statusCode)});request.on('error',reject)});
    assert.equal(badHostStatus,403);
    const catalog=await (await fetch(base+'/api/accounts')).json();
    assert.deepEqual(catalog.accounts.map(a=>a.slug),['01_ray_hunt','02_belibisamantha','04_lisa_panetta_official']);
    assert.equal((await fetch(base+'/api/account/03_profile_61590550622121')).status,404);
    assert.equal((await fetch(base+'/api/account/not-collected')).status,404);
    assert.equal((await fetch(base+'/media/01_ray_hunt/text/..%5c..%5cREADME.md')).status,400);
    assert.equal((await fetch(base+'/media/03_profile_61590550622121/text/visible_text.txt')).status,404);
    assert.equal((await fetch(base+'/README.md')).status,404);
    for(const account of catalog.accounts){
      const result=await (await fetch(base+'/api/account/'+account.slug)).json();
      for(const [kind,files] of Object.entries(result.files)){
        const disk=await readdir(new URL('../data/final_accounts/'+account.slug+'/'+kind+'/',import.meta.url));
        for(const file of files)assert.ok(disk.includes(file.name));
      }
      const file=result.files.video[0]||result.files.image[0];
      assert.ok(file);
      const head=await fetch(base+file.url,{method:'HEAD'});
      assert.equal(head.status,200);assert.equal(Number(head.headers.get('content-length')),file.bytes);
      const range=await fetch(base+file.url,{headers:{range:'bytes=0-15'}});
      assert.equal(range.status,206);assert.equal((await range.arrayBuffer()).byteLength,16);
      const suffix=await fetch(base+file.url,{headers:{range:'bytes=-8'}});
      assert.equal(suffix.status,206);assert.equal((await suffix.arrayBuffer()).byteLength,8);
      assert.equal((await fetch(base+file.url,{headers:{range:'bytes=999999999999999-'}})).status,416);
    }
    const unknown=await readdir(new URL('../data/final_accounts/03_profile_61590550622121/',import.meta.url));
    assert.ok(unknown.includes('index.json'),'excluded account must still exist');
    const targets=JSON.parse(await readFile(new URL('../crawler/targets.json',import.meta.url),'utf8'));
    assert.equal(targets.length,4,'original target inventory is preserved');
  } finally {const exited=once(child,'exit');child.kill();await exited;}
});
