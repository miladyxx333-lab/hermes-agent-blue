import numpy as np
import math
import random
import os
import subprocess
import platform
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import shutil

# --- Configuration ---
VW, VH = 1920, 1080
FPS = 24
DURATION = 30 # seconds
N_FRAMES = DURATION * FPS

# Colors (RGBA)
COLOR_DARK_BG = (10, 10, 15)
COLOR_MATRIX_GREEN = (34, 197, 94)
COLOR_ELECTRIC_CYAN = (34, 211, 238)
COLOR_DEEP_PURPLE = (99, 102, 241)
COLOR_GOLD = (251, 191, 36)
COLOR_SUCCESS_GREEN = (0, 255, 0)

# Custom Character Palette
PAL_CLAVIGER = " ◈ ◆ ■ ░ ▓ █ ● ○ ✦.`'-:;!><=+*^~?/|(){}[]#&$@%"
PAL_CODE = "01_[]{}().;:,+-*/<>&^|~"
PAL_LOCK = "🔐🔑🔒🔓"

# Font preferences (try to find a suitable monospace font)
FONT_PREFS_MACOS = [
    ("Source Code Pro", "/System/Library/Fonts/SourceCodePro-Regular.ttf"),
    ("Menlo", "/System/Library/Fonts/Menlo.ttc"),
    ("Monaco", "/System/Library/Fonts/Monaco.ttf"),
    ("SF Mono", "/System/Library/Fonts/SFNSMono.ttf"),
]
FONT_PREFS_LINUX = [
    ("Source Code Pro", "/usr/share/fonts/opentype/public/source-code-pro/SourceCodePro-Regular.otf"),
    ("DejaVu Sans Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ("Liberation Mono", "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
    ("Noto Sans Mono", "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf"),
]
FONT_PREFS = FONT_PREFS_MACOS if platform.system() == "Darwin" else FONT_PREFS_LINUX
FONT_PATH = None

# --- Hardware Detection and Optimization (Placeholder) ---
# In a real scenario, this would detect CPU cores, RAM, etc.
# For now, we'll set a reasonable default.
N_WORKERS = os.cpu_count() or 4
CRF = 20 # Constant Rate Factor for x264 (18-24 is good quality)

# --- Helper Functions ---

def find_font(preferences):
    global FONT_PATH
    for name, path in preferences:
        if os.path.exists(path):
            FONT_PATH = path
            return path
    raise FileNotFoundError(f"No monospace font found. Tried: {[p for _,p in preferences]}")

def log(msg):
    print(msg, flush=True)

def hsv2rgb(h, s, v):
    h = h % 1.0
    c = v * s
    x = c * (1 - np.abs((h * 6) % 2 - 1))
    m = v - c

    r, g, b = np.zeros_like(h), np.zeros_like(h), np.zeros_like(h)

    idx0 = (h * 6 < 1)
    r[idx0], g[idx0], b[idx0] = c[idx0], x[idx0], 0

    idx1 = (h * 6 >= 1) & (h * 6 < 2)
    r[idx1], g[idx1], b[idx1] = x[idx1], c[idx1], 0

    idx2 = (h * 6 >= 2) & (h * 6 < 3)
    r[idx2], g[idx2], b[idx2] = 0, c[idx2], x[idx2]

    idx3 = (h * 6 >= 3) & (h * 6 < 4)
    r[idx3], g[idx3], b[idx3] = 0, x[idx3], c[idx3]

    idx4 = (h * 6 >= 4) & (h * 6 < 5)
    r[idx4], g[idx4], b[idx4] = x[idx4], 0, c[idx4]

    idx5 = (h * 6 >= 5)
    r[idx5], g[idx5], b[idx5] = c[idx5], 0, x[idx5]

    R = (np.clip((r + m) * 255, 0, 255)).astype(np.uint8)
    G = (np.clip((g + m) * 255, 0, 255)).astype(np.uint8)
    B = (np.clip((b + m) * 255, 0, 255)).astype(np.uint8)
    return R, G, B

def hsv2rgb_scalar(h, s, v):
    h = h % 1.0
    c = v * s; x = c * (1 - abs((h * 6) % 2 - 1)); m = v - c
    if h * 6 < 1:   r, g, b = c, x, 0
    elif h * 6 < 2:  r, g, b = x, c, 0
    elif h * 6 < 3:  r, g, b = 0, c, x
    elif h * 6 < 4:  r, g, b = 0, x, c
    elif h * 6 < 5:  r, g, b = x, 0, c
    else:             r, g, b = c, 0, x
    return (int((r+m)*255), int((g+m)*255), int((b+m)*255))

def rgb_to_np_array(color_tuple):
    return np.array(color_tuple, dtype=np.uint8)

def tonemap(canvas, gamma=0.75):
    f = canvas.astype(np.float32)
    lo = np.percentile(f, 1)
    hi = np.percentile(f, 99.5)
    if hi - lo < 1: hi = lo + 1
    f = (f - lo) / (hi - lo)
    f = np.clip(f, 0, 1) ** gamma
    return (f * 255).astype(np.uint8)

def blend_canvas(canvas_a, canvas_b, mode="add", opacity=1.0):
    if canvas_a.shape != canvas_b.shape:
        raise ValueError("Canvases must have the same shape for blending.")

    result = np.copy(canvas_a).astype(np.float32)
    top_layer = canvas_b.astype(np.float32)

    if mode == "add":
        result = result + top_layer * opacity
    elif mode == "screen":
        result = 255 - ((255 - result) * (255 - top_layer * opacity)) / 255
    elif mode == "multiply":
        result = (result * top_layer * opacity) / 255
    elif mode == "overlay":
        # Simplified overlay: blend of multiply and screen
        mask = result < 128
        result[mask] = (2 * result[mask] * top_layer[mask]) / 255
        result[~mask] = 255 - (2 * (255 - result[~mask]) * (255 - top_layer[~mask])) / 255
    elif mode == "exclusion":
        result = result + top_layer - (2 * result * top_layer) / 255
    else: # Default to normal blend
        result = result * (1 - opacity) + top_layer * opacity

    return np.clip(result, 0, 255).astype(np.uint8)

def val2char(v, mask, pal):
    n = len(pal)
    idx = np.clip((v * n).astype(int), 0, n - 1)
    out = np.full(v.shape, " ", dtype="U1")
    for i, ch in enumerate(pal):
        out[mask & (idx == i)] = ch
    return out

def stamp_text(grid_layer, text, row, col, color):
    for i, char in enumerate(text):
        cc = col + i
        if 0 <= row < grid_layer.rows and 0 <= cc < grid_layer.cols:
            grid_layer.chars[row, cc] = char
            grid_layer.colors[row, cc] = color

def center_text_row(grid_layer, text):
    return (grid_layer.cols - len(text)) // 2

# --- GridLayer Class ---
class GridLayer:
    def __init__(self, font_path, font_size, all_chars):
        self.font = ImageFont.truetype(font_path, font_size)
        asc, desc = self.font.getmetrics()
        # textbbox gives more reliable width, getmetrics for height
        bbox = self.font.getbbox("M")
        self.cw = bbox[2] - bbox[0]
        self.ch = asc + desc

        self.cols = VW // self.cw
        self.rows = VH // self.ch
        self.ox = (VW - self.cols * self.cw) // 2
        self.oy = (VH - self.rows * self.ch) // 2

        self.rr = np.arange(self.rows, dtype=np.float32)[:, None]
        self.cc = np.arange(self.cols, dtype=np.float32)[None, :]

        cx, cy = self.cols / 2.0, self.rows / 2.0
        asp = self.cw / self.ch
        self.dx = self.cc - cx
        self.dy = (self.rr - cy) * asp
        self.dist = np.sqrt(self.dx**2 + self.dy**2)
        self.angle = np.arctan2(self.dy, self.dx)

        self.dx_n = (self.cc - cx) / max(self.cols, 1)
        self.dy_n = (self.rr - cy) / max(self.rows, 1) * asp
        self.dist_n = np.sqrt(self.dx_n**2 + self.dy_n**2)

        self.bm = {}
        for c in all_chars:
            img = Image.new("L", (self.cw, self.ch), 0)
            ImageDraw.Draw(img).text((0, 0), c, fill=255, font=self.font)
            if np.array(img).max() == 0 and c != " ":
                log(f"WARNING: char '{c}' (U+{ord(c):04X}) not in font, skipping.")
                continue
            self.bm[c] = np.array(img, dtype=np.float32) / 255.0

        self.chars = np.full((self.rows, self.cols), " ", dtype="U1")
        self.colors = np.zeros((self.rows, self.cols, 3), dtype=np.uint8)

    def render_to_canvas(self, canvas=None):
        if canvas is None:
            canvas = np.zeros((VH, VW, 3), dtype=np.uint8)

        for row in range(self.rows):
            y = self.oy + row * self.ch
            if y + self.ch > VH: continue
            for col in range(self.cols):
                c = self.chars[row, col]
                if c == " " or c not in self.bm: continue
                x = self.ox + col * self.cw
                if x + self.cw > VW: continue

                char_bitmap = self.bm[c]
                char_color = self.colors[row, col]

                # Composite using np.maximum for additive blending
                target_region = canvas[y:y+self.ch, x:x+self.cw]
                colored_char = (char_bitmap[:, :, None] * char_color).astype(np.uint8)
                canvas[y:y+self.ch, x:x+self.cw] = np.maximum(target_region, colored_char)
        return canvas

# --- Renderer Class ---
class Renderer:
    def __init__(self):
        self.grids = {}
        self.S = {} # Persistent state

    def get_grid(self, key, all_chars):
        if key not in self.grids:
            sizes = {"xs": 8, "sm": 10, "md": 16, "lg": 20, "xl": 24, "xxl": 40, "title": 60}
            if FONT_PATH is None:
                find_font(FONT_PREFS)
            self.grids[key] = GridLayer(FONT_PATH, sizes[key], all_chars)
        return self.grids[key]

# --- Global collection of all characters used in the video ---
ALL_CHARS = set()
ALL_CHARS.update(PAL_CLAVIGER)
ALL_CHARS.update(PAL_CODE)
ALL_CHARS.update(PAL_LOCK)
ALL_CHARS.update("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,-:'!?/|#@&{}[]<>")
ALL_CHARS.discard(" ")

# --- _render_vf helper function ---
def _render_vf(r, grid_key, vf_func, hf_func, pal, f, t, S, sat=1.0, val_mult=1.0, custom_chars=None):
    g = r.get_grid(grid_key, ALL_CHARS)
    g.chars[:] = " " # Clear grid
    g.colors[:] = 0 # Clear colors

    val = vf_func(g, f, t, S) * val_mult
    val = np.clip(val, 0, 1)
    mask = val > 0.01

    if custom_chars is not None:
        ch = custom_chars
    else:
        ch = val2char(val, mask, pal)
    g.chars = ch

    hue = hf_func(g, f, t, S)
    R, G, B = hsv2rgb(hue, np.full_like(val, sat), val)
    g.colors = np.stack([R, G, B], axis=-1)

    return g.render_to_canvas()

# --- Placeholder ShaderChain and FeedbackBuffer (for future use/compatibility) ---
class ShaderChain:
    def __init__(self):
        self.shaders = []
    def add(self, name, **kwargs):
        pass # Not implemented for this demo
    def apply(self, canvas, f={}, t=0):
        return canvas

class FeedbackBuffer:
    def __init__(self):
        self.buffer = None
    def apply(self, canvas, **kwargs):
        if self.buffer is None or self.buffer.shape != canvas.shape:
            self.buffer = np.zeros_like(canvas)
        # Simplified feedback: just add a fraction of the previous frame
        decay = kwargs.get("decay", 0.9)
        self.buffer = (self.buffer * decay + canvas * (1-decay)).astype(np.uint8)
        return self.buffer

# --- Effect Functions (Scenes) ---

def fx_intro(r, f, t, S):
    g_sm = r.get_grid("sm", ALL_CHARS)
    g_lg = r.get_grid("lg", ALL_CHARS)
    g_title = r.get_grid("title", ALL_CHARS)

    canvas = np.full((VH, VW, 3), COLOR_DARK_BG, dtype=np.uint8)

    # Falling code particles (small grid)
    if "code_particles" not in S:
        S["code_particles"] = {
            "x": np.random.randint(0, g_sm.cols, 200).astype(np.float32),
            "y": np.random.uniform(-g_sm.rows, 0, 200).astype(np.float32),
            "speed": np.random.uniform(0.5, 2.0, 200).astype(np.float32),
            "char": np.random.choice(list(PAL_CODE), 200),
            "color_h": np.random.uniform(0.3, 0.4, 200) # Matrix green/cyan hue range
        }
    
    S["code_particles"]["y"] += S["code_particles"]["speed"] * 0.5 # slower for aesthetic
    
    # Reset particles that fall off screen
    reset_mask = S["code_particles"]["y"] > g_sm.rows
    S["code_particles"]["x"][reset_mask] = np.random.randint(0, g_sm.cols, reset_mask.sum())
    S["code_particles"]["y"][reset_mask] = np.random.uniform(-g_sm.rows / 2, 0, reset_mask.sum())
    S["code_particles"]["speed"][reset_mask] = np.random.uniform(0.5, 2.0, reset_mask.sum())
    S["code_particles"]["char"][reset_mask] = np.random.choice(list(PAL_CODE), reset_mask.sum())
    S["code_particles"]["color_h"][reset_mask] = np.random.uniform(0.3, 0.4, reset_mask.sum())

    g_sm.chars[:] = " "
    g_sm.colors[:] = 0
    for i in range(len(S["code_particles"]["x"])):
        row, col = int(S["code_particles"]["y"][i]), int(S["code_particles"]["x"][i])
        if 0 <= row < g_sm.rows and 0 <= col < g_sm.cols:
            hue = S["code_particles"]["color_h"][i]
            val = np.clip(1 - (row / g_sm.rows) * 0.5, 0.2, 1.0) # Fade at bottom
            R, G, B = hsv2rgb_scalar(hue, 0.8, val)
            g_sm.chars[row, col] = S["code_particles"]["char"][i]
            g_sm.colors[row, col] = (R, G, B)
    canvas = blend_canvas(canvas, g_sm.render_to_canvas(), "add")

    # Title "◈ CLAVIGER"
    title_text = "◈ CLAVIGER"
    title_row = g_title.rows // 2 - 2
    title_col = center_text_row(g_title, title_text)
    stamp_text(g_title, title_text, title_row, title_col, rgb_to_np_array(COLOR_MATRIX_GREEN))
    canvas = blend_canvas(canvas, g_title.render_to_canvas(), "screen")

    # Subtitle "Privacy Skill for Hermes Agent"
    subtitle_text = "Privacy Skill for Hermes Agent"
    subtitle_row = g_lg.rows // 2 + 2
    subtitle_col = center_text_row(g_lg, subtitle_text)
    stamp_text(g_lg, subtitle_text, subtitle_row, subtitle_col, rgb_to_np_array(COLOR_ELECTRIC_CYAN))
    canvas = blend_canvas(canvas, g_lg.render_to_canvas(), "screen")

    return canvas

def fx_what_it_does(r, f, t, S):
    canvas = np.full((VH, VW, 3), COLOR_DARK_BG, dtype=np.uint8)
    g_md = r.get_grid("md", ALL_CHARS)
    g_lg = r.get_grid("lg", ALL_CHARS)

    features = [
        "Real ECIES Encryption (secp256k1 + AES-256-GCM)",
        "IPFS Decentralized Storage",
        "Cloudflare KV Indexing",
        "x402 Payment Protocol"
    ]
    lock_chars = list(PAL_LOCK)
    current_feature_idx = int((t - 5) / (7 / len(features))) % len(features)
    display_feature = features[current_feature_idx]

    # Lock/key motif (large grid)
    lock_char = lock_chars[int(t * 2) % len(lock_chars)]
    for row in range(g_lg.rows):
        for col in range(g_lg.cols):
            if (row + col) % 5 == 0:
                g_lg.chars[row, col] = lock_char
                hue = (t * 0.05 + g_lg.dist_n[row, col] * 0.2) % 1.0
                R, G, B = hsv2rgb_scalar(hue, 0.8, 0.4)
                g_lg.colors[row, col] = (R, G, B)
    canvas = blend_canvas(canvas, g_lg.render_to_canvas(), "add")

    # Feature text (medium grid)
    text_row = g_md.rows // 2
    text_col = center_text_row(g_md, display_feature)
    stamp_text(g_md, display_feature, text_row, text_col, rgb_to_np_array(COLOR_GOLD))
    canvas = blend_canvas(canvas, g_md.render_to_canvas(), "screen")

    return canvas

def fx_how_it_works(r, f, t, S):
    canvas = np.full((VH, VW, 3), COLOR_DARK_BG, dtype=np.uint8)
    g_lg = r.get_grid("lg", ALL_CHARS)
    g_md = r.get_grid("md", ALL_CHARS)

    # Background vortex/tunnel effect
    val_field = lambda g, f, t, S: (np.sin(g.dist * 0.1 - t * 3) * 0.5 + 0.5)
    hue_field = lambda g, f, t, S: (g.angle / (2 * np.pi) + t * 0.05 + 0.6) % 1.0 # Deep purple to cyan
    pal = PAL_CLAVIGER
    background_canvas = _render_vf(r, "md", val_field, hue_field, pal, f, t, S, sat=0.7, val_mult=0.7)
    canvas = blend_canvas(canvas, background_canvas, "screen")

    # Forge flow text
    flow_text = "Agent forges secret → ECIES encrypts → IPFS stores → KV indexes → Lockbox sealed"
    text_row = g_lg.rows // 2
    text_col = center_text_row(g_lg, flow_text)

    # Typing effect for the text
    display_length = min(len(flow_text), int((t - 12) * 5)) # Starts at 12s, 5 chars/sec
    current_text = flow_text[:display_length]

    stamp_text(g_lg, current_text, text_row, text_col, rgb_to_np_array(COLOR_ELECTRIC_CYAN))
    canvas = blend_canvas(canvas, g_lg.render_to_canvas(), "screen")

    return canvas

def fx_live_proof(r, f, t, S):
    canvas = np.full((VH, VW, 3), COLOR_DARK_BG, dtype=np.uint8)
    g_lg = r.get_grid("lg", ALL_CHARS)
    g_md = r.get_grid("md", ALL_CHARS)
    g_sm = r.get_grid("sm", ALL_CHARS)

    # CID text
    cid_text = "CID: QmXrfcVoggLnDar3W2DUMARG2xf6qc3pbq812hdsQoWDZn"
    cid_row = g_lg.rows // 2 - 2
    cid_col = center_text_row(g_lg, cid_text)
    stamp_text(g_lg, cid_text, cid_row, cid_col, rgb_to_np_array(COLOR_SUCCESS_GREEN))
    canvas = blend_canvas(canvas, g_lg.render_to_canvas(), "screen")

    # Verification text
    verify_text = "✅ Real encryption. Real IPFS. Real Cloudflare KV."
    verify_row = g_md.rows // 2 + 2
    verify_col = center_text_row(g_md, verify_text)
    stamp_text(g_md, verify_text, verify_row, verify_col, rgb_to_np_array(COLOR_SUCCESS_GREEN))
    canvas = blend_canvas(canvas, g_md.render_to_canvas(), "screen")

    # Particle sparks (small grid, green)
    if "sparks" not in S:
        S["sparks"] = {
            "x": np.random.uniform(0, g_sm.cols, 100).astype(np.float32),
            "y": np.random.uniform(0, g_sm.rows, 100).astype(np.float32),
            "vx": np.random.uniform(-1, 1, 100).astype(np.float32),
            "vy": np.random.uniform(-1, 1, 100).astype(np.float32),
            "life": np.random.uniform(0.5, 1.5, 100).astype(np.float32),
            "char": np.random.choice(list("*.o+"), 100)
        }
    
    S["sparks"]["x"] += S["sparks"]["vx"] * 0.5
    S["sparks"]["y"] += S["sparks"]["vy"] * 0.5
    S["sparks"]["life"] -= 0.05
    
    reset_mask = S["sparks"]["life"] <= 0
    S["sparks"]["x"][reset_mask] = np.random.uniform(0, g_sm.cols, reset_mask.sum())
    S["sparks"]["y"][reset_mask] = np.random.uniform(0, g_sm.rows, reset_mask.sum())
    S["sparks"]["vx"][reset_mask] = np.random.uniform(-1, 1, reset_mask.sum())
    S["sparks"]["vy"][reset_mask] = np.random.uniform(-1, 1, reset_mask.sum())
    S["sparks"]["life"][reset_mask] = np.random.uniform(0.5, 1.5, reset_mask.sum())
    S["sparks"]["char"][reset_mask] = np.random.choice(list("*.o+"), reset_mask.sum())

    g_sm.chars[:] = " "
    g_sm.colors[:] = 0
    for i in range(len(S["sparks"]["x"])):
        row, col = int(S["sparks"]["y"][i]), int(S["sparks"]["x"][i])
        if 0 <= row < g_sm.rows and 0 <= col < g_sm.cols:
            alpha = S["sparks"]["life"][i] / 1.5
            color = (int(COLOR_SUCCESS_GREEN[0] * alpha), int(COLOR_SUCCESS_GREEN[1] * alpha), int(COLOR_SUCCESS_GREEN[2] * alpha))
            g_sm.chars[row, col] = S["sparks"]["char"][i]
            g_sm.colors[row, col] = color
    canvas = blend_canvas(canvas, g_sm.render_to_canvas(), "add")

    return canvas

def fx_outro(r, f, t, S):
    canvas = np.full((VH, VW, 3), COLOR_DARK_BG, dtype=np.uint8)
    g_sm = r.get_grid("sm", ALL_CHARS)
    g_lg = r.get_grid("lg", ALL_CHARS)
    g_title = r.get_grid("title", ALL_CHARS)

    # Aurora effect (background)
    val_field = lambda g, f, t, S: (np.sin(g.dx_n * 5 + t) * np.cos(g.dy_n * 3) + 1) * 0.5
    hue_field = lambda g, f, t, S: (g.dist_n * 0.3 + t * 0.03 + 0.6) % 1.0 # Purple to blueish green
    background_canvas = _render_vf(r, "sm", val_field, hue_field, PAL_CLAVIGER, f, t, S, sat=0.8, val_mult=0.6)
    canvas = blend_canvas(canvas, background_canvas, "screen")

    # Title "◈ CLAVIGER"
    title_text = "◈ CLAVIGER"
    title_row = g_title.rows // 2 - 4
    title_col = center_text_row(g_title, title_text)
    stamp_text(g_title, title_text, title_row, title_col, rgb_to_np_array(COLOR_MATRIX_GREEN))
    canvas = blend_canvas(canvas, g_title.render_to_canvas(), "screen")

    # Tagline
    tagline_text = "Agents That Keep Secrets"
    tagline_row = g_lg.rows // 2 + 1
    tagline_col = center_text_row(g_lg, tagline_text)
    stamp_text(g_lg, tagline_text, tagline_row, tagline_col, rgb_to_np_array(COLOR_ELECTRIC_CYAN))
    canvas = blend_canvas(canvas, g_lg.render_to_canvas(), "screen")

    # GitHub and Social
    github_text = "github.com/miladyxx333-lab/hermes-agent-blue"
    github_row = g_sm.rows // 2 + 10
    github_col = center_text_row(g_sm, github_text)
    stamp_text(g_sm, github_text, github_row, github_col, rgb_to_np_array(COLOR_GOLD))
    canvas = blend_canvas(canvas, g_sm.render_to_canvas(), "screen")

    social_text = "@NousResearch #HermesAgent"
    social_row = g_sm.rows // 2 + 12
    social_col = center_text_row(g_sm, social_text)
    stamp_text(g_sm, social_text, social_row, social_col, rgb_to_np_array(COLOR_GOLD))
    canvas = blend_canvas(canvas, g_sm.render_to_canvas(), "screen")

    return canvas

# --- Scene Definitions ---
SCENES = [
    {"start": 0.0,  "end": 5.0,  "name": "intro",        "grid": "xl", "fx": fx_intro,       "gamma": 0.8},
    {"start": 5.0,  "end": 12.0, "name": "what_it_does", "grid": "lg", "fx": fx_what_it_does, "gamma": 0.8},
    {"start": 12.0, "end": 20.0, "name": "how_it_works", "grid": "lg", "fx": fx_how_it_works, "gamma": 0.75},
    {"start": 20.0, "end": 25.0, "name": "live_proof",   "grid": "lg", "fx": fx_live_proof,   "gamma": 0.8},
    {"start": 25.0, "end": 30.0, "name": "outro",        "grid": "xl", "fx": fx_outro,       "gamma": 0.7},
]

# --- Main Rendering Logic ---

def render_clip(seg, clip_path):
    r = Renderer()
    random.seed(hash(seg["id"]) + 42)

    fx_fn = seg["fx"]

    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF),
        "-pix_fmt", "yuv420p", clip_path
    ]
    
    log_file_path = clip_path.replace(".mp4", ".log")
    with open(log_file_path, "w") as stderr_fh:
        pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=stderr_fh)

        for fi in range(seg["frame_start"], seg["frame_end"]):
            t = fi / FPS
            canvas = fx_fn(r, {}, t, r.S) # Pass empty features for now
            canvas = tonemap(canvas, gamma=seg.get("gamma", 0.75))
            pipe.stdin.write(canvas.tobytes())

        pipe.stdin.close()
        pipe.wait()
    log(f"Rendered clip: {clip_path}")

def main():
    find_font(FONT_PREFS) # Initialize FONT_PATH
    if FONT_PATH is None:
        log("ERROR: Could not find a suitable monospace font. Please install one or adjust FONT_PREFS.")
        return

    temp_dir = "claviger_temp_clips"
    os.makedirs(temp_dir, exist_ok=True)

    segments_to_render = []
    for i, scene in enumerate(SCENES):
        segment = {
            "id": f"s{i:02d}_{scene['name']}",
            "name": scene["name"],
            "grid": scene["grid"],
            "fx": scene["fx"],
            "gamma": scene.get("gamma", 0.75),
            "frame_start": int(scene["start"] * FPS),
            "frame_end": int(scene["end"] * FPS),
        }
        segments_to_render.append(segment)

    clip_paths = [os.path.join(temp_dir, f"{seg['id']}.mp4") for seg in segments_to_render]

    log(f"Starting parallel rendering of {len(segments_to_render)} clips with {N_WORKERS} workers...")
    start_time = time.time()
    with ProcessPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {
            pool.submit(render_clip, seg, clip_path): seg["id"]
            for seg, clip_path in zip(segments_to_render, clip_paths)
        }
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as e:
                log(f"ERROR rendering clip {futures[fut]}: {e}")
                # Potentially re-raise or mark as failed for a retry mechanism
    
    end_time = time.time()
    log(f"All clips rendered in {end_time - start_time:.2f} seconds.")

    # Concatenate clips
    output_video_path = os.path.expanduser("~/Desktop/claviger_demo.mp4")
    concat_file_path = os.path.join(temp_dir, "concat_list.txt")

    with open(concat_file_path, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{os.path.abspath(cp)}'\n")
    
    log(f"Concatenating clips to {output_video_path}...")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file_path,
        "-c", "copy",
        output_video_path
    ]
    subprocess.run(concat_cmd, check=True)
    log("Video concatenation complete.")

    # Clean up temporary clips
    shutil.rmtree(temp_dir)
    log(f"Cleaned up temporary directory: {temp_dir}")
    log(f"Final video saved to {output_video_path}")

if __name__ == "__main__":
    main()
