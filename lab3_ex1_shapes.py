import math
import sys
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import glutInit, glutBitmapCharacter, GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_HELVETICA_12

# ── constants ────────────────────────────────────────────────────────
WIDTH, HEIGHT = 800, 600
SHAPE_NAMES = [
    "Rectangle", "RoundRectangle", "Ellipse", "Arc",
    "Line", "QuadCurve", "CubicCurve", "Polygon",
]
RECT, RRECT, ELLIPSE, ARC, LINE, QUAD, CUBIC, POLY = range(8)

# ── state ────────────────────────────────────────────────────────────
current_shape = RECT
shapes: list = []          # finished shapes: (type, data)
click_pts: list = []       # points collected so far for the current shape
drag_pt = None             # current mouse position while dragging
dragging = False


# ── drawing helpers ─────────────────────────────
def draw_text_gl(x: float, y: float, text: str, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def gl_ellipse(cx, cy, rx, ry, start_deg=0, end_deg=360, segs=72):
    """Draw an elliptical arc from start_deg to end_deg."""
    glBegin(GL_LINE_STRIP)
    for i in range(segs + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / segs)
        glVertex2f(cx + rx * math.cos(a), cy + ry * math.sin(a))
    glEnd()


def gl_round_rect(x1, y1, x2, y2, r=15):
    """Rectangle with rounded corners of radius r."""
    if abs(x2 - x1) < 2 * r or abs(y2 - y1) < 2 * r:
        r = min(abs(x2 - x1), abs(y2 - y1)) / 2
    lx, rx_ = min(x1, x2), max(x1, x2)
    ly, hy = min(y1, y2), max(y1, y2)
    # four corner arcs + four sides
    segs = 16
    glBegin(GL_LINE_STRIP)
    # top-left corner (180→270)
    for i in range(segs + 1):
        a = math.radians(180 + 90 * i / segs)
        glVertex2f(lx + r + r * math.cos(a), ly + r + r * math.sin(a))
    # top-right corner (270→360)
    for i in range(segs + 1):
        a = math.radians(270 + 90 * i / segs)
        glVertex2f(rx_ - r + r * math.cos(a), ly + r + r * math.sin(a))
    # bottom-right corner (0→90)
    for i in range(segs + 1):
        a = math.radians(0 + 90 * i / segs)
        glVertex2f(rx_ - r + r * math.cos(a), hy - r + r * math.sin(a))
    # bottom-left corner (90→180)
    for i in range(segs + 1):
        a = math.radians(90 + 90 * i / segs)
        glVertex2f(lx + r + r * math.cos(a), hy - r + r * math.sin(a))
    glEnd()


def bezier_quad(p0, p1, p2, segs=64):
    """Draw a quadratic Bézier curve."""
    glBegin(GL_LINE_STRIP)
    for i in range(segs + 1):
        t = i / segs
        u = 1 - t
        x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
        y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        glVertex2f(x, y)
    glEnd()


def bezier_cubic(p0, p1, p2, p3, segs=64):
    """Draw a cubic Bézier curve."""
    glBegin(GL_LINE_STRIP)
    for i in range(segs + 1):
        t = i / segs
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        glVertex2f(x, y)
    glEnd()


# ── render one finished shape ──────────────────────────
def draw_shape(stype, data):
    glColor3f(0.0, 0.0, 0.0)
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
        gl_ellipse((x1 + x2) / 2, (y1 + y2) / 2,
                   abs(x2 - x1) / 2, abs(y2 - y1) / 2)
    elif stype == ARC:
        x1, y1, x2, y2 = data
        gl_ellipse((x1 + x2) / 2, (y1 + y2) / 2,
                   abs(x2 - x1) / 2, abs(y2 - y1) / 2,
                   start_deg=0, end_deg=180)
    elif stype == LINE:
        glBegin(GL_LINES)
        glVertex2f(data[0], data[1]); glVertex2f(data[2], data[3])
        glEnd()
    elif stype == QUAD:
        bezier_quad(data[0], data[1], data[2])
    elif stype == CUBIC:
        bezier_cubic(data[0], data[1], data[2], data[3])
    elif stype == POLY:
        if len(data) >= 3:
            glBegin(GL_LINE_LOOP)
            for px, py in data:
                glVertex2f(px, py)
            glEnd()


# ── render preview while user is still drawing ──────────
def draw_preview():
    if not click_pts:
        return
    glColor3f(0.5, 0.5, 0.5)
    p0 = click_pts[0]
    ep = drag_pt or (click_pts[-1] if len(click_pts) > 1 else p0)

    if current_shape in (RECT, RRECT, ELLIPSE, ARC, LINE):
        if dragging and drag_pt:
            if current_shape == RECT:
                glBegin(GL_LINE_LOOP)
                glVertex2f(p0[0], p0[1]); glVertex2f(ep[0], p0[1])
                glVertex2f(ep[0], ep[1]); glVertex2f(p0[0], ep[1])
                glEnd()
            elif current_shape == RRECT:
                gl_round_rect(p0[0], p0[1], ep[0], ep[1])
            elif current_shape == ELLIPSE:
                gl_ellipse((p0[0] + ep[0]) / 2, (p0[1] + ep[1]) / 2,
                           abs(ep[0] - p0[0]) / 2, abs(ep[1] - p0[1]) / 2)
            elif current_shape == ARC:
                gl_ellipse((p0[0] + ep[0]) / 2, (p0[1] + ep[1]) / 2,
                           abs(ep[0] - p0[0]) / 2, abs(ep[1] - p0[1]) / 2,
                           0, 180)
            elif current_shape == LINE:
                glBegin(GL_LINES)
                glVertex2f(p0[0], p0[1]); glVertex2f(ep[0], ep[1])
                glEnd()

    elif current_shape == QUAD:
        # show collected points and partial curve
        for pt in click_pts:
            glPointSize(5)
            glBegin(GL_POINTS); glVertex2f(pt[0], pt[1]); glEnd()
        if len(click_pts) == 2 and drag_pt:
            bezier_quad(click_pts[0], click_pts[1], drag_pt)

    elif current_shape == CUBIC:
        for pt in click_pts:
            glPointSize(5)
            glBegin(GL_POINTS); glVertex2f(pt[0], pt[1]); glEnd()
        if len(click_pts) == 3 and drag_pt:
            bezier_cubic(click_pts[0], click_pts[1], click_pts[2], drag_pt)

    elif current_shape == POLY:
        for pt in click_pts:
            glPointSize(5)
            glBegin(GL_POINTS); glVertex2f(pt[0], pt[1]); glEnd()
        if len(click_pts) >= 2:
            glBegin(GL_LINE_STRIP)
            for pt in click_pts:
                glVertex2f(pt[0], pt[1])
            glEnd()
        if click_pts and drag_pt:
            glBegin(GL_LINES)
            glVertex2f(click_pts[-1][0], click_pts[-1][1])
            glVertex2f(drag_pt[0], drag_pt[1])
            glEnd()


# ── HUD overlay ─────────────────────────────────────
def draw_hud():
    glColor3f(0.2, 0.2, 0.8)
    draw_text_gl(10, 20, f"Shape: {SHAPE_NAMES[current_shape]}  [1-8 to switch]")
    glColor3f(0.4, 0.4, 0.4)
    draw_text_gl(10, HEIGHT - 10, "C=Clear  Q/Esc=Quit  Enter=Finish poly/curve", GLUT_BITMAP_HELVETICA_12)


# ── finish current multi-click shape ──────────
def finish_shape():
    global click_pts, drag_pt
    if current_shape == QUAD and len(click_pts) >= 3:
        shapes.append((QUAD, (click_pts[0], click_pts[1], click_pts[2])))
        click_pts.clear(); drag_pt = None
    elif current_shape == CUBIC and len(click_pts) >= 4:
        shapes.append((CUBIC, (click_pts[0], click_pts[1], click_pts[2], click_pts[3])))
        click_pts.clear(); drag_pt = None
    elif current_shape == POLY and len(click_pts) >= 3:
        shapes.append((POLY, list(click_pts)))
        click_pts.clear(); drag_pt = None


# ── main ─────────────────────────────────────────────────────────────
def main():
    global current_shape, click_pts, drag_pt, dragging

    pygame.init()
    glutInit()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Program to draw all Shapes – PyOpenGL")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(1, 1, 1, 1)

    clock = pygame.time.Clock()
    running = True

    while running:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False

            elif ev.type == KEYDOWN:
                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif ev.key == pygame.K_c:
                    shapes.clear(); click_pts.clear(); drag_pt = None
                elif ev.key == pygame.K_RETURN:
                    finish_shape()
                elif ev.key in range(pygame.K_1, pygame.K_9):
                    idx = ev.key - pygame.K_1
                    if 0 <= idx < len(SHAPE_NAMES):
                        current_shape = idx
                        click_pts.clear(); drag_pt = None

            elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if current_shape in (RECT, RRECT, ELLIPSE, ARC, LINE):
                    click_pts = [(mx, my)]
                    dragging = True
                elif current_shape in (QUAD, CUBIC, POLY):
                    click_pts.append((mx, my))

            elif ev.type == MOUSEBUTTONUP and ev.button == 1:
                mx, my = ev.pos
                if current_shape in (RECT, RRECT, ELLIPSE, ARC, LINE) and click_pts:
                    p0 = click_pts[0]
                    if current_shape in (RECT, RRECT, ELLIPSE, ARC):
                        shapes.append((current_shape, (p0[0], p0[1], mx, my)))
                    elif current_shape == LINE:
                        shapes.append((LINE, (p0[0], p0[1], mx, my)))
                    click_pts.clear(); drag_pt = None; dragging = False
                elif current_shape == QUAD and len(click_pts) >= 3:
                    finish_shape()
                elif current_shape == CUBIC and len(click_pts) >= 4:
                    finish_shape()

            elif ev.type == MOUSEMOTION:
                drag_pt = ev.pos

        # ── draw ─────────────────────────────────────────────────
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        for stype, data in shapes:
            draw_shape(stype, data)

        draw_preview()
        draw_hud()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
