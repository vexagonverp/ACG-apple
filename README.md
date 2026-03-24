# pymeshlab Demo — Apple Mesh

A minimal demo for getting started with [pymeshlab](https://pymeshlab.readthedocs.io/), using a Blender-exported apple mesh. Intended for shared use across the study group so everyone runs the same tooling.

## What it does

`demo.py` loads `mesh/apple.obj`, prints basic mesh stats (vertex/face count, surface area, volume, bounding box), recolors all vertices gold, and exports the result as a PLY file to `.out/`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> `requirements.txt` includes `pybind11-stubgen` for generating type stubs (see [Type stubs](#type-stubs) below).

## Run

```bash
python demo.py
```

Expected output:
```
Vertices : 169
Faces    : 330
Surface area : 328.4109
Volume       : 447.7678
Bounding box : min=[-4.735197  0.109593 -4.641729], max=[5.227317 9.945931 5.242008], diag=17.1375

Has vertex color : False
Painted gold!
Saved: .out/apple_gold.ply
```

## View the result

The script opens an interactive 3D viewer automatically after saving via pyvista.

## Type stubs

pymeshlab is a C++ extension (pybind11) and ships without type stubs. Stubs are not committed — generate them locally after setup:

```bash
python -m pybind11_stubgen pymeshlab -o typings --ignore-invalid-expressions "m\..+"
```

The `--ignore-invalid-expressions` flag suppresses harmless warnings about numpy array types that pymeshlab aliases internally as `m`.

## Project structure

```
.
├── mesh/
│   ├── apple.obj          # input mesh
│   ├── apple.mtl          # material definitions
│   └── apple.mtl.bak      # original material backup
├── typings/               # generated type stubs (gitignored, generate locally)
├── .out/                  # generated outputs (gitignored)
├── demo.py                # main demo script
├── requirements.txt       # Python dependencies
└── README.md
```

## VS Code

A `.vscode/extensions.json` is included with recommended extensions:

- **ms-python.python** — Python language support
- **ms-python.vscode-pylance** — type checking and intellisense (picks up the `typings/` stubs automatically)
- **ms-python.mypy-type-checker** — mypy integration
- **ms-python.black-formatter** — code formatting

VS Code will prompt you to install these when you open the project.

## Requirements

- Python 3.13.x (see `.python-version`)
- pymeshlab (installed via `requirements.txt`)
- pyvista (installed via `requirements.txt`)
- pybind11-stubgen (dev tool for regenerating type stubs)
