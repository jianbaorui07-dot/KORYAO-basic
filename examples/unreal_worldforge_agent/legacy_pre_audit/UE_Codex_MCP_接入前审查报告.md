# UE Codex MCP 接入前审查报告

生成时间：2026-07-04

## 1. 审查范围

- UE 项目：`<ORIGINAL_PROJECT8>\我的项目8.uproject`
- UE 实际运行程序：`<UE_5_2_ROOT>\Engine\Binaries\Win64\UnrealEditor.exe`
- 目标接入方式：Codex Native MCP，仅限本机 `localhost` / `127.0.0.1`
- 本阶段执行方式：只读检查；未安装、未克隆、未写配置、未启动服务、未编译。

## 2. 项目结构检查

检查结果：

- `.uproject`：存在
- `Config/`：存在
- `Content/`：存在
- `Saved/`：存在
- `Intermediate/`：存在
- `Source/`：不存在
- `Plugins/`：不存在
- `.sln`：未发现
- `.uproject` 内未发现 `Modules` 字段

结论：当前项目是纯蓝图项目，不是 C++ 项目。

目录规模：

- `Config/`：7 个文件，43,775 bytes
- `Content/`：6 个文件，177,954 bytes
- `Saved/`：46 个文件，381,625 bytes
- `Intermediate/`：13 个文件，13,326,849 bytes

## 3. UE 版本与运行状态

检查结果：

- Unreal Editor 进程：正在运行
- 进程 ID：4684
- 窗口标题：`我的项目8 - 虚幻编辑器`
- 响应状态：Responding = True
- `Build.version`：
  - MajorVersion = 5
  - MinorVersion = 2
  - PatchVersion = 1
  - Changelist = 26001984
  - BranchName = `++UE5+Release-5.2`

结论：当前实际 UE 版本为 Unreal Engine 5.2.1。

未保存内容检查：

- 外部进程检查确认 UE 仍打开并响应。
- 前台截图 `UE_Codex_MCP_audit_ue_foreground.png` 显示当前地图为 `Codex_StarterScene`，未看到保存确认、崩溃、编译、插件缺失或版本转换弹窗。
- 为避免通过 UE 控制台执行只读 Python 命令而改写 `Saved\Config\ConsoleHistory.ini`，本阶段未调用 Editor API 枚举 dirty packages。

结论：未发现明显未保存提示；但未使用 UE 内部 dirty package API 做强证明。进入任何写入或关闭 UE 步骤前，仍建议人工确认保存状态。

## 4. C++ 编译环境检查

Visual Studio / Build Tools：

- `vswhere.exe`：未发现
- `C:\Program Files\Microsoft Visual Studio`：不存在
- `C:\Program Files (x86)\Microsoft Visual Studio`：不存在
- `C:\BuildTools`：不存在
- `D:\Microsoft Visual Studio`：不存在
- `cl.exe`：不在 PATH
- `msbuild.exe`：不在 PATH

Windows SDK：

- `C:\Program Files (x86)\Windows Kits\10`：存在
- `Include/`：不存在
- `Lib/`：不存在
- 未发现可用于 C++ 编译的完整 Windows SDK Include/Lib 目录。

UnrealBuildTool：

- `<UE_5_2_ROOT>\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.dll`：存在
- `<UE_5_2_ROOT>\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe`：存在
- `<UE_5_2_ROOT>\Engine\Binaries\ThirdParty\DotNet\6.0.302\windows\dotnet.exe`：存在
- `<UE_5_2_ROOT>\Engine\Build\BatchFiles\Build.bat`：存在

系统 DotNet：

- `dotnet.exe`：存在于 `C:\Program Files\dotnet\dotnet.exe`

结论：UE 自带 UBT 存在，但本机未发现 MSVC C++ 编译器、MSBuild 或完整 Windows SDK Include/Lib，因此当前不具备直接安全编译 UE 原生 C++ 插件的完整环境。

## 5. 磁盘空间检查

项目目录：

- 项目大小约：0.013 GB
- 备份一份项目预计至少需要：0.013 GB

磁盘剩余：

- C: `Windows-SSD`：约 141.07 GB 可用，总 400 GB
- D: `Data`：约 374.46 GB 可用，总 551.64 GB

结论：磁盘空间足够做项目级备份，也足够放置插件源码；但编译能力受缺少 MSVC/SDK 阻断。

## 6. Codex 配置检查

检查文件：

- `<CODEX_HOME>\config.toml`：存在，已只读读取。

关键检查：

- 未发现 `mcp` 配置项。
- 未发现 `default_tools_approval_mode`。
- 未发现 `127.0.0.1`、`localhost`、`3000` 相关 MCP 地址。

结论：当前 Codex 配置中未发现已配置的 UE MCP 连接；本阶段未修改该文件。

## 7. 端口 3000 检查

检查结果：

- 未发现本机 TCP 端口 3000 连接或监听项。

结论：当前没有端口 3000 冲突。

## 8. 已有 Python 脚本用途分析

脚本目录：

- `<WORLDFORGE_ROOT>`

脚本 1：`Codex_UE_CreateStarterScene.py`

- 用途：在 UE 内创建 `/Game/CodexTests/Codex_StarterScene`，生成地面、Cube、Sphere、Cylinder、Point Light、Camera Actor，并保存当前新关卡。
- 写入范围：`/Game/CodexTests/Codex_StarterScene` 及外部结果 JSON。
- 风险点：会新建关卡并写入 UE Content；不能重复执行，因为脚本内已检查目标地图存在并拒绝覆盖。
- 本阶段状态：只分析，未执行，未修改。

脚本 2：`Codex_UE_AdjustStarterSceneView.py`

- 用途：加载 `/Game/CodexTests/Codex_StarterScene`，查找 `CODEX_TEST_Camera` 和 `CODEX_TEST_Light`，调整相机和灯光位置并保存当前关卡。
- 写入范围：仅新建测试关卡内的相机、灯光及外部结果 JSON。
- 风险点：会修改并保存 `Codex_StarterScene`；不应在只读审查阶段执行。
- 本阶段状态：只分析，未执行，未修改。

## 9. 当前直接接入风险判断

A. 是否可以直接接入：

否。当前项目是纯蓝图项目，且本机缺少 MSVC C++ 编译器、MSBuild 和完整 Windows SDK。按安全规则，不能直接创建项目级 Native MCP C++ 插件、不能自动转 C++、不能自动编译。

B. 是否必须把项目转成 C++：

如果目标是在当前项目内编译 Native MCP 插件，是。当前项目没有 `Source/`、没有 `.sln`、没有 `Modules` 字段。根据既定规则，纯蓝图项目需要先停止并等待确认，不能自动转为 C++。

C. 是否必须安装 Visual Studio C++ 组件：

是。若要在本机编译 UE 原生 C++ 插件，需要安装或补齐 Visual Studio C++ Build Tools、MSVC 工具链、MSBuild 和完整 Windows SDK。当前安全规则禁止自动安装，因此只能由用户确认并手动处理或另行授权。

D. 是否存在端口冲突：

否。端口 3000 当前未被占用。

E. 哪些动作风险最低：

1. 保持当前项目不变，只保留本次只读审查结果。
2. 若继续评估 Native MCP，优先新建独立 MCP 测试项目，而不是直接接入当前项目。
3. 先读取第三方仓库 README / LICENSE / 目录结构和 UE 版本要求，再决定是否接入。
4. 如必须接入当前项目，先关闭 UE、确认保存、备份整个项目目录，再人工确认是否转 C++。
5. MCP 监听必须限定 `127.0.0.1:3000`，Codex 工具审批必须保持 prompt，不允许自动批准危险操作。

F. 推荐“当前项目接入”还是“新建独立 MCP 测试项目”：

推荐新建独立 MCP 测试项目。

原因：

- 当前项目是纯蓝图项目，直接接入 Native MCP 会触发转 C++ / 插件编译 / 工程生成等高风险步骤。
- 当前本机缺少完整 C++ 编译环境，直接在当前项目上推进会很容易卡在工具链和编译问题上。
- 独立测试项目可以验证 Native MCP 插件、localhost 监听、Codex 配置和只读工具调用，不影响当前项目旧内容。

## 10. 审查结论

当前不建议直接对 `我的项目8` 执行 Native MCP 接入。

建议路径：

1. 停在当前只读审查状态，等待用户确认。
2. 若用户确认继续，优先选择“新建独立 MCP 测试项目”路线。
3. 若用户坚持当前项目接入，必须先备份当前项目，并在用户明确确认后再讨论是否转 C++ 和补齐编译环境。

本阶段未执行：

- 未安装任何软件。
- 未克隆 GitHub 仓库。
- 未创建 `Plugins/` 或 `Source/`。
- 未修改 `.uproject`。
- 未修改 `<CODEX_HOME>\config.toml`。
- 未启动 MCP 服务。
- 未打开远程访问。
- 未绑定 `0.0.0.0`、局域网 IP 或公网 IP。
- 未编译项目。
