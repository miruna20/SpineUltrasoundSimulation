import collections

import numpy as np
import h5py
import os
import open3d as o3d
import sys
import math
from collections import Counter
import argparse
import glob

scale_factor = 0.01

def processOneVertebra(pathCompleteVertebra, pathToPartialPCD, nrPointsProPartialPC=2048,
                       nrPointsProCompletePC=4098,
                       visualize=False):
    """

    :param pathCompleteVertebra: path to the .obj file representing a complete vertebra
    :param pathToRootPartialPCD: path to the root folder containing the .pcd files which represent partial point clouds
    :param nrPartialPCDPerSample: number of partial pointclouds per vertebra
    :param nrPointsProPointCloud: number of points to be sampled from a pointcloud
    :param visualize: flag for visualization
    :return: complete vertebra point cloud, list of partial point clouds

    """

    print("Processing: " + pathCompleteVertebra)

    # load complete vertebra and its partial point cloud
    completeVertebra = o3d.io.read_triangle_mesh(pathCompleteVertebra)
    partial_pcd = o3d.io.read_point_cloud(pathToPartialPCD)

    # delete all points that are below the center of mass of completeVert
    center_pcd = partial_pcd.get_center()
    points = np.asarray(partial_pcd.points).tolist()
    #points_above_center_of_mass = [point for point in points if (point[1] > center_pcd[1] or point[0] > center_pcd[0]+3 or point[0] < center_pcd[0]-3)]
    #points_above_center_of_mass = [point for point in points if (point[1] > center_pcd[1]-4)]
    points_above_center_of_mass = [point for point in points]
    partial_pcd.points = o3d.utility.Vector3dVector(np.asarray(points_above_center_of_mass))

    #scale down
    completeVertebra.scale(scale_factor, completeVertebra.get_center())
    partial_pcd.scale(scale_factor, partial_pcd.get_center())

    center_vertebra = completeVertebra.get_center()
    center_pcd = partial_pcd.get_center()
    completeVertebra.vertices = o3d.utility.Vector3dVector(completeVertebra.vertices - center_vertebra)
    partial_pcd.points = o3d.utility.Vector3dVector(partial_pcd.points - center_pcd)

    # sample complete vertebra with the poisson disk sampling technique
    pointCloudComplete = o3d.geometry.TriangleMesh.sample_points_poisson_disk(completeVertebra, nrPointsProCompletePC)

    # sample partial point cloud Farthest Point Sample

    # check if partial_pcd has >= nrPointsProPartialPC points
    # if yes then sample this number directly
    # if it has at least half of the nrPointsProPartialPC duplicate the number of points then resample
    nr_points_in_partial_pcd = np.asarray(partial_pcd.points).shape[0]
    if(nr_points_in_partial_pcd >= nrPointsProPartialPC):
        sampled_partial_pcd = partial_pcd.farthest_point_down_sample(nrPointsProPartialPC)
    elif(nr_points_in_partial_pcd >= nrPointsProPartialPC/2):
        # duplicate the number of points available
        print("Duplicated the number of points")
        sampled_partial_pcd = partial_pcd.farthest_point_down_sample(int(nrPointsProPartialPC/2))
        duplicated_points = np.repeat(np.asarray(sampled_partial_pcd.points), repeats=2, axis=0)
        sampled_partial_pcd.points = o3d.utility.Vector3dVector(np.asarray(duplicated_points))
    else:
        print("PCD with less than " + str(nrPointsProPartialPC) + "points" + str(os.path.basename(pathToPartialPCD)))
        return 0, []
    if (visualize):
        coord_sys = o3d.geometry.TriangleMesh.create_coordinate_frame()

        print("Visualizing input and ground truth after scaling and centering")
        pointCloudComplete.paint_uniform_color([0,1,0])
        partial_pcd.paint_uniform_color([0,0,1])
        o3d.visualization.draw([partial_pcd, coord_sys])

        #print("Visualizing initial partial pointcloud and the sampled one")
        #sampled_partial_pcd_translated = o3d.geometry.PointCloud.translate(sampled_partial_pcd,np.asarray([1.5, 0, 0]))
        #o3d.visualization.draw([partial_pcd, sampled_partial_pcd_translated, coord_sys])

    partial_pcds = []
    partial_pcds.append(np.asarray(sampled_partial_pcd.points))

    return np.asarray(pointCloudComplete.points), partial_pcds


def extractLabel(nameVertebra):
    label = nameVertebra.split("verLev")[1]
    label = label.split(".")[0]

    return int(label)


def computeNrPerClass(labels, nrSamplesPerClass=16):
    # the labels need to start with 0 (make sure that if you have labels for lumbar vertebrae you substract minimal label

    nr_samples_per_class = Counter(labels)
    ordered_dict = collections.OrderedDict(sorted(nr_samples_per_class.items()))

    nr_samples_per_class_as_list = []
    for key in ordered_dict.keys():
        nr_samples_per_class_as_list.append(math.floor(ordered_dict[key] / nrSamplesPerClass))

    return np.asarray(nr_samples_per_class_as_list)


def saveToH5(fileName, stackedCropped, stackedComplete, labels,datasets_ids, nrSamplesPerClass=16):
    # save the dataset in a .h5 file for VRCNet
    vertebrae_file = h5py.File(fileName, "w")
    dset_incompletepcds = vertebrae_file.create_dataset("incomplete_pcds", data=stackedCropped)
    dset_completepcds = vertebrae_file.create_dataset("complete_pcds", data=stackedComplete)
    dset_labels = vertebrae_file.create_dataset("labels", data=labels)
    dset_ids = vertebrae_file.create_dataset("datasets_ids", data=datasets_ids)
    number_per_class = computeNrPerClass(labels, nrSamplesPerClass)
    dset_number_per_class = vertebrae_file.create_dataset("number_per_class", data=number_per_class)
    print("Number_per_class" + str(number_per_class))


def processAllVertebrae(list_path, rootDirectoryVertebrae, saveTo,
                        nr_deform_per_sample, visualize=False, nrPointsProPartialPC=2048,
                        nrPointsProCompletePC=4096):
    # prepare lists for storing all vertebrae
    labels = []
    complete_pcds_all_vertebrae = []
    partial_pcds_all_vertebrae = []
    dataset_ids = []

    # create a list with all vertebrae names
    with open(os.path.join(list_path)) as file:
        model_list = [line.strip() for line in file]

    # get min label
    all_labels = [extractLabel(model_id) for model_id in model_list]
    min_label = np.min(np.asarray(all_labels))

    idx = 0

    # iterate over the vertebrae names
    for model_id in model_list:
        for deform in range(nr_deform_per_sample):
            print(str(idx) + "/" + str(len(model_list) * nr_deform_per_sample))
            print("Processing " + str(model_id) + " deformation: " + str(deform))

            # obtain the path to the complete vertebra and to the root of the partial point clouds
            unique_identifier_mesh_vertebra = "*verLev*" + "*forces*" + str(deform) + "*_deformed_centered*" "*.obj"
            paths = glob.glob(os.path.join(rootDirectoryVertebrae, model_id, unique_identifier_mesh_vertebra))
            # make sure not to accidentally select the scaled ones
            model_path  = [path for path in paths if 'scaled' not in os.path.basename(path)][0]

            unique_identifier_partial_pcd = "*verLev*" + "*forces*" + str(deform) + "*deformed_clean_aligned*" +  "*.pcd"
            partial_model_path =  glob.glob(os.path.join(rootDirectoryVertebrae, model_id, unique_identifier_partial_pcd))[0]

            #  process each vertebra individually
            complete_pcd, partial_pcds = processOneVertebra(pathCompleteVertebra=model_path,
                                                            pathToPartialPCD=partial_model_path,
                                                            visualize=visualize,
                                                            nrPointsProPartialPC=nrPointsProPartialPC,
                                                            nrPointsProCompletePC=nrPointsProCompletePC)


            # if the partial point cloud has less than nrPointsProPartialPC then partial_pcds will be an empty list
            if len(partial_pcds) == 0:
                continue
            print(partial_pcds[0].shape)
            # add it to h5py
            # make sure that the smallest label will be 0
            label_normalized = extractLabel(model_id) - min_label
            complete_pcds_all_vertebrae.append(complete_pcd)
            partial_pcds_all_vertebrae.extend(partial_pcds)
            dataset_ids.append((model_id + "_deform" + str(deform)).encode("ascii"))

            # size of labels = size of all_partial_pcds
            labels.extend([label_normalized for j in range(0, 1)])
            idx += 1

    # stack the results
    stacked_partial_pcds = np.stack(partial_pcds_all_vertebrae, axis=0)
    stacked_complete_pcds = np.stack(complete_pcds_all_vertebrae, axis=0)
    stacked_dataset_ids = np.stack(dataset_ids,axis=0)
    labels_array = np.asarray(labels)

    # for debugging print the shape
    print("Shape of stacked_partial_pcds: " + str(stacked_partial_pcds.shape))
    print("Shape of stacked_complete_pcds" + str(stacked_complete_pcds.shape))
    print("Shape of labels" + str(labels_array.shape))

    saveToH5(saveTo, stackedCropped=stacked_partial_pcds, stackedComplete=stacked_complete_pcds,
             labels=labels_array, datasets_ids=stacked_dataset_ids,  nrSamplesPerClass=1)

def create_dataset_withoutGT(nrPointsProPartialPC,nrPointsProCompletePC,visualize, saveTo):
    model_path = "/home/miruna20/Documents/Thesis/Dataset/VerSe2020/vertebrae/01_training/sub-verse534_verLev21/sub-verse534_verLev21_forces0_deformed_20_0.obj"
    partial_model_root = "/home/miruna20/Documents/Thesis/Dataset/Maria_dataset"
    partial_model_paths =[
        os.path.join(partial_model_root, "Maria's_spine_centered_verLev20.pcd"),
        os.path.join(partial_model_root, "Maria's_spine_centered_verLev21.pcd"),
        os.path.join(partial_model_root, "Maria's_spine_centered_verLev22.pcd"),
        os.path.join(partial_model_root, "Maria's_spine_centered_verLev23.pcd")]
    min_label = 20
    complete_pcds_all_vertebrae = []
    partial_pcds_all_vertebrae = []
    labels = []
    for partial_model_path in partial_model_paths:
        complete_pcd, partial_pcds = processOneVertebra(pathCompleteVertebra=model_path,
                                                        pathToPartialPCD=partial_model_path,
                                                        visualize=visualize,
                                                        nrPointsProPartialPC=nrPointsProPartialPC,
                                                        nrPointsProCompletePC=nrPointsProCompletePC)
        # if the partial point cloud has less than nrPointsProPartialPC then partial_pcds will be an empty list
        if len(partial_pcds) == 0:
            continue
        print(partial_pcds[0].shape)

        label_normalized = extractLabel(partial_model_path) - min_label
        complete_pcds_all_vertebrae.append(complete_pcd)
        partial_pcds_all_vertebrae.extend(partial_pcds)

        # size of labels = size of all_partial_pcds
        labels.extend([label_normalized for j in range(0, 1)])

    stacked_partial_pcds = np.stack(partial_pcds_all_vertebrae, axis=0)
    stacked_complete_pcds = np.stack(complete_pcds_all_vertebrae, axis=0)
    labels_array = np.asarray(labels)

    # for debugging print the shape
    print("Shape of stacked_partial_pcds: " + str(stacked_partial_pcds.shape))
    print("Shape of stacked_complete_pcds" + str(stacked_complete_pcds.shape))
    print("Shape of labels" + str(labels_array.shape))

    saveToH5(saveTo, stackedCropped=stacked_partial_pcds, stackedComplete=stacked_complete_pcds,
             labels=labels_array, datasets_ids=np.asarray([]), nrSamplesPerClass=1)


if __name__ == "__main__":

    """
     arg_parser = argparse.ArgumentParser(description="Create a dataset for completion training")
    arg_parser.add_argument(
        "--vertebrae_list",
        required=True,
        dest="vertebrae_list",
        help="txt file with names of vertebrae that will be included in the dataset"
    )
    arg_parser.add_argument(
        "--root_path_vertebrae",
        required=True,
        dest="folder_complete_meshes",
        help="Root path of the vertebrae folders"

    )
    arg_parser.add_argument(
        "--result_h5_file",
        required=True,
        dest="result_h5_file",
        help="Path to the h5 file where the dataset will be saved"
    )

    arg_parser.add_argument(
        "--nr_deform_per_sample",
        required=True,
        dest="nr_deform_per_sample",
        help="Number of deformations for one spine."
    )
    arg_parser.add_argument(
        "--nr_points_per_point_cloud",
        required=True,
        dest="nr_points_per_point_cloud",
        help="Number of points that will be sampled both from the partial point cloud and from the complete mesh"
    )

    arg_parser.add_argument(
        "--visualize_vertebrae",
        action="store_true",
        default=False,
        help="Visualize vertebrae before they are added to the dataset"
    )

    args = arg_parser.parse_args()
    print("Creating the shape completion dataset from partial point clouds obtained from US")
    # process all vertebrae
    processAllVertebrae(list_path=args.vertebrae_list,
                        rootDirectoryVertebrae=args.folder_complete_meshes,
                        saveTo=args.result_h5_file,
                        nr_deform_per_sample=int(args.nr_deform_per_sample),
                        visualize=args.visualize_vertebrae,
                        nrPointsProPartialPC=int(args.nr_points_per_point_cloud),
                        nrPointsProCompletePC=int(args.nr_points_per_point_cloud),
                        )
    """
    create_dataset_withoutGT(nrPointsProPartialPC=4096,nrPointsProCompletePC=4096,visualize=True,saveTo="/home/miruna20/Documents/Thesis/Dataset/Maria_dataset/dataset_Maria.h5")
