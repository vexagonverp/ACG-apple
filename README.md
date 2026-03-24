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

## Project structure

```
.
├── mesh/
│   ├── apple.obj          # input mesh
│   ├── apple.mtl          # material definitions
│   └── apple.mtl.bak      # original material backup
├── .out/                  # generated outputs (gitignored)
├── demo.py                # main demo script
├── requirements.txt       # Python dependencies
└── README.md
```

## Requirements

- Python 3.10+
- pymeshlab (installed via `requirements.txt`)
- pyvista (installed via `requirements.txt`)
