import math
import sys
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import glutInit, glutBitmapCharacter, GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_HELVETICA_12

WIDTH, HEIGHT = 900, 650
CX, CY = WIDTH // 2, HEIGHT // 2

# -- shape constants --
SHAPE_NAMES = [
    "Rectangle", "RoundRectangle", "Ellipse", "Arc",
    "Line", "QuadCurve", "CubicCurve", "Polygon",
]
RECT, RRECT, ELLIPSE, ARC, LINE, QUAD, CUBIC, POLY = range(8)

# -- transform constants --
TNONE, TRANSLATION, ROTATION, SCALING, SHEARING, REFLECTION = range(6)
TMODE_NAMES = ["None", "Translation", "Rotation", "Scaling", "Shearing", "Reflection"]

# -- state --
draw_mode = True
current_shape = RECT
shapes: list = []       # list of (type, data) where data is raw points
click_pts: list = []
drag_pt = None
dragging = False

tmode = TNONE
press_pt = None
reflect_axis = 0


# -- drawing helpers --
def draw_text_gl(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def gl_ellipse(cx, cy, rx, ry, s=0, e=360, segs=72):
    glBegin(GL_LINE_STRIP)
    for i in range(segs + 1):
        a = math.radians(s + (e - s) * i / segs)
        glVertex2f(cx + rx * math.cos(a), cy + ry * math.sin(a))
    glEnd()


def gl_round_rect(x1, y1, x2, y2, r=15):
    if abs(x2 - x1) < 2 * r or abs(y2 - y1) < 2 * r:
        r = min(abs(x2 - x1), abs(y2 - y1)) / 2
    lx, rx_ = min(x1, x2), max(x1, x2)
    ly, hy = min(y1, y2), max(y1, y2)
    segs = 16
    glBegin(GL_LINE_STRIP)
    for acx, acy, start in [(lx + r, ly + r, 180),
                             (rx_ - r, ly + r, 270),
                             (rx_ - r, hy - r, 0),
                             (lx + r, hy - r, 90)]:
        for i in range(segs + 1):
            a = math.radians(start + 90 * i / segs)
            glVertex2f(acx + r * math.cos(a), acy + r * math.sin(a))
    glEnd()


def bezier_quad(p0, p1, p2, segs=64):
    glBegin(GL_LINE_STRIP)
    for i in range(segs + 1):
        t = i / segs; u = 1 - t
        glVertex2f(u*u*p0[0]+2*u*t*p1[0]+t*t*p2[0],
                   u*u*p0[1]+2*u*t*p1[1]+t*t*p2[1])
    glEnd()


def bezier_cubic(p0, p1, p2, p3, segs=64):
    glBegin(GL_LINE_STRIP)
    for i in range(segs + 1):
        t = i / segs; u = 1 - t
        glVertex2f(u**3*p0[0]+3*u**2*t*p1[0]+3*u*t**2*p2[0]+t**3*p3[0],
                   u**3*p0[1]+3*u**2*t*p1[1]+3*u*t**2*p2[1]+t**3*p3[1])
    glEnd()


def draw_shape(stype, data):
    glColor3f(0, 0, 0)
    if stype == RECT:
        x1, y1, x2, y2 = data
        glBegin(GL_LINE_LOOP)
        glVertex2f(x1, y1); glVertex2f(x2, y1)
        glVertex2f(x2, y2); glVertex2f(x1, y2)
        glEnd()
    elif stype == RRECT:
        gl_round_rect(*data)
    elif stype == ELLIPSE:
        x1, y1, x2, y2 = data
        gl_ellipse((x1+x2)/2, (y1+y2)/2, abs(x2-x1)/2, abs(y2-y1)/2)
    elif stype == ARC:
        x1, y1, x2, y2 = data
        gl_ellipse((x1+x2)/2, (y1+y2)/2, abs(x2-x1)/2, abs(y2-y1)/2, 0, 180)
    elif stype == LINE:
        glBegin(GL_LINES)
        glVertex2f(data[0], data[1]); glVertex2f(data[2], data[3])
        glEnd()
    elif stype == QUAD:
        bezier_quad(*data)
    elif stype == CUBIC:
        bezier_cubic(*data)
    elif stype == POLY and len(data) >= 3:
        glBegin(GL_LINE_LOOP)
        for px, py in data:
            glVertex2f(px, py)
        glEnd()


# -- transform a single point --
def transform_point(px, py, dx, dy):
    """Transform a point based on current mode and mouse delta."""
    if tmode == TRANSLATION:
        return (px + dx, py + dy)

    if tmode == ROTATION:
        a1 = math.atan2(press_pt[1] - CY, press_pt[0] - CX)
        a2 = math.atan2((press_pt[1] + dy) - CY, (press_pt[0] + dx) - CX)
        angle = a2 - a1
        c, s = math.cos(angle), math.sin(angle)
        # rotate around the canvas centre
        rx, ry = px - CX, py - CY
        return (CX + rx * c - ry * s, CY + rx * s + ry * c)

    if tmode == SCALING:
        if press_pt[0] == CX or press_pt[1] == CY:
            return (px, py)
        sx = abs((press_pt[0] + dx - CX) / (press_pt[0] - CX))
        sy = abs((press_pt[1] + dy - CY) / (press_pt[1] - CY))
        return (CX + (px - CX) * sx, CY + (py - CY) * sy)

    if tmode == SHEARING:
        if press_pt[0] == CX or press_pt[1] == CY:
            return (px, py)
        shx = ((press_pt[0] + dx - CX) / (press_pt[0] - CX)) - 1
        shy = ((press_pt[1] + dy - CY) / (press_pt[1] - CY)) - 1
        rx, ry = px - CX, py - CY
        return (CX + rx + shx * ry, CY + ry + shy * rx)

    if tmode == REFLECTION:
        if reflect_axis == 0:
            return (2 * CX - px, py)  # reflect across vertical centre
        else:
            return (px, 2 * CY - py)  # reflect across horizontal centre

    return (px, py)


def transform_shape_data(stype, data, dx, dy):
    """Apply transform to a shape's stored data, return new data."""
    if stype in (RECT, RRECT, ELLIPSE, ARC):
        x1, y1, x2, y2 = data
        nx1, ny1 = transform_point(x1, y1, dx, dy)
        nx2, ny2 = transform_point(x2, y2, dx, dy)
        return (nx1, ny1, nx2, ny2)
    elif stype == LINE:
        x1, y1, x2, y2 = data
        nx1, ny1 = transform_point(x1, y1, dx, dy)
        nx2, ny2 = transform_point(x2, y2, dx, dy)
        return (nx1, ny1, nx2, ny2)
    elif stype in (QUAD, CUBIC):
        return tuple(transform_point(px, py, dx, dy) for px, py in data)
    elif stype == POLY:
        return [transform_point(px, py, dx, dy) for px, py in data]
    return data


# -- draw preview --
def draw_preview():
    if not click_pts:
        return
    glColor3f(0.5, 0.5, 0.5)
    p0 = click_pts[0]
    ep = drag_pt or p0
    if current_shape in (RECT, RRECT, ELLIPSE, ARC, LINE) and dragging and drag_pt:
        if current_shape == RECT:
            glBegin(GL_LINE_LOOP)
            glVertex2f(p0[0], p0[1]); glVertex2f(ep[0], p0[1])
            glVertex2f(ep[0], ep[1]); glVertex2f(p0[0], ep[1])
            glEnd()
        elif current_shape == RRECT:
            gl_round_rect(p0[0], p0[1], ep[0], ep[1])
        elif current_shape == ELLIPSE:
            gl_ellipse((p0[0]+ep[0])/2, (p0[1]+ep[1])/2, abs(ep[0]-p0[0])/2, abs(ep[1]-p0[1])/2)
        elif current_shape == ARC:
            gl_ellipse((p0[0]+ep[0])/2, (p0[1]+ep[1])/2, abs(ep[0]-p0[0])/2, abs(ep[1]-p0[1])/2, 0, 180)
        elif current_shape == LINE:
            glBegin(GL_LINES); glVertex2f(p0[0], p0[1]); glVertex2f(ep[0], ep[1]); glEnd()
    elif current_shape == QUAD:
        for pt in click_pts:
            glBegin(GL_POINTS); glVertex2f(*pt); glEnd()
        if len(click_pts) == 2 and drag_pt:
            bezier_quad(click_pts[0], click_pts[1], drag_pt)
    elif current_shape == CUBIC:
        for pt in click_pts:
            glBegin(GL_POINTS); glVertex2f(*pt); glEnd()
        if len(click_pts) == 3 and drag_pt:
            bezier_cubic(click_pts[0], click_pts[1], click_pts[2], drag_pt)
    elif current_shape == POLY:
        for pt in click_pts:
            glBegin(GL_POINTS); glVertex2f(*pt); glEnd()
        if len(click_pts) >= 2:
            glBegin(GL_LINE_STRIP)
            for pt in click_pts:
                glVertex2f(*pt)
            glEnd()
        if click_pts and drag_pt:
            glBegin(GL_LINES); glVertex2f(*click_pts[-1]); glVertex2f(*drag_pt); glEnd()


def finish_shape():
    global click_pts, drag_pt
    if current_shape == QUAD and len(click_pts) >= 3:
        shapes.append((QUAD, (click_pts[0], click_pts[1], click_pts[2])))
        click_pts = []; drag_pt = None
    elif current_shape == CUBIC and len(click_pts) >= 4:
        shapes.append((CUBIC, (click_pts[0], click_pts[1], click_pts[2], click_pts[3])))
        click_pts = []; drag_pt = None
    elif current_shape == POLY and len(click_pts) >= 3:
        shapes.append((POLY, list(click_pts)))
        click_pts = []; drag_pt = None


# -- HUD --
def draw_hud():
    glColor3f(0.1, 0.5, 0.1)
    mode_label = "DRAW" if draw_mode else "TRANSFORM"
    draw_text_gl(10, 20, f"Mode: {mode_label}  [Tab to switch]")
    glColor3f(0.2, 0.2, 0.8)
    if draw_mode:
        draw_text_gl(10, 42, f"Shape: {SHAPE_NAMES[current_shape]}  [1-8]")
    else:
        draw_text_gl(10, 42, f"Transform: {TMODE_NAMES[tmode]}  [T/R/S/H/F]")
    glColor3f(0.4, 0.4, 0.4)
    info = f"Shapes: {len(shapes)}   C=Clear  Q=Quit"
    draw_text_gl(10, HEIGHT - 10, info, GLUT_BITMAP_HELVETICA_12)


# -- main --
def main():
    global draw_mode, current_shape, click_pts, drag_pt, dragging
    global tmode, press_pt, reflect_axis, shapes

    pygame.init()
    glutInit()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Combined: Choose Objects / Transforms / System")

    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glClearColor(1, 1, 1, 1)

    clock = pygame.time.Clock()
    running = True
    temp_shapes = None  # preview of transformed shapes

    while running:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False

            elif ev.type == KEYDOWN:
                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif ev.key == pygame.K_TAB:
                    draw_mode = not draw_mode
                    click_pts = []; drag_pt = None; dragging = False
                    press_pt = None; temp_shapes = None
                elif ev.key == pygame.K_c:
                    shapes.clear(); click_pts = []; drag_pt = None
                    temp_shapes = None
                elif ev.key == pygame.K_RETURN and draw_mode:
                    finish_shape()

                if draw_mode:
                    if ev.key in range(pygame.K_1, pygame.K_9):
                        idx = ev.key - pygame.K_1
                        if 0 <= idx < len(SHAPE_NAMES):
                            current_shape = idx; click_pts = []; drag_pt = None
                if not draw_mode:
                    if ev.key == pygame.K_t: tmode = TRANSLATION
                    elif ev.key == pygame.K_r: tmode = ROTATION
                    elif ev.key == pygame.K_s: tmode = SCALING
                    elif ev.key == pygame.K_h: tmode = SHEARING
                    elif ev.key == pygame.K_f:
                        tmode = REFLECTION
                        # apply reflection immediately to all shapes
                        shapes = [(st, transform_shape_data(st, d, 0, 0))
                                  for st, d in shapes]
                        reflect_axis = 1 - reflect_axis

            elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if draw_mode:
                    if current_shape in (RECT, RRECT, ELLIPSE, ARC, LINE):
                        click_pts = [(mx, my)]; dragging = True
                    elif current_shape in (QUAD, CUBIC, POLY):
                        click_pts.append((mx, my))
                else:
                    press_pt = ev.pos; temp_shapes = None

            elif ev.type == MOUSEBUTTONUP and ev.button == 1:
                mx, my = ev.pos
                if draw_mode:
                    if current_shape in (RECT, RRECT, ELLIPSE, ARC, LINE) and click_pts:
                        p0 = click_pts[0]
                        if current_shape in (RECT, RRECT, ELLIPSE, ARC):
                            shapes.append((current_shape, (p0[0], p0[1], mx, my)))
                        elif current_shape == LINE:
                            shapes.append((LINE, (p0[0], p0[1], mx, my)))
                        click_pts = []; drag_pt = None; dragging = False
                    elif current_shape == QUAD and len(click_pts) >= 3:
                        finish_shape()
                    elif current_shape == CUBIC and len(click_pts) >= 4:
                        finish_shape()
                else:
                    # apply transform permanently to all shapes
                    if press_pt and tmode not in (TNONE, REFLECTION):
                        dx, dy = mx - press_pt[0], my - press_pt[1]
                        shapes = [(st, transform_shape_data(st, d, dx, dy))
                                  for st, d in shapes]
                    press_pt = None; temp_shapes = None

            elif ev.type == MOUSEMOTION:
                if draw_mode:
                    drag_pt = ev.pos
                elif press_pt and tmode not in (TNONE, REFLECTION):
                    mx, my = ev.pos
                    dx, dy = mx - press_pt[0], my - press_pt[1]
                    temp_shapes = [(st, transform_shape_data(st, d, dx, dy))
                                   for st, d in shapes]

        # -- draw --
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # draw shapes (or their transform preview)
        if temp_shapes:
            # show originals faintly
            for stype, data in shapes:
                glColor3f(0.8, 0.8, 0.8)
                draw_shape(stype, data)
            # show transformed preview
            for stype, data in temp_shapes:
                draw_shape(stype, data)
        else:
            for stype, data in shapes:
                draw_shape(stype, data)

        if draw_mode:
            draw_preview()

        # draw axes in transform mode
        if not draw_mode:
            glColor3f(0.85, 0.85, 0.85)
            glBegin(GL_LINES)
            glVertex2f(CX - 400, CY); glVertex2f(CX + 400, CY)
            glVertex2f(CX, CY - 300); glVertex2f(CX, CY + 300)
            glEnd()

        draw_hud()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
