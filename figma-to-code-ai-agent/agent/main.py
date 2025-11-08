# agent/main.py
from __future__ import annotations
import json, os, math
from typing import Optional, Dict, Any, List, Tuple
import typer

from .config import Settings
from .figma_api import FigmaAPI
from .schema import UISchema, Node, Bounds, Color, TextStyle
from .codegen import CodeGen
from .writers.react_writer import init_scaffold, write_llm_files
from .writers.web_exporter import write_web_export
from .utils.logging import log

app = typer.Typer(add_completion=False)

def _rgba_from_solid(paint: Dict[str, Any]) -> Optional[Color]:
    if not paint or paint.get("type") != "SOLID":
        return None
    c = (paint.get("color") or {})
    return Color(r=c.get("r",0), g=c.get("g",0), b=c.get("b",0), a=paint.get("opacity",1) or 1)

def _gradient_from_paint(paint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    t = paint.get("type")
    if t not in ("GRADIENT_LINEAR","GRADIENT_RADIAL"):
        return None
    # Figma provides stops and a transform. For simplicity we:
    # - use stops directly
    # - approximate angle from gradientTransform for linear (falls back to 180deg)
    stops = []
    for s in (paint.get("gradientStops") or []):
        col = s.get("color") or {}
        rgba = {
            "r": col.get("r",0), "g": col.get("g",0),
            "b": col.get("b",0), "a": col.get("a",1)
        }
        stops.append({"position": s.get("position",0), "color": rgba})

    angle = 180.0
    if t == "GRADIENT_LINEAR":
        m = paint.get("gradientTransform") or [[1,0,0],[0,1,0]]
        # crude angle estimate from transform basis vector (m00,m10)
        try:
            angle = (math.degrees(math.atan2(m[0][1], m[0][0])) + 360) % 360
        except Exception:
            angle = 180.0

    return {
        "type": "linear" if t == "GRADIENT_LINEAR" else "radial",
        "stops": stops,
        "angle": angle
    }

def _effects_from_node(n: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for eff in (n.get("effects") or []):
        if not eff.get("visible", True):
            continue
        et = eff.get("type")
        if et not in ("DROP_SHADOW","INNER_SHADOW"):
            continue
        col = eff.get("color") or {}
        out.append({
            "type": "inner" if et == "INNER_SHADOW" else "drop",
            "x": (eff.get("offset") or {}).get("x",0),
            "y": (eff.get("offset") or {}).get("y",0),
            "blur": eff.get("radius",0),
            "spread": 0,
            "color": {"r": col.get("r",0), "g": col.get("g",0), "b": col.get("b",0), "a": col.get("a",1)}
        })
    return out

def _corner_radii(n: Dict[str, Any]):
    if "rectangleCornerRadii" in n and n["rectangleCornerRadii"]:
        tl, tr, br, bl = n["rectangleCornerRadii"]
        return dict(corner_radius_tl=tl, corner_radius_tr=tr, corner_radius_br=br, corner_radius_bl=bl)
    if "cornerRadius" in n and n["cornerRadius"] not in (None, 0):
        return dict(corner_radius_all=n["cornerRadius"])
    return {}

def _walk(node: Dict[str, Any], image_map: Dict[str, str]) -> Node:
    ntype = node.get("type", "GROUP")
    name = node.get("name", ntype)

    absolute = node.get("absoluteBoundingBox") or {}
    bounds = None
    if absolute:
        bounds = Bounds(
            x=absolute.get("x",0), y=absolute.get("y",0),
            width=absolute.get("width",0), height=absolute.get("height",0)
        )

    fill = None
    gradient = None
    image_url = None
    fills = node.get("fills") or []
    if fills and isinstance(fills, list):
        p0 = fills[0]
        # decide between solid / gradient / image
        if p0.get("type") == "SOLID":
            fill = _rgba_from_solid(p0)
        elif p0.get("type","").startswith("GRADIENT_"):
            gradient = _gradient_from_paint(p0)
        elif p0.get("type") == "IMAGE":
            # use rendered node image from image API
            image_url = image_map.get(node.get("id",""))

    stroke = None
    stroke_w = None
    strokes = node.get("strokes") or []
    if strokes and isinstance(strokes, list):
        stroke = _rgba_from_solid(strokes[0])
        stroke_w = node.get("strokeWeight")

    text = node.get("characters")
    text_style = None
    if ntype == "TEXT" and "style" in node:
        st = node["style"] or {}
        text_style = TextStyle(
            font_family=st.get("fontFamily"),
            font_size=st.get("fontSize"),
            font_weight=int(st.get("fontWeight", 400)) if st.get("fontWeight") else None,
            line_height=st.get("lineHeightPx"),
            letter_spacing=st.get("letterSpacing"),
            text_align=st.get("textAlignHorizontal"),
        )

    children = [_walk(c, image_map) for c in (node.get("children") or [])]

    return Node(
        id=node.get("id",""),
        name=name,
        type=ntype,
        bounds=bounds,
        fill=fill,
        gradient=gradient,
        effects=_effects_from_node(node),
        image_url=image_url,
        stroke=stroke,
        stroke_width=stroke_w,
        opacity=node.get("opacity"),
        text=text,
        text_style=text_style,
        children=children,
        **_corner_radii(node),
    )

def _collect_image_node_ids(node: Dict[str, Any], out: List[str]) -> None:
    for n in (node.get("children") or []):
        fills = n.get("fills") or []
        if fills and any(p.get("type") == "IMAGE" for p in fills):
            if n.get("id"):
                out.append(n["id"])
        _collect_image_node_ids(n, out)

def _figma_to_schema(figma_json: Dict[str, Any], image_map: Dict[str, str]) -> UISchema:
    doc = figma_json.get("document", {})
    file_name = figma_json.get("name", "Untitled")

    frames: List[Node] = []

    def gather_frames(n: Dict[str, Any]):
        if n.get("type") in ("FRAME","COMPONENT"):
            frames.append(_walk(n, image_map))
        for c in n.get("children", []) or []:
            gather_frames(c)

    for top in doc.get("children", []) or []:
        if top.get("type") in ("CANVAS","PAGE"):
            gather_frames(top)

    if not frames:
        log("[yellow]No frames detected. Ensure your design is inside at least one Frame.[/yellow]")

    return UISchema(file_name=file_name, root_frames=frames, tokens={"spacing":{"md":16,"lg":24}})

@app.command(help="Run end-to-end generation.")
def run(
    file_id: Optional[str] = typer.Option(None, "--file-id", help="Figma file key"),
    out: str = typer.Option("generated-ui", "--out", help="Output directory"),
    framework: str = typer.Option("react", "--framework", help="(unused for web export)"),
    sample: bool = typer.Option(False, "--sample", help="Use bundled sample schema"),
    deterministic: bool = typer.Option(False, "--deterministic", help="Bypass LLM; render schema directly"),
    format: str = typer.Option("react", "--format", help="Output format: react | web"),
):
    os.makedirs(out, exist_ok=True)
    init_scaffold(out)

    if sample:
        with open(os.path.join(os.path.dirname(__file__), "..", "samples", "figma_sample.json"), "r", encoding="utf-8") as f:
            figma_json = json.load(f)
        image_map = {}
    else:
        settings = Settings.validate()
        if file_id is None:
            file_id = settings.figma_file_id or ""
        if not settings.figma_token or not file_id:
            raise RuntimeError("FIGMA_TOKEN and a file id are required (pass --file-id or set FIGMA_FILE_ID).")
        api = FigmaAPI(settings.figma_token, timeout=settings.http_timeout)
        figma_json = api.get_file(file_id)
        # resolve image nodes -> URLs
        ids: List[str] = []
        _collect_image_node_ids(figma_json.get("document", {}), ids)
        image_map = {}
        if ids:
            try:
                resp = api.get_images(file_id, ids, scale=2)
                image_map = resp.get("images", {}) or {}
            except Exception as e:
                log(f"[yellow]Image fetch failed, continuing without images: {e}[/yellow]")

    schema = _figma_to_schema(figma_json, image_map).model_dump()

    if deterministic and format.lower() == "web":
        write_web_export(out, schema)
        log(f"[green]Done (web export). Open {out}\\index.html in your browser.[/green]")
        return

    # (Other modes unchanged)
    from .writers.react_renderer import write_schema_render  # optional path if you added it
    if deterministic and format.lower() == "react":
        write_schema_render(out, schema)
        log(f"[green]Done (deterministic React). Open {out} and run npm install && npm run dev[/green]")
        return

    # LLM mode
    settings = Settings.validate()
    cg = CodeGen(settings.model_name, settings.gemini_api_key)
    llm_text = cg.generate(schema)
    files = cg.parse_fenced_files(llm_text) or [("src/App.tsx","export default function App(){return <div>LLM output empty</div>}")]
    write_llm_files(out, files)
    log(f"[green]Done. Open {out} and run npm install && npm run dev[/green]")

if __name__ == "__main__":
    app()
