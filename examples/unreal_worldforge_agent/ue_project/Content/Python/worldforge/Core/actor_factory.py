"""Small UE actor helpers used by recipe builders."""

from __future__ import annotations

from typing import Any


def _unreal():
    import unreal  # type: ignore

    return unreal


def actor_labels() -> list[str]:
    unreal = _unreal()
    return [actor.get_actor_label() for actor in unreal.EditorLevelLibrary.get_all_level_actors()]


def find_actor_by_label(label: str):
    unreal = _unreal()
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def set_tags(actor: Any, tags: list[str]) -> None:
    actor.tags = tags


def set_transform(actor: Any, loc: list[float], rot: list[float] | None = None, scale: list[float] | None = None) -> None:
    unreal = _unreal()
    actor.set_actor_location(unreal.Vector(*loc), False, False)
    if rot is not None:
        actor.set_actor_rotation(unreal.Rotator(*rot), False)
    if scale is not None:
        actor.set_actor_scale3d(unreal.Vector(*scale))


def spawn_basic_mesh(label: str, mesh_name: str, loc: list[float], scale: list[float], tags: list[str]):
    unreal = _unreal()
    mesh = unreal.EditorAssetLibrary.load_asset(f"/Engine/BasicShapes/{mesh_name}.{mesh_name}")
    if mesh is None:
        raise RuntimeError(f"Missing engine basic mesh: {mesh_name}")
    actor = find_actor_by_label(label)
    if actor is None:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    set_transform(actor, loc, [0, 0, 0], scale)
    set_tags(actor, tags)
    return actor
