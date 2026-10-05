import json

import pytest

from src.macros.macro import InvalidMacro
from src.macros.preset_store import PresetNotFound, PresetReadOnly, PresetStore


def test_lists_bundled_presets_when_user_dir_missing(preset_dirs):
    store = PresetStore(*preset_dirs)
    presets = store.list()
    assert [preset.id for preset in presets] == ["cube", "zoom"]
    assert presets[0].builtin is True


def test_save_creates_user_preset_and_overrides_bundled_id(preset_dirs):
    store = PresetStore(*preset_dirs)
    saved = store.save({"name": "Zoom", "steps": "_.ZOOM _W"})
    assert saved.id == "zoom"
    assert store.get("zoom").builtin is False
    assert store.get("zoom").steps == ("_.ZOOM _W",)


def test_save_rejects_invalid_macro(preset_dirs):
    with pytest.raises(InvalidMacro):
        PresetStore(*preset_dirs).save({"name": "Vide", "steps": ""})


def test_delete_user_preset(preset_dirs):
    store = PresetStore(*preset_dirs)
    store.save({"name": "Mien", "steps": ["_.LINE"]})
    store.delete("mien")
    with pytest.raises(PresetNotFound):
        store.get("mien")


def test_delete_bundled_preset_is_refused(preset_dirs):
    with pytest.raises(PresetReadOnly):
        PresetStore(*preset_dirs).delete("zoom")


def test_delete_unknown_preset(preset_dirs):
    with pytest.raises(PresetNotFound):
        PresetStore(*preset_dirs).delete("nope")


def test_corrupt_file_is_skipped(preset_dirs):
    bundled, user = preset_dirs
    (bundled / "broken.json").write_text("{not json", encoding="utf-8")
    (bundled / "nosteps.json").write_text(json.dumps({"name": "X"}), encoding="utf-8")
    assert [preset.id for preset in PresetStore(bundled, user).list()] == ["cube", "zoom"]
