# agent/schema.py
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Bounds(BaseModel):
    x: float
    y: float
    width: float
    height: float

class Color(BaseModel):
    r: float  # 0..1
    g: float
    b: float
    a: float = 1.0

class TextStyle(BaseModel):
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    font_weight: Optional[int] = None
    line_height: Optional[float] = None
    letter_spacing: Optional[float] = None
    text_align: Optional[str] = None

class Node(BaseModel):
    id: str
    name: str
    type: str
    bounds: Optional[Bounds] = None
    fill: Optional[Color] = None

    # NEW: visual enhancements
    gradient: Optional[Dict[str, Any]] = None        # {"type": "linear|radial", "stops":[(pos,rgba),...], "angle":deg}
    effects: List[Dict[str, Any]] = []               # [{"type":"drop|inner","x":..,"y":..,"blur":..,"color":{...}}]
    image_url: Optional[str] = None                  # resolved via Figma images API

    stroke: Optional[Color] = None
    stroke_width: Optional[float] = None
    corner_radius_all: Optional[float] = None
    corner_radius_tl: Optional[float] = None
    corner_radius_tr: Optional[float] = None
    corner_radius_br: Optional[float] = None
    corner_radius_bl: Optional[float] = None
    opacity: Optional[float] = None
    text: Optional[str] = None
    text_style: Optional[TextStyle] = None
    children: List["Node"] = []

class UISchema(BaseModel):
    file_name: str
    root_frames: List[Node]
    tokens: Dict[str, Any] = {}
