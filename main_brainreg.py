from pathlib import Path
import os
import yaml
import subprocess


INPUT= Path('/ceph/sjones/projects/FlexiVexi/brainsaw_data')
OUTPUT = Path('/ceph/sjones/projects/FlexiVexi/brainreg')
ORIENTATION = 'psr'
full_size = False
mouselist =  ['FNT098', 'FNT101']
#mouse = 'FNT104'
down_025= True


def find_files_with_prefix(path, prefix):
    files = []
    for file_name in os.listdir(path):
        if file_name.startswith(prefix):
            files.append(os.path.join(path, file_name))
    return files

def find_files_with_suffix(path, suffix):
    files = []
    for file_name in os.listdir(path):
        if file_name.endswith(suffix):
            files.append(os.path.join(path, file_name))
    return files

def read_voxel_size(yaml_file_path):
    with open(yaml_file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Retrieve voxel size from the root 'VoxelSize' key
    voxel_size = data.get('VoxelSize', None)
    
    return voxel_size

for mouse in mouselist:

    print(mouse)


    if full_size:

        input_path = INPUT / mouse/ 'stitchedImages_100' / '2'
        output_path = OUTPUT/ mouse
        output_path.mkdir(exist_ok=True)

        recipes = find_files_with_prefix((INPUT / mouse), 'recipe')

        if len(recipes) != 1:
            print('CAREFUL!!!!!!!! MORE THAN ONE RECIPE FILE')
            exit()

        voxel_size = read_voxel_size(recipes[0])

        command = f'brainreg {input_path} {output_path} -v {voxel_size['X']} {voxel_size['Y']} {voxel_size['Z']} --orientation {ORIENTATION}'

    if down_025:

        input_path = INPUT / mouse/ 'downsampled_stacks' / '025_micron'

        output_path = OUTPUT/ mouse
        output_path.mkdir(exist_ok=True)

        blue = find_files_with_suffix(input_path, 'blue.tif')
        red = find_files_with_suffix(input_path, 'red.tif')
        green = find_files_with_suffix(input_path, 'green.tif')

        recipes = find_files_with_prefix((INPUT / mouse), 'recipe')

        if len(recipes) != 1:
            print('CAREFUL!!!!!!!! MORE THAN ONE RECIPE FILE')
            exit()

        original_voxel_size = read_voxel_size(recipes[0]) #image has been downsampled by a specific factor taken from the downsampling log

        voxel_size = {'X': 10.953*original_voxel_size['X'], 'Y':10.953*original_voxel_size['Y'], 'Z': 1.25*original_voxel_size['Z']}

        command = f'brainreg {blue[0]} {output_path} -v {voxel_size['X']} {voxel_size['Y']} {voxel_size['Z']} --orientation {ORIENTATION} -a {red[0]} {green[0]}'


    subprocess.run(command, shell=True, check=True)
