import argparse
import os

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description="Align point cloud to spine mesh")

    arg_parser.add_argument(
        "--list_file_names",
        required=True,
        dest="txt_file",
        help="Txt file that contains all spines that contain all lumbar vertebrae"
    )
    arg_parser.add_argument(
        "--workspace_file",
        required=True,
        dest="workspace_file",
        help="ImFusion workspace file that applies ICP to the mesh and the pointcloud"
    )
    arg_parser.add_argument(
        "--root_path_spines",
        required=True,
        dest="root_path_spines",
        help="Root path to the spine folders."
    )
    arg_parser.add_argument(
        "--nr_deform_per_spine",
        required=True,
        dest="nr_deform_per_spine",
        help="Number of deformations per spine"
    )

    args = arg_parser.parse_args()
    print("Align point cloud to spine mesh")

    # iterate over the txt file
    with open(args.txt_file) as file:
        spine_ids = [line.strip() for line in file]

    placeholders = ['MeshPath', 'PCDPath', 'PathToSavePcd']

    for spine_id in spine_ids:
        for deform in range(int(args.nr_deform_per_spine)):
            print("Aligning the point cloud and the mesh of: " + str(spine_id) + "and deformation " + str(deform))
            arguments = ""

            pcd_path = os.path.join(args.root_path_spines, spine_id, spine_id + "_partial_spine_pcd_force" + str(deform) + ".pcd")

            for p in placeholders:
                if p == 'MeshPath':
                    value = os.path.join(args.root_path_spines, spine_id, spine_id + "forcefield" + str(deform) + "_lumbar_deformed_centered.obj")
                elif p == 'PCDPath':
                    value = pcd_path
                elif p == 'PathToSavePcd':
                    value = pcd_path.replace(".pcd","_aligned.pcd")

                arguments += p + "=" + str(value) + " "

            print('ARGUMENTS: ', arguments)
            os.system("ImFusionConsole" + " " + args.workspace_file + " " + arguments)
            print('################################################### ')