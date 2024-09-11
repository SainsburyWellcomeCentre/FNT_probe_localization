import matplotlib.pyplot as plt
from pathlib import Path


import spikeinterface.full as si
import spikeinterface.extractors as se
import spikeinterface.widgets as sw

import numpy as np
import  multitaper
from tqdm import tqdm
import pandas as pd
import os

INPUT = Path('/ceph/sjones/projects/FlexiVexi/raw_data/')
OUTPUT = Path('/ceph/sjones/projects/FlexiVexi/data_analysis/probe_location/')

def get_record_node_path(root_folder):
    # Traverse the directory tree
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Check if 'settings.xml' is in the current directory
        if 'settings.xml' in filenames:
            return dirpath
    return None

class probe_mapper():

    '''
    Used to generate the power spectrum per channel
     during a particular session. Choice between one_shank (the first)
     or four shanks. 
    '''

    def __init__(self, mouse, session, mode = 'four_shanks'):

        self.mouse = mouse
        self.session  = session
        self.mode = mode

        root_path = INPUT  / self.mouse / self.session

        self.node_path = get_record_node_path(root_path)

        mousepath = OUTPUT  / mouse
        mousepath.mkdir(exist_ok=True)

        self.output_path =  mousepath / f'{session}_{mode}'
        self.output_path.mkdir(exist_ok=True)
        #reading

        recording = se.read_openephys(self.node_path, stream_id  = '1')

        if recording.get_num_segments() > 1:
            recording = recording.select_segments(0)
            print('More than one segment. Selecting the first.')

        print(f'Reading recording at {self.node_path}')
        print(recording)

        if self.mode == 'one_shank':

            split_recording_dict = recording.split_by("group")

            print('Separating probe 1')
            self.probe1 = split_recording_dict[1]

        elif self.mode == 'four_shanks':

            self.probe1 = recording

        #Keep 10s of data
        self.samp = self.probe1.sampling_frequency
        print(f'Sampling freq is {self.samp}Hz')
        print('Extracting 10s')
        self.traces =  (self.probe1.get_traces(start_frame=5*self.samp, end_frame=15*self.samp)).T

        nChans, nSamps = self.traces.shape
        print('Data has %d channels and %d samples',(nChans,nSamps))

    def fourier(self, mode = 'multitaper'):
        '''
        Calculates the Fourier transform of the first channel. Can use multitaper
        (precise w small sample sizes, but slow), or fft (fast, maybe  imprecise in
        low frequencies)

        Returns:
            pxx: power spectrum in V**2
            f: frequencies of pxx in Hz
        '''
        if  mode  == 'multitaper':

            psd = multitaper.MTSpec(x=self.traces[0,:]/10E6, dt=1.0/self.samp, nw=5) # run the multitaper spectrum
            self.pxx, self.f = psd.spec, psd.freq # unpack power spectrum and frequency from output
            plot_range = (self.f<=10) & (self.f>=0) # find the frequencies we want to plot
            fig, ax = plt.subplots()

            # Correct method call for semilogy
            ax.semilogy(self.f[plot_range], self.pxx[plot_range])

            # Set axis labels
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Power (V**2)')


            fig.suptitle('Multitaper spectrum of first channel')
            fig.savefig(self.output_path / 'spectrum.png')

    def probe_spectrum(self, mode = 'multitaper'):

        self.pxx_list = list(np.zeros(len(self.probe1.channel_ids)))
        self.f_list = list(np.zeros(len(self.probe1.channel_ids)))

        if mode ==  'multitaper':

            for i in tqdm(np.arange(len(self.pxx_list))):
                print (i)
                psd = multitaper.MTSpec(x=self.traces[i,:]/10E6, dt=1.0/self.samp, nw=5) # run the multitaper spectrum
                pxx, f = psd.spec, psd.freq # unpack power spectrum and frequency from output
                self.pxx_list[i] = pxx
                self.f_list[i] = f

            freq_per_channel = {
                'channel': np.arange(len(self.probe1.channel_ids)), 
                'pxx': self.pxx_list, 
                'f': self.f_list
            }

            self.freq =  pd.DataFrame(freq_per_channel)

    def get_delta_power(self, pxx, f):

        '''
        Extracts the power in the delta band and transforms it into
        decibels. 
        '''

        # Define the frequency range of interest (0-4 Hz)
        band_range = (f >= 0) & (f <= 4)

        # Calculate the total power in the 0-4 Hz band by summing the power values in that range
        power_band = np.sum(pxx[band_range])

        # Convert the power to dB
        power_db = 10 * np.log10(power_band)

        return power_db
    
    def calculate_delta_power(self):

        self.freq['delta_power'] =  [self.get_delta_power(pxx, f) for pxx,f in zip(self.pxx_list, self.f_list)]
        self.freq.to_csv(self.output_path / 'freq.csv')

    def build_probemap(self):

        '''
        Assuming the order of the  channels is the order  of the  
        contact points, which I took from the openephys code
        '''
        self.probemap = self.probe1.get_probe().to_dataframe()

        self.probemap['channel'] = self.probe1.channel_ids
        self.probemap['dbs'] = self.freq['delta_power']

        fig, ax = plt.subplots()

        # Create a scatter plot
        sc = ax.scatter(self.probemap['x'], self.probemap['y'], c=self.probemap['dbs'], cmap='viridis', s=50)

        # Add color bar for the 'dfs' values (make sure to pass the scatter plot object `sc`)
        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label('Delta power (power in Db from 0 to 4 Hz in a signal in V)')

        if self.mode == 'one_shank':

            # Set x-axis limits
            ax.set_xlim((100, 450))
            ax.set_ylabel('depth (microns)')

            fig.suptitle('Map of the shank 1 and delta power')

        elif self.mode == 'four_shanks':

            # Set x-axis limits
            ax.set_ylabel('depth (microns)')

            fig.suptitle('Map of the four shanks and delta power')
        
        #save
        fig.savefig(self.output_path / 'delta_map.png')
        self.probemap.to_csv(self.output_path / 'probemap.csv')

class  whole_probe():

    '''
    Collects data generated by probe_mapper to generate a map of delta power
    over the whole probe. 
    '''

    def __init__(self, mouse, mode = 'four_shanks'):

        self.mouse  = mouse
        self.mode = mode

        self.probemap = pd.DataFrame()

        self.root_path = OUTPUT  / self.mouse 

        mousepath = OUTPUT  / self.mouse
        mousepath.mkdir(exist_ok=True)

        if self.mode == 'one_shank':

            self.output_path =  mousepath / 'whole_probe'
            self.output_path.mkdir(exist_ok=True)
        
        elif self.mode == 'four_shanks':

            self.output_path =  mousepath / 'whole_probe_four_shanks'
            self.output_path.mkdir(exist_ok=True)

    def build_whole_probemap(self):

        for root, dirs, files in os.walk(self.root_path):
            for directory in dirs:

                self.session = directory

                dir_path = os.path.join(root, directory)

                if dir_path.endswith(self.mode):

                    self.colect_data(dir_path)
        
        self.probemap.to_csv(self.output_path / 'complete_probemap.csv')

    def colect_data(self, path):

        # Construct the full path to the CSV file
        probemap_path = os.path.join(path, 'probemap.csv')

        # Check if the file exists
        if os.path.exists(probemap_path):
            # Read the CSV file
            new_probemap = pd.read_csv(probemap_path)

            new_probemap['session'] = self.session

            # Check if the class has the probemap attribute
            if hasattr(self, 'probemap'):
                # Append the new data to the existing probemap DataFrame
                self.probemap = pd.concat([self.probemap, new_probemap], ignore_index=True)
            else:
                # If probemap does not exist, assign the new CSV as probemap
                self.probemap = new_probemap
        else:
            print(f"{probemap_path} does not exist.")

    def process_probemap(self):
        '''
        Deals with  duplicate entries for a  single  point  (more than two
        sessions on the  same bank) by keeping the average value for  dbs
        on that point in space.  )
        '''
        self.processed_probemap = self.probemap.groupby(['x', 'y'], as_index=False)['dbs'].mean()
        self.processed_probemap.to_csv(self.output_path / 'processed_probemap.csv')

        
    def plot_probemap(self, combine = 'processed'):

        '''
        Combine stands for wether all the datapoints are plotted, or
        datapoints of the same channel are averaged across sessions
        '''

        fig, ax = plt.subplots()

        # Create a scatter plot
        if combine  == 'raw':
            sc = ax.scatter(self.probemap['x'], self.probemap['y'], c=self.probemap['dbs'], cmap='viridis', s=50)
        elif combine  == 'processed':
            sc = ax.scatter(self.processed_probemap['x'], self.processed_probemap['y'], c=self.processed_probemap['dbs'], cmap='viridis', s=50)

        # Add color bar for the 'dfs' values (make sure to pass the scatter plot object `sc`)
        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label('Delta power (power in Db from 0 to 4 Hz in a signal in V)')

        if self.mode == 'one_shank':

            # Set x-axis limits
            ax.set_xlim((100, 450))
            ax.set_ylabel('depth (microns)')

            fig.suptitle('Map of the shank 1 and delta power')

        elif self.mode == 'four_shanks':

            # Set x-axis limits
            ax.set_ylabel('depth (microns)')

            fig.suptitle('Map of the four shanks and delta power')
        
        #save
        fig.savefig(self.output_path / 'complete_delta_map.png')

