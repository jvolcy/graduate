#!/usr/bin/env python3
"""64x64 side-view player spritesheet: idle, run, jump, die.

The character faces right. Grounded frames share a sole pixel so a
bottom-center pivot stays put. Jump height comes from gameplay; the jump
row only changes the pose.
"""

import math
from PIL import Image, ImageDraw

FW, FH = 64, 64
COLS, ROWS = 6, 4
PAD = 80
BASE_SOLE = 58

OUT = (28, 18, 16, 255)
SKIN_D = (86, 50, 38, 255)
SKIN = (122, 74, 56, 255)
SKIN_L = (156, 102, 78, 255)
HAIR = (20, 14, 12, 255)
HAIR_L = (54, 40, 34, 255)
SHIRT = (242, 196, 52, 255)
SHIRT_D = (196, 140, 32, 255)
SHORTS = (46, 78, 168, 255)
SHORTS_D = (30, 52, 120, 255)
SHOE = (246, 242, 234, 255)
SHOE_D = (176, 166, 152, 255)
SOLE = (32, 26, 24, 255)
EYE_W = (250, 246, 238, 255)
PUPIL = (16, 12, 10, 255)
LIP = (154, 72, 80, 255)
HOOP = (236, 190, 84, 255)

THIGH, SHIN = 8, 7
UPPER, FORE = 8, 7


def ang_vec(deg, length):
    rad = math.radians(deg)
    return (math.sin(rad) * length, math.cos(rad) * length)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def rot_pt(p, deg, origin):
    if not deg:
        return p
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    dx, dy = p[0] - origin[0], p[1] - origin[1]
    return (origin[0] + dx * c - dy * s, origin[1] + dx * s + dy * c)


def canvas():
    return Image.new("RGBA", (FW + PAD * 2, FH + PAD * 2), (0, 0, 0, 0))


def stamp_disc(im, cx, cy, r, color):
    px = im.load()
    r2 = r * r
    x0, x1 = int(cx - r - 1), int(cx + r + 2)
    y0, y1 = int(cy - r - 1), int(cy + r + 2)
    w, h = im.size
    for y in range(y0, y1):
        for x in range(x0, x1):
            if 0 <= x < w and 0 <= y < h and (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                px[x, y] = color


def stamp_capsule(im, a, b, r, color, t0=0.0, t1=1.0):
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    steps = max(1, int(length * 2))
    for i in range(steps + 1):
        t = i / steps
        if t < t0 - 1e-6 or t > t1 + 1e-6:
            continue
        stamp_disc(im, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, r, color)


def fill_poly(im, pts, color):
    if len(pts) < 3:
        return
    ImageDraw.Draw(im).polygon([(p[0] + PAD, p[1] + PAD) for p in pts], fill=color)


def outline(im):
    src = im.copy()
    sp, dp = src.load(), im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            if sp[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and sp[nx, ny][3] != 0:
                    dp[x, y] = OUT
                    break


def to_game(im):
    """Return a drawable wrapper whose coordinates are in 64x64 space."""
    px = im.load()
    w, h = im.size

    def put(x, y, color):
        ix, iy = int(round(x + PAD)), int(round(y + PAD))
        if 0 <= ix < w and 0 <= iy < h:
            px[ix, iy] = color

    def disc(cx, cy, r, color):
        stamp_disc(im, cx + PAD, cy + PAD, r, color)

    def capsule(a, b, r, color, t0=0.0, t1=1.0):
        stamp_capsule(
            im,
            (a[0] + PAD, a[1] + PAD),
            (b[0] + PAD, b[1] + PAD),
            r,
            color,
            t0,
            t1,
        )

    return put, disc, capsule


def shift_canvas(im, dx, dy):
    out = canvas()
    src = im.load()
    dst = out.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            col = src[x, y]
            if col[3] == 0:
                continue
            nx, ny = x + int(dx), y + int(dy)
            if 0 <= nx < w and 0 <= ny < h:
                dst[nx, ny] = col
    return out


def crop_cell(im):
    return im.crop((PAD, PAD, PAD + FW, PAD + FH))


def spine_frame(hip, shoulder):
    dx, dy = shoulder[0] - hip[0], shoulder[1] - hip[1]
    length = math.hypot(dx, dy) or 1
    fx, fy = -dy / length, dx / length
    return fx, fy


def point_on_torso(hip, shoulder, t, side):
    fx, fy = spine_frame(hip, shoulder)
    x = hip[0] + (shoulder[0] - hip[0]) * t + fx * side
    y = hip[1] + (shoulder[1] - hip[1]) * t + fy * side
    return (x, y)


def draw_torso(im, hip, shoulder):
    # t = 0 at the hip, t = 1 at the shoulder. +side faces right when upright.
    keys = [
        (1.00, 3.2, -3.6),
        (0.72, 4.0, -3.6),
        (0.42, 2.6, -3.2),
        (0.12, 4.2, -4.2),
        (0.00, 3.4, -4.0),
    ]
    front = [point_on_torso(hip, shoulder, t, f) for t, f, _b in keys]
    back = [point_on_torso(hip, shoulder, t, b) for t, _f, b in reversed(keys)]
    poly = front + back
    fill_poly(im, poly, SHIRT_D)
    # Shift the fill up along the spine so the back and hem stay in shadow.
    fx, fy = spine_frame(hip, shoulder)
    lifted = [(x + fx * 0.6 - fy * 0.8, y + fy * 0.6 + fx * 0.8) for x, y in poly]
    fill_poly(im, lifted, SHIRT)
    # Neck.
    n0 = point_on_torso(hip, shoulder, 1.0, 1.2)
    n1 = point_on_torso(hip, shoulder, 1.0, -1.4)
    head_anchor = add(shoulder, ang_vec(0, 0))
    neck_top_f = add(shoulder, (-fy * -3.2 + fx * 1.4, fx * -3.2 + fy * 1.4))
    # Simple neck quad toward the head.
    up = (-fy, fx)  # points up the spine? fx,fy is forward. Up the spine is shoulder-hip.
    ux = (shoulder[0] - hip[0])
    uy = (shoulder[1] - hip[1])
    ul = math.hypot(ux, uy) or 1
    ux, uy = ux / ul * 3.2, uy / ul * 3.2
    neck = [
        add(n1, (0, 0)),
        add(n0, (0, 0)),
        add(n0, (ux, uy)),
        add(n1, (ux, uy)),
    ]
    fill_poly(im, neck, SKIN)
    return add(shoulder, (ux, uy))


def draw_shorts(im, hip, shoulder):
    keys = [(0.22, 4.4, -4.6), (0.0, 4.6, -4.8), (-0.08, 3.2, -3.4)]
    front = [point_on_torso(hip, shoulder, t, f) for t, f, _b in keys]
    back = [point_on_torso(hip, shoulder, t, b) for t, _f, b in reversed(keys)]
    fill_poly(im, front + back, SHORTS)
    waist = [
        point_on_torso(hip, shoulder, 0.22, 4.4),
        point_on_torso(hip, shoulder, 0.22, -4.6),
        point_on_torso(hip, shoulder, 0.12, -4.4),
        point_on_torso(hip, shoulder, 0.12, 4.2),
    ]
    fill_poly(im, waist, SHORTS_D)


def draw_leg(im, hip, thigh_deg, knee_bend, front, rot, pivot):
    put, disc, capsule = to_game(im)
    knee = add(hip, ang_vec(thigh_deg, THIGH))
    shin_deg = thigh_deg - knee_bend
    ankle = add(knee, ang_vec(shin_deg, SHIN))

    def X(p):
        return rot_pt(p, rot, pivot)

    skin = SKIN if front else SKIN_D
    shorts = SHORTS if front else SHORTS_D
    capsule(X(hip), X(knee), 2.05 if front else 1.9, skin)
    capsule(X(knee), X(ankle), 1.85 if front else 1.75, skin)
    capsule(X(hip), X(knee), 2.05 if front else 1.9, shorts, 0.0, 0.42)
    draw_shoe(put, ankle, shin_deg, rot, pivot)
    return [X(p) for p in shoe_soles(ankle, shin_deg)]


def shoe_soles(ankle, shin_deg):
    ang = max(-40, min(55, shin_deg * 0.35))
    soles = []
    for lx, ly in ((1, 3), (7, 3)):
        soles.append(rot_pt(add(ankle, (lx, ly)), ang, ankle))
    return soles


def draw_shoe(put, ankle, shin_deg, rot, pivot):
    ang = max(-40, min(55, shin_deg * 0.35))
    for lx in range(-1, 9):
        for ly in range(0, 4):
            if ly == 0 and (lx < 1 or lx > 6):
                continue
            if lx >= 8 and ly < 2:
                continue
            local = rot_pt(add(ankle, (lx, ly)), ang, ankle)
            world = rot_pt(local, rot, pivot)
            if ly >= 3:
                col = SOLE
            elif lx >= 6 or ly == 2:
                col = SHOE_D
            else:
                col = SHOE
            put(world[0], world[1], col)
    for lx, ly in ((3, 1), (4, 1)):
        local = rot_pt(add(ankle, (lx, ly)), ang, ankle)
        world = rot_pt(local, rot, pivot)
        put(world[0], world[1], SOLE)


def draw_arm(im, shoulder, upper_deg, fore_deg, front, rot, pivot):
    _put, _disc, capsule = to_game(im)
    elbow = add(shoulder, ang_vec(upper_deg, UPPER))
    hand = add(elbow, ang_vec(fore_deg, FORE))

    def X(p):
        return rot_pt(p, rot, pivot)

    skin = SKIN if front else SKIN_D
    capsule(X(shoulder), X(elbow), 1.65, skin)
    capsule(X(elbow), X(hand), 1.5, skin)
    stamp_disc(im, X(hand)[0] + PAD, X(hand)[1] + PAD, 1.7, SKIN_L if front else skin)


def head_feature_pixels(expr):
    """Pixels relative to the neck anchor. +x faces right, +y is down."""
    pix = []

    def blob(cx, cy, rx, ry, col):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    pix.append((x, y, col))

    # High puff behind the crown, with a couple of coils.
    blob(-6, -13, 7, 5, HAIR)
    blob(-11, -10, 4, 4, HAIR)
    blob(-3, -16, 4, 3, HAIR)
    blob(-12, -6, 3, 3, HAIR)
    blob(-4, -15, 2, 2, HAIR_L)

    # Skull in profile.
    profile = [
        (-5, -2),
        (-6, -6),
        (-5, -10),
        (-2, -12),
        (2, -12),
        (4, -9),
        (4, -6),
        (7, -5),
        (4, -3),
        (5, -2),
        (3, 0),
        (0, 1),
        (-4, 1),
        (-5, -1),
    ]
    # Filled later as a polygon; features are stamped after.
    pix.append(("POLY", profile))

    # Bangs. Kept off the eye.
    for x, y in (
        (-3, -12), (-2, -12), (-1, -12), (0, -12), (1, -12), (2, -12), (3, -11),
        (-2, -11), (-1, -11), (0, -11), (1, -11),
        (3, -10),
    ):
        pix.append((x, y, HAIR))

    # Ear and hoop on the visible side of the skull.
    for x, y in ((-2, -6), (-1, -6), (-2, -5), (-1, -5), (-3, -5)):
        pix.append((x, y, SKIN_D))
    pix.append((-2, -6, SKIN_L))
    for x, y in ((-3, -3), (-2, -2), (-3, -1), (-4, -2)):
        pix.append((x, y, HOOP))

    eye = (2, -8)
    if expr == "blink" or expr == "dead":
        for x in range(3):
            pix.append((eye[0] + x, eye[1], PUPIL))
    elif expr == "hurt":
        pix.append((eye[0], eye[1], EYE_W))
        pix.append((eye[0] + 1, eye[1], EYE_W))
        pix.append((eye[0] + 2, eye[1], PUPIL))
        pix.append((eye[0] + 1, eye[1] - 1, PUPIL))
        pix.append((eye[0] + 1, eye[1] + 1, LIP))
    else:
        pix.append((eye[0], eye[1], EYE_W))
        pix.append((eye[0] + 1, eye[1], PUPIL))
        pix.append((eye[0] + 2, eye[1], PUPIL))
        pix.append((eye[0], eye[1] - 1, PUPIL))  # lash
        if expr != "focus":
            pix.append((eye[0] + 1, eye[1] - 1, EYE_W))

    brow_y = eye[1] - 2 if expr != "hurt" else eye[1] - 3
    for x in range(3):
        pix.append((eye[0] + x, brow_y, HAIR))

    # Nose, nostril, lips.
    pix.append((7, -5, SKIN_L))
    pix.append((6, -4, SKIN_D))
    if expr == "hurt":
        pix.append((4, -2, LIP))
        pix.append((5, -2, (48, 22, 24, 255)))
        pix.append((4, -1, LIP))
    elif expr == "dead":
        pix.append((4, -2, SKIN_D))
        pix.append((5, -2, SKIN_D))
    else:
        pix.append((4, -2, LIP))
        pix.append((5, -2, LIP))
    return pix


def draw_head(im, anchor, expr, rot):
    """Anchor is already in world space. Offsets rotate around the anchor."""
    put, disc, _capsule = to_game(im)
    ax, ay = anchor

    def place(lx, ly):
        ox, oy = rot_pt((lx, ly), rot, (0, 0))
        return (ax + ox, ay + oy)

    features = head_feature_pixels(expr)
    poly = None
    discs = []
    for item in features:
        if isinstance(item, tuple) and item and item[0] == "POLY":
            poly = item[1]
            break
    if poly:
        # Shadow pass, then a one-pixel up-right base so the jaw stays darker.
        fill_poly(im, [place(x, y) for x, y in poly], SKIN_D)
        fill_poly(im, [place(x + 1, y - 1) for x, y in poly], SKIN)
    for item in features:
        if isinstance(item, tuple) and item and item[0] == "POLY":
            continue
        x, y, col = item
        # Hair highlights were baked into the puff; hair_dx shifts the whole head
        # a pixel so the puff lags. Feature pixels use the same shift.
        p = place(x, y)
        put(p[0], p[1], col)


def compute_joints(spec, hip_lock):
    lean = spec.get("lean", 0)
    if hip_lock is not None:
        hip = (hip_lock[0] + spec.get("hx", 0), hip_lock[1] + spec.get("bob", 0))
    else:
        hip = (32 + spec.get("hx", 0), 36 + spec.get("bob", 0))
    shoulder = (hip[0] - 1 + lean * 0.12, hip[1] - 12)
    return hip, shoulder


def render_spec(spec, hip_lock):
    hip, shoulder = compute_joints(spec, hip_lock)
    rot = spec.get("rot", 0)
    # Parts are separate so each gets its own outline, then composited back to front.
    layers = []

    def new_layer():
        im = canvas()
        layers.append(im)
        return im

    # Back arm, both legs, torso, shorts, front arm, head.
    back_arm = new_layer()
    back_leg = new_layer()
    front_leg = new_layer()
    body = new_layer()
    front_arm = new_layer()
    head = new_layer()

    # Decide which spec limb is visually in front from the upright ankle x.
    f_ankle_x = add(hip, ang_vec(spec["f_thigh"], THIGH))[0]
    f_shin = spec["f_thigh"] - spec["f_knee"]
    f_ankle_x += ang_vec(f_shin, SHIN)[0]
    b_ankle_x = add((hip[0] - 1, hip[1]), ang_vec(spec["b_thigh"], THIGH))[0]
    b_shin = spec["b_thigh"] - spec["b_knee"]
    b_ankle_x += ang_vec(b_shin, SHIN)[0]
    f_in_front = f_ankle_x >= b_ankle_x

    if f_in_front:
        soles = draw_leg(back_leg, (hip[0] - 1, hip[1]), spec["b_thigh"], spec["b_knee"], False, rot, hip)
        soles += draw_leg(front_leg, hip, spec["f_thigh"], spec["f_knee"], True, rot, hip)
    else:
        soles = draw_leg(back_leg, hip, spec["f_thigh"], spec["f_knee"], False, rot, hip)
        soles += draw_leg(front_leg, (hip[0] - 1, hip[1]), spec["b_thigh"], spec["b_knee"], True, rot, hip)

    f_hand_x = add(shoulder, ang_vec(spec["f_upper"], UPPER))[0]
    b_hand_x = add(shoulder, ang_vec(spec["b_upper"], UPPER))[0]
    if f_hand_x >= b_hand_x:
        draw_arm(back_arm, add(shoulder, (-1, 1)), spec["b_upper"], spec["b_fore"], False, rot, hip)
        draw_arm(front_arm, add(shoulder, (2, 1)), spec["f_upper"], spec["f_fore"], True, rot, hip)
    else:
        draw_arm(back_arm, add(shoulder, (2, 1)), spec["f_upper"], spec["f_fore"], False, rot, hip)
        draw_arm(front_arm, add(shoulder, (-1, 1)), spec["b_upper"], spec["b_fore"], True, rot, hip)

    def X(p):
        return rot_pt(p, rot, hip)

    # The layer allocated above was a placeholder; draw the posed body into it.
    layers[3] = canvas()
    body = layers[3]
    draw_torso(body, X(hip), X(shoulder))
    draw_shorts(body, X(hip), X(shoulder))
    ux = shoulder[0] - hip[0]
    uy = shoulder[1] - hip[1]
    ul = math.hypot(ux, uy) or 1
    anchor = add(shoulder, (ux / ul * 3.0, uy / ul * 3.0))
    anchor = add(anchor, (spec.get("head_dx", 0) + spec.get("hair_dx", 0), spec.get("head_dy", 0) + spec.get("hair_dy", 0)))
    draw_head(head, X(anchor), spec.get("expr", "neutral"), rot)

    for layer in layers:
        outline(layer)

    # Hoop and face were outlined with the head, which is what we want.
    out = canvas()
    for layer in layers:
        out.alpha_composite(layer)

    if spec.get("settle"):
        bbox = out.getbbox()
        if bbox:
            l, t, r, b = bbox
            dx = int(round((PAD + 32) - (l + r) / 2))
            dy = int(round((PAD + BASE_SOLE) - (b - 1)))
            out = shift_canvas(out, dx, dy)
    elif spec.get("grounded", True):
        if soles:
            lowest = max(p[1] for p in soles)
            dy = int(round(BASE_SOLE - lowest))
            hip_x = X(hip)[0]
            dx = int(round(32 - hip_x))
            out = shift_canvas(out, dx, dy)
    else:
        hip_x = X(hip)[0]
        dx = int(round(32 - hip_x))
        out = shift_canvas(out, dx, 0)
    return crop_cell(out)


def mirror_limbs(spec):
    swapped = dict(spec)
    for a, b in (
        ("f_thigh", "b_thigh"),
        ("f_knee", "b_knee"),
        ("f_upper", "b_upper"),
        ("f_fore", "b_fore"),
    ):
        swapped[a], swapped[b] = spec[b], spec[a]
    swapped["hair_dx"] = -spec.get("hair_dx", 0)
    return swapped


# 0 degrees points down. Positive swings forward, to the right.
IDLE = [
    dict(lean=2, f_thigh=4, f_knee=6, b_thigh=-3, b_knee=6, f_upper=18, f_fore=72, b_upper=8, b_fore=36, expr="neutral", grounded=True),
    dict(lean=1, f_thigh=6, f_knee=2, b_thigh=-2, b_knee=2, f_upper=24, f_fore=84, b_upper=12, b_fore=48, hair_dx=1, hair_dy=-1, expr="neutral", grounded=True),
    dict(lean=2, f_thigh=5, f_knee=12, b_thigh=-4, b_knee=12, f_upper=14, f_fore=64, b_upper=4, b_fore=28, expr="blink", grounded=True),
    dict(lean=2, f_thigh=4, f_knee=8, b_thigh=-5, b_knee=8, f_upper=28, f_fore=90, b_upper=14, b_fore=52, hair_dx=-1, expr="neutral", grounded=True),
]

RUN_HALF = [
    dict(lean=14, f_thigh=42, f_knee=10, b_thigh=-48, b_knee=16, f_upper=-58, f_fore=-12, b_upper=36, b_fore=100, hair_dx=-2, expr="focus", grounded=True),
    dict(lean=16, f_thigh=18, f_knee=48, b_thigh=-8, b_knee=62, f_upper=-16, f_fore=18, b_upper=6, b_fore=48, hair_dx=-1, expr="focus", grounded=True),
    dict(lean=10, f_thigh=58, f_knee=92, b_thigh=-28, b_knee=30, f_upper=22, f_fore=70, b_upper=-36, b_fore=-8, hair_dx=1, hair_dy=-1, expr="focus", grounded=True),
]
RUN = RUN_HALF + [mirror_limbs(s) for s in RUN_HALF]

JUMP = [
    dict(lean=18, f_thigh=24, f_knee=62, b_thigh=-6, b_knee=54, f_upper=-48, f_fore=-8, b_upper=-24, b_fore=10, hair_dx=-1, expr="focus", grounded=True),
    dict(lean=-4, bob=-2, f_thigh=62, f_knee=88, b_thigh=28, b_knee=96, f_upper=122, f_fore=108, b_upper=-150, b_fore=-168, hair_dx=0, hair_dy=-1, expr="focus", grounded=False),
    dict(lean=8, f_thigh=16, f_knee=14, b_thigh=-30, b_knee=20, f_upper=128, f_fore=112, b_upper=-142, b_fore=-160, hair_dx=-1, expr="focus", grounded=False),
    dict(lean=16, f_thigh=26, f_knee=66, b_thigh=-2, b_knee=58, f_upper=20, f_fore=48, b_upper=-36, b_fore=-6, hair_dx=0, hair_dy=1, expr="focus", grounded=True),
]

DIE = [
    dict(lean=-16, f_thigh=10, f_knee=8, b_thigh=-18, b_knee=14, f_upper=-28, f_fore=8, b_upper=-55, b_fore=-18, hair_dx=1, expr="hurt", grounded=True),
    dict(lean=-8, rot=-22, f_thigh=16, f_knee=18, b_thigh=-6, b_knee=12, f_upper=-48, f_fore=-8, b_upper=-78, b_fore=-36, hair_dx=1, expr="hurt", grounded=True),
    dict(rot=-50, f_thigh=12, f_knee=14, b_thigh=-10, b_knee=12, f_upper=-16, f_fore=24, b_upper=8, b_fore=36, expr="hurt", settle=True, grounded=False),
    dict(rot=-72, f_thigh=18, f_knee=22, b_thigh=-6, b_knee=16, f_upper=6, f_fore=28, b_upper=-12, b_fore=8, expr="dead", settle=True, grounded=False),
    dict(rot=-90, f_thigh=34, f_knee=58, b_thigh=10, b_knee=36, f_upper=18, f_fore=34, b_upper=-8, b_fore=10, expr="dead", settle=True, grounded=False),
    dict(rot=-90, f_thigh=22, f_knee=30, b_thigh=4, b_knee=18, f_upper=8, f_fore=16, b_upper=-4, b_fore=6, expr="dead", settle=True, grounded=False),
]


def render_row(poses, hip_lock, air_lock):
    frames = []
    for spec in poses:
        lock = air_lock if (not spec.get("grounded", True) and not spec.get("settle")) else hip_lock
        if spec.get("grounded", True) and not spec.get("settle"):
            lock = None
        frames.append(render_spec(spec, lock if not spec.get("grounded", True) else None))
    return frames


def main():
    # Standing hip, used so airborne frames stay on the same vertical line.
    probe = render_spec(IDLE[0], None)
    # Recover hip from a dedicated joint computation after foot clamp by
    # re-simulating: render_spec clamps feet, so measure the idle hip by
    # computing joints then applying the same sole delta.
    hip, _shoulder = compute_joints(IDLE[0], None)
    from_soles = []
    knee = add(hip, ang_vec(IDLE[0]["f_thigh"], THIGH))
    ankle = add(knee, ang_vec(IDLE[0]["f_thigh"] - IDLE[0]["f_knee"], SHIN))
    from_soles += shoe_soles(ankle, IDLE[0]["f_thigh"] - IDLE[0]["f_knee"])
    knee = add(hip, ang_vec(IDLE[0]["b_thigh"], THIGH))
    ankle = add(knee, ang_vec(IDLE[0]["b_thigh"] - IDLE[0]["b_knee"], SHIN))
    from_soles += shoe_soles(ankle, IDLE[0]["b_thigh"] - IDLE[0]["b_knee"])
    dy = BASE_SOLE - max(p[1] for p in from_soles)
    hip_lock = (hip[0], hip[1] + dy)

    idle = [render_spec(s, None) for s in IDLE]
    run = [render_spec(s, None) for s in RUN]
    jump = []
    for s in JUMP:
        jump.append(render_spec(s, None if s.get("grounded", True) else hip_lock))
    die = [render_spec(s, None if s.get("grounded", True) else hip_lock) for s in DIE]

    sheet = Image.new("RGBA", (COLS * FW, ROWS * FH), (0, 0, 0, 0))
    for r, frames in enumerate((idle, run, jump, die)):
        for c, frame in enumerate(frames):
            sheet.alpha_composite(frame, dest=(c * FW, r * FH))
            box = frame.getbbox()
            clipped = box and (box[0] <= 0 or box[1] <= 0 or box[2] >= FW or box[3] >= FH)
            print(f"r{r}c{c} bbox={box} clipped={clipped}")

    out = "Assets/Art/Player/PlayerSpritesheet.png"
    sheet.save(out)
    print(f"wrote {out} {sheet.size}")
    # Silence unused probe image.
    probe.close()


if __name__ == "__main__":
    main()
