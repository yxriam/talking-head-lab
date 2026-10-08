# AI 人像视频网站：从零安装、日常启动与排错

这份说明按“第一次安装”和“以后每天使用”分开写。当前这台电脑已经完成第一次安装，平时直接看第二部分即可。

## 1. 先认识网站的组成

网站由三层组成：

1. **网页前端**运行在 Windows，地址是 `http://localhost:3100/studio`。
2. **AI 后端**运行在 WSL2 的 Ubuntu 22.04 中，由网页代理连接当前 WSL 地址。
3. **模型**保存在 Ubuntu 的 `/opt/media-models`，生成任务使用 NVIDIA 显卡。

主要功能和实际执行位置如下：

| 功能 | 执行方式 |
|---|---|
| 音色克隆 | Ubuntu 本地 Chatterbox，使用显卡 |
| AI 人像视频 | Ubuntu 本地 SadTalker / EchoMimic V1，或腾讯 TokenHub HumanActor API |
| 媒体真伪检测 | Ubuntu 本地 GenD、NPR、UCF、RECCE、F3-Net，并结合频谱和连续性分析 |
| 网页界面 | Windows 上的 Node.js / vinext |
| 爬取信息 | Windows 上的 Python + Playwright，独立采集队列 |

Windows 中的源代码只有一份，位于 `D:\project\NZ\cv`。需要更新 Ubuntu 后端时，脚本只复制有变化的运行文件，不会在 Ubuntu 中再次执行 `git clone` 或 `git pull`。

## 2. 当前电脑每天怎么启动

### 方法一：推荐的一键启动

1. 打开 Windows 开始菜单。
2. 输入“PowerShell”，打开普通的 Windows PowerShell。平时不需要选择“以管理员身份运行”。
3. 逐行复制下面两条命令，每行输入后按一次回车：

```powershell
Set-Location D:\project\NZ\cv
powershell -ExecutionPolicy Bypass -File .\local-media\start-local.ps1
```

启动脚本会按顺序完成这些事情：

1. 启动 `Ubuntu-22.04`。
2. 创建一个隐藏的 WSL 保持进程，防止后端在空闲时随 WSL 自动退出。
3. 启动 `local-media.service` 后端服务。
4. 自动读取当前 WSL 地址并检查 8002 后端。
5. 让网页代理直接连接该地址，日常启动不再反复修改端口转发。
6. 启动网页前端并等待它真正可访问。
7. 自动打开 `http://localhost:3100/studio`。

看到下面的文字，就表示启动完成：

```text
5/5 Startup complete.
Website: http://localhost:3100/studio
Backend: http://当前WSL地址:8002 (proxied through the website)
```

如果浏览器没有自动打开，手动复制这个地址到浏览器：

```text
http://localhost:3100/studio
```

如果只想启动服务，不想自动打开浏览器：

```powershell
powershell -ExecutionPolicy Bypass -File .\local-media\start-local.ps1 -NoBrowser
```

### 启动后做一次快速检查

在 PowerShell 中运行：

```powershell
curl.exe http://localhost:3100/api/health
```

命令应返回 JSON，且其中包含 `"status":"ok"`。该请求经过网页代理，可以同时证明网页和后端之间已经连通。

进入网站后还可以做最小测试：

1. 打开“音色克隆”，上传参考语音并输入一小段文字。
2. 生成语音后进入“AI 人像视频”，选择一张清晰正脸照片和刚才生成的语音。
3. 选择 SadTalker 做本地快速测试，或选择 HumanActor 测试云端高质量模式。
4. 视频生成后点击“直接检测”，无需下载再上传。
5. 在“视频真伪检测”页也可以上传其他视频。

## 3. 怎么正确停止

正常关闭浏览器页面不会停止服务。如果之后还要继续使用，可以让它保持运行。

要完整停止 Ubuntu 后端和 WSL 保持进程，在 PowerShell 中运行：

```powershell
wsl --terminate Ubuntu-22.04
```

然后停止占用 3100 端口的网页进程：

```powershell
$listenerProcessId = (Get-NetTCPConnection -LocalPort 3100 -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($listenerProcessId) { Stop-Process -Id $listenerProcessId }
```

下次仍然使用第二部分的一键启动命令。不要直接结束不认识的 Python 或 Node 进程。

## 4. 第一次在新电脑上安装

本节只用于重装电脑或复制到另一台设备。当前电脑已经做完，可以跳过。

### 4.1 硬件和系统要求

- Windows 11，或支持 WSL2 的 Windows 10。
- NVIDIA 显卡和较新的 Windows NVIDIA 驱动。
- 建议至少 12 GB 显存、32 GB 内存、100 GB 可用磁盘空间。
- 项目放在 `D:\project\NZ\cv`。如果换了路径，需要同步修改脚本中的 `/mnt/d/project/NZ/cv`。
- 能访问 GitHub、PyPI 和模型权重下载地址的网络。

显存主要决定可运行的模型和分辨率；内存用于视频帧、模型载入和中间结果；磁盘用于多个模型仓库、Python 环境、权重和生成文件。

### 4.2 安装 WSL2 与 Ubuntu 22.04

以管理员身份打开 PowerShell，运行：

```powershell
wsl --install -d Ubuntu-22.04
```

如果 Microsoft Store 下载失败，可以运行项目内的安装脚本：

```powershell
Set-Location D:\project\NZ\cv
powershell -ExecutionPolicy Bypass -File .\local-media\install-ubuntu.ps1 -WebDownload
```

安装要求重启时先重启 Windows。重启后从开始菜单打开 Ubuntu，创建 Linux 用户名和密码。Linux 密码输入时屏幕不会显示圆点或星号，这是正常现象。

检查安装结果：

```powershell
wsl --status
wsl --list --verbose
```

列表中的 `Ubuntu-22.04` 应为版本 `2`。如果不是，运行：

```powershell
wsl --set-version Ubuntu-22.04 2
```

### 4.3 检查显卡是否能被 Ubuntu 使用

NVIDIA 驱动安装在 Windows。不要在 WSL 中另装一套 Linux NVIDIA 内核驱动。

```powershell
nvidia-smi
wsl -d Ubuntu-22.04 -- nvidia-smi
```

两处都应显示显卡名称和显存。当前设备曾验证为 RTX 5070 Ti Laptop GPU、约 12 GB 显存。

### 4.4 安装 Ubuntu 基础依赖

以管理员身份打开 PowerShell，运行：

```powershell
Set-Location D:\project\NZ\cv
powershell -ExecutionPolicy Bypass -File .\local-media\prepare-linux.ps1
```

这个步骤安装 Python 3.10、虚拟环境、编译工具和 FFmpeg。完成后查看日志：

```powershell
Get-Content .\local-media\linux-prepare.txt -Tail 30
```

日志中应出现 `PREPARE_COMPLETE` 和 `ExitCode: 0`。

### 4.5 下载并安装本地模型

下面步骤耗时最长，也最占磁盘。逐条运行，上一条完成后再运行下一条：

```powershell
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task setup-models
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-generators
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-echomimic
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-detectors
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-npr
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-gend
```

每一步都会生成同名日志，例如 `setup-models.log` 和 `setup-models-error.log`。首次安装时下载可能持续几十分钟到数小时。不要因为一段时间没有新输出就反复重新运行；先查看任务管理器中的网络、磁盘和 GPU 使用情况以及日志末尾。

模型统一保存在：

```text
/opt/media-models
```

项目脚本会复用已存在的模型，不会在日常启动时重新下载，也不会反复调用 Git。

### 4.6 安装并注册后端服务

运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task activate-api
```

这个步骤会：

- 将必要运行文件从 Windows 同步到 `/opt/media-app/local-media`；
- 创建后端 Python 虚拟环境；
- 安装 API 依赖；
- 运行后端测试；
- 创建无登录权限的 `media-app` 服务账户；
- 注册并启动 `local-media.service`。

检查服务：

```powershell
wsl -d Ubuntu-22.04 -u root -- systemctl status local-media.service --no-pager
```

状态应为 `active (running)`。

### 4.7 安装前端依赖

安装 Node.js 22 LTS，然后重新打开 PowerShell，检查：

```powershell
node --version
npm --version
```

`node --version` 应为 `v22.13.0` 或更高版本。进入前端目录并安装依赖：

```powershell
Set-Location D:\project\NZ\cv\facebook-scam\video-forensics-web
npm install
npm run build
```

构建成功后返回项目根目录：

```powershell
Set-Location D:\project\NZ\cv
```

### 4.8 可选：配置腾讯 TokenHub HumanActor

本地 SadTalker、EchoMimic 和检测功能不依赖 TokenHub。只有使用云端 HumanActor 时才需要本节。

需要准备：

- TokenHub API Key；
- 腾讯云 CAM 子用户的 `SecretId` 和 `SecretKey`；
- 一个 COS 存储桶及其地域。

密钥配置文件只保存在 Ubuntu 的：

```text
/etc/media-app/tokenhub.env
```

权限应为 `600`，不要把密钥写入 Git、网页代码、截图或聊天记录。配置项名称如下：

```text
TOKENHUB_API_KEY=
TENCENT_COS_SECRET_ID=
TENCENT_COS_SECRET_KEY=
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET=你的存储桶名称
```

先创建安全配置文件：

```powershell
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/configure-tokenhub-service.sh
```

如果 CAM 密钥下载成 CSV，可以用导入脚本避免在终端显示密钥。将下面的 CSV 路径换成实际文件名：

```powershell
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/project/cv/local-media/import_cos_credentials.py /mnt/c/Users/你的Windows用户名/Downloads/密钥文件.csv /etc/media-app/tokenhub.env
```

把 TokenHub API Key 单独放在只有一行内容的文本文件中，再运行：

```powershell
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/project/cv/local-media/import_env_secret.py TOKENHUB_API_KEY /mnt/c/Users/你的Windows用户名/Downloads/tokenhub-key.txt /etc/media-app/tokenhub.env
```

存储桶名称和地域可以用下面的命令编辑：

```powershell
wsl -d Ubuntu-22.04 -u root -- nano /etc/media-app/tokenhub.env
```

在 nano 中按 `Ctrl+O` 保存，按回车确认，再按 `Ctrl+X` 退出。最后重启服务：

```powershell
wsl -d Ubuntu-22.04 -u root -- systemctl restart local-media.service
```

HumanActor 会把输入媒体临时上传到 COS，取得腾讯 API 可访问的 URL。任务完成后程序会删除临时对象。接口参数使用官方兼容格式，例如 `audio_url` 和 `image_base64`。

### 4.9 首次建立 Windows 到 WSL 的本地连接

用管理员 PowerShell 运行：

```powershell
Set-Location D:\project\NZ\cv
powershell -ExecutionPolicy Bypass -File .\local-media\repair-local-network.ps1
```

脚本只建立 `127.0.0.1:8002` 到当前 WSL 地址的转发，并为 8002 端口创建受限的 WSL Hyper-V 防火墙规则。网站不会直接监听局域网地址。

之后执行第二部分的一键启动。WSL IP 改变时，一键脚本会再次弹出管理员确认并自动更新这条转发。

## 5. 修改代码后怎么更新

### 只修改网页前端

关闭并重新启动网页进程即可。最简单的做法是完整停止，再运行一键启动脚本。开发服务器通常也会自动刷新页面。

### 修改 `local-media` 后端

先同步有变化的文件，再重启服务：

```powershell
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/sync-runtime.sh
wsl -d Ubuntu-22.04 -u root -- systemctl restart local-media.service
```

`sync-runtime.sh` 会逐文件计算 SHA256，只复制内容发生变化的文件，不删除目标文件，也不执行任何 Git 网络操作。
它还会自动恢复 Linux shell 脚本的可执行权限，避免 systemd 出现 `203/EXEC`。

如果修改了 `requirements.txt`，重新运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task activate-api
```

## 6. 日志和任务文件在哪里

### 网页日志

```text
D:\project\NZ\cv\local-media\web.log
D:\project\NZ\cv\local-media\web-error.log
```

查看最后 100 行：

```powershell
Get-Content D:\project\NZ\cv\local-media\web.log -Tail 100
Get-Content D:\project\NZ\cv\local-media\web-error.log -Tail 100
```

### 后端服务日志

```powershell
wsl -d Ubuntu-22.04 -u root -- journalctl -u local-media.service -n 100 --no-pager
```

持续观察新日志，按 `Ctrl+C` 退出：

```powershell
wsl -d Ubuntu-22.04 -u root -- journalctl -u local-media.service -f
```

### 上传、生成和检测文件

实际运行目录是：

```text
/opt/media-app/local-media/data
```

每个任务有独立目录和状态文件。文件不会自动清理。确认不再需要时再手动删除具体任务目录，不要删除 `/opt/media-models`。

## 7. 常见问题

### 页面显示“无法连接本地服务”

先重新运行一键启动脚本。它会启动服务并在必要时修复 WSL IP 转发。

仍然失败时依次运行：

```powershell
wsl --list --verbose
wsl -d Ubuntu-22.04 -u root -- systemctl status local-media.service --no-pager
curl.exe http://127.0.0.1:8002/health
```

如果服务是 `active`，但 curl 无法连接，以管理员身份运行：

```powershell
powershell -ExecutionPolicy Bypass -File D:\project\NZ\cv\local-media\repair-local-network.ps1
```

### 启动一会儿后又无法连接

这是 WSL 自动退出的典型表现。新版 `start-local.ps1` 会启动隐藏的 `sleep infinity` 保持进程，并把其 Windows PID 记录在 `.wsl-keeper.pid`。不要手动结束这个 `wsl.exe` 进程；需要停止时使用第三部分的命令。

### 浏览器提示空响应或 JSON 提前结束

通常是网页代理还在，但 Ubuntu 后端已经停止。重新运行一键启动脚本，然后检查两条健康地址。

### 提示 `AudioUrl is invalid`

当前代码已经改为 TokenHub 官方兼容参数名，并为 COS 音频对象设置正确的 Content-Type。先同步后端并重启：

```powershell
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/sync-runtime.sh
wsl -d Ubuntu-22.04 -u root -- systemctl restart local-media.service
```

如果仍失败，查看后端日志，并确认 COS 存储桶、地域和 CAM 权限对应同一个账号及地域。

### systemd 显示 `status=203/EXEC` 或 `Permission denied`

这表示后端启动脚本没有 Linux 可执行权限。当前同步脚本会自动修复。运行：

```powershell
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/sync-runtime.sh
wsl -d Ubuntu-22.04 -u root -- systemctl reset-failed local-media.service
wsl -d Ubuntu-22.04 -u root -- systemctl restart local-media.service
```

### 提示没有 Node.js 或 `node` 不是命令

一键脚本会先尝试系统 Node.js，再尝试当前 Codex 自带的 Node.js。新电脑复现时应安装 Node.js 22 LTS。安装后关闭并重新打开 PowerShell，让 PATH 更新。

### 3100 端口已被占用

先检查是不是网站已经启动：

```powershell
curl.exe http://localhost:3100/studio
```

能返回网页内容就不需要再次启动。如果端口被其他程序使用：

```powershell
Get-NetTCPConnection -LocalPort 3100 -State Listen | Select-Object OwningProcess
```

在任务管理器中根据 PID 确认程序身份后再关闭它。

### 8002 端口无法连接

检查后端和转发：

```powershell
wsl -d Ubuntu-22.04 -u root -- systemctl status local-media.service --no-pager
netsh interface portproxy show v4tov4
```

端口转发表中应有 `127.0.0.1  8002`。如果连接地址与 `wsl -d Ubuntu-22.04 -- hostname -I` 的第一个地址不同，运行网络修复脚本。

### 生成速度很慢或显存不足

先运行：

```powershell
wsl -d Ubuntu-22.04 -- nvidia-smi
```

确认模型使用的是 NVIDIA GPU。SadTalker 适合快速本地验证；EchoMimic V1 更慢；HumanActor 的速度还受上传和云端排队影响。不要同时提交多个大任务，当前后端会顺序执行 GPU 推理。

### 管理员窗口被取消

只有修复 Windows 端口转发时需要管理员确认。取消后不会修改系统设置，但网站可能继续无法连接。准备好后重新运行 `repair-local-network.ps1` 或一键启动脚本。

## 8. 安全和数据注意事项

- 网站只通过 `localhost` / `127.0.0.1` 提供给本机使用。
- 不要提交、复制或截图 `/etc/media-app/tokenhub.env` 的内容。
- CAM 子用户只授予所需 COS 存储桶和 TokenHub 调用权限。
- 本地生成结果和上传文件不会自动清理。
- 语音克隆和人像生成只使用已获得授权的声音、照片和视频。
- 检测结果是模型证据汇总，不是经过现实数据校准的法律结论；模型分歧时网站会显示“不确定”。

## 9. 最常用命令速查

启动全部：

```powershell
Set-Location D:\project\NZ\cv
powershell -ExecutionPolicy Bypass -File .\local-media\start-local.ps1
```

检查全部：

```powershell
curl.exe http://127.0.0.1:8002/health
curl.exe http://localhost:3100/api/health
```

查看后端日志：

```powershell
wsl -d Ubuntu-22.04 -u root -- journalctl -u local-media.service -n 100 --no-pager
```

后端代码更新后同步：

```powershell
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/sync-runtime.sh
wsl -d Ubuntu-22.04 -u root -- systemctl restart local-media.service
```

停止 Ubuntu：

```powershell
wsl --terminate Ubuntu-22.04
```
