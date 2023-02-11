import os
import argparse
import glob

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Get a list of all vertebra ids from a folder which contains at least one pointcloud file")

    arg_parser.add_argument(
        "--root_path_vertebrae",
        required=True,
        dest="root_path_vertebrae",
        help="Root path to the vertebrae folders."
    )
    arg_parser.add_argument(
        "--list_file_names",
        required=True,
        dest="txt_file",
        help="Txt file where the file names will be saved"
    )
    arg_parser.add_argument(
        "--list_file_names_spines",
        required=True,
        dest="txt_file_spines",
        help="Txt file that contains all spines that contain all lumbar spines"
    )
    arg_parser.add_argument(
        "--nr_deform_per_spine",
        required=True,
        dest="nr_deform_per_spine",
        help="Number of deformations per spine"
    )

    args = arg_parser.parse_args()

    if(not os.path.exists(os.path.dirname(args.txt_file,))):
        os.makedirs(os.path.dirname(args.txt_file,))

    vertebrae_file = open(args.txt_file, "w")

    # iterate over the txt file
    with open(args.txt_file_spines) as file:
        spine_ids = [line.strip() for line in file]

    for spine in spine_ids:
        for verLev in range(20,25):
            pcds = False
            unique_identifier_pcds = "*/**" + spine + "*verLev" + str(verLev) + "*deformed_centered*" + "*.pcd"
            files = glob.glob(os.path.join(args.root_path_vertebrae, unique_identifier_pcds))
            spine_id_and_verLev =  spine + "_verLev" + str(verLev)
            if(len(files) == int(args.nr_deform_per_spine)):
                pcds = True
            else:
                print("Vertebra " + str(spine_id_and_verLev) + " has" + str(len(files)) + " pointclouds when they should be " + str(args.nr_deform_per_spine))

            meshes = False
            unique_identifier_meshes ="*/**" + spine +  "*verLev" +str(verLev) + "*deformed_centered*" + ".obj"
            files = glob.glob(os.path.join(args.root_path_vertebrae, unique_identifier_meshes))
            if(len(files) == int(args.nr_deform_per_spine)):
                meshes = True
            else:
                print("Vertebra " + str(spine_id_and_verLev) + " has" + str(len(files)) + " meshes when they should be " + str(args.nr_deform_per_spine))

            if(pcds and meshes):
                print("Added spine %s vert %s" %(spine, "verLev" +str(verLev) ))
                vertebrae_file.write(spine_id_and_verLev)
                vertebrae_file.write("\n")



