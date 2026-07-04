# Blender 三维场景桥

这个目录是 Blender bridge 的技术占位。当前 maturity 是 `planned/prototype`，提供本机只读 probe、基础场景 dry-run 计划和参考图重建 dry-run 计划。不生成模型、不渲染、不写 `.blend`。

## probe 做什么

- 检查 `STARBRIDGE_BLENDER_EXE` 或 `BLENDER_EXE` 是否存在。
- 检查 PATH 中是否能找到 `blender`。
- 可选读取命令线索，但不启动复杂渲染任务。
- 输出统一安全 JSON report。

## probe 不做什么

- 不创建真实模型。
- 不打开或保存 `.blend`。
- 不读取贴图、资产库或渲染缓存。

## reference reconstruction plan 做什么

- 把“看图建模”拆成分割、深度/点云初始化、单视图量测、Blender 重建和同相机渲染反查。
- 明确单张图不可证明的内容：背面、遮挡内部、真实厚度和无尺度锚点的绝对尺寸。
- 规定交付门槛：轮廓、边缘、部件覆盖和材质区域误差必须通过阈值。
- 只输出计划，不读取用户图片，不调用 Blender，不下载模型。

## 命令

```powershell
python examples\blender_bridge\probe.py
python examples\blender_bridge\probe.py --json
python examples\blender_bridge\scene_plan.py --json
python examples\blender_bridge\reference_reconstruction_plan.py --json
```
