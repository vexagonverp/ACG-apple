import math
import sys
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import glutInit, glutBitmapCharacter, GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_HELVETICA_12

# ── constants ────────────────────────────────────────────────────────
WIDTH, HEIGHT = 800, 600
CX, CY = WIDTH // 2, HEIGHT // 2       # centre of the coordinate axes

NONE, TRANSLATION, ROTATION, SCALING, SHEARING, REFLECTION = range(6)
MODE_NAMES = ["None", "Translation", "Rotation", "Scaling", "Shearing", "Reflection"]

# ── state ────────────────────────────────────────────────────────────
mode = NONE
# Shape stored as list of (x, y) vertices (relative to CX,CY)
shape_pts = [(-50, -50), (50, -50), (50, 50), (-50, 50)]
press_pt = None
reflect_axis = 0  # 0 = x-reflection, 1 = y-reflection


# ── helpers ──────────────────────────────────────────────────────────
def draw_text_gl(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def apply_transform(pts, dx, dy):
    """Return a new list of transformed points based on current mode and mouse delta."""
    if mode == TRANSLATION:
        return [(px + dx, py + dy) for px, py in pts]

    if mode == ROTATION:
        # angle between press vector and current vector (relative to origin)
        a1 = math.atan2(press_pt[1] - CY, press_pt[0] - CX)
        a2 = math.atan2((press_pt[1] + dy) - CY, (press_pt[0] + dx) - CX)
        angle = a2 - a1
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        return [(px * cos_a - py * sin_a, px * sin_a + py * cos_a) for px, py in pts]

    if mode == SCALING:
        if press_pt[0] == CX or press_pt[1] == CY:
            return pts
        sx = abs((press_pt[0] + dx - CX) / (press_pt[0] - CX))
        sy = abs((press_pt[1] + dy - CY) / (press_pt[1] - CY))
        return [(px * sx, py * sy) for px, py in pts]

    if mode == SHEARING:
        if press_pt[0] == CX or press_pt[1] == CY:
            return pts
        shx = ((press_pt[0] + dx - CX) / (press_pt[0] - CX)) - 1
        shy = ((press_pt[1] + dy - CY) / (press_pt[1] - CY)) - 1
        return [(px + shx * py, py + shy * px) for px, py in pts]

    if mode == REFLECTION:
        if reflect_axis == 0:  # reflect across x-axis
            return [(px, -py) for px, py in pts]
        else:                  # reflect across y-axis
            return [(-px, py) for px, py in pts]

    return pts


def draw_axes():
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_LINES)
    glVertex2f(CX - 250, CY); glVertex2f(CX + 250, CY)
    glVertex2f(CX, CY - 250); glVertex2f(CX, CY + 250)
    glEnd()


def draw_polygon(pts, ox=0, oy=0, color=(0, 0, 0)):
    glColor3f(*color)
    glBegin(GL_LINE_LOOP)
    for px, py in pts:
        glVertex2f(ox + px, oy + py)
    glEnd()


def draw_hud():
    glColor3f(0.2, 0.2, 0.8)
    draw_text_gl(10, 20, f"Transform: {MODE_NAMES[mode]}")
    glColor3f(0.4, 0.4, 0.4)
    draw_text_gl(10, HEIGHT - 10,
                 "T=Translate R=Rotate S=Scale H=Shear F=Reflect Z=Reset Q=Quit",
                 GLUT_BITMAP_HELVETICA_12)


# ── main ─────────────────────────────────────────────────────────────
def main():
    global mode, shape_pts, press_pt, reflect_axis

    pygame.init()
    glutInit()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Affine Transforms – PyOpenGL")

    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glClearColor(1, 1, 1, 1)

    clock = pygame.time.Clock()
    running = True
    temp_pts = None

    while running:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False

            elif ev.type == KEYDOWN:
                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif ev.key == pygame.K_t:
                    mode = TRANSLATION
                elif ev.key == pygame.K_r:
                    mode = ROTATION
                elif ev.key == pygame.K_s:
                    mode = SCALING
                elif ev.key == pygame.K_h:
                    mode = SHEARING
                elif ev.key == pygame.K_f:
                    mode = REFLECTION
                    # apply reflection immediately
                    shape_pts = apply_transform(shape_pts, 0, 0)
                    reflect_axis = 1 - reflect_axis  # toggle for next press
                elif ev.key == pygame.K_z:
                    shape_pts = [(-50, -50), (50, -50), (50, 50), (-50, 50)]

            elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                press_pt = ev.pos
                temp_pts = None

            elif ev.type == MOUSEBUTTONUP and ev.button == 1:
                if press_pt and mode not in (NONE, REFLECTION):
                    mx, my = ev.pos
                    shape_pts = apply_transform(shape_pts, mx - press_pt[0], my - press_pt[1])
                press_pt = None
                temp_pts = None

            elif ev.type == MOUSEMOTION:
                if press_pt and mode not in (NONE, REFLECTION):
                    mx, my = ev.pos
                    temp_pts = apply_transform(shape_pts, mx - press_pt[0], my - press_pt[1])

        # ── draw ─────────────────────────────────────────────────
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        draw_axes()

        if temp_pts:
            draw_polygon(shape_pts, CX, CY, color=(0.7, 0.7, 0.7))
            draw_polygon(temp_pts, CX, CY, color=(0.0, 0.0, 0.0))
        else:
            draw_polygon(shape_pts, CX, CY)

        draw_hud()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
