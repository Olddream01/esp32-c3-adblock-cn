> **转载来自：<https://github.com/fengyindong/esp32-c3-adblock>**
> 上游原作者：<https://github.com/M-Abozaid/esp32-c3-adblock>（MIT 协议）
> 本仓库为**二次创作**，在上述中文版基础上重新编译固件并修复了若干问题。

## 🇨🇳 本仓库做了什么

项目链路：**M-Abozaid（原项目）→ fengyindong（中文翻译）→ 本仓库（定制固件）**

`docs/` 里放的不是上游 2026-07-26 的预编译固件，而是**重新编译的定制固件**。相对上游预编译版改了什么：

| 项目 | 上游预编译固件 | 本定制版 |
|---|---|---|
| DNS 上游 | Quad9 `9.9.9.9`，单点，一挂全挂 | **119.29.29.29 + 223.5.5.5 双路并发竞速**（DNSPod + 阿里，国内可达；谁先答用谁，一方挂了另一方顶上） |
| WiFi 配置 | 只存 NVS；开机 30 秒没连上就掉进配网门户，门户表单又是空的 —— 看上去像"每次重启都要重新配一次" | **NVS + LittleFS 双备份**；开机 3 次 × 20 秒重试；进门户后后台每 15 秒继续重连，路由器一恢复就自己接上 |
| 清空 WiFi 的触发 | 按住 BOOT 键 **60 毫秒**（插线时蹭一下就清空） | 按住 BOOT 键 **3 秒** |
| 面板口令 | 编译期写死，公开仓库里人人可读 | **整个取消**，面板的增删改接口不需要任何口令 |
| 网络 OTA 口令 | 同上 | **整个取消**，ArduinoOTA 也不设口令 |
| 封禁名单 | 约 5.7 万条（仓库构建时的旧快照） | **129,651 条**（官方每周一重建的周更列表） |
| 分区表 | app 槽位 1,376,256 B —— 新版 Arduino 核心编出的固件已经装不下了 | app 槽位加宽到 **1,572,864 B**，LittleFS 相应缩到 983,040 B（上限 19.6 万条域名） |

> ⚠️ **本固件没有任何口令。** 面板的增删改接口（封禁、加自定义域名、**上传固件**、改封禁列表）以及网络 OTA（ArduinoOTA）都不需要密码 —— 局域网里任何设备都能改你的配置、给你的板子刷进任意固件。**请只在可信网络（最好把板子放进访客 / IoT 隔离网段）里使用。**
>
> 仍然保留的一道防护：所有写操作要求请求带自定义头 `X-Requested-With: c3-adblock`，普通网页用 `<img>` 或自动提交的表单伪造不了它，**网页跨站攻击这条路是堵着的**（这不是认证，只是 CSRF 防护）。
>
> 顺带一提：上游那个 7 月的预编译固件**也完全没有认证**（`/ban` `/addblock` `/upload` `/update` `/forgetwifi` 全是裸的）；上游在 2026-10-04 的 PR #11 里补上了认证 + CSRF 防护，本版是**主动选择去掉**认证、只留 CSRF 那部分。

完整改动清单、实测数据与补丁文件见 **[定制版说明.md](定制版说明.md)**；源码级改动可以用 `git apply WiFi持久化补丁.diff` 复现。

### 一键网页刷机

1. 在仓库 **Settings → Pages** 开启 Pages（Source 选 `main` 分支、目录选 `/docs`）
2. 用**桌面版 Chrome 或 Edge** 打开 `https://olddream01.github.io/esp32-c3-adblock-cn/`
3. 点「⚡ 连接并安装」，选 ESP32-C3 的 COM 口，约 30 秒刷完
4. 手机连上 `C3-AdBlock-XXXX` 热点，在弹出的页面里填 WiFi 密码，点 Connect
5. 面板在 `http://c3adblock.local`（**不需要登录**）

> 不想开 Pages 也能刷：把 `docs/` 里的 7 个文件下到本地，起个静态服务器（`python -m http.server`）再打开 `index.html` 即可 —— 浏览器只要求 `localhost` 属于安全上下文，不需要 HTTPS。

### 校验刷机包

仓库里的 `校验固件包.py` 可以先跑一遍再刷：它会解析分区表二进制、核对 manifest 偏移、并把封禁名单从 `littlefs.bin` 里逐字节还原出来，确认 100% 完整。

```
python 校验固件包.py
```

### 自己编译

仓库里带的是**完整源码**（`src/`、`tools/`、`platformio.ini`、`partitions.csv`）：

```bash
python -m pip install -U platformio
cp src/secrets.example.h src/secrets.h      # 可以留空，走配网页面
python tools/build_blocklist.py data/blocklist.bin
pio run -e c3 -t upload
pio run -e c3 -t uploadfs
```

改上游 DNS 改 `platformio.ini` 里的 `-DUPSTREAM_IP=` 和 `-DUPSTREAM2_IP=` —— 两个地址会**并发竞速**，谁先答用谁。

### 直接下载

不想用网页刷机的，直接下 `release-assets/` 里的文件：

| 文件 | 说明 |
|---|---|
| [**Releases 页**](https://github.com/Olddream01/esp32-c3-adblock-cn/releases) | 版本化的下载入口，最新的是 `v2.1.0-cn`（双路上游 DNS） |
| [`release-assets/C3-AdBlock-定制版-119DNS.zip`](release-assets/C3-AdBlock-定制版-119DNS.zip) | 完整刷机包（2.1 MB）：固件文件 + 中文刷机页 + 一键启动脚本 + 串口日志工具 + 使用说明 |
| [`release-assets/WiFi持久化补丁.patch`](release-assets/WiFi持久化补丁.patch) | 相对上游 HEAD 的源码补丁（+173/-64），`git apply` 直接用 |

解锁 zip 后双击 `启动刷写.bat`，或把 `docs/` 里的 7 个文件单独下下来配 `manifest.json` 也能刷。

> Release 附件用的是纯 ASCII 文件名（`C3-AdBlock-Custom-119DNS.zip`、`WiFi-Persistence-Patch.patch` / `.diff`）—— GitHub 会把 Release 附件名里的中文替换成 `.`，所以两边名字不同，**内容完全一致**。

---

## 以下为上游项目文档（中文翻译版）

> **⚠️ 先看这一条（定制版与上游的差异）**
>
> 下面这一整节是**上游项目**的原文翻译。其中讲「Basic Auth 认证」「`secrets.h` 里的
> `WEB_PASS` / `OTA_PASS`」「默认凭据 `CHANGE_ME_WEB_PASSWORD`」的部分**只适用于上游**。
>
> **本定制版把面板口令和网络 OTA 口令整个去掉了** —— 固件里不存在 `WEB_PASS` / `OTA_PASS`，
> 也没有 Basic Auth 登录框，**不用去改 `secrets.h`**。留下来的只有一道 CSRF 头校验
> （写操作必须带 `X-Requested-With: c3-adblock`），它不是认证、也不是加密。
>
> 代价是：局域网里任何设备都能改你的封禁列表、给板子刷进任意固件。
> **请只在可信网络（最好放访客 / IoT 隔离网段）里用。**

esp32-c3-adblock
一个运行在 2 美元 ESP32-C3 上的 Pi-hole 风格 DNS 广告拦截器——无需 PSRAM。

📰 曾被 Tom's Hardware、XDA Developers 和 Korben 报道。

所有人都忽略的诀窍：你不需要把拦截名单放在 RAM 里。把域名存成排序好的 40 位哈希值放在 Flash 中，然后二分查找。14 万+ 域名只占约 0.7 MB Flash，匹配耗时约 10 ms，仅用约 50 KB RAM。

text
查询进入 ──▶ 提取域名 ──▶ FNV-1a 哈希（含父级后缀）
         ──▶ 在 Flash 哈希表中二分查找
              ├─ 命中  ──▶ 应答 0.0.0.0   （黑洞）
              └─ 未命中 ──▶ 转发给上游解析器，中继回复
为什么这个方案有意思
大多数 ESP32 DNS 黑洞方案会把拦截名单（域名字符串）加载进 RAM，因此需要 PSRAM。本项目改为在 Flash 中存储固定的 5 字节（40 位）哈希值：

字符串存 RAM 方案	本方案（哈希存 Flash）
硬件	ESP32 + PSRAM（约 8 美元）	ESP32-C3，无需 PSRAM（约 2 美元）
14.1 万域名	约 2.5 MB RAM	0.67 MB Flash
RAM 占用	几乎全部	约 50 KB
查找	字符串比较	约 18 次 Flash 读取（含 Wi-Fi RTT 约 10 ms）
碰撞	不适用	14.1 万时 0 次（53.7 万时 1 次）
为什么是 40 位？ 这是该 Flash 预算下的最佳平衡点。碰撞遵循生日悖论——14.1 万域名时约 0 次，53.7 万时约 1 次（即一个倒霉域名被过度拦截）。降到 32 位能省 20% Flash，但 25 万时会有约 7 次碰撞；升到 64 位则每个域名浪费 3 字节，去解决一个你根本不存在的问题。

同样的技巧在更大的芯片上也成立——它不是 C3 的变通方案。在 16 MB 的 ESP32-S3 上，这些哈希可容纳约 270 万域名，而 8 MB PSRAM 存字符串只能容纳约 46.6 万。哈希存 Flash 基本上在所有场景都优于字符串存 PSRAM；C3 只是让这一点无可辩驳。

硬件
任意 ESP32-C3 开发板（在 C3 SuperMini 上测试过），4 MB Flash，无需 PSRAM

经典 ESP32（DevKit / WROOM，4 MB）也可构建：pio run -e esp32dev -t upload（社区贡献，已编译测试；C3 是实测目标）

用稳定的 USB 电源供电（手机充电器或路由器的 USB 口）。劣质/松动的 USB-C→A 转接头会在 Wi-Fi 发射时导致射频欠压。

一个 USB-A → USB-C 转接头可以让它直接插进大多数路由器背面的空闲 USB 口——无需电源、无需额外盒子。

外壳
C3 SuperMini 的可打印外壳：hardware/esp32-c3-supermini-enclosure.stl

打印说明：

无需支撑；0.2 mm 层高、约 15% 填充即可。

保持天线端空旷。 C3 的 PCB 天线是 USB-C 口对侧短边上的锯齿状走线——不要把它埋进实心塑料里或在附近放金属，否则 RSSI 会变差。

保持通风口敞开：板子空闲时约 45–55 °C。

构建与烧录（PlatformIO）
一次 USB 烧录即可启动——之后固件和拦截名单都可通过 Wi-Fi 更新（见下文）。

⚠️ 使用较新的 PlatformIO——VSCode PlatformIO 插件自带的核，或在 venv 中 pip install -U platformio。发行版/apt 的 platformio 包（如 4.3.4）太旧，会报 AttributeError: ... 'resultcallback'（issue #4）。一键浏览器安装器正在开发中（托管待定）。

bash
# 1. 复制 secrets 模板（已被 gitignore，仅本地保留）并编辑：
#    - WIFI_SSID / WIFI_PASS 是可选的——保留占位符，改用设备上的
#      配网门户（见下文）。
#    - WEB_USER / WEB_PASS / OTA_PASS 不是可选的：它们保护仪表盘的状态变更
#      端点（/ban、/addblock、/upload、/update、/setupdate、/forgetwifi）
#      和网络 OTA。请设置真实值——这些端点以前对局域网内任何人都是敞开的。
cp src/secrets.example.h src/secrets.h
#    然后编辑 src/secrets.h

# 2. 构建拦截名单哈希表（默认 = StevenBlack base + Hagezi Light，
#    约 10 万条，对 WhatsApp/社交安全）
python3 tools/build_blocklist.py data/blocklist.bin

# 3. 烧录固件 + 拦截名单文件系统（唯一一次 USB 烧录）
pio run -t upload
pio run -t uploadfs

# 4. 观察启动，记下 IP / 打开仪表盘
pio device monitor          # -> http://c3adblock.local
使用自己的拦截名单
build_blocklist.py OUT.bin [SOURCE ...] 接受任意混合的 URL 和本地文件，支持以下格式：

hosts 文件——0.0.0.0 ads.example.com tracker.example.com（行内所有域名都会包含）

纯域名列表——每行一个域名

AdGuard / Adblock 基础规则——||ads.example.com^ 拦截，@@||ok.example.com^ 移除某个域名（例如镜像 AdGuard Home 的白名单）

被拦截的域名也会拦截其子域名。DNS 哈希列表无法表达的规则（正则、通配符、$ 修饰符、外观类 ## 规则）会被跳过并计数。@@ 规则只能取消拦截该精确条目——它无法从被拦截的父域名中单独放行子域名。如果某个来源无法下载，构建会停止而不是静默生成更小的列表（用 --allow-missing 覆盖）。

Wi-Fi 设置（无需重新烧录）
如果无法连接（或你从未设置 secrets.h），它会启动一个开放热点 C3-AdBlock-XXXX 并带强制门户——用手机加入，选择你的网络，输入密码，完成。以后要换网络：点击仪表盘上的 Forget WiFi，或上电时按住 BOOT 按钮，配网门户会重新出现。（/forgetwifi 现在需要认证，所以不再是可以直接访问的裸 URL——见下方安全说明。）

空中升级（不再需要 USB）
http://c3adblock.local 的仪表盘全部搞定：

拦截名单——把新构建的 blocklist.bin 拖进 Blocklist → Upload，或在 Remote auto-update 下设置 URL，设备会按计划拉取预构建的 blocklist.bin。默认名单由 GitHub Actions 每周一重新构建并发布到稳定 URL，粘贴一次即可让设备自行保持更新：
https://github.com/M-Abozaid/esp32-c3-adblock/releases/download/blocklist/blocklist.bin

固件——在 Firmware → OTA update 下上传 .pio/build/c3/firmware.bin；设备会校验并重启进入新镜像。或从命令行通过 Wi-Fi 推送：

bash
pio run -t upload --upload-port c3adblock.local --upload-protocol espota
4 MB Flash 的取舍： 固件 OTA 需要两个 app 分区，这给拦截名单留下约 1.3 MB（最多约 25 万域名）。激进的 53.7 万“终极”名单只能适配单 app 分区表（无固件 OTA）。在 partitions.csv 中选择你的取舍。

安全
仪表盘的只读视图（/、/stats.json）保持开放，但所有状态变更端点都需要 HTTP Basic Auth（来自 secrets.h 的 WEB_USER/WEB_PASS）：

/ban、/addblock、/unblock、/forgetwifi

/upload、/update（拦截名单和固件 OTA）

/setupdate、/fetchnow

网络 OTA（ArduinoOTA，如 pio run -t upload --upload-port c3adblock.local --upload-protocol espota）需要同一文件中的 OTA_PASS。

没有这些，局域网内任何能访问设备的人都能零凭据重刷任意固件或重写拦截名单——考虑到设备位于你网络每个 DNS 查询的路径上，这一点值得知道。自定义拦截域名在仪表盘渲染前也会做 HTML 转义，关闭了一条存储型 XSS 路径（否则通过 /addblock 添加的含标记的域名字符串会在查看浏览器中执行）。

这里的 Basic Auth 是局域网信任边界控制，不是加密。 所有内容都是 :80 上的明文 HTTP——这颗芯片没有现实预算跑 TLS 服务器。Basic Auth 凭据是 base64（非加密）且每个认证请求都会发送；任何能嗅探你局域网流量的人（开放/访客 Wi-Fi、ARP 欺骗）都能从线路上读到它们。这加固的是常见情况——你网络上的另一台设备零凭据访问 API，或浏览器标签页 CSRF——而不是路径上的网络攻击者。

缓存 Basic Auth 导致的 CSRF： 浏览器会自动把缓存的 Basic Auth 凭据附加到对已认证源的任何后续请求——包括同一浏览器稍后访问的完全无关页面触发的请求（例如 <img src="http://c3adblock.local/forgetwifi">，无需 JS）。这会让任何网页在你登录仪表盘一次后静默驱动此 API，无论谁在你的局域网上。上述每个变更端点现在还需要自定义 X-Requested-With: c3-adblock 头，普通 <img>/自动提交的 <form> CSRF 无法附加（只有同源 fetch() 可以，这正是仪表盘自己的 JS 所做的）——这就是为什么 /forgetwifi 不再是可以直接访问的裸 URL；请使用仪表盘按钮。

默认凭据： 如果 secrets.h 仍是 secrets.example.h 中的占位值 CHANGE_ME_WEB_PASSWORD / CHANGE_ME_OTA_PASSWORD，设备会以一个公开的“密码”启动（它就放在本仓库的示例文件里）。此时固件会通过串口打印警告并在仪表盘显示横幅——但它仍会启动运行，所以在不完全受控的网络上信任它之前，不要跳过在 secrets.h 中设置真实值。

目前不在范围内：Wi-Fi 配网门户的接入点（C3-AdBlock-XXXX）按设计仍是开放的（未加密）——它需要在不预先知道密码的情况下可加入。你在门户中输入的真实 Wi-Fi 密码，在短暂配网窗口内仅与那段本地无线电链路同等安全。

使用它
把某设备的 DNS 指向 C3 的 IP，或把它作为主 DNS 后面的辅助解析器。测试：

bash
dig @<c3-ip> doubleclick.net   # -> 0.0.0.0  （已拦截）
dig @<c3-ip> github.com        # -> 真实 IP  （已转发）
踩过的坑（血泪教训）
ModemManager（Fedora/Ubuntu 默认启用）会抢占 /dev/ttyACM0 并切换 DTR/RTS，导致 C3 复位并阻塞串口。修复：

bash
sudo systemctl stop ModemManager
echo 'ATTRS{idVendor}=="303a", ENV{ID_MM_DEVICE_IGNORE}="1"' | sudo tee /etc/udev/rules.d/99-esp-no-modemmanager.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
C3 的 USB-Serial-JTAG 控制台在主机连接前会吞掉早期启动输出（while(!Serial) 有帮助）。

DNS 客户端会添加 EDNS OPT 记录；被拦截的回复必须只包含问题 + 答案（ANCOUNT=1, NSCOUNT=ARCOUNT=0），否则格式错误。

已完成 / 未来可扩展
✅ Web 仪表盘——按客户端拦截/放行计数、封禁客户端、添加自定义域名

✅ mDNS（c3adblock.local）用于发现

✅ OTA——固件 + 拦截名单通过 Wi-Fi 更新，加上定时远程拉取拦截名单

✅ 强制门户 Wi-Fi 配网（无需硬编码凭据）+ 一键浏览器网页安装器

⬜ 分桶前缀索引——每次查找约 18 次 Flash 读取 → 约 1–2 次（issue #3），吞吐量提升

⬜ 充当 DHCP 服务器（把自己作为 DNS 分发出去）实现真正即插即用

致谢
灵感来自 s60sc/ESP32_AdBlocker——"对拦截名单域名应答 0.0.0.0" 的想法。本项目是独立从零实现，聚焦于无 PSRAM 芯片的哈希存 Flash 优化。