import os
import argparse
import glob
import sys
from pathlib import Path
import nibabel as nib
import numpy as np

def get_name_labelmap_deformed_vertebra(spine_id,verLev,deform):
    return spine_id + "_verLev" + str(verLev) + "_forces" + str(deform) + "_deformed_centered_20_0.nii.gz"

def get_vertebrae_labelmaps_deformed_centered_paths(vertebrae_dir, spine_id,deform):
    vertebrae_labelmaps = []

    # get all 5 vertebrae paths for one spine id and one deformation
    for i in range(20,25):
        curr_vert_path = os.path.join(vertebrae_dir,spine_id + "_verLev" + str(i),get_name_labelmap_deformed_vertebra(spine_id, i, deform ))
        if(not Path(curr_vert_path).is_file()):
            print("No deformed vertebra labelmap found for spine %s, vert %s and deform %d" % (spine_id, str(i), deform), file=sys.stderr)
        vertebrae_labelmaps.append(curr_vert_path)
    return vertebrae_labelmaps


def merge_labelmaps(vertebrae_labelmaps_paths):
    labelmaps = [nib.load(vertebrae_labelmaps_path) for vertebrae_labelmaps_path in vertebrae_labelmaps_paths]
    labelmap1 = labelmaps[0].get_fdata()
    labelmap2 = labelmaps[1].get_fdata()

    labelmap1_padded = np.pad(labelmap1, ((4, 4), (2, 3), (0, 0)), 'constant',
                              constant_values=((12, 12), (12, 12), (12, 12)))
    """
    # concatenate the images with numpy and padding
    concatenation_numpy = np.concatenate((labelmap1_padded, labelmap2_padded), axis=2)
    concatenated_image_from_numpy = nib.Nifti1Image(concatenation_numpy,affine=np.eye(4))
    nib.save(concatenated_image_from_numpy, "test_numpy_concat.nii.gz")
    """

    labelmap1_padded_image = nib.Nifti1Image(labelmap1_padded,affine=labelmaps[1].affine)
    nib.save(labelmap1_padded_image, "labelmap1_padded.nii.gz")


    # concatenate images with the nibabel concatenate
    firstTwo = ["labelmap1_padded.nii.gz",vertebrae_labelmaps_paths[1]]
    concatenation_nibabel = nib.funcs.concat_images(firstTwo,check_affines=True,axis=2)
    nib.save(concatenation_nibabel, "test_nibabel_concat.nii.gz")

    a = 3


    #return combined_labelmap


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Generate strings in between vertebrae for spine deformation")

    arg_parser.add_argument(
        "--list_file_names",
        required=True,
        dest="txt_file",
        help="Txt file that contains all spines that contain all lumbar spines"
    )

    arg_parser.add_argument(
        "--root_path_vertebrae",
        required=True,
        dest="root_path_vertebrae",
        help="Root path to the vertebrae folders."
    )

    arg_parser.add_argument(
        "--nr_deform_per_spine",
        required=True,
        dest="nr_deform_per_spine",
        help="Number of deformations per spine"
    )

    args = arg_parser.parse_args()

    with open(args.txt_file) as file:
        spine_ids = [line.strip() for line in file]

    for spine_id in spine_ids:
        for deform in range(int(args.nr_deform_per_spine)):
            vertebrae_labelmaps = get_vertebrae_labelmaps_deformed_centered_paths(vertebrae_dir=args.root_path_vertebrae,spine_id=spine_id, deform=deform )
            merge_labelmaps(vertebrae_labelmaps)
