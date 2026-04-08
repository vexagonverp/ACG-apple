import vtk

# Load the apple mesh
reader = vtk.vtkOBJReader()
reader.SetFileName("mesh/apple.obj")
reader.Update()

poly_data = reader.GetOutput()
print(f"Vertices : {poly_data.GetNumberOfPoints()}")
print(f"Faces    : {poly_data.GetNumberOfCells()}")
bounds = poly_data.GetBounds()
print(f"Bounds   : x[{bounds[0]:.2f}, {bounds[1]:.2f}] "
      f"y[{bounds[2]:.2f}, {bounds[3]:.2f}] z[{bounds[4]:.2f}, {bounds[5]:.2f}]")

# Compute normals for smooth shading
normals = vtk.vtkPolyDataNormals()
normals.SetInputData(poly_data)
normals.ComputePointNormalsOn()
normals.SplittingOff()
normals.Update()

# --- Build 4 viewports with different representations ---

renderer_bg = (0.15, 0.15, 0.15)
ren_window = vtk.vtkRenderWindow()
ren_window.SetSize(1200, 900)
ren_window.SetWindowName("VTK Demo - Apple Mesh")

viewports = [
    (0.0, 0.5, 0.5, 1.0),  # top-left
    (0.5, 0.5, 1.0, 1.0),  # top-right
    (0.0, 0.0, 0.5, 0.5),  # bottom-left
    (0.5, 0.0, 1.0, 0.5),  # bottom-right
]

configs: list[dict[str, object]] = [
    {"label": "Surface", "color": (0.9, 0.2, 0.2), "repr": "surface"},
    {"label": "Wireframe", "color": (0.2, 0.8, 0.9), "repr": "wireframe"},
    {"label": "Points", "color": (0.2, 0.9, 0.3), "repr": "points"},
    {"label": "Surface + Edges", "color": (0.9, 0.7, 0.2), "repr": "surface_edges"},
]

for vp, cfg in zip(viewports, configs):
    renderer = vtk.vtkRenderer()
    renderer.SetViewport(*vp)
    renderer.SetBackground(*renderer_bg)  # type: ignore[arg-type]

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*cfg["color"])  # type: ignore[arg-type]

    if cfg["repr"] == "wireframe":
        actor.GetProperty().SetRepresentationToWireframe()
        actor.GetProperty().SetLineWidth(1.5)
    elif cfg["repr"] == "points":
        actor.GetProperty().SetRepresentationToPoints()
        actor.GetProperty().SetPointSize(3)
    elif cfg["repr"] == "surface_edges":
        actor.GetProperty().EdgeVisibilityOn()
        actor.GetProperty().SetEdgeColor(0.1, 0.1, 0.1)

    renderer.AddActor(actor)

    # Add label
    text_actor = vtk.vtkTextActor()
    text_actor.SetInput(str(cfg["label"]))
    text_actor.GetTextProperty().SetFontSize(20)
    text_actor.GetTextProperty().SetColor(1.0, 1.0, 1.0)
    text_actor.SetPosition(10, 10)
    renderer.AddActor2D(text_actor)

    renderer.ResetCamera()
    ren_window.AddRenderer(renderer)

# Interactive window — press 'q' to close
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(ren_window)
interactor.Initialize()
ren_window.Render()
print("Showing VTK window — press 'q' to close")
interactor.Start()
