from agent.schema import UISchema, Node, Bounds

def test_schema_roundtrip():
    ui = UISchema(file_name="x", root_frames=[Node(id="1", name="Frame", type="FRAME")])
    d = ui.model_dump()
    assert d["file_name"] == "x"
    assert d["root_frames"][0]["type"] == "FRAME"
