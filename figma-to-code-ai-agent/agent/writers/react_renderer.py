from __future__ import annotations
import os
from typing import Dict, Any, List, Optional

def _css_rgba(c: Optional[Dict[str, Any]]) -> Optional[str]:
    if not c: return None
    return f"rgba({int(c['r']*255)},{int(c['g']*255)},{int(c['b']*255)},{c.get('a',1)})"

def _style_from_node(n: Dict[str, Any]) -> str:
    b = n.get("bounds") or {}
    styles = {
        "position":"absolute",
        "left": f"{b.get('x',0)}px",
        "top": f"{b.get('y',0)}px",
        "width": f"{b.get('width',0)}px",
        "height": f"{b.get('height',0)}px",
        "opacity": n.get("opacity",1)
    }
    if n.get("fill"):
        styles["backgroundColor"] = _css_rgba(n["fill"])
    if n.get("stroke") and n.get("stroke_width"):
        styles["border"] = f"{n['stroke_width']}px solid {_css_rgba(n['stroke'])}"
    # corner radii
    if n.get("corner_radius_all"):
        styles["borderRadius"] = f"{n['corner_radius_all']}px"
    else:
        if n.get("corner_radius_tl") is not None: styles["borderTopLeftRadius"] = f"{n['corner_radius_tl']}px"
        if n.get("corner_radius_tr") is not None: styles["borderTopRightRadius"] = f"{n['corner_radius_tr']}px"
        if n.get("corner_radius_br") is not None: styles["borderBottomRightRadius"] = f"{n['corner_radius_br']}px"
        if n.get("corner_radius_bl") is not None: styles["borderBottomLeftRadius"] = f"{n['corner_radius_bl']}px"
    # text styles
    ts = n.get("text_style") or {}
    if ts.get("font_family"): styles["fontFamily"] = ts["font_family"]
    if ts.get("font_size"): styles["fontSize"] = f"{ts['font_size']}px"
    if ts.get("font_weight"): styles["fontWeight"] = str(ts["font_weight"])
    if ts.get("line_height"): styles["lineHeight"] = f"{ts['line_height']}px"
    if ts.get("text_align"): styles["textAlign"] = ts["text_align"].lower()
    return ", ".join([f"{k}: '{v}'" for k,v in styles.items()])

def _render_node(n: Dict[str, Any], indent=4) -> str:
    pad = " " * indent
    t = n.get("type")
    style = _style_from_node(n)

    # simple node renderers
    if t == "TEXT":
        txt = (n.get("text") or "").replace("\\", "\\\\").replace("`","\\`").replace("{","{{").replace("}","}}")
        children_tsx = ""  # text has no children
        return f"{pad}<div style={{ {{ {style} }} }}>{txt}</div>"

    # treat vectors/ellipses/rectangles/groups as div boxes; recurse children
    children_tsx = "\n".join(_render_node(c, indent+2) for c in (n.get("children") or []))
    return f"""{pad}<div style={{ {{ {style} }} }}>
{children_tsx}
{pad}</div>"""

def _render_frame_component(frame: Dict[str, Any], idx: int) -> str:
    b = frame.get("bounds") or {}
    w = int(b.get("width", 1200))
    h = int(b.get("height", 800))
    children = "\n".join(_render_node(c, indent=6) for c in (frame.get("children") or []))
    return f"""import React from "react";

export default function Frame{idx}(){{
  return (
    <div className="relative mx-auto my-10 rounded-xl shadow" style={{ {{ width: '{w}px', height: '{h}px', background: '#fff' }} }}>
{children}
    </div>
  );
}}
"""

def write_schema_render(out_dir: str, schema: Dict[str, Any]) -> None:
    src = os.path.join(out_dir, "src")
    comps = os.path.join(src, "components")
    os.makedirs(comps, exist_ok=True)

    frames: List[Dict[str, Any]] = schema.get("root_frames") or []
    imports, uses = [], []
    for i, fr in enumerate(frames, start=1):
        code = _render_frame_component(fr, i)
        fn = os.path.join(comps, f"Frame{i}.tsx")
        with open(fn, "w", encoding="utf-8") as f: f.write(code)
        imports.append(f'import Frame{i} from "./components/Frame{i}";')
        uses.append(f"      <Frame{i} />")

    if not frames:
        # fallback
        imports = []
        uses = ["      <div className=\"p-10\">No frames detected.</div>"]

    app_tsx = f"""import React from "react";
{os.linesep.join(imports)}

export default function App(){{
  return (
    <main className="min-h-screen bg-gray-50 p-8">
{os.linesep.join(uses)}
    </main>
  );
}}
"""
    with open(os.path.join(src, "App.tsx"), "w", encoding="utf-8") as f:
        f.write(app_tsx)
