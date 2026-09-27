"""Illustrative ARCH set for 8014 Chateau St, Houston TX 77028, drawn from public data:
HCAD acct 0300170170004 (A1 single-family, built 1940), lot ~40' x 100' (3,980 sf), house footprint ~28' x 40'
(OSM), detached accessory building at rear, east side yard ~9'-6" (driveway), west side yard ~1'-10",
CenterPoint Energy (overhead service, pole on west), FEMA Zone X. Meter placement and service upgrade are
illustrative (renovation scope), clearly marked as a sample."""
import os
W, H = 3600, 2400
INK, THIN, DIM, RED, GRN = "#111", "#444", "#1f4fa0", "#b3261e", "#1f7a3a"
FONT = "Arial, Helvetica, sans-serif"

def T(x, y, s, size=22, anchor="start", weight="normal", color=INK, rot=0):
    tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
    s = str(s).replace("&", "&amp;")
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{tr}>{s}</text>'
def L(x1, y1, x2, y2, w=2, c=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}"{d}/>'
def R(x, y, w, h, sw=2, c=INK, fill="none", dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{c}" stroke-width="{sw}"{d}/>'
def dimH(x1, x2, y, label, size=20):
    return L(x1, y, x2, y, 1.5, DIM) + L(x1, y - 10, x1, y + 10, 2, DIM) + L(x2, y - 10, x2, y + 10, 2, DIM) + T((x1 + x2) / 2, y - 10, label, size, "middle", color=DIM)
def dimV(x, y1, y2, label, size=20):
    return L(x, y1, x, y2, 1.5, DIM) + L(x - 10, y1, x + 10, y1, 2, DIM) + L(x - 10, y2, x + 10, y2, 2, DIM) + T(x - 12, (y1 + y2) / 2, label, size, "middle", color=DIM, rot=-90)

def title_block(sheet, name, scale):
    x = W - 560
    s = R(40, 40, W - 80, H - 80, 4) + R(x, 40, 520, H - 80, 3)
    s += R(x + 20, 70, 480, 120, 3, INK, "#fff") + T(x + 260, 122, "ARCHITECTURAL", 40, "middle", "bold") + T(x + 260, 168, "DRAWINGS", 40, "middle", "bold")
    rows = [("PROJECT", "SINGLE-FAMILY RESIDENCE"), ("", "RENOVATION · SERVICE UPGRADE"), ("ADDRESS", "8014 CHATEAU ST"), ("", "HOUSTON, TX 77028"),
            ("COUNTY", "HARRIS · HCAD 0300170170004"), ("USE / YEAR", "A1 SINGLE-FAMILY · BUILT 1940"), ("UTILITY", "CENTERPOINT ENERGY"),
            ("SERVICE", "(N) 200A · 120/240V · OVERHEAD"), ("SET", "ARCH · A1.0 / E1.0 / A3.0 / A4.0"), ("SCALE", scale), ("SHEET NAME", name)]
    y = 250
    for k, v in rows:
        s += T(x + 20, y, k, 18, color=THIN) + T(x + 20, y + 30, v, 23, weight="bold") + L(x, y + 48, x + 520, y + 48, 1, THIN)
        y += 78
    s += T(x + 260, H - 150, sheet, 110, "middle", "bold") + T(x + 260, H - 96, "ILLUSTRATIVE SAMPLE", 20, "middle", "bold", RED) + T(x + 260, H - 68, "NOT FOR CONSTRUCTION", 20, "middle", "bold", RED)
    return s
def north(x, y):
    return f'<circle cx="{x}" cy="{y}" r="46" fill="none" stroke="{INK}" stroke-width="2"/><path d="M{x} {y-40} L{x+16} {y+18} L{x} {y+6} L{x-16} {y+18} Z" fill="{INK}"/>' + T(x, y - 58, "N", 28, "middle", "bold")
def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#fff"/>{body}</svg>'

# ---------- A1.0 SITE PLAN  (lot 40' x 100', street to the north; 1 ft = 16 px, rotated so street is at top) ----------
def site():
    F = 16; ox, oy = 700, 260          # lot NW corner
    s = title_block("A1.0", "SITE / PLOT PLAN", '1" = 8\'-0"')
    s += T(ox + 20 * F, oy - 70, "CHATEAU ST", 30, "middle", "bold") + L(ox - 200, oy - 40, ox + 40 * F + 200, oy - 40, 2, THIN, "20 12")
    s += f'<rect x="{ox}" y="{oy}" width="{40*F}" height="{100*F}" fill="none" stroke="{INK}" stroke-width="3" stroke-dasharray="34 8 6 8"/>'
    s += T(ox + 40 * F + 20, oy + 50 * F, "PROPERTY LINE · 40'-0\" x 100'-0\" · 3,980 SF", 20, rot=90)
    # chain-link fence at front + east wood fence along driveway
    s += L(ox, oy + 12, ox + 40 * F, oy + 12, 2.5, THIN, "4 6") + T(ox + 30, oy + 40, "(E) 4' CHAIN-LINK FENCE", 18, color=THIN)
    s += L(ox + 40 * F - 6, oy + 12 * F, ox + 40 * F - 6, oy + 70 * F, 3, THIN, "18 6") + T(ox + 40 * F - 20, oy + 72 * F + 20, "(E) 6' WOOD FENCE", 18, "end", color=THIN)
    # house: 28' wide x 40' deep, 16' from front, 1'-10" from west line
    hx, hy = ox + 1.8 * F, oy + 16 * F
    body = f"M{hx} {hy} H{hx + 28*F} V{hy + 25*F} H{hx + 14.5*F} V{hy + 40*F} H{hx} Z"
    s += f'<path d="{body}" fill="#ececec" stroke="{INK}" stroke-width="5"/>'
    s += T(hx + 14 * F, hy + 12 * F, "(E) 1-STORY RESIDENCE", 26, "middle", "bold") + T(hx + 14 * F, hy + 12 * F + 34, "≈ 880 SF · BUILT 1940 · F.F.E. 43.5'", 20, "middle")
    s += R(hx + 5 * F, hy - 6 * F, 12 * F, 6 * F, 2, THIN) + T(hx + 11 * F, hy - 2.6 * F, "PORCH", 18, "middle", color=THIN)
    # rear accessory building
    s += R(ox + 18.5 * F, oy + 68 * F, 21 * F, 28 * F, 3, INK, "#f4f4f4") + T(ox + 29 * F, oy + 82 * F, "(E) DETACHED", 20, "middle", "bold") + T(ox + 29 * F, oy + 82 * F + 28, "ACCESSORY BLDG", 20, "middle", "bold")
    # driveway along east
    s += R(hx + 28 * F + 4, oy, 9.2 * F, 66 * F, 1.5, THIN, dash="10 6") + T(hx + 32.6 * F, oy + 45 * F, "(E) DRIVEWAY", 18, "middle", color=THIN, rot=90)
    # east wall: meter, ATS, pads (toward rear)
    ex = hx + 28 * F; my = hy + 4 * F
    s += R(ex + 4, my - 14, 22, 28, 3, RED, "#fff") + T(ex + 36, my + 8, "EM · (N) 200A", 22, weight="bold", color=RED)
    for k, lbl in ((0, "ATS"), (1, "BATT 1"), (2, "BATT 2")):
        by = my + 18 + k * 3 * F
        s += R(ex + 3, by, 3 * F - 4, 3 * F - 4, 2.5, GRN, "#e6f4ea" if k else "#fff") + T(ex + 1.5 * F, by + 1.9 * F, lbl, 13, "middle", "bold", GRN)
    s += dimV(ex - 26, my + 18, my + 18 + 11 * F, "11'-0\" CLEAR WALL", 16)
    s += dimH(ex, ox + 40 * F - 6, hy + 20 * F, "9'-6\" (114\")", 18)
    s += dimH(ox, hx, hy + 30 * F, "1'-10\"", 16)
    s += R(hx - 26, hy + 3 * F, 22, 22, 3, "#8a5a00", "#fff") + T(hx - 34, hy + 3 * F + 18, "GM", 20, "end", "bold", "#8a5a00")
    s += L(ox - 160, hy + 10 * F, hx, hy + 10 * F, 1.5, THIN, "8 6") + T(ox - 14, hy + 10 * F - 10, "(E) OVERHEAD DROP · POLE (W)", 16, "end", color=THIN)
    s += north(W - 700, 220)
    notes = ["SITE NOTES:",
             "1. (N) 200A OVERHEAD SERVICE; METER EM RELOCATED TO EAST WALL, 5'-0\" A.F.F. TO CENTER.",
             "2. (E) GAS METER GM ON WEST WALL · OPPOSITE SIDE OF HOUSE FROM BATTERY ZONE (>30' AWAY).",
             "3. BATTERY ZONE: 11'-0\" CLEAR EAST WALL FROM METER (30\" ATS + TWO 3'x3' PADS), NO WINDOWS.",
             "4. PADS WITHIN 1'-0\" OF WALL AND 20'-0\" OF METER · HARNESS SURFACE-RUN · NO TRENCHING.",
             "5. EAST SIDE YARD 9'-6\" (114\") WALL TO FENCE (≥ 56\" REQ'D) · WEST SIDE YARD 1'-10\" NOT USED.",
             "6. BATTERY ZONE KEPT CLEAR OF A/C, HOSE BIBS AND LANDSCAPING · GRADE LEVEL ±1% · FEMA ZONE X.",
             "7. NO PHOTOVOLTAIC SYSTEM IN THIS SCOPE."]
    y = 1960
    for t in notes:
        s += T(1500, y, t, 20, weight="bold" if t.endswith(":") else "normal"); y += 32
    return svg(s)

# ---------- E1.0 ELECTRICAL ----------
def electrical():
    s = title_block("E1.0", "ELECTRICAL PLAN & RISER", '1/4" = 1\'-0"')
    G = 36; ox, oy = 330, 300
    s += T(ox, oy - 40, "PARTIAL PLAN · EAST WALL AT UTILITY ROOM / METER", 30, weight="bold")
    s += f'<rect x="{ox + 4*G}" y="{oy}" width="{20*G}" height="{24*G}" fill="#f4f4f4" stroke="{INK}" stroke-width="6"/>'
    s += T(ox + 14 * G, oy + 10 * G, "UTILITY / LAUNDRY", 30, "middle", "bold")
    wall = ox + 4 * G
    s += R(wall - 3 * G, oy + 3 * G, 3 * G, 3 * G, 2, DIM, "#e8eef9", "8 6") + T(wall - 3 * G - 14, oy + 5.6 * G, "36\" x 30\" CLEAR", 20, "end", color=DIM)
    s += R(wall - 30, oy + 4 * G, 26, 40, 3, RED, "#fff") + T(wall - 3 * G - 14, oy + 4 * G + 8, "EM (EXTERIOR)", 24, "end", "bold", RED)
    s += R(wall + 6, oy + 3.6 * G, 30, 70, 3, INK, "#fff") + T(wall + 50, oy + 4 * G + 20, "(N) MP · 200A MAIN", 24, weight="bold")
    s += T(wall + 50, oy + 4 * G + 50, "UTILITY ROOM WALL (NOT A CLOSET) · BACK-TO-BACK W/ METER", 20)
    s += R(wall - 1.1 * G, oy + 6.2 * G, 1.0 * G, 2.5 * G, 2.5, GRN, "#fff") + T(wall - 1.25 * G, oy + 7.7 * G, "ATS 30\"", 20, "end", "bold", GRN)
    for k in (0, 1):
        by = oy + (9 + k * 3) * G
        s += R(wall - 3 * G, by, 3 * G - 6, 3 * G - 6, 2.5, GRN, "#e6f4ea") + T(wall - 1.5 * G, by + 1.6 * G, f"BATT {k+1}", 20, "middle", "bold", GRN)
    s += R(wall - 12, oy + 17 * G, 12, 3 * G, 2, INK, "#dfe9f5") + T(wall - 20, oy + 18.6 * G, "(E) WINDOW 11'-0\" FROM EM", 18, "end")
    s += dimV(wall - 3.4 * G, oy + 6.5 * G, oy + 15 * G, "11'-0\" CLEAR FROM EM", 20)
    rx, ry = 1400, 380
    s += T(rx, ry - 50, "ELECTRICAL RISER DIAGRAM", 30, weight="bold")
    boxes = [("CENTERPOINT ENERGY", "(E) OVERHEAD SERVICE DROP · (N) MAST + WEATHERHEAD"), ("METER SOCKET", "(N) CL200 · 200A · EAST WALL"), ("MAIN PANEL MP", "(N) 200A MAIN BREAKER · 200A BUS · 30 CKT")]
    for i, (a, b) in enumerate(boxes):
        y = ry + i * 230
        s += R(rx, y, 620, 150, 3) + T(rx + 310, y + 62, a, 28, "middle", "bold") + T(rx + 310, y + 105, b, 20, "middle")
        if i < 2: s += L(rx + 310, y + 150, rx + 310, y + 230, 4)
    s += T(rx + 660, ry + 520, "ONE (1) MAIN PANEL · (E) 100A FUSE PANEL REMOVED", 23, weight="bold") + T(rx + 660, ry + 556, "NO SUBPANELS · NO PV · NO GENERATOR", 21)
    px, py = 1400, 1150
    s += T(px, py - 20, "SERVICE & LOAD SUMMARY", 28, weight="bold")
    rows = [("SERVICE SIZE", "(N) 200A, 120/240V, 1Ø, 3W"), ("MAIN BREAKER", "200A"), ("CALCULATED LOAD (NEC 220.82)", "84A"),
            ("HVAC", "(N) 2-TON HEAT PUMP"), ("WATER HEATER", "(E) 40 GAL GAS"), ("RANGE / DRYER", "ELECTRIC / GAS"), ("METER HEIGHT", "5'-0\" A.F.F. TO CENTER")]
    for i, (a, b) in enumerate(rows):
        y = py + 20 + i * 62
        s += R(px, y, 1500, 62, 1.5, THIN) + T(px + 20, y + 40, a, 22, weight="bold") + T(px + 780, y + 40, b, 22)
    notes = ["ELECTRICAL NOTES:", "1. METER AND MAIN PANEL SHARE THE EAST EXTERIOR WALL (BACK-TO-BACK).",
             "2. PROVIDE 30\" CLEAR WALL ADJACENT TO METER FOR BATTERY TRANSFER SWITCH.",
             "3. MAINTAIN NEC 110.26 WORKING SPACE 36\" DEEP x 30\" WIDE AT METER AND PANEL.",
             "4. PANEL NOT IN A CLOTHES CLOSET (NEC 240.24(D)) · METER + MAST SECURELY ATTACHED (NEC 110.12).",
             "5. HARNESS ROUTED SURFACE ON WALL · NO TRENCHING OR ATTIC RUNS."]
    y = 1760
    for t in notes:
        s += T(330, y, t, 21, weight="bold" if t.endswith(":") else "normal"); y += 34
    return svg(s)

# ---------- A3.0 EAST ELEVATION ----------
def elevation():
    s = title_block("A3.0", "EXTERIOR ELEVATION", '1/4" = 1\'-0"')
    E = 44; ox, gy = 300, 1500
    s += T(ox, 300, "EAST ELEVATION · METER WALL (DRIVEWAY SIDE)", 30, weight="bold")
    s += L(ox - 60, gy, ox + 30 * E, gy, 5)
    s += R(ox, gy - 10 * E, 25 * E, 10 * E, 5, INK, "#fafafa")
    s += f'<polygon points="{ox - 20},{gy - 10*E} {ox + 12.5*E},{gy - 16*E} {ox + 25*E + 20},{gy - 10*E}" fill="#e3e3e3" stroke="{INK}" stroke-width="4"/>'
    for k in range(1, 10):  # lap siding
        s += L(ox, gy - k * E, ox + 25 * E, gy - k * E, 1, "#bbb")
    mx = ox + 21 * E          # meter 4 ft from front corner (front = right)
    s += R(mx, gy - 5.5 * E, 26, 40, 3, RED, "#fff") + T(mx - 4, gy - 5.5 * E - 16, "EM · 5'-0\" A.F.F.", 22, "end", "bold", RED)
    s += L(mx + 60, gy - 5.2 * E, mx + 60, gy - 14.5 * E, 3, INK) + L(mx + 26, gy - 5.2 * E, mx + 60, gy - 5.2 * E, 2, INK) + T(mx + 72, gy - 13 * E, "(N) SERVICE MAST", 18)
    x = mx
    for name, wft in (("ATS", 2.5), ("BATT 1", 3), ("BATT 2", 3)):
        x -= wft * E
        h = 3 * E if name != "ATS" else 1.5 * E
        yb = gy - h if name != "ATS" else gy - 5.5 * E
        s += R(x + 4, yb, wft * E - 8, h, 3, GRN, "#e6f4ea" if name != "ATS" else "#fff") + T(x + wft * E / 2, yb + h / 2 + 8, name, 18, "middle", "bold", GRN)
    s += dimH(mx - 11 * E, mx + 26, gy - 8 * E, "11'-0\" CLEAR WALL · NO WINDOWS OR DOORS", 20)
    for wx in (mx - 14 * E, mx - 21 * E):  # windows beyond the battery zone
        s += R(wx, gy - 7.5 * E, 3 * E, 4.5 * E, 3, INK, "#dfe9f5") + L(wx + 1.5 * E, gy - 7.5 * E, wx + 1.5 * E, gy - 3 * E, 2)
    s += T(mx - 16 * E, gy - 8.3 * E, "(E) WINDOWS · 11'-0\" AND 18'-0\" FROM EM", 18, "middle")
    s += T(ox + 12.5 * E, gy + 50, "FINISH GRADE · LEVEL AT BATTERY PADS (±1%)", 22, "middle", "bold")
    s += T(ox + 25 * E + 20, gy - 2 * E, "FRONT (CHATEAU ST) →", 18)
    return svg(s)

# ---------- A4.0 BATTERY INSTALL COMPLIANCE SUMMARY ----------
def summary():
    s = title_block("A4.0", "BATTERY INSTALL COMPLIANCE SUMMARY", 'NTS')
    s += T(180, 220, "BASE POWER UNIT · INSTALL REQUIREMENT COMPLIANCE SCHEDULE", 34, weight="bold")
    s += T(180, 258, "This schedule states the as-designed value for each requirement, cross-referenced to the sheet and note that governs it.", 20, color=THIN)
    cols = [("#", 60), ("REQUIREMENT", 460), ("AS-DESIGNED VALUE", 620), ("STATUS", 140), ("REFERENCE", 460)]
    x0, y0 = 180, 320
    xs = [x0]
    for _, w in cols:
        xs.append(xs[-1] + w)
    rowh = 96
    IN = "″"  # inch mark used inline so it never collides with the Python string delimiter
    rows = [
        ("C1", "PANEL SIZE", "1 (N) MAIN PANEL · 200A MAIN BREAKER · 200A BUS (E) 100A FUSE PANEL REMOVED", "COMPLIES", "E1.0 RISER DIAGRAM · SERVICE & LOAD SUMMARY"),
        ("C2", "METER & PANEL LOCATION", "METER (EM) & MAIN PANEL (MP) BACK-TO-BACK ON EAST EXTERIOR WALL · EM 5'-0" + IN + " A.F.F.", "COMPLIES", "E1.0 PARTIAL PLAN, NOTE 1 · A3.0 ELEVATION"),
        ("C3", "WALL SPACE AT METER", "11'-0" + IN + " CLEAR EAST WALL FROM EM · NO WINDOWS OR DOORS (NEAREST WINDOW 11'-0" + IN + ")", "COMPLIES", "A1.0 NOTE 3 · A3.0 ELEVATION"),
        ("C4", "SIDE CLEARANCE", "EAST SIDE YARD 9'-6" + IN + " (114" + IN + ") WALL-TO-FENCE ≥ 56" + IN + " MIN. REQUIRED", "COMPLIES", "A1.0 SITE PLAN, NOTE 5"),
        ("C5", "GAS METER SEPARATION", "GAS METER (GM) ON WEST WALL, OPPOSITE SIDE OF HOUSE, > 30'-0" + IN + " FROM BATTERY ZONE ≥ 3'-0" + IN + " MIN. REQUIRED", "COMPLIES", "A1.0 NOTE 2"),
        ("C6", "NEC WORKING SPACE", "36" + IN + " DEEP x 30" + IN + " WIDE CLEAR AT EM & MP (110.26) · MP NOT IN CLOSET (240.24(D)) · EM/MAST SECURE (110.12)", "COMPLIES", "E1.0 NOTE 2-4"),
    ]
    y = y0
    for i, (a, w) in enumerate(cols):
        s += T((xs[i] + xs[i+1]) / 2, y - 14, a, 19, "middle", "bold", "#fff" if False else INK)
    s += R(x0, y - 46, xs[-1] - x0, 46, 2, INK, "#e7e7e7")
    for i, (a, w) in enumerate(cols):
        s += T((xs[i] + xs[i+1]) / 2, y - 14, a, 19, "middle", "bold")
    for r_i, (cid, req, val, stat, ref) in enumerate(rows):
        ry = y + r_i * rowh
        fill = "#f4f9f4" if r_i % 2 == 0 else "#ffffff"
        s += R(x0, ry, xs[-1] - x0, rowh, 1.5, THIN, fill)
        cells = [cid, req, val, stat, ref]
        for i, val_ in enumerate(cells):
            cx = xs[i] + 14
            col = GRN if i == 3 else INK
            wt = "bold" if i in (0, 1, 3) else "normal"
            words = val_.split(" ")
            line = ""; ly = ry + 30; maxw = cols[i][1] - 24
            for w_ in words:
                test = (line + " " + w_).strip()
                if len(test) * (10.5 if i in (2, 4) else 11) > maxw and line:
                    s += T(cx, ly, line, 17 if i in (2, 4) else 19, weight=wt, color=col)
                    line = w_; ly += 24
                else:
                    line = test
            s += T(cx, ly, line, 17 if i in (2, 4) else 19, weight=wt, color=col)
        for i in range(1, len(cols)):
            s += L(xs[i], ry, xs[i], ry + rowh, 1, THIN)
    s += L(x0, y - 46, x0, y + len(rows) * rowh, 2, INK)
    s += L(xs[-1], y - 46, xs[-1], y + len(rows) * rowh, 2, INK)
    s += L(x0, y + len(rows) * rowh, xs[-1], y + len(rows) * rowh, 2, INK)

    ny = y + len(rows) * rowh + 60
    s += T(180, ny, "RESULT", 26, weight="bold")
    s += R(180, ny + 20, 1400, 80, 3, GRN, "#e6f4ea") + T(880, ny + 70, "ALL 6 REQUIREMENTS COMPLY · SITE ELIGIBLE FOR A BASE POWER BATTERY INSTALL", 22, "middle", "bold", GRN)
    s += T(180, ny + 150, "RECOMMENDED CONFIGURATION", 22, weight="bold")
    s += T(180, ny + 184, "DOUBLE · 2 x 25 kWh UNITS (200A SERVICE + 9'-0" + IN + " MIN. CLEAR WALL, BOTH PROVIDED)", 20)
    s += T(180, ny + 240, "NOTES:", 20, weight="bold")
    for i, t in enumerate(["1. THIS SCHEDULE SUMMARIZES INFORMATION SHOWN IN DETAIL ON SHEETS A1.0, E1.0 AND A3.0. WHERE A CONFLICT",
                            "    EXISTS, THE DETAIL SHEET GOVERNS.",
                            "2. AS-BUILT CONDITIONS SHALL BE FIELD VERIFIED BY THE INSTALLER PRIOR TO EQUIPMENT SET.",
                            "3. THIS IS AN ILLUSTRATIVE SAMPLE PREPARED FOR DEMONSTRATION; NOT A PERMITTED CONSTRUCTION DOCUMENT."]):
        s += T(180, ny + 272 + i * 28, t, 18, color=THIN)
    return svg(s)

out = os.path.dirname(os.path.abspath(__file__))
for name, fn in (("CH-A1.0-site", site), ("CH-E1.0-electrical", electrical), ("CH-A3.0-elevation", elevation), ("CH-A4.0-summary", summary)):
    open(os.path.join(out, name + ".svg"), "w", encoding="utf-8").write(fn())
print("chateau svgs written")
