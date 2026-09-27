"""Generate a SAMPLE builder plan set (3 sheets) for the checker demo.
Drawn to satisfy every Base Power install requirement. Clearly marked as sample/demo."""
import os

W, H = 3600, 2400
INK, THIN, DIM, RED = "#111", "#444", "#1f4fa0", "#b3261e"
FONT = "Arial, Helvetica, sans-serif"

def T(x, y, s, size=22, anchor="start", weight="normal", color=INK, rot=0):
    tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{tr}>{s}</text>'

def L(x1, y1, x2, y2, w=2, c=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}"{d}/>'

def R(x, y, w, h, sw=2, c=INK, fill="none", dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{c}" stroke-width="{sw}"{d}/>'

def dim(x1, y1, x2, y2, label, off=0, vertical=False, size=22):
    s = ""
    if vertical:
        s += L(x1 + off, y1, x2 + off, y2, 1.5, DIM)
        s += L(x1 + off - 10, y1, x1 + off + 10, y1, 2, DIM) + L(x2 + off - 10, y2, x2 + off + 10, y2, 2, DIM)
        s += T(x1 + off - 12, (y1 + y2) / 2, label, size, "middle", color=DIM, rot=-90)
    else:
        s += L(x1, y1 + off, x2, y2 + off, 1.5, DIM)
        s += L(x1, y1 + off - 10, x1, y1 + off + 10, 2, DIM) + L(x2, y2 + off - 10, x2, y2 + off + 10, 2, DIM)
        s += T((x1 + x2) / 2, y1 + off - 10, label, size, "middle", color=DIM)
    return s

def title_block(sheet, name, scale):
    x = W - 560
    s = R(40, 40, W - 80, H - 80, 4) + R(x, 40, 520, H - 80, 3)
    s += R(x + 20, 70, 480, 120, 3, INK, "#fff") + T(x + 260, 122, "ARCHITECTURAL", 40, "middle", "bold") + T(x + 260, 168, "DRAWINGS", 40, "middle", "bold")
    rows = [("PROJECT", "DUPLEX RESIDENCE · UNITS A &amp; B"), ("ADDRESS", "104 GUNNER RD"), ("", "BUDA, TX 78610"),
            ("LEGAL", "LOT 20, BLOCK D"), ("", "EMMA PARK SUBD. PH. 2"), ("COUNTY", "HAYS · PROP ID 205025"),
            ("UTILITY", "PEDERNALES ELEC. COOP"), ("SERVICE", "200A PER UNIT · 120/240V"), ("SET", "ARCH · A1.0 / E1.0 / A3.0"),
            ("SCALE", scale), ("SHEET NAME", name)]
    y = 250
    for k, v in rows:
        s += T(x + 20, y, k, 18, color=THIN) + T(x + 20, y + 30, v, 24, weight="bold")
        s += L(x, y + 48, x + 520, y + 48, 1, THIN); y += 78
    s += T(x + 260, H - 150, sheet, 110, "middle", "bold") + T(x + 260, H - 96, "ILLUSTRATIVE SAMPLE", 20, "middle", "bold", RED) + T(x + 260, H - 68, "NOT FOR CONSTRUCTION", 20, "middle", "bold", RED)
    return s

def north(x, y):
    return f'<circle cx="{x}" cy="{y}" r="46" fill="none" stroke="{INK}" stroke-width="2"/><path d="M{x} {y-40} L{x+16} {y+18} L{x} {y+6} L{x-16} {y+18} Z" fill="{INK}"/>' + T(x, y - 58, "N", 28, "middle", "bold")

def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#fff"/>{body}</svg>'

# ---------- A1.0 SITE / PLOT PLAN  (1" = 10'-0" ; 1 ft = 14 px) ----------
F = 11
def site():
    s = title_block("A1.0", "SITE / PLOT PLAN", '1" = 10\'-0"')
    ox, oy = 420, 300
    # lot (simplified pie lot on cul-de-sac)
    lot = [(0, 0), (150, 0), (150, 118), (110, 148), (40, 148), (0, 118)]
    pts = " ".join(f"{ox + x * F},{oy + y * F}" for x, y in lot)
    s += f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="3" stroke-dasharray="34 8 6 8"/>'
    s += T(ox + 75 * F, oy - 24, "PROPERTY LINE · 0.475 AC", 24, "middle", "bold")
    # setbacks
    s += R(ox + 7 * F, ox and oy + 25 * F, 136 * F, 88 * F, 1.5, THIN, dash="10 8")
    s += T(ox + 8 * F, oy + 25 * F - 10, "BUILDING SETBACK LINE", 18, color=THIN)
    # duplex footprint: 90 ft wide x 44 ft deep, garages at outer ends
    hx, hy, hw, hd = 30, 44, 90, 44
    X0, Y0 = ox + hx * F, oy + hy * F
    s += f'<rect x="{X0}" y="{Y0}" width="{hw*F}" height="{hd*F}" fill="#ececec" stroke="{INK}" stroke-width="5"/>'
    s += L(X0 + 45 * F, Y0, X0 + 45 * F, Y0 + hd * F, 4)
    for gx, lbl in ((0, "GARAGE A"), (68, "GARAGE B")):
        s += R(X0 + gx * F, Y0 + 20 * F, 22 * F, 24 * F, 2, THIN, "#f7f7f7") + T(X0 + (gx + 11) * F, Y0 + 33 * F, lbl, 22, "middle", "bold")
    s += T(X0 + 22 * F, Y0 + 12 * F, "UNIT A", 34, "middle", "bold") + T(X0 + 68 * F, Y0 + 12 * F, "UNIT B", 34, "middle", "bold")
    s += T(X0 + 45 * F, Y0 + hd * F + 34, "2-STORY DUPLEX · 1,885 SF PER UNIT · F.F.E. 730.0'", 22, "middle")
    # side walls: meters on outer garage walls
    for side, wx, sign, u in (("A", X0, -1, "A"), ("B", X0 + hw * F, 1, "B")):
        my = Y0 + 36 * F
        s += R(wx + (sign * 4 if sign > 0 else -26), my - 14, 22, 28, 3, RED, "#fff") + T(wx + sign * 40, my + 8, f"EM-{u}", 24, "start" if sign > 0 else "end", "bold", RED)
        # transfer switch zone + 2 battery zones heading toward rear
        for k, lbl in ((0, "ATS"), (1, "BATT 1"), (2, "BATT 2")):
            by = my - 18 - (k + 1) * 3 * F
            bx = wx + (0 if sign > 0 else -3 * F)
            s += R(bx + (2 if sign > 0 else -2), by, 3 * F - 4, 3 * F - 4, 2.5, "#1f7a3a", "#e6f4ea" if k else "#fff")
            s += T(bx + 1.5 * F, by + 1.9 * F, lbl, 15, "middle", "bold", "#1f7a3a")
        s += dim(wx, my - 18 - 9 * F, wx, my - 18, "9'-0\" CLEAR WALL · NO WINDOWS", off=sign * (3 * F + 60), vertical=True, size=18)
        # side yard + fence
        fx = wx + sign * 12 * F
        s += L(fx, Y0 - 6 * F, fx, Y0 + hd * F + 4 * F, 3, THIN, "18 6")
        s += T(fx + sign * 12, Y0 - 6 * F - 12, "6' FENCE", 18, "start" if sign > 0 else "end", color=THIN)
        s += dim(min(wx, fx), Y0 + 6 * F, max(wx, fx), Y0 + 6 * F, "12'-0\" SIDE YARD", off=0, size=18)
    # drive + walk to cul-de-sac
    s += R(X0 + 2 * F, Y0 + hd * F, 18 * F, 18 * F, 2, THIN) + R(X0 + 70 * F, Y0 + hd * F, 18 * F, 18 * F, 2, THIN)
    s += T(X0 + 11 * F, Y0 + (hd + 10) * F, "DRIVE A", 18, "middle", color=THIN) + T(X0 + 79 * F, Y0 + (hd + 10) * F, "DRIVE B", 18, "middle", color=THIN)
    s += T(ox + 75 * F, oy + 148 * F + 50, "GUNNER RD (CUL-DE-SAC)", 26, "middle", "bold")
    # dimensions
    s += dim(X0, Y0, X0 + hw * F, Y0, "90'-0\"", off=-60) + dim(X0 + hw * F, Y0, X0 + hw * F, Y0 + hd * F, "44'-0\"", off=12 * F + 90, vertical=True)
    s += north(W - 700, 220)
    notes = ["SITE NOTES:",
             "1. ALL-ELECTRIC UNITS · NO GAS SERVICE OR GAS METER ON SITE.",
             "2. ELECTRIC METERS EM-A / EM-B ON OUTER GARAGE SIDE WALLS, 5'-0\" A.F.F. TO CENTER.",
             "3. BATTERY ZONE: 9'-0\" CLEAR EXTERIOR WALL FROM METER (30\" ATS + TWO 3'x3' PADS),",
             "   PADS WITHIN 1'-0\" OF WALL, WITHIN 20'-0\" OF METER. NO TRENCHING REQUIRED.",
             "4. BATTERY ZONE KEEP CLEAR: NO LANDSCAPING, A/C, HOSE BIBS OR FENCE POSTS.",
             "5. PAD AREA FINISH-GRADED LEVEL (±1%). FEMA ZONE X.",
             "6. SIDE YARD 12'-0\" WALL TO FENCE (≥ 56\" REQUIRED: BATTERY + 32-38\" WALKWAY).",
             "7. NO PHOTOVOLTAIC SYSTEM IN THIS SCOPE."]
    y = 2060
    for n in notes:
        s += T(200, y, n, 22, "start", "bold" if n.endswith(":") else "normal")
        y += 34
    return svg(s)

# ---------- E1.0 ELECTRICAL (partial plan + riser + schedule) ----------
def electrical():
    s = title_block("E1.0", "ELECTRICAL PLAN &amp; RISER", '1/4" = 1\'-0"')
    # partial plan of Unit A garage side wall (1 ft = 36 px)
    G = 36; ox, oy = 330, 300
    s += T(ox, oy - 40, "PARTIAL PLAN · UNIT A GARAGE / METER WALL (UNIT B MIRROR)", 30, weight="bold")
    s += f'<rect x="{ox + 4*G}" y="{oy}" width="{22*G}" height="{24*G}" fill="#f4f4f4" stroke="{INK}" stroke-width="6"/>'
    s += T(ox + 15 * G, oy + 12 * G, "GARAGE A", 34, "middle", "bold")
    wall = ox + 4 * G
    s += R(wall - 3 * G, oy + 15 * G, 3 * G, 3 * G, 2, DIM, "#e8eef9", "8 6") + T(wall - 1.5 * G, oy + 18 * G + 34, "36\" x 30\" CLEAR", 20, "middle", color=DIM)
    s += R(wall - 30, oy + 16 * G, 26, 40, 3, RED, "#fff") + T(wall - 3 * G - 14, oy + 16 * G + 28, "EM-A (EXTERIOR)", 24, "end", "bold", RED)
    s += R(wall + 6, oy + 15.6 * G, 30, 70, 3, INK, "#fff") + T(wall + 50, oy + 16 * G + 20, "MP-A · 200A MAIN", 24, weight="bold")
    s += T(wall + 50, oy + 16 * G + 50, "GARAGE WALL (NOT A CLOSET) · BACK-TO-BACK W/ METER", 20)
    s += R(wall - 1.1 * G, oy + 12.4 * G, 1.0 * G, 2.5 * G, 2.5, "#1f7a3a", "#fff") + T(wall - 1.25 * G, oy + 13.9 * G, "ATS 30\"", 20, "end", "bold", "#1f7a3a")
    for k in (0, 1):
        by = oy + (9.2 - k * 3) * G
        s += R(wall - 3 * G, by, 3 * G - 6, 3 * G - 6, 2.5, "#1f7a3a", "#e6f4ea") + T(wall - 1.5 * G, by + 1.6 * G, f"BATT {k+1}", 20, "middle", "bold", "#1f7a3a")
    s += dim(wall, oy + 6.2 * G, wall, oy + 15.2 * G, "9'-0\" CLEAR · NO WINDOWS / DOORS", off=-3.6 * G, vertical=True, size=20)
    # riser diagram
    rx, ry = 1300, 380
    s += T(rx, ry - 50, "ELECTRICAL RISER DIAGRAM (PER UNIT)", 30, weight="bold")
    boxes = [("PEC UTILITY", "UNDERGROUND SERVICE LATERAL"), ("METER SOCKET", "CL200 · 200A · EM-A"), ("MAIN PANEL MP-A", "200A MAIN BREAKER · 200A BUS · 40 CKT")]
    for i, (a, b) in enumerate(boxes):
        y = ry + i * 230
        s += R(rx, y, 520, 150, 3) + T(rx + 260, y + 62, a, 28, "middle", "bold") + T(rx + 260, y + 105, b, 22, "middle")
        if i < 2: s += L(rx + 260, y + 150, rx + 260, y + 230, 4)
    s += T(rx + 560, ry + 520, "ONE (1) MAIN PANEL PER DWELLING UNIT", 24, weight="bold")
    s += T(rx + 560, ry + 556, "NO SUBPANELS · NO PV · NO GENERATOR", 22)
    # panel schedule / load calc
    px, py = 1300, 1150
    s += T(px, py - 20, "SERVICE &amp; LOAD SUMMARY · UNIT A (UNIT B IDENTICAL)", 28, weight="bold")
    rows = [("SERVICE SIZE", "200A, 120/240V, 1Ø, 3W"), ("MAIN BREAKER", "200A"), ("CALCULATED LOAD (NEC 220.82)", "118A"),
            ("HVAC", "3-TON HEAT PUMP (ALL-ELECTRIC)"), ("WATER HEATER", "50 GAL ELECTRIC"), ("RANGE / DRYER", "ELECTRIC"), ("METER HEIGHT", "5'-0\" A.F.F. TO CENTER")]
    for i, (a, b) in enumerate(rows):
        y = py + 20 + i * 62
        s += R(px, y, 1600, 62, 1.5, THIN) + T(px + 20, y + 40, a, 22, weight="bold") + T(px + 820, y + 40, b, 22)
    notes = ["ELECTRICAL NOTES:", "1. METER AND MAIN PANEL SHARE THE SAME EXTERIOR WALL (BACK-TO-BACK).",
             "2. PROVIDE 30\" CLEAR WALL ADJACENT TO METER FOR BATTERY TRANSFER SWITCH.",
             "3. MAINTAIN NEC 110.26 WORKING SPACE 36\" DEEP x 30\" WIDE AT METER AND PANEL.",
             "4. HARNESS ROUTED SURFACE ON WALL · NO TRENCHING OR ATTIC RUNS."]
    y = 1760
    for n in notes:
        s += T(200, y, n, 22, weight="bold" if n.endswith(":") else "normal"); y += 36
    return svg(s)

# ---------- A3.0 ELEVATION (meter wall) ----------
def elevation():
    s = title_block("A3.0", "EXTERIOR ELEVATIONS", '1/4" = 1\'-0"')
    E = 40; ox, gy = 220, 1500  # ground line y
    s += T(ox, 300, "WEST ELEVATION · UNIT A GARAGE SIDE WALL (METER WALL) · UNIT B EAST ELEVATION MIRROR", 30, weight="bold")
    s += L(ox - 60, gy, ox + 50 * E, gy, 5)
    s += R(ox, gy - 20 * E, 44 * E, 20 * E, 5, INK, "#fafafa")
    s += f'<polygon points="{ox - 20},{gy - 20*E} {ox + 22*E},{gy - 30*E} {ox + 44*E + 20},{gy - 20*E}" fill="#e3e3e3" stroke="{INK}" stroke-width="4"/>'
    s += L(ox, gy - 10 * E, ox + 44 * E, gy - 10 * E, 2, THIN)
    # meter at 5'-0" AFF near front (right side of this elevation = front)
    mx = ox + 38 * E
    s += R(mx, gy - 5.5 * E, 26, 40, 3, RED, "#fff") + T(mx + 13, gy - 5.5 * E - 16, "EM-A · 5'-0\" A.F.F.", 24, "middle", "bold", RED)
    s += dim(mx - 30, gy - 5 * E, mx - 30, gy, "5'-0\"", off=-20, vertical=True, size=20)
    # ATS + batteries heading toward rear (left)
    zones = [("ATS", 2.5), ("BATT 1", 3), ("BATT 2", 3)]
    x = mx
    for name, wft in zones:
        x -= wft * E
        h = 3 * E if name != "ATS" else 1.5 * E
        yb = gy - h if name != "ATS" else gy - 5.5 * E
        s += R(x + 4, yb, wft * E - 8, h, 3, "#1f7a3a", "#e6f4ea" if name != "ATS" else "#fff") + T(x + wft * E / 2, yb + h / 2 + 8, name, 20, "middle", "bold", "#1f7a3a")
    s += dim(x, gy - 8 * E, mx + 26, gy - 8 * E, "9'-0\" CLEAR WALL · NO WINDOWS OR DOORS", size=22)
    # windows only on the rear half, well away from the battery zone
    for wx in (4, 12):
        s += R(ox + wx * E, gy - 16 * E, 4 * E, 5 * E, 3, INK, "#dfe9f5") + L(ox + (wx + 2) * E, gy - 16 * E, ox + (wx + 2) * E, gy - 11 * E, 2)
    s += T(ox + 10 * E, gy - 17 * E, "2ND FLOOR WINDOWS (REAR, >10' FROM BATTERY ZONE)", 20, "middle")
    s += T(ox + 22 * E, gy + 50, "FINISH GRADE · LEVEL AT BATTERY PADS (±1%)", 22, "middle", "bold")
    return svg(s)

out = os.path.dirname(os.path.abspath(__file__))
for name, fn in (("A1.0-site", site), ("E1.0-electrical", electrical), ("A3.0-elevation", elevation)):
    open(os.path.join(out, name + ".svg"), "w", encoding="utf-8").write(fn())
print("svgs written")
