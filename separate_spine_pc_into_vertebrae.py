import math
import argparse
import open3d as o3d
import numpy as np
import glob
import os
import sys

# Algorithm:
# 1. Load the individual vertebrae
# 2. for each individual vertebra
    # get the bounding box
    # increase the box size slightly in x direction
    # save as pointcloud all of the points within this bounding box


def load_unmerged_centered_deformed_vertebrae(root_path_vertebrae, spine_id, deform):
    look_for = "**/*" + str(spine_id) + "*forces*" + str(deform) + "*deformed*" + "*centered*" + '*.obj'
    paths_vertebrae = sorted(glob.glob(os.path.join(root_path_vertebrae, look_for), recursive=True))

    if (len(paths_vertebrae) != 5):
        print("More or less than 5 vertebrae found for " + str(spine_id), file=sys.stderr)

    vertebrae_meshes = []
    for path_vertebra in paths_vertebrae:
        vertebrae_meshes.append(o3d.io.read_triangle_mesh(path_vertebra))

    return vertebrae_meshes, paths_vertebrae

def load_pcd(root_path_spine, spine_id, deform):
    look_for = "**/*" + str(spine_id) + "*force*" + str(deform) + "*aligned*" +  '*.pcd'
    path_pcd = glob.glob(os.path.join(root_path_spine, look_for), recursive=True)

    if (len(path_pcd) != 1):
        print("More than 1 or no pcd found for spine " + str(spine_id) + "and deformation" + str(deform),
              file=sys.stderr)

    pcd = o3d.io.read_point_cloud(path_pcd[0])

    return pcd

def separate_US_pointcloud_into_vertebrae(root_path_spine, root_path_vertebrae, spine_id, deform,visualize=False):
    print("Separating US point cloud from: " + str(spine_id) + " and deformation " + str(deform))

    #  its original unmerged, centered as a whole spine, deformed vertebrae
    vertebrae_meshes, vertebrae_paths = load_unmerged_centered_deformed_vertebrae(root_path_vertebrae, spine_id, deform)

    # load the point cloud
    spine_pcd = load_pcd(root_path_spine, spine_id, deform)

    # for each individual vertebra
    for vert_ind in range(5):

        curr_vert = vertebrae_meshes[vert_ind]

        # get the bounding box
        bounding_box_current_vert = curr_vert.get_axis_aligned_bounding_box()

        # get the corners of the bounding box
        corner_points = bounding_box_current_vert.get_box_points()

        new_corner_points = []
        for corner_point in corner_points:
            # increase the box size slightly in x direction
            if(corner_point[0] < 0):
                corner_point[0] -=20
            elif(corner_point[0] > 0):
                corner_point[0] +=20
            new_corner_points.append(corner_point)

        # create a new bounding box from the new points
        points_to_create_bb_vect = o3d.utility.Vector3dVector(np.asarray(new_corner_points))
        bounding_box_curr_vert = o3d.geometry.AxisAlignedBoundingBox.create_from_points(points_to_create_bb_vect)

        # extract points that are within the bounding box
        indices_from_vert_within_bb = o3d.geometry.AxisAlignedBoundingBox.get_point_indices_within_bounding_box(
            bounding_box_curr_vert, spine_pcd.points)
        curr_vert_points = np.asarray(spine_pcd.points)[indices_from_vert_within_bb]

        # write points belonging to the curr vert to a new point cloud
        curr_vert_pcd = o3d.geometry.PointCloud()
        curr_vert_pcd.points = o3d.utility.Vector3dVector(curr_vert_points)

        # save point cloud to the folder of the vertebra
        o3d.io.write_point_cloud(vertebrae_paths[vert_ind].replace('.obj','.pcd'), curr_vert_pcd)

        if(visualize):
            curr_vert.paint_uniform_color([1,0,0])
            o3d.visualization.draw([curr_vert,spine_pcd, bounding_box_curr_vert])


if __name__ == "__main__":

    # example setup:
    """
    root_spines = "/home/miruna20/Documents/Thesis/Dataset/VerSe2020/full_spines/subjectbased_structure/01_training"
    root_vertebrae = "/home/miruna20/Documents/Thesis/SpineDeformation/vertebrae/train"
    txt_file = "/home/miruna20/Documents/Thesis/SpineDeformation/script/SpineDeformation/results/lumbar_spines_subsample.txt"
    nr_deform = 1
    """

    arg_parser = argparse.ArgumentParser(
        description="Separate point cloud of the spine obtained through raycasting of US labelmaps into individual "
                    "vertebrae pointclouds")

    arg_parser.add_argument(
        "--list_file_names",
        required=True,
        dest="txt_file",
        help="Txt file that contains all spines ids"
    )

    arg_parser.add_argument(
        "--root_path_vertebrae",
        required=True,
        dest="root_path_vertebrae",
        help="Root path to the vertebrae folders."
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
        help="Number of deformed spines per initial spine."
    )
    arg_parser.add_argument(
        "--visualize",
        action="store_true",
        default=False,
        dest="visualize",
        help="Activate flag for visualization"
    )


    print("Separate point cloud of the spine obtained through raycasting of US labelmaps into individual "
                    "vertebrae pointclouds")

    args = arg_parser.parse_args()

    # iterate over all spines
    with open(args.txt_file) as file:
        spine_ids = [line.strip() for line in file]

    for spine_id in spine_ids:
        for deform in range(int(args.nr_deform_per_spine)):
            separate_US_pointcloud_into_vertebrae(args.root_path_spines, args.root_path_vertebrae, spine_id, deform,visualize=args.visualize)