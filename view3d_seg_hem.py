###############################################################################
# Performs brain hemisphere segmentation on 3D
#
#   Author:      Dr. Pamela Franco
#   Time-stamp:  2025-11-5
#   E-mail:      pamela.franco@unab.cl / pafranco@uc.cl
###############################################################################
import os
import numpy as np
import nibabel as nib
import plotly.graph_objects as go
from skimage import measure

###############################################################################
path = r"C:\Users\pfran\Desktop\DTI processing\Paciente1"
left_mask_file = os.path.join(path, "hemis_watershed_left.nii.gz")
right_mask_file = os.path.join(path, "hemis_watershed_right.nii.gz")
save_html = os.path.join(path, "hemis_3D.html")
###############################################################################
img_left = nib.load(left_mask_file)
img_right = nib.load(right_mask_file)
mask_left = img_left.get_fdata().astype(bool)
mask_right = img_right.get_fdata().astype(bool)
affine = img_left.affine

print(f"Left voxels: {mask_left.sum()}, Right voxels: {mask_right.sum()}")

vertsL, facesL, _, _ = measure.marching_cubes(mask_left, level=0.5)
vertsR, facesR, _, _ = measure.marching_cubes(mask_right, level=0.5)

vertsL_world = nib.affines.apply_affine(affine, vertsL)
vertsR_world = nib.affines.apply_affine(affine, vertsR)

mesh_left = go.Mesh3d(
    x=vertsL_world[:, 0], y=vertsL_world[:, 1], z=vertsL_world[:, 2],
    i=facesL[:, 0], j=facesL[:, 1], k=facesL[:, 2],
    color='blue', opacity=0.5, name='Left Hemisphere'
)
mesh_right = go.Mesh3d(
    x=vertsR_world[:, 0], y=vertsR_world[:, 1], z=vertsR_world[:, 2],
    i=facesR[:, 0], j=facesR[:, 1], k=facesR[:, 2],
    color='red', opacity=0.5, name='Right Hemisphere'
)

fig = go.Figure(data=[mesh_left, mesh_right])
fig.update_layout(
    scene=dict(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        zaxis=dict(visible=False),
        aspectmode='data'
    ),
    title="3D Brain Hemispheres (Watershed Segmentation)",
)

fig.show()

fig.write_html(save_html)
print(f"Figura guardada en: {save_html}")


