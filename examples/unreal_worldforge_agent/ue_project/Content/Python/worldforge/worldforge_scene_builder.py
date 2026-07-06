"""WF-0009 small playable blockout builder.

This module must run inside a loaded Unreal Editor Python session. It creates
real UE assets when resource policy allows it; it does not mark the world
completed because PIE and interaction verification are separate gates.
"""

from __future__ import annotations

from . import worldforge_asset_registry as registry
from . import worldforge_blueprint_builder
from . import worldforge_material_builder


def _unreal():
    import unreal  # type: ignore

    return unreal


def ensure_content_dirs() -> None:
    unreal = _unreal()
    for path in [
        f"{registry.SCENE_ROOT}/Maps",
        f"{registry.SCENE_ROOT}/Blueprints",
        f"{registry.SCENE_ROOT}/Materials",
        f"{registry.SCENE_ROOT}/MaterialInstances",
        f"{registry.SCENE_ROOT}/Meshes",
        f"{registry.SCENE_ROOT}/Niagara",
        f"{registry.SCENE_ROOT}/Sequences",
        f"{registry.SCENE_ROOT}/Data",
        f"{registry.SCENE_ROOT}/Textures",
        f"{registry.SCENE_ROOT}/References",
        f"{registry.SCENE_ROOT}/Preview",
    ]:
        if not unreal.EditorAssetLibrary.does_directory_exist(path):
            unreal.EditorAssetLibrary.make_directory(path)


def load_basic_mesh(name: str):
    unreal = _unreal()
    path = {
        "cube": "/Engine/BasicShapes/Cube.Cube",
        "sphere": "/Engine/BasicShapes/Sphere.Sphere",
        "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
    }[name]
    return unreal.EditorAssetLibrary.load_asset(path)


def spawn_mesh(label: str, mesh_name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], material=None):
    unreal = _unreal()
    mesh = load_basic_mesh(mesh_name)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        mesh,
        unreal.Vector(*loc),
        unreal.Rotator(0, 0, 0),
    )
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.tags = ["WorldForgeManaged", "WF0009"]
    if material:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_material(0, material)
    return actor


def create_level_sequence():
    unreal = _unreal()
    package = registry.SEQUENCES[0]
    directory, name = package.rsplit("/", 1)
    if unreal.EditorAssetLibrary.does_asset_exist(package):
        return unreal.load_asset(package)
    factory = unreal.LevelSequenceFactoryNew()
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, directory, unreal.LevelSequence, factory)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def open_or_create_map() -> None:
    unreal = _unreal()
    if unreal.EditorAssetLibrary.does_asset_exist(registry.MAP):
        unreal.EditorLevelLibrary.load_level(registry.MAP)
    else:
        unreal.EditorLevelLibrary.new_level(registry.MAP)


def build_scene(worldspec: dict) -> dict:
    unreal = _unreal()
    ensure_content_dirs()
    materials = worldforge_material_builder.build_wf0009_materials()
    blueprints = worldforge_blueprint_builder.build_wf0009_blueprints()
    open_or_create_map()

    snow = materials[f"{registry.SCENE_ROOT}/MaterialInstances/MI_WF0009_SnowStone_Cold"]
    rock = materials[f"{registry.SCENE_ROOT}/Materials/M_WF0009_IceRock"]
    wood = materials[f"{registry.SCENE_ROOT}/Materials/M_WF0009_AncientDarkWood"]
    bronze = materials[f"{registry.SCENE_ROOT}/Materials/M_WF0009_WeatheredBronze"]
    robot = materials[f"{registry.SCENE_ROOT}/MaterialInstances/MI_WF0009_RobotWhite"]

    spawn_mesh("WF0009_Ground_SnowCourtyard", "cube", (0, 0, -20), (18, 12, 0.35), snow)
    spawn_mesh("WF0009_Path_StoneApproach", "cube", (-450, 0, 2), (5.8, 1.4, 0.12), rock)

    # Eastern temple blockout: columns, beams, roof, eaves, plinths.
    for x in [-420, -180, 60, 300]:
        for y in [-230, 230]:
            spawn_mesh(f"WF0009_Temple_StoneColumn_{x}_{y}", "cylinder", (x, y, 130), (0.42, 0.42, 2.55), rock)
    spawn_mesh("WF0009_Temple_MainBeam_Lower", "cube", (-60, 0, 260), (8.0, 5.2, 0.22), wood)
    spawn_mesh("WF0009_Temple_MainBeam_Upper", "cube", (-60, 0, 330), (8.8, 5.8, 0.18), wood)
    roof = spawn_mesh("WF0009_Temple_SnowRoof_Main", "cube", (-60, 0, 392), (9.6, 6.4, 0.24), snow)
    roof.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
    spawn_mesh("WF0009_Temple_LeftEaveTip", "cube", (-610, 0, 405), (1.4, 6.9, 0.12), snow)
    spawn_mesh("WF0009_Temple_RightEaveTip", "cube", (490, 0, 405), (1.4, 6.9, 0.12), snow)
    spawn_mesh("WF0009_Temple_BronzeShrineMarker", "sphere", (120, -300, 88), (0.55, 0.12, 0.55), bronze)

    # Snow mountain backdrop with editable primitive silhouettes.
    for idx, data in enumerate([(-1150, -900, 210, 3.8, 1.0, 4.4), (-620, -1040, 300, 4.8, 1.0, 6.0), (120, -1120, 360, 5.8, 1.0, 7.2), (850, -960, 260, 4.2, 1.0, 5.0)]):
        actor = spawn_mesh(f"WF0009_MountainBackdrop_{idx + 1:02d}", "cube", data[:3], data[3:], snow)
        actor.set_actor_rotation(unreal.Rotator(0, 0, 18 + idx * 9), False)

    # White robot proxy. It is made of real editable UE mesh actors, not an image.
    robot_parts = [
        ("Pelvis", (720, 165, 95), (0.52, 0.26, 0.35)),
        ("Chest", (720, 165, 185), (0.74, 0.34, 0.76)),
        ("Head", (720, 165, 284), (0.34, 0.32, 0.34)),
        ("LeftArm", (720, 88, 185), (0.18, 0.18, 0.72)),
        ("RightArm", (720, 242, 185), (0.18, 0.18, 0.72)),
        ("LeftLeg", (720, 125, 35), (0.19, 0.19, 0.82)),
        ("RightLeg", (720, 205, 35), (0.19, 0.19, 0.82)),
    ]
    for part, loc, scale in robot_parts:
        spawn_mesh(f"WF0009_RobotScout_{part}", "sphere", loc, scale, robot)
    chest_light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, unreal.Vector(675, 165, 205), unreal.Rotator(0, 0, 0))
    chest_light.set_actor_label("WF0009_RobotScout_ChestLight_FeedbackTarget")
    chest_light.point_light_component.set_editor_property("intensity", 0.0)
    chest_light.point_light_component.set_editor_property("attenuation_radius", 520.0)

    trigger = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TriggerBox, unreal.Vector(120, -300, 90), unreal.Rotator(0, 0, 0))
    trigger.set_actor_label("WF0009_TempleApproach_TriggerBox_PendingPIE")
    trigger.set_actor_scale3d(unreal.Vector(2.2, 2.2, 1.2))
    trigger.tags = ["WorldForgeManaged", "WF0009", "InteractionPendingVerification"]

    player_start = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(-850, 0, 120), unreal.Rotator(0, 0, 0))
    player_start.set_actor_label("WF0009_PlayerStart")

    sun = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 800), unreal.Rotator(-38, -45, 0))
    sun.set_actor_label("WF0009_ColdMorningKeyLight")
    sun.directional_light_component.set_editor_property("intensity", 2.0)
    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 420), unreal.Rotator(0, 0, 0))
    sky.set_actor_label("WF0009_ColdSkyLight")
    sky.sky_light_component.set_editor_property("intensity", 0.65)
    fog = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    fog.set_actor_label("WF0009_ThinColdFog")

    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-920, 720, 360), unreal.Rotator(-14, -38, 0))
    camera.set_actor_label("WF0009_HeroCamera_28mm")
    try:
        camera.camera_component.set_editor_property("current_focal_length", 28.0)
    except Exception:
        pass

    create_level_sequence()
    world = unreal.EditorLevelLibrary.get_editor_world()
    settings = world.get_world_settings()
    settings.set_editor_property("default_game_mode", blueprints[f"{registry.SCENE_ROOT}/Blueprints/BP_WF0009_GameMode"].generated_class)
    unreal.EditorLevelLibrary.save_current_level()
    unreal.EditorAssetLibrary.save_directory(registry.SCENE_ROOT, only_if_is_dirty=False, recursive=True)
    return {
        "map": registry.MAP,
        "blueprints": sorted(blueprints.keys()),
        "materials": sorted(materials.keys()),
        "sequence": registry.SEQUENCES[0],
        "note": "PIE movement and trigger feedback still require a separate verification gate.",
        "world_title": worldspec.get("title"),
    }
