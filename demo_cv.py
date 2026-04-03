import cv2
import numpy as np
import pyvista as pv

# Render the apple mesh to an image using PyVista off-screen
mesh: pv.PolyData = pv.read("mesh/apple.obj")  # type: ignore[assignment]

plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
plotter.add_mesh(mesh, color="red")
plotter.camera_position = "xy"  # type: ignore[assignment]
plotter.screenshot(".out/apple_render.png")
plotter.close()

# Load the rendered image with OpenCV
img: cv2.typing.MatLike = cv2.imread(".out/apple_render.png") # type: ignore[assignment]
assert img is not None, "Failed to load .out/apple_render.png"

# --- Apply some filters side by side ---

# 1. Grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 2. Edge detection (Canny)
edges = cv2.Canny(gray, threshold1=50, threshold2=150)

# 3. Gaussian blur
blurred = cv2.GaussianBlur(img, (21, 21), sigmaX=0)

# Build a comparison grid
gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

top_row = np.hstack([img, gray_bgr])
bot_row = np.hstack([edges_bgr, blurred])
grid = np.vstack([top_row, bot_row])

# Add labels
font = cv2.FONT_HERSHEY_SIMPLEX
w, h = int(img.shape[1]), int(img.shape[0])
labels: list[tuple[str, tuple[int, int]]] = [
    ("Original", (10, 30)), ("Grayscale", (w + 10, 30)),
    ("Canny Edges", (10, h + 30)), ("Gaussian Blur", (w + 10, h + 30)),
]
for text, pos in labels:
    cv2.putText(grid, text, pos, font, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

cv2.imwrite(".out/apple_cv_grid.png", grid)
print("Saved: .out/apple_cv_grid.png")

# Show in a window — press 'q' or close the window to exit
cv2.imshow("OpenCV Demo - Apple Mesh", grid)
while cv2.getWindowProperty("OpenCV Demo - Apple Mesh", cv2.WND_PROP_VISIBLE) >= 1:
    if cv2.waitKey(100) & 0xFF == ord("q"):
        break
cv2.destroyAllWindows()
