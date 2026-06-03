# Blender Drawing Learning 参数规范

本文档定义 `blender-drawing-learning` skill 与后续 Codex Blender 插件工具可复用的数据结构。目标是让 Codex 能稳定读取 Blender 文件，拆解建模、材质、灯光、相机和渲染参数，并输出可学习、可复现、可提交到 GitHub 的脱敏数据。

## 输入参数

### 1. 资产目录索引

对应脚本：`scripts/analyze_blender_learning_assets.py`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `--root` | string | 是 | 无 | 本地 Blender 素材根目录。只用于本地读取，不写入公开输出。 |
| `--out-dir` | string | 是 | 无 | 输出目录，建议为 `docs/blender-drawing-learning/data`。 |

输出文件：

| 文件 | 说明 |
| --- | --- |
| `asset_inventory_redacted.csv` | 逐文件脱敏索引。 |
| `asset_summary_redacted.json` | 文件数量、大小、扩展名、分类统计。 |

### 2. `.blend` 场景 profile

对应脚本：`scripts/blender_scene_profile.py`

必须通过 Blender 后台运行：

```powershell
& $env:BLENDER_EXE --background --python scripts\blender_scene_profile.py -- --root $env:BLENDER_ASSET_ROOT --out docs\blender-drawing-learning\data\blend_scene_profiles_redacted.json
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `--root` | string | 是 | 无 | 本地 `.blend` 搜索根目录。公开输出只保留相对标签。 |
| `--out` | string | 是 | 无 | 输出 JSON 文件路径。 |
| `--limit` | integer | 否 | `0` | 限制读取前 N 个 `.blend`；`0` 表示不限制。 |
| `--match-label` | string | 否 | 空字符串 | 只读取相对标签中包含该文本的 `.blend`，适合单案例实验。 |

输出顶层结构：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source_redaction` | string | 脱敏说明。 |
| `blend_file_count_attempted` | integer | 尝试读取的 `.blend` 数量。 |
| `profile_count` | integer | 成功生成 profile 的数量。 |
| `error_count` | integer | 失败数量。 |
| `profiles` | array | 场景 profile 列表。 |
| `errors` | array | 失败案例，包含相对标签和错误信息。 |

## Scene Profile Schema

每个 `profiles[]` 元素代表一个 `.blend` 文件。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema_version` | string | 当前为 `0.2`。 |
| `relative_label` | string | 相对资产标签，不含本机绝对路径。 |
| `scene_name` | string | Blender scene 名称。 |
| `render_engine` | string | 渲染引擎，如 `CYCLES`、`BLENDER_EEVEE`。 |
| `resolution` | array[number] | `[width, height]`。 |
| `frame_range` | array[number] | `[frame_start, frame_end]`。 |
| `render_settings` | object | 详细渲染参数。 |
| `object_count` | integer | 对象总数。 |
| `object_type_counts` | object | 按 `MESH`、`LIGHT`、`CAMERA` 等类型统计。 |
| `mesh_count` | integer | Mesh 对象数量。 |
| `material_count` | integer | 材质数量。 |
| `light_count` | integer | 灯光数量。 |
| `camera_count` | integer | 相机数量。 |
| `mesh_material_slot_counts` | object | Mesh 材质槽数量分布。 |
| `modifier_counts` | object | 修改器类型统计。 |
| `lights` | array | 灯光参数样本，最多 12 个。 |
| `cameras` | array | 相机参数样本，最多 8 个。 |
| `objects_sample` | array | 对象样本，最多 48 个。 |
| `materials_sample` | array | 材质样本，最多 20 个。 |
| `world` | object | World 节点与环境参数。 |
| `drawing_learning_notes` | array[string] | 自动生成的学习提示。 |

### render_settings

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `engine` | string | 当前渲染引擎。 |
| `resolution` | array[number] | 输出宽高。 |
| `resolution_percentage` | integer | 分辨率百分比。 |
| `frame_range` | array[number] | 起止帧。 |
| `fps` | integer | 帧率。 |
| `film_transparent` | boolean | 是否透明背景。 |
| `cycles.samples` | integer/null | Cycles 最终采样。 |
| `cycles.preview_samples` | integer/null | Cycles 预览采样。 |
| `cycles.use_denoising` | boolean/null | 是否降噪。 |
| `cycles.max_bounces` | integer/null | 最大反弹次数。 |
| `eevee.taa_render_samples` | integer/null | EEVEE 渲染抗锯齿采样。 |
| `eevee.taa_samples` | integer/null | EEVEE 视图采样。 |

### transform

`transform` 用于对象、灯光、相机。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `location` | array[number] | 世界坐标位置 `[x, y, z]`。 |
| `rotation_euler` | array[number] | 欧拉旋转 `[x, y, z]`，单位为弧度。 |
| `scale` | array[number] | 缩放 `[x, y, z]`。 |
| `dimensions` | array[number] | 物体包围尺寸 `[x, y, z]`。 |

### lights[]

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 灯光对象名。 |
| `type` | string | `AREA`、`POINT`、`SUN`、`SPOT` 等。 |
| `energy` | number | 光照强度。 |
| `color` | array[number] | RGB 颜色。 |
| `transform` | object | 位置、旋转、缩放、尺寸。 |
| `shadow_soft_size` | number/null | 软阴影尺寸。 |
| `use_shadow` | boolean/null | 是否投影。 |
| `size` | number/null | Area Light 宽度或灯尺寸。 |
| `size_y` | number/null | Area Light 高度。 |
| `angle` | number/null | Sun 灯角度。 |
| `spot_size` | number/null | Spot 锥角。 |
| `spot_blend` | number/null | Spot 边缘混合。 |

### cameras[]

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 相机名。 |
| `lens` | number | 焦段，单位 mm。 |
| `sensor_width` | number | 传感器宽度。 |
| `type` | string | `PERSP` 或 `ORTHO` 等。 |
| `transform` | object | 位置、旋转、缩放、尺寸。 |
| `clip_start` | number/null | 近裁剪距离。 |
| `clip_end` | number/null | 远裁剪距离。 |
| `dof.use_dof` | boolean/null | 是否启用景深。 |
| `dof.aperture_fstop` | number/null | 光圈 f-stop。 |

### objects_sample[]

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 对象名称。 |
| `type` | string | 对象类型。 |
| `transform` | object | 位置、旋转、缩放、尺寸。 |
| `material_slot_count` | integer | 材质槽数量。 |
| `mesh_stats.vertices` | integer | 顶点数，仅 Mesh。 |
| `mesh_stats.edges` | integer | 边数，仅 Mesh。 |
| `mesh_stats.polygons` | integer | 面数，仅 Mesh。 |
| `mesh_stats.uv_layers` | integer | UV 层数量，仅 Mesh。 |
| `modifiers` | array | 修改器样本，仅 Mesh。 |

### modifiers[]

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 修改器名称。 |
| `type` | string | 修改器类型，如 `SUBSURF`、`MIRROR`、`BEVEL`。 |
| `parameters` | object | 可安全读取的关键参数。 |

常见 `parameters`：

| 参数 | 说明 |
| --- | --- |
| `levels` | 视图细分级别。 |
| `render_levels` | 渲染细分级别。 |
| `width` | 倒角宽度。 |
| `segments` | 倒角段数。 |
| `thickness` | Solidify 厚度。 |
| `offset` | Solidify 偏移。 |
| `use_clip` | Mirror 裁切。 |
| `mode` | 修改器模式。 |

### materials_sample[]

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 材质名称。 |
| `uses_nodes` | boolean | 是否使用节点。 |
| `node_types` | object | 节点类型统计。 |
| `nodes_sample` | array | 节点样本，最多 32 个。 |
| `diffuse_color` | array[number] | 材质视图颜色。 |
| `blend_method` | string/null | 透明混合方式。 |
| `use_screen_refraction` | boolean | 是否屏幕折射。 |

### nodes_sample[]

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 节点名称。 |
| `label` | string | 节点标签。 |
| `type` | string | 节点类型，如 `ShaderNodeBsdfPrincipled`。 |
| `inputs` | object | 前 12 个输入 socket 的默认值。 |
| `image_name` | string/null | 贴图节点引用的图片名称，不含本机路径。 |

### world

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `has_world` | boolean | 是否有 World。 |
| `uses_nodes` | boolean | World 是否使用节点。 |
| `color` | array[number] | 非节点 World 颜色。 |
| `nodes_sample` | array | World 节点样本。 |

## 学习判断规则

Codex 使用这些字段判断案例重点：

| 条件 | 学习判断 |
| --- | --- |
| `modifier_counts.SUBSURF > 0` | 学低模控制线和细分轮廓。 |
| `modifier_counts.MIRROR > 0` | 学对称建模。 |
| `modifier_counts.BEVEL > 0` | 学硬表面边缘高光。 |
| `modifier_counts.SOLIDIFY > 0` | 学衣物、壳体、薄片厚度。 |
| `modifier_counts.ARMATURE > 0` 或 `object_type_counts.ARMATURE > 0` | 学角色绑定和姿势。 |
| `light_count > 0` | 先拆主光、补光、轮廓光，再看材质。 |
| `camera_count > 0` | 记录焦段和机位，用同机位复建出图。 |
| `materials_sample[].uses_nodes = true` | 学节点材质和贴图角色。 |
| `world.uses_nodes = true` | 学 HDR/World 环境光。 |
