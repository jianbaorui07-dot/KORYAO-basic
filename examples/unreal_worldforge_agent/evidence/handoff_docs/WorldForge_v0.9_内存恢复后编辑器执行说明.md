# WorldForge v0.9 内存恢复后编辑器执行说明

当前内存低于 6GB 时不得启动 UE。本文件只是恢复说明，不是完成证明。

等可用内存恢复后，执行顺序：

1. 确认只打开 `<WORLDFORGE_PROJECT_ROOT>\我的项目8.uproject`。
2. 不使用 UnrealEditor-Cmd.exe。
3. 不使用 load_level、OpenLevel、execute_console_command、ExecCmd、HighResShot。
4. 在正常 UE 编辑器完全打开并稳定后，手动通过 File > Execute Python Script 选择：
   `WorldForgeEditorScripts\WF0009_create_mountain_temple_scene_editor_only.py`
5. 脚本目标是创建：
   `/Game/WorldForge/Maps/v09/M_WF_MountainTemplePlayable_v09`
6. 脚本会生成真实几何寺庙、山体剪影、机器人、灯光、PlayerStart、TriggerBox 和 v0.9 材质资产。
7. 脚本执行后必须人工在 UE 中打开地图并进行 PIE 验证，确认玩家可移动、靠近触发器有可见互动变化。

当前状态：脚本已准备，未执行 UE，未创建真实 .umap/.uasset 成果。
