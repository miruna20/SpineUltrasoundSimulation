import argparse
import os
import glob
import sys
import nibabel as nib
import numpy as np

def transform_pixels_to_mm(i, j, k,M,abc):
   """ Return X, Y, Z coordinates for i, j, k """
   # TODO figure out why multiplying with the affine doesn't work
   """
   mult = M.dot([i, j, k])
   result = mult+abc
   return result.tolist()
   """

   return [i-abc[0],j-abc[1],k+abc[2]]
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Generate strings in between vertebrae for spine deformation")

    arg_parser.add_argument(
        "--list_file_names",
        required=True,
        dest="txt_file",
        help="Txt file that contains all spines that contain all lumbar vertebrae"
    )

    arg_parser.add_argument(
        "--root_path_spines",
        required=True,
        dest="root_path_spines",
        help="Root path to the spine folders."
    )

    arg_parser.add_argument(
        "--path_splinedata",
        required=True,
        dest="splinedata",
        help="Path to csv file that will contain contains the transducer spline and the direction spline for every labelmap."
    )
    arg_parser.add_argument(
        "--nr_deform_per_spine",
        required=True,
        dest="nr_deform_per_spine",
        help="Number of deformations per spine"
    )

    args = arg_parser.parse_args()
    print("Generating transducer splines and direction splines for each deformed spine. These are further used in the ultrasound simulation")

    # iterate over the txt file
    with open(args.txt_file) as file:
        spine_ids = [line.strip() for line in file]

    # open the csv for writing
    csv_file = open(args.splinedata,'w')
    # add the first row
    csv_file.write("Name;TransdSpline;DirSpline;\n")

    for spine_id in spine_ids:
        for deform in range(int(args.nr_deform_per_spine)):
            look_for = "**/*" + str(spine_id) + "*forcefield" + str(deform) + "*deformed*" + '*.nii.gz'
            filenames = sorted(
                glob.glob(os.path.join(args.root_path_spines, look_for), recursive=True))
            if (len(filenames) != 1):
                print("More or less than 1 spine found for " + str(spine_id),
                      file=sys.stderr)
                continue

            # open with nii gz
            vol = nib.load(filenames[0])
            data = vol.get_fdata()
            shape = data.shape
            M = (vol.affine)[:3,:3]
            transl = (vol.affine)[:3,3]

            transd_spline = []
            transd_spline_pixels = [shape[0]/2,shape[1]-2,shape[2]-2, shape[0]/2, shape[1]-2, 2]
            print("transd_spline_pixels" + str(transd_spline_pixels))
            transd_spline.extend(transform_pixels_to_mm(shape[0]/2,shape[1]-2,shape[2]-2,M,transl))
            transd_spline.extend(transform_pixels_to_mm(shape[0]/2, shape[1]-2, 2,M,transl))

            dir_spline = []
            dir_spline.extend(transform_pixels_to_mm( shape[0]/2, 0+2, shape[2]-2,M,transl))
            dir_spline.extend(transform_pixels_to_mm(shape[0]/2, 0+2, 0+2,M,transl))

            row = ""
            row += spine_id + "forcefield" + str(deform) + ";"

            for individ_coord in transd_spline:
                row += str(individ_coord) + " "
            row+= ";"

            for individ_coord in dir_spline:
                row += str(individ_coord) + " "
            row += ";\n"
            print(row)
            # save row in a csv
            csv_file.write(row)





