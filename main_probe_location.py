import probe_location
from pathlib import Path
import os

mouselist = ['FNT099']

calculate_power = False
re_calculate_power = False
build_whole_probe = True

mode = 'four_shanks'

INPUT = Path('/ceph/sjones/projects/FlexiVexi/raw_data/')
OUTPUT = Path('/ceph/sjones/projects/FlexiVexi/data_analysis/probe_location/')

if calculate_power:

    for mouse in mouselist:

        mouse_path = INPUT / mouse

        # List the directories directly under mouse_path
        for directory in next(os.walk(mouse_path))[1]:  # [1] gives the list of directories at the top level

            dir_path = os.path.join(mouse_path, directory)

            result = probe_location.get_record_node_path(dir_path)

            if result is not None:

                output_probemap = Path(OUTPUT) / mouse / f'{directory}_{mode}' / 'probemap.csv'

                if output_probemap.is_file() and not re_calculate_power:
                    print(f'{directory} is already processed. SKIPPING!')
                    continue

                print('\n \n #################################')
                print(f'Processing {mouse} session {directory}')
                print('#################################\n \n ')
                print(dir_path)
                print(result)

                probe_mapper = probe_location.probe_mapper(mouse, directory, mode=mode)

                probe_mapper.fourier()

                print('If done in slow mode, takes about 20')
                probe_mapper.probe_spectrum()

                probe_mapper.calculate_delta_power()

                probe_mapper.build_probemap()

if build_whole_probe:

    for mouse in mouselist:

        probe = probe_location.whole_probe(mouse)

        probe.build_whole_probemap()

        probe.process_probemap()

        probe.plot_probemap()
