from pathlib import Path

import scripts.pkimm_model as pm

ROOT = Path(__file__).resolve().parents[2]


def test_loads_model_and_builds_index():
    model = pm.load_model(ROOT, "2.0.0")
    assert model["version"] == "2.0.0"
    idx = pm.ModelIndex(model)
    assert idx.category_in_module("G", "strategy-and-vision") is True
    assert idx.category_in_module("M", "strategy-and-vision") is False
    assert idx.requirement_in_category("strategy-and-vision", "sponsor-support") is True
    # wrong-parent: 'policy-scope' is a real requirement, but under
    # 'policies-and-documentation', not 'strategy-and-vision' → must be False
    assert idx.requirement_in_category("strategy-and-vision", "policy-scope") is False
    # nonexistent id → also False
    assert idx.requirement_in_category("strategy-and-vision", "not-a-req") is False
    assert idx.category_title("strategy-and-vision") == "Strategy and vision"
    assert idx.requirement_description("strategy-and-vision", "sponsor-support")


def test_loads_reference_ids():
    ids = pm.load_references(ROOT, "2.0.0")
    assert isinstance(ids, set) and len(ids) > 0
