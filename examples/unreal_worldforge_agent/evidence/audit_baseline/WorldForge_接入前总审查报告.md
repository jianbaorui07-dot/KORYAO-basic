# WorldForge 接入前总审查报告

生成时间：2026-07-05 14:17:30 +08:00
执行阶段：第一阶段 - 读取和审查已有进度
结论：有条件可继续到下一阶段；不得启动原始项目；下一次 UE 启动必须仅针对增强副本，并使用一次性 -UDPMESSAGING_TRANSPORT_ENABLE=False，若日志或端口仍出现 UdpMessaging、0.0.0.0、组播或局域网地址则立即停止。

## 1. 路径确认

- Windows Desktop 真实路径：<USER_DESKTOP>
- WORLDFORGE_ROOT：<WORLDFORGE_ROOT>
- WORLDFORGE_ROOT 存在：True
- 本次新建审查目录：<WORLDFORGE_ROOT>\00_审查与基线
- 现有增强副本只读清单：<WORLDFORGE_ROOT>\00_审查与基线\现有增强副本只读清单_20260705_141729.csv

## 2. 当前 UE 版本与 exe

- UE Build.version：<UE_5_2_ROOT>\Engine\Build\Build.version
- 当前 UE 真实版本：5.2.1 (++UE5+Release-5.2)
- UE 5.2.1 exe 路径：<UE_5_2_ROOT>\Engine\Binaries\Win64\UnrealEditor.exe
- UE exe 存在：True
- 本阶段未启动 UE。

## 3. 原始项目、备份、增强副本

- 原始项目8真实路径：<ORIGINAL_PROJECT8>
- 原始 .uproject：<ORIGINAL_PROJECT8>\我的项目8.uproject
- 原始项目存在：True
- 原始项目文件数：75
- 原始项目字节数：14184723
- 原始项目 Source 存在：False
- 原始项目 Plugins 存在：False
- 备份路径：<WORLDFORGE_ROOT>\01_项目8原始备份
- 备份存在：True
- 备份文件数：75
- 备份只读文件数：75
- 原始项目与备份哈希差异数：0
- 当前既有增强副本路径：<WORLDFORGE_ROOT>\02_项目8_Codex增强版
- 当前既有增强副本存在：True
- 当前既有增强副本文件数：77
- 本次目标 WorldForge 增强副本路径：<WORLDFORGE_ROOT>\02_项目8_WorldForge增强版
- 本次目标 WorldForge 增强副本存在：False
- 说明：现有增强副本名为 02_项目8_Codex增强版，不是目标要求的 02_项目8_WorldForge增强版。后续不得覆盖现有增强副本；若严格执行目标路径，应新建或定位 02_项目8_WorldForge增强版 后再启动 UE。

## 4. 当前已有 WORLDFORGE_ROOT 顶层结构

- 目录: 00_审查与基线
- 目录: 00_审查与日志
- 目录: 01_项目8原始备份
- 目录: 02_项目8_Codex增强版
- 目录: 03_UE_MCP独立测试工程
- 目录: 04_本地MCP桥接
- 目录: 05_报告与说明
- 目录: 99_临时文件


## 5. 已阅读的既有报告

- <WORLDFORGE_ROOT>\99_临时文件\legacy_root_files_20260705_132931\Codex_UE_首次测试报告.md | 2026-07-04T22:01:09 | 1578 bytes
- <WORLDFORGE_ROOT>\99_临时文件\legacy_root_files_20260705_132931\UE_Codex_MCP_接入前审查报告.md | 2026-07-04T22:14:30 | 7778 bytes
- <WORLDFORGE_ROOT>\00_审查与日志\项目8接入前审查报告.md | 2026-07-05T13:35:11 | 2055 bytes
- <WORLDFORGE_ROOT>\00_审查与日志\项目8备份与增强副本复制报告_20260705_133559.md | 2026-07-05T13:35:59 | 7758 bytes
- <WORLDFORGE_ROOT>\00_审查与日志\项目8备份与增强副本复制报告_20260705_133650_corrected.md | 2026-07-05T13:36:52 | 667 bytes
- <WORLDFORGE_ROOT>\05_报告与说明\UE_Codex接入与项目8增强完成报告.md | 2026-07-05T13:49:43 | 6446 bytes


关键结论：

- UE_Codex接入与项目8增强完成报告.md 记录：原始项目未修改；全局 Codex 配置未修改；未安装软件；Remote Control 和 MCP 未创建。
- 上次停止原因：增强副本首次加载时 UE 默认 UdpMessaging 初始化，出现 0.0.0.0:0 -> 230.0.0.1:6666 和 192.168.0.104 局域网地址，因此停止后续 Remote Control / MCP。
- UE_Codex_MCP_接入前审查报告.md 记录：原项目是纯蓝图项目，没有 Source、Plugins、sln、Modules；本机未发现可用于安全编译 UE C++ 插件的完整 MSVC/MSBuild/Windows SDK 环境。
- 项目8备份与增强副本复制报告_20260705_133650_corrected.md 记录：原始、备份、增强副本初始哈希通过；本次现场复核确认原始项目与备份仍完全一致。
- 早期 项目8备份与增强副本复制报告_20260705_133559.md 显示复制差异，但已被后续修正版和本次现场复核覆盖。

## 6. 原始项目与备份一致性

- 可比较：True
- 原始文件数：75
- 备份文件数：75
- 差异数：0
- 结论：原始项目8与 WORLDFORGE_ROOT 备份当前一致，未发现哈希差异。

## 7. 原始项目与现有增强副本差异

- 可比较：True
- 原始文件数：75
- 增强副本文件数：77
- 差异数：4
- 主要差异：Intermediate\CachedAssetRegistry.bin、Saved\Logs、CrashReportClient 配置等 UE 首次加载产生的缓存/日志类文件。
- 结论：未发现 Content\WorldForge 或 Content\CodexIntegration；没有证据显示增强副本已创建 WorldForge 框架内容。

## 8. ue_python_api_probe.py 只读审查

- 存在：<WORLDFORGE_ROOT>\99_临时文件\ue_python_api_probe.py
- 未发现 requests/urllib/http/https/socket 外网访问关键字
- 未发现 pip/npm/install 安装关键字
- 未发现 subprocess/os.system/Popen/Start-Process 任意 shell 执行
- 未发现 remove/delete/rmtree/unlink 删除行为
- 未发现 0.0.0.0、局域网地址、listen()/bind() 网络监听行为
- 会创建 OUT_DIR；默认位于 WORLDFORGE_ROOT\99_临时文件，属于允许写入范围
- 会写入 ue_python_api_probe.json；默认位于 WORLDFORGE_ROOT\99_临时文件


审查结论：ue_python_api_probe.py 可判定为低风险探针脚本：不访问外网、不安装软件、不执行 shell、不删除文件、不监听网络；如将来执行，会在 WORLDFORGE_ROOT 的 99_临时文件 下写入一个 JSON 文件。未经后续阶段需要，不在本阶段执行。

## 9. 已存在风险

- 上次 UE 默认 UdpMessaging 曾出现 0.0.0.0、组播地址和局域网地址；这是继续流程的最高优先级风险。
- 当前目标要求的 02_项目8_WorldForge增强版 尚不存在，而旧增强副本为 02_项目8_Codex增强版；后续必须避免覆盖旧增强副本。
- 原项目是纯蓝图项目，无 Source/Plugins/Modules；不得创建 C++、Native Plugin 或编译路径。
- 原项目已有 Content\CodexTests 测试内容，这是既有状态；本次 WorldForge 内容不得修改旧内容。
- Remote Control 和 MCP 均未创建，后续必须等 UDP 隔离、UE 稳定、性能基线通过后再进入。

## 10. 是否可进入下一阶段

有条件可以继续。允许继续的边界如下：

1. 不启动原始项目8。
2. 不覆盖 02_项目8_Codex增强版。
3. 若需要严格满足本次目标路径，先在 WORLDFORGE_ROOT 内创建新的 02_项目8_WorldForge增强版 或确认已有目标路径后再启动 UE。
4. 启动 UE 前必须确认无 UnrealEditor.exe / UnrealEditor-Cmd.exe 残留、检查端口 30010/30020/8000/6666/30000。
5. 仅对增强副本使用一次性启动参数 -UDPMESSAGING_TRANSPORT_ENABLE=False。
6. 若 UE 日志或端口仍出现 UdpMessaging、0.0.0.0、230.0.0.1:6666、局域网地址或异常监听，立即停止并生成停止报告。

本阶段未执行：未启动 UE，未安装软件，未修改原始项目，未修改全局 Codex 配置，未修改系统设置，未启动 Remote Control，未创建 MCP。
