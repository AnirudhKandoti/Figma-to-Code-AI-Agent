# agent/writers/web_exporter.py
from __future__ import annotations
import os, json, re
from typing import Dict, Any, Optional, List
import requests

ASSET_DIR = "assets"

def _rgba(c: Optional[Dict[str, Any]]) -> Optional[str]:
    if not c: return None
    r = int((c.get("r", 0) or 0) * 255)
    g = int((c.get("g", 0) or 0) * 255)
    b = int((c.get("b", 0) or 0) * 255)
    a = float(c.get("a", 1) or 1)
    return f"rgba({r},{g},{b},{a})"

def _gradient_css(g: Optional[Dict[str, Any]]) -> Optional[str]:
    if not g: return None
    stops = g.get("stops") or []
    if not stops: return None
    parts = [f"{_rgba(s['color'])} {round((s.get('position',0)*100),2)}%" for s in stops]
    if g.get("type") == "radial":
        return f"radial-gradient(circle, {', '.join(parts)})"
    angle = round(g.get("angle", 180), 2)
    return f"linear-gradient({angle}deg, {', '.join(parts)})"

def _box_shadow(effects: List[Dict[str, Any]]) -> Optional[str]:
    if not effects: return None
    out = []
    for e in effects:
        color = _rgba(e.get("color"))
        x = int(e.get("x",0)); y = int(e.get("y",0))
        blur = int(e.get("blur",0)); spread = int(e.get("spread",0))
        inset = " inset" if e.get("type") == "inner" else ""
        out.append(f"{x}px {y}px {blur}px {spread}px {color}{inset}")
    return ", ".join(out) if out else None

def _ensure_assets_dir(out_dir: str) -> str:
    d = os.path.join(out_dir, ASSET_DIR)
    os.makedirs(d, exist_ok=True)
    return d

def _download_image(url: str, dest_dir: str, name_hint: str) -> Optional[str]:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        # pick extension if present
        ext = ".png"
        m = re.search(r"\.(png|jpg|jpeg|webp)(?:\?|$)", url, re.I)
        if m: ext = "." + m.group(1).lower()
        fn = f"{name_hint}{ext}"
        path = os.path.join(dest_dir, fn)
        with open(path, "wb") as f: f.write(r.content)
        return f"./{ASSET_DIR}/{fn}"
    except Exception:
        return None

def _style(n: Dict[str, Any]) -> Dict[str, str]:
    b = n.get("bounds") or {}
    css = {
        "position": "absolute",
        "left": f"{b.get('x',0)}px",
        "top": f"{b.get('y',0)}px",
        "width": f"{b.get('width',0)}px",
        "height": f"{b.get('height',0)}px",
        "opacity": str(n.get("opacity", 1)),
    }
    # fill / gradient / image
    grad = _gradient_css(n.get("gradient"))
    if grad:
        css["background"] = grad
    else:
        fill = _rgba(n.get("fill"))
        if fill: css["background"] = fill
        img = n.get("image_url")
        if img:
            css["background-image"] = f"url('{img}')"
            css["background-size"] = "cover"
            css["background-position"] = "center center"
            css["background-repeat"] = "no-repeat"

    # stroke
    if n.get("stroke") and n.get("stroke_width"):
        css["border"] = f"{int(n['stroke_width'])}px solid {_rgba(n['stroke'])}"

    # corners
    if n.get("type") == "ELLIPSE":
        css["border-radius"] = "9999px"
    elif n.get("corner_radius_all") is not None:
        css["border-radius"] = f"{n['corner_radius_all']}px"
    else:
        if n.get("corner_radius_tl") is not None: css["border-top-left-radius"] = f"{n['corner_radius_tl']}px"
        if n.get("corner_radius_tr") is not None: css["border-top-right-radius"] = f"{n['corner_radius_tr']}px"
        if n.get("corner_radius_br") is not None: css["border-bottom-right-radius"] = f"{n['corner_radius_br']}px"
        if n.get("corner_radius_bl") is not None: css["border-bottom-left-radius"] = f"{n['corner_radius_bl']}px"

    # text styles
    ts = n.get("text_style") or {}
    if ts.get("font_family"): css["font-family"] = ts["font_family"]
    if ts.get("font_size"): css["font-size"] = f"{ts['font_size']}px"
    if ts.get("font_weight"): css["font-weight"] = str(ts["font_weight"])
    if ts.get("line_height"): css["line-height"] = f"{ts['line_height']}px"
    if ts.get("text_align"): css["text-align"] = str(ts["text_align"]).lower()

    # shadows
    bs = _box_shadow(n.get("effects") or [])
    if bs: css["box-shadow"] = bs

    return css

def _style_inline(style_dict: Dict[str, str]) -> str:
    return "; ".join(f"{k}: {v}" for k,v in style_dict.items())

def _escape_text(t: str) -> str:
    return (t or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _render_node(n: Dict[str, Any], indent: int = 6) -> str:
    pad = " " * indent
    style = _style(n)
    if n.get("type") == "TEXT":
        return f'{pad}<div class="node text" style="{_style_inline(style)}">{_escape_text(n.get("text") or "")}</div>'
    children_html = "\n".join(_render_node(c, indent+2) for c in (n.get("children") or []))
    return f"""{pad}<div class="node {n.get('type','').lower()}" style="{_style_inline(style)}">
{children_html}
{pad}</div>"""

def _render_frame(frame: Dict[str, Any], idx: int) -> str:
    b = frame.get("bounds") or {}
    w = int(b.get("width", 1200))
    h = int(b.get("height", 800))
    children = "\n".join(_render_node(c, 8) for c in (frame.get("children") or []))
    return f"""    <section class="frame" id="frame-{idx}" style="width:{w}px; height:{h}px;">
{children}
    </section>"""

def _gather_all_nodes(n: Dict[str, Any], out: List[Dict[str, Any]]):
    out.append(n)
    for c in (n.get("children") or []):
        _gather_all_nodes(c, out)

def write_web_export(out_dir: str, schema: Dict[str, Any]) -> None:
    os.makedirs(out_dir, exist_ok=True)
    assets_dir = _ensure_assets_dir(out_dir)

    # optionally mirror image URLs locally (if available)
    # we rewrite node.image_url to local path after download succeeds
    frames: List[Dict[str, Any]] = schema.get("root_frames") or []
    for fr in frames:
        nodes: List[Dict[str, Any]] = []
        _gather_all_nodes(fr, nodes)
        for n in nodes:
            u = n.get("image_url")
            if u and u.startswith("http"):
                local = _download_image(u, assets_dir, f"node-{n.get('id','img')}")
                if local:
                    n["image_url"] = local  # rewrite CSS to local asset

    src_html = os.path.join(out_dir, "index.html")
    css = os.path.join(out_dir, "styles.css")
    js = os.path.join(out_dir, "script.js")
    json_path = os.path.join(out_dir, "ui-schema.json")

    frames_html = "\n".join(_render_frame(fr, i+1) for i, fr in enumerate(frames)) or \
        '    <section class="frame" style="width:1200px;height:800px;"><div class="node text" style="position:absolute;left:40px;top:40px">No frames detected.</div></section>'

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{schema.get('file_name','Export')}</title>
  <link rel="stylesheet" href="./styles.css"/>
</head>
<body>
  <main>
{frames_html}
  </main>
  <script src="./script.js"></script>
</body>
</html>
"""
    with open(src_html, "w", encoding="utf-8") as f:
        f.write(html)

    base_css = """*{box-sizing:border-box}html,body{height:100%}body{margin:0;background:#f6f7f9;font-family:Inter,system-ui,Segoe UI,Roboto,Arial,sans-serif}
main{padding:32px}
.frame{position:relative;margin:40px auto;background:#fff;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.05);overflow:hidden}
.node{position:absolute;white-space:pre-wrap;color:#111}
.node.text{pointer-events:none}
"""
    with open(css, "w", encoding="utf-8") as f:
        f.write(base_css)

    with open(js, "w", encoding="utf-8") as f:
        f.write("// optional runtime hooks; empty by default\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
