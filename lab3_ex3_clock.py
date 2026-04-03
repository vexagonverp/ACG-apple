import math
import sys
import time
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import glutInit, glutBitmapCharacter, GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_TIMES_ROMAN_24

WIDTH, HEIGHT = 640, 480
CX, CY = WIDTH // 2, HEIGHT // 2
RADIUS = 190


def draw_text_gl(x, y, text, font=GLUT_BITMAP_TIMES_ROMAN_24):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def draw_circle(cx, cy, r, segs=72):
    glBegin(GL_LINE_LOOP)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
    glEnd()


def fill_circle(cx, cy, r, segs=72):
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segs + 1):
        a = 2 * math.pi * i / segs
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
    glEnd()


def draw_hand(angle_deg, length, width=3.0):
    """Draw a clock hand at the given angle (0° = 12 o'clock, clockwise)."""
    a = math.radians(90 - angle_deg)  # convert to standard math angle
    ex = CX + length * math.cos(a)
    ey = CY - length * math.sin(a)    # y flipped for screen coords
    glLineWidth(width)
    glBegin(GL_LINES)
    glVertex2f(CX, CY)
    glVertex2f(ex, ey)
    glEnd()
    glLineWidth(1.0)


def draw_clock_face():
    # gradient-like clock face (two filled circles for shading effect)
    glColor3f(0.85, 0.85, 0.85)
    fill_circle(CX, CY, RADIUS)
    glColor3f(0.75, 0.75, 0.75)
    fill_circle(CX + 5, CY + 5, RADIUS - 10)
    glColor3f(0.82, 0.82, 0.82)
    fill_circle(CX, CY, RADIUS - 10)

    # border
    glColor3f(0.3, 0.3, 0.3)
    glLineWidth(3.0)
    draw_circle(CX, CY, RADIUS)
    glLineWidth(1.0)

    # numbers 1–12
    glColor3f(0.15, 0.15, 0.15)
    num_r = RADIUS - 30
    for i in range(1, 13):
        angle = math.radians(90 - i * 30)
        nx = CX + num_r * math.cos(angle)
        ny = CY - num_r * math.sin(angle)
        text = str(i)
        # crude centering: shift left ~5px per digit, down ~5px
        offset_x = -5 * len(text)
        offset_y = 5
        draw_text_gl(nx + offset_x, ny + offset_y, text)

    # label
    glColor3f(0.5, 0.5, 0.5)
    draw_text_gl(CX - 45, CY + 60, "Clock - PyOpenGL", GLUT_BITMAP_HELVETICA_18)


def main():
    pygame.init()
    glutInit()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Clock – PyOpenGL")

    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glClearColor(1, 1, 1, 1)

    clock = pygame.time.Clock()
    running = True

    while running:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False
            elif ev.type == KEYDOWN and ev.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False

        # current time
        t = time.localtime()
        hour = t.tm_hour % 12
        minute = t.tm_min
        second = t.tm_sec

        hour_angle = (hour + minute / 60.0) * 30    # 360/12 = 30° per hour
        min_angle = minute * 6                        # 360/60 = 6° per minute
        sec_angle = second * 6

        # ── draw ──
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        draw_clock_face()

        # hour hand
        glColor3f(0.0, 0.0, 0.0)
        draw_hand(hour_angle, 80, width=5.0)

        # minute hand
        glColor3f(0.0, 0.0, 0.0)
        draw_hand(min_angle, 120, width=3.0)

        # second hand
        glColor3f(0.8, 0.0, 0.0)
        draw_hand(sec_angle, 130, width=1.5)

        # centre dot
        glColor3f(0.0, 0.0, 0.0)
        fill_circle(CX, CY, 5)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
