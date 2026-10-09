// Screenshot the existing UI with the bounded run's public excerpt. No source edits or model calls.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/10379/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root='D:/project/facebook/talking-head-lab';
const record=__dirname;
const job=JSON.parse(fs.readFileSync(path.join(record,'public-ui-job.json'),'utf8'));
const receipt=JSON.parse(fs.readFileSync(path.join(record,'collection-receipt.json'),'utf8'));
const out=path.join(root,'docs/showcase/facebook-trump');
assert.equal(job.status,'done');assert.equal(job.result.analysis,undefined);
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'zh-CN'});
 const page=await context.newPage();const calls=[];
 try{
  page.on('request',req=>{
   const url=new URL(req.url());
   if(url.pathname.startsWith('/crawl/')){
    calls.push({method:req.method(),path:url.pathname});
    assert.equal(req.method(),'GET','Screenshots must not submit crawl, login or analysis jobs');
   }
  });
  await page.route('**/api/**',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Inference is not used for collection screenshots"}'}));
  await page.goto('http://localhost:3101/studio#crawl');
  await page.getByRole('heading',{name:'采集结果',exact:true}).waitFor();
  await page.getByText('Donald J. Trump',{exact:true}).waitFor();
  await page.getByLabel('Facebook 链接',{exact:true}).fill(job.source_url);
  await page.getByLabel('采集范围',{exact:true}).selectOption('4');
  assert.equal(await page.locator('.st-crawl-history button').count(),1);
  const capture=async(name)=>{
   const box=await page.locator('.st-crawl-layout > .st-input-card').boundingBox();
   const result=await page.locator('.st-crawl-layout > .st-result-card').boundingBox();
   const width=1440;
   const height=Math.min(1000,Math.ceil(Math.max(box.y+box.height,result.y+result.height)));
   await page.screenshot({path:path.join(out,name),type:'jpeg',quality:92,clip:{x:0,y:0,width,height}});
  };
  await capture('text-zh.jpg');
  await page.getByRole('combobox',{name:'选择语言',exact:true}).selectOption('en');
  await page.getByRole('heading',{name:'Collection result',exact:true}).waitFor();
  await capture('text-en.jpg');
  await page.getByRole('tab',{name:/Images 11/}).click();
  await page.waitForFunction(()=>Array.from(document.querySelectorAll('.st-crawl-media img')).filter(img=>img.complete && img.naturalWidth>0).length>=4);
  await capture('images-en.jpg');
  await page.getByRole('combobox',{name:'Select language',exact:true}).selectOption('zh');
  await capture('images-zh.jpg');
  await page.getByRole('combobox',{name:'选择语言',exact:true}).selectOption('en');
  await page.getByRole('tab',{name:/Videos 7/}).click();
  await page.getByText('Source link only or download failed',{exact:true}).first().waitFor();
  await capture('video-links-en.jpg');
  await page.getByRole('combobox',{name:'Select language',exact:true}).selectOption('zh');
  await capture('video-links-zh.jpg');
  fs.writeFileSync(path.join(record,'screenshot-receipt.json'),JSON.stringify({
   permission:'用户已明确允许现有工具只截图，不改业务源码、不安装工具、不再次推理',
   actual_job_id:job.id,local_url:'http://localhost:3101/studio#crawl',
   method:'Existing Playwright/Edge; real localhost UI/API loading public excerpt of actual completed direct collector run',
   collector_service_online_during_capture:true,source_changed_for_screenshots:false,
   new_model_jobs:false,network_calls:calls,files:['text-zh.jpg','text-en.jpg','images-zh.jpg','images-en.jpg','video-links-zh.jpg','video-links-en.jpg']},null,2));
  console.log('SIX_REAL_RESULT_UI_SCREENSHOTS_READY; real API GET only, no project source changes');
 }finally{await browser.close();}
})().catch(error=>{console.error(error.stack);process.exit(1)});
