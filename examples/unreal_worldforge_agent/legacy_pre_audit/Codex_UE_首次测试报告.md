# Codex UE 首次测试报告

- UE 项目路径：<ORIGINAL_PROJECT8>\我的项目8.uproject
- 项目实际使用的 UE 版本：Unreal Engine 5.2.1（Build.version: Major 5, Minor 2, Patch 1, Changelist 26001984）
- 是否成功打开 UE：是
- 新建关卡路径：/Game/CodexTests/Codex_StarterScene
- 新建 Actor 名称列表：
  - CODEX_TEST_Floor
  - CODEX_TEST_Cube_Left
  - CODEX_TEST_Sphere_Center
  - CODEX_TEST_Cylinder_Right
  - CODEX_TEST_Light
  - CODEX_TEST_Camera
- 是否修改过旧资源：否
- 是否安装插件或修改系统：否
- 是否遇到弹窗、异常或需要人工确认的步骤：未遇到版本转换、插件缺失、编译、更新引擎、权限申请、异常报错或崩溃提示；远程执行节点不可用，因此改用项目已启用的 UE Python 控制台命令执行受控脚本。
- 当前 UE 是否仍保持打开状态：是，UnrealEditor 进程仍在运行并响应。

## 验证记录

- 新增项目内容：<ORIGINAL_PROJECT8>\Content\CodexTests\Codex_StarterScene.umap
- 旧 Content 资源修改检查：过去 2 小时内未发现 Content 下非 CodexTests 文件被改写。
- 外部产物目录：<WORLDFORGE_ROOT>
- 初始界面截图：Codex_UE_before_execute.png
- 最终 Viewport 截图：Codex_UE_viewport_final.png
- 执行脚本：Codex_UE_CreateStarterScene.py；Codex_UE_AdjustStarterSceneView.py
- 执行结果 JSON：Codex_UE_CreateStarterScene_result.json；Codex_UE_AdjustStarterSceneView_result.json
