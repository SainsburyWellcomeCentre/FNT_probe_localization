"""
This example visualizes `.npy` files exported from brainglobe-segmentation
"""

from pathlib import Path
import numpy as np

from brainrender import Scene
from brainrender.actors import Points

resource_path = Path('/Users/antoniocolas/Desktop/SWC/Marcus/location/FNT099/tracks')

scene = Scene(title="Silicon Probe Visualization")

# Visualise the probe target regions
cp = scene.add_brain_region("CP", alpha=0.15)
#HY = scene.add_brain_region("HY", alpha=0.15)
RT = scene.add_brain_region("RT", alpha=0.15) 
int = scene.add_brain_region("int", alpha=0.15)



# Add probes to the scene.
# Each .npy file should contain a numpy array with the coordinates of each
# part of the probe.
scene.add(
    Points(
        np.load(resource_path / "track_0.npy"),
        name="probe_0",
        colors="darkred",
        radius=50,
    )
)
scene.add(
    Points(
        np.load(resource_path / "track_1.npy"),
        name="probe_1",
        colors="orange",
        radius=50,
    )
)

scene.add(
    Points(
        np.load(resource_path / "track_2.npy"),
        name="probe_2",
        colors="green",
        radius=50,
    )
)

scene.add(
    Points(
        np.load(resource_path / "track_3.npy"),
        name="probe_3",
        colors="blue",
        radius=50,
    )
)

# render
scene.render()