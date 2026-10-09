const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('C:/Users/10379/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root='D:/project/facebook/talking-head-lab';
const record='D:/project/NZ/cv/docs/change-records/2026-10-09-original-image-video';
const video=JSON.parse(fs.readFileSync(path.join(record,'video-job.json'),'utf8'));
const detect=JSON.parse(fs.readFileSync(path.join(record,'detection-job.json'),'utf8'));
const assert=require('node:assert/strict');
assert.equal(video.status,'done');assert.equal(video.result.scene,'original');assert.equal(detect.status,'done');
(async()=>{
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try {
    const context=await browser.newContext({viewport:{width:1280,height:900},locale:'zh-CN'});
    const page=await context.newPage();let replayed=[];
    await page.route('**/api/jobs',async route=>{
      const data=route.request().postDataJSON();
      assert.equal(route.request().method(),'POST');
      if(data.kind==='video'){
        assert.equal(data.model,'sadtalker');assert.equal(data.text,undefined);
        replayed.push({kind:'video',actual_job_id:video.id});
        await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(video)});
      }else{
        assert.equal(data.kind,'detect');assert.equal(data.use_truthscan,'false');
        replayed.push({kind:'detect',actual_job_id:detect.id});
        await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(detect)});
      }
    });
    await page.goto('http://localhost:3100/studio#video');
    await page.getByRole('heading',{name:'AI 人像视频',exact:true}).waitFor();
    await page.getByLabel('上传人像照片',{exact:true}).setInputFiles(path.join(root,'docs/showcase/synthetic-input.png'));
    await page.getByLabel('上传驱动语音',{exact:true}).setInputFiles(path.join(root,'docs/showcase/generated-voice.wav'));
    await page.getByRole('button',{name:'生成视频',exact:true}).click();
    await page.getByRole('button',{name:'检测这个视频',exact:true}).waitFor({state:'visible'});
    await page.waitForFunction(()=>document.querySelector('video.st-generated-video')?.readyState>=2);
    await page.locator('video.st-generated-video').evaluate(async video=>{video.muted=true;await video.play()});
    await page.waitForFunction(()=>document.querySelector('video.st-generated-video').currentTime>0.6);
    await page.locator('video.st-generated-video').evaluate(video=>video.pause());
    assert.ok(await page.getByText('原图直接交给模型，不额外替换背景。',{exact:false}).isVisible());
    await page.screenshot({path:path.join(root,'docs/showcase/video-original-zh.jpg'),fullPage:true,type:'jpeg',quality:90});
    await page.getByRole('combobox',{name:'选择语言',exact:true}).selectOption('en');
    await page.getByRole('heading',{name:'AI Portrait Video',exact:true}).waitFor();
    await page.screenshot({path:path.join(root,'docs/showcase/video-original-en.jpg'),fullPage:true,type:'jpeg',quality:90});
    await page.getByRole('combobox',{name:'Select language',exact:true}).selectOption('zh');
    await page.getByRole('button',{name:'检测这个视频',exact:true}).click();
    const cloud=page.getByRole('checkbox',{name:'使用 TruthScan 免费云端复核 视频会上传；每月免费 30 秒',exact:true});
    if(await cloud.isVisible())await cloud.uncheck();
    await page.getByRole('button',{name:'开始检测',exact:true}).click();
    await page.getByRole('heading',{name:'AI 生成倾向',exact:true}).waitFor();
    await page.locator('main video').evaluate(async video=>{video.muted=true;await video.play()});
    await page.waitForFunction(()=>document.querySelector('main video').currentTime>0.6);
    await page.locator('main video').evaluate(video=>video.pause());
    await page.screenshot({path:path.join(root,'docs/showcase/detect-original-zh.jpg'),fullPage:true,clip:{x:0,y:0,width:1280,height:1250},type:'jpeg',quality:90});
    await page.getByRole('combobox',{name:'选择语言',exact:true}).selectOption('en');
    await page.getByRole('heading',{name:'AI-generated likely',exact:true}).waitFor();
    await page.screenshot({path:path.join(root,'docs/showcase/detect-original-en.jpg'),fullPage:true,clip:{x:0,y:0,width:1280,height:1250},type:'jpeg',quality:90});
    assert.equal(replayed.length,2);
    fs.writeFileSync(path.join(record,'screenshot-capture.json'),JSON.stringify({method:'existing Playwright and Edge, isolated localhost screenshot context',user_permission:'可以，只截图',project_source_modified_for_capture:false,new_model_jobs_submitted:false,replayed_actual_completed_jobs:replayed,files:['video-original-zh.jpg','video-original-en.jpg','detect-original-zh.jpg','detect-original-en.jpg']},null,2));
    console.log('CURRENT_ORIGINAL_IMAGE_UI_SCREENSHOTS_CAPTURED_WITH_NO_SOURCE_CHANGE_OR_NEW_INFERENCE');
  }finally{await browser.close();}
})().catch(error=>{console.error(error.message);process.exit(1)});
