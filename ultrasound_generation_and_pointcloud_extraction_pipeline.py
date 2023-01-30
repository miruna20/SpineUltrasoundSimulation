import subprocess
import argparse

if __name__ == '__main__':
    """
    Pipeline for ultrasound generation, partial point cloud extraction and dataset creation for shape completion
    1. Automatically generate transducer splines and direction splines for each deformed spine. 
    These are further used in the ultrasound simulation --> generate_splines.py
    2. Use imfusion workspace file to simulate ultrasound and segment the bone -->  simulate_US_and_save_segmentations.py
        Steps followed in the IWS file simulate_US_and_save_segmentations.iws
        1.1 Load labelmap from deformed spine 
        1.2 Simulate ultrasound sweep 
        1.3 Resample sweep to 1x1x1 mm
        1.4 Create US segmentations through volume reslicing (from US and initial labelmap) and export them
        1.5 Extract tracking stream and export it 
    3. Raycast the obtained segmentations (otherwise parts of vert that are not visible in the ultrasound will appear in the 
    segmentation --> raycast_bmode_data.py
    4. Use imfusion workspace file to extract a point cloud from the segmentations --> extract_pcd_from_US_labelmaps.py
        Steps followed in the IWS file extract_pcd_from_US_labelmaps.iws
        3.1 Segmentations + tracking stream => Segmentation sweep with correct geometry 
        3.2 Apply volume compounding on segmentation sweep 
        3.3 Extract mesh 
        3.4 Extract point cloud from mesh and export it 
    5. Separate the point cloud of the spine into individual pointclouds of vertebrae. These will be used as partial 
    point clouds for the completion --> separate_spine_pc_into_vertebrae.py
    6. Get a list of all of the lumbar vertebrae for which poinclouds are available 
    7. Combine pairs of complete and incomplete pointclouds in h5 dataset that will be used for the VRCNet for shape completion
    """

    arg_parser = argparse.ArgumentParser(description="Pipeline of ultrasound simulation and point cloud extraction")

    arg_parser.add_argument(
        "--root_path_spines",
        required=True,
        dest="root_path_spines",
        help="Root path to the spine folders."
    )

    arg_parser.add_argument(
        "--root_path_vertebrae",
        required=True,
        dest="root_path_vertebrae",
        help="Root path to the vertebrae folders."
    )

    arg_parser.add_argument(
        "--list_file_names_spines",
        required=True,
        dest="txt_file_spines",
        help="Txt file that contains all spines that contain all lumbar spines"
    )
    arg_parser.add_argument(
        "--list_file_names_vertebrae",
        required=True,
        dest="txt_file_vertebrae",
        help="Txt file that contains all spines that contain all lumbar vertebrae"
    )


    arg_parser.add_argument(
        "--path_splinedata",
        required=True,
        dest="splinedata",
        help="Path to csv file that will contain contains the transducer spline and the direction spline for every "
             "labelmap. "
    )
    arg_parser.add_argument(
        "--nr_deform_per_spine",
        required=True,
        dest="nr_deform_per_spine",
        help="Number of deformations per spine"
    )

    arg_parser.add_argument(
        "--workspace_file_simulate_us",
        required=True,
        dest="workspace_file_simulate_us",
        help="ImFusion workspace files that generates US and saves the segmentations and tracking stream"
    )
    arg_parser.add_argument(
        "--workspace_file_extract_pointcloud",
        required=True,
        dest="workspace_file_extract_pointcloud",
        help="ImFusion workspace file that extracts the point cloud from an ultrasound segmentation"
    )

    arg_parser.add_argument(
        "--result_h5_file",
        required=True,
        dest="result_h5_file",
        help="Path to the h5 file where the dataset will be saved"
    )

    arg_parser.add_argument(
        "--nr_points_per_point_cloud",
        required=True,
        dest="nr_points_per_point_cloud",
        help="Number of points per point cloud. This number is used for the sampling technique."
    )

    arg_parser.add_argument(
        "--pipeline",
        nargs='+',
        default=['all'],
        help="Specify the steps of the pipeline that will be executed "
    )

    args = arg_parser.parse_args()

    root_path_spines = args.root_path_spines
    root_path_vertebrae = args.root_path_vertebrae

    txt_file_lumbar_spines = args.txt_file_spines
    txt_file_lumbar_vertebrae = args.txt_file_vertebrae
    path_splinedata = args.splinedata
    nr_deform_per_spine = args.nr_deform_per_spine

    workspace_file_simulate_us = args.workspace_file_simulate_us
    workspace_file_extract_pointcloud = args.workspace_file_extract_pointcloud

    result_h5_file = args.result_h5_file
    nr_points_per_point_cloud = args.nr_points_per_point_cloud

    pipeline = args.pipeline

    if 'generate_splines' in pipeline or 'all' in pipeline:
        subprocess.run(['python', 'generate_splines.py',
                        '--list_file_names', txt_file_lumbar_spines,
                        '--root_path_spines', root_path_spines,
                        '--path_splinedata', path_splinedata,
                        '--nr_deform_per_spine', nr_deform_per_spine])

    if 'simulate_US' in pipeline or 'all' in pipeline:
        subprocess.run(['python', 'simulate_lumbar_spine_ultrasound.py',
                        '--list_file_names', txt_file_lumbar_spines,
                        '--workspace_file', workspace_file_simulate_us,
                        '--root_path_spines', root_path_spines,
                        '--nr_deform_per_spine', nr_deform_per_spine,
                        '--path_splinedata', path_splinedata])

    if 'raycast' in pipeline or 'all' in pipeline:
        subprocess.run(['python', 'raycast_bmode_data.py',
                        '--list_file_names', txt_file_lumbar_spines,
                        '--root_path_spines', root_path_spines])

    if 'extract_pcd' in pipeline or 'all' in pipeline:
        subprocess.run(['python', 'extract_pcd_from_US_labelmaps.py',
                        '--list_file_names', txt_file_lumbar_spines,
                        '--workspace_file',  workspace_file_extract_pointcloud,
                        '--root_path_spines', root_path_spines,
                        '--nr_deform_per_spine', nr_deform_per_spine])

    if 'separate_spine_pc_into_vertebrae' in pipeline or 'all' in pipeline:
        subprocess.run(['python', 'separate_spine_pc_into_vertebrae.py',
                        '--list_file_names', txt_file_lumbar_spines,
                        '--root_path_vertebrae', root_path_vertebrae,
                        '--root_path_spines', root_path_spines,
                        '--nr_deform_per_spine', nr_deform_per_spine
                        ])

    if 'get_list_of_vertebrae_in_folder' in pipeline or 'all' in pipeline:
        subprocess.run(['python', 'get_list_of_vertebrae_in_folder.py',
                        '--root_path_vertebrae', root_path_vertebrae,
                        '--list_file_names', txt_file_lumbar_vertebrae])

    if 'create_dataset' in pipeline or 'all' in pipeline:
        subprocess.run(['python', 'create_dataset_for_shape_completion.py',
                        '--vertebrae_list', txt_file_lumbar_vertebrae,
                        '--root_path_vertebrae', root_path_vertebrae,
                        '--result_h5_file', result_h5_file,
                        '--nr_partial_pcds_per_sample', nr_deform_per_spine,
                        '--nr_points_per_point_cloud', nr_points_per_point_cloud])