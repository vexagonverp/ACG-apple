import math
import sys
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import glutInit

WIDTH, HEIGHT = 800, 400
GROUND_Y = 300
CAR_SPEED = 2.0
WHEEL_R = 25


def draw_rect(x, y, w, h):
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y);       glVertex2f(x + w, y)
    glVertex2f(x + w, y + h); glVertex2f(x, y + h)
    glEnd()


def draw_circle(cx, cy, r, segs=36):
    glBegin(GL_LINE_LOOP)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
    glEnd()


def draw_wheel(cx, cy, r, angle):
    draw_circle(cx, cy, r)
    for i in range(4):
        a = angle + math.pi / 2 * i
        glBegin(GL_LINES)
        glVertex2f(cx, cy)
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
        glEnd()


def draw_car(x, wa):
    body_y = GROUND_Y - WHEEL_R - 40
    # body
    draw_rect(x, body_y, 180, 40)
    # cabin
    draw_rect(x + 40, body_y - 30, 100, 30)
    # wheels
    wy = GROUND_Y - WHEEL_R
    draw_wheel(x + 40, wy, WHEEL_R, wa)
    draw_wheel(x + 140, wy, WHEEL_R, wa)


def main():
    pygame.init()
    glutInit()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Animated Car")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(1, 1, 1, 1)

    clock = pygame.time.Clock()
    running = True
    car_x = -200.0
    wheel_angle = 0.0

    while running:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False
            elif ev.type == KEYDOWN and ev.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False

        car_x += CAR_SPEED
        if car_x > WIDTH + 20:
            car_x = -200.0
        wheel_angle -= CAR_SPEED / WHEEL_R

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glColor3f(0, 0, 0)

        # ground line
        glBegin(GL_LINES)
        glVertex2f(0, GROUND_Y); glVertex2f(WIDTH, GROUND_Y)
        glEnd()

        draw_car(car_x, wheel_angle)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
