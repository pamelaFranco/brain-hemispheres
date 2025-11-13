###############################################################################
# Performs brain hemisphere segmentation on a T1-weighted MRI by creating a 
# brain mask from tissue probability maps (c1, c2), estimating the midline, 
# and applying a 3D watershed algorithm to generate left and right hemisphere masks.
#
#   Author:      Dr. Pamela Franco
#   Time-stamp:  2025-11-5
#   E-mail:      pamela.franco@unab.cl / pafranco@uc.cl
###############################################################################
import os
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, binary_erosion, binary_closing, binary_fill_holes
from skimage import measure, morphology
from skimage.filters import sobel
from skimage.segmentation import watershed

###############################################################################
path = r"C:\Users\pfran\Desktop\DTI processing\Paciente1"
t1_name = "Ax_FSPGR_3D_N.nii"   # T1-weighted image
c1_name = "c1Ax_FSPGR_3D_N.nii" # white matter (binary mask)
c2_name = "c2Ax_FSPGR_3D_N.nii" # gray matter (binary mask)
out_prefix = os.path.join(path, "hemis_watershed")

smooth_sigma = 1.0
erosion_radius = 5
mid_margin_vox = 2
###############################################################################
img_t1 = nib.load(os.path.join(path, t1_name))
img_c1 = nib.load(os.path.join(path, c1_name))
img_c2 = nib.load(os.path.join(path, c2_name))
t1 = img_t1.get_fdata().astype(np.float32)
c1 = img_c1.get_fdata().astype(np.float32)
c2 = img_c2.get_fdata().astype(np.float32)
affine = img_t1.affine

# create mask
brain_mask = (c1 + c2) > 0.2
brain_mask = binary_closing(brain_mask, iterations=2)
brain_mask = binary_fill_holes(brain_mask)
brain_mask = morphology.remove_small_objects(brain_mask.astype(bool), 2000)

# smooth and gradient 
intracranial = t1 * brain_mask
intracranial_sm = gaussian_filter(intracranial, sigma=smooth_sigma)

gx = np.zeros_like(intracranial_sm)
gy = np.zeros_like(intracranial_sm)
gz = np.zeros_like(intracranial_sm)
for z in range(intracranial_sm.shape[2]):
    gx[:,:,z] = sobel(intracranial_sm[:,:,z])
for x in range(intracranial_sm.shape[0]):
    gy[x,:,:] = sobel(intracranial_sm[x,:,:])
for y in range(intracranial_sm.shape[1]):
    gz[:,y,:] = sobel(intracranial_sm[:,y,:])
grad = np.sqrt(gx**2 + gy**2 + gz**2) * brain_mask

# estimate midline 
mid_x = t1.shape[0] // 2  # simple midpoint (native orientation)

# seeds
seed_region = binary_erosion(brain_mask, iterations=erosion_radius)
x_coords = np.arange(brain_mask.shape[0])[:,None,None]
left_seed = seed_region & (x_coords < (mid_x - mid_margin_vox))
right_seed = seed_region & (x_coords > (mid_x + mid_margin_vox))

# watershed
markers = np.zeros_like(brain_mask, dtype=np.int32)
markers[left_seed] = 1
markers[right_seed] = 2
ws_labels = watershed(grad, markers=markers, mask=brain_mask)

left_mask = (ws_labels == 1)
right_mask = (ws_labels == 2)

#clean
left_mask = binary_fill_holes(binary_closing(left_mask, iterations=2))
right_mask = binary_fill_holes(binary_closing(right_mask, iterations=2))

# save segmentations
out_left = out_prefix + "_left.nii.gz"
out_right = out_prefix + "_right.nii.gz"
nib.save(nib.Nifti1Image(left_mask.astype(np.uint8), affine), out_left)
nib.save(nib.Nifti1Image(right_mask.astype(np.uint8), affine), out_right)
print("Save:", out_left, out_right)

# display
def show_planes(img, lmask=None, rmask=None, title=""):
    sx, sy, sz = img.shape
    midx, midy, midz = sx//2, sy//2, sz//2

    fig, axs = plt.subplots(1, 3, figsize=(15, 5))

    # axial
    axs[0].imshow(np.rot90(img[:, :, midz]), cmap='gray')
    if lmask is not None: axs[0].imshow(np.rot90(lmask[:, :, midz]), cmap='Reds', alpha=0.35)
    if rmask is not None: axs[0].imshow(np.rot90(rmask[:, :, midz]), cmap='Blues', alpha=0.35)
    axs[0].set_title('Axial'); axs[0].axis('off')

    # coronal
    axs[1].imshow(np.rot90(img[:, midy, :]), cmap='gray')
    if lmask is not None: axs[1].imshow(np.rot90(lmask[:, midy, :]), cmap='Reds', alpha=0.35)
    if rmask is not None: axs[1].imshow(np.rot90(rmask[:, midy, :]), cmap='Blues', alpha=0.35)
    axs[1].set_title('Coronal'); axs[1].axis('off')

    # saggital
    axs[2].imshow(np.rot90(img[midx, :, :]), cmap='gray')
    if lmask is not None: axs[2].imshow(np.rot90(lmask[midx, :, :]), cmap='Reds', alpha=0.35)
    if rmask is not None: axs[2].imshow(np.rot90(rmask[midx, :, :]), cmap='Blues', alpha=0.35)
    axs[2].set_title('Sagittal'); axs[2].axis('off')

    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig('hemispheres.png', format='png')
    plt.show()
    
show_planes(t1, left_mask, right_mask, "Hemispheres (aligned with T1)")
