# Tools for Probe Localization
> Antonio Colás Nieto  
> anconi.1999@gmail.com  

This repository contains tools for probe localization within the Stephenson-Jones lab, developed during my rotation. It includes a pipeline for brain registration with Brainreg and a pipeline for mapping the frequency components within a Neuropixels probe, for comparisons with the IBL Brain-Wide Map.

## Brainreg Pipeline

This pipeline launches a Brainreg alignment of a brainsaw output to Allen Brain Atlas coordinates.

### Setup
First, create the Brainreg environment. The pipeline does not use Brainreg Python tools but relies on the Brainreg CLI.

```
conda create --name brainreg 
conda activate brainreg 
conda install pip 
pip install -r requirements.txt
```

The pipeline assumes that the outputs from brainsaw remain constant, but if anything changes, adjustments should be easy to make. The code is designed to use the downsampled images since the raw images are too large. However, I have included the code for processing raw images, should it be useful in the future.

Run `main_braibreg.py` to start the process.

The outputs will be created in `FlexiVexi/brainreg`. Keep in mind that the paths are configured to work on the cluster.

You can open these outputs graphically using the [Napari plugin](https://brainglobe.info/tutorials/tutorial-whole-brain-registration.html) for Brainreg, and refer to the [Brainreg tutorials](https://brainglobe.info/tutorials/segmenting-1d-tracks.html) to register a Neuropixels probe.

For me, installing everything via the command line (Brainreg bundled with Napari) didn’t work well. I recommend following their instructions and installing Napari plugins via the Napari GUI. Since a GUI is required, doing this on the cluster may be challenging, and probably unnecessary.

## Probe Power Spectrum Pipeline

The IBL conducted a [brain-wide Neuropixels mapping](https://viz.internationalbrainlab.org/app) where they analyzed how the power spectrum changes depending on the brain area being recorded, specifically focusing on delta power (0-4 Hz).

This pipeline generates maps of delta power for the FlexiVexi task recordings, but it likely works for any other Neuropixels recordings processed through the OpenEphys GUI with minimal modifications.

### Running the Pipeline

Typically, this pipeline is run as a batch job since it takes a long time. Start it from `probe_location.batch`. Please update the email address to your own and change the path to your data in both the main script and `probe_location` (bad practice, I know, but I just realised and it's my last day). 

You can edit parameters in `main_probe_location.py`. It accepts a list of mouse names. You can calculate all the delta powers and decide whether to recalculate everything from scratch (if you’ve made changes) or skip already processed data. 


If a recording contains multiple segments (i.e., several directories and `.xml` files in the recording folder), the pipeline will iterate over all of them and indicate the origin of each recording in the final map.

You can opt to use the Welch method to calculate the Fourier transform. It will take a 40-second segment of the recording (between seconds 5 and 45), break it into four windows, compute the spectrogram, and average it.

Alternatively, you can use the multitaper method to calculate the power spectrum over a 10-second probe snippet, although this is significantly slower.

The IBL uses a different method: they break the signal into non-overlapping 3-second windows, high-pass filter below 1 Hz, calculate the Welch power spectrum, and sum all the windows to estimate the total energy spectrum of the signal. This is unusual, as Megan Lockwood and I expected them to normalize the power spectrum for a time-invariant measure.

- [Here’s how they calculate the energy spectrum](https://github.com/int-brain-lab/ibllib/blob/master/ibllib/ephys/ephysqc.py)  
- [Here’s how they plot it](https://github.com/int-brain-lab/ibllib/blob/master/brainbox/ephys_plots.py#L11)

## Registering Probe Spectrum to Brainreg Data

This pipeline addresses two issues. When you trace a track in Brainreg, it generates a `.csv` file containing thousands of points sampled from the spline, along with their anatomical locations. It also produces a `.npy` file with the coordinates of these points in Allen Brain Atlas space. Mapping these points to probe channels is non-trivial; some people infer channel locations based on the probe’s geometry and the position of the tip. However:

- If the probe is inserted deep, the tip may be hard to locate or lost entirely. Additionally, if the animal has been implanted for a long time, the dye may diffuse, making tip identification noisy.
- Brainreg warps your brain to fit the Allen Brain Atlas. Since your brain may differ in size from the reference brain, a micron in the Allen Atlas may not correspond to a micron in your brainsaw volume.

The idea of this pipeline is to identify shared points between probe space (via delta power analysis) and Allen Brain Atlas space (via Brainreg tracks).

In the `main_physiology_alignment` script, you’ll find an intuitive method for running the code in `physiology_alignment`.

- Write down the positions of shared features in probe space and Brainreg space. These could include transitions between brain regions (e.g., cortex to striatum or in-out transitions of the dentate gyrus). If you have more than one transition point, write them as a list. More points yield better results. 
    -  Neuropixels distances are indicated as in the probemap files: in microns from electrode 0, which is the deepest electrode. 
    - Brainreg distances are indicated as in brainreg `track.csv` files: in microns from the most superficial point of the track. To be clear, these are the files generated from the segmentation pipeline. 
- The code will map channels in each session to positions along your Brainreg track. With only one feature, it aligns the tracks but cannot correct for warping. With more than one, it fits a line to the points, creating a linear map from probe space to the Brainreg track:

```
brainreg_position = intercept + slope * probe_position 
OR 
brainreg_position = difference + probe_position
```

The result is a `complete_probemap.csv` file, similar to the one generated by the `probe_location` pipeline, but containing Allen Brain coordinates for each channel in each session. Additionally, the `areas_per_session.csv` file shows which brain areas were spanned during each recording session.

## Visualization

I’ve included a modified example from the Brainreg team to visualize probes and selected structures in the Allen Brain space. You can include as many animals as needed since they’ve all been registered to the reference brain.

Alternatively, you can visualize the Allen Brain coordinate space in many tools, like [this 3D explorer in the browser](https://community.brain-map.org/t/allen-brain-explorer-beta-user-guide/3020). 