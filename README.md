# Tools to find where probes are
> Antonio Colás Nieto  
> anconi.1999@gmail.com  

This repo contains tools for probe localization within the Stephenson-Jones lab, written on the course of my rotation. It contains a pipeline for brain registration with Brainreg and a pipeline for mapping the frequency components within a neuropixels probe, for comparisons with the IBL Brain Wide Map. 

## Brainreg pipeline

This pipeline launches a brainreg alignment of a brainsaw output to ALlen Brain Atlas coordinates. 

First, create the brainreg environment. The pipeline does not use the brainreg python tools, but it uses the brainreg CLI. 

```
conda create --name brainreg
conda activate brainreg
conda install pip
pip install requirements.txt
```

It's made assuming that the outputs of brainsaw remain constant, but should things change, it should be easy to change it. I assume that you want to use the downsampled images, as the raw images are too big, but I tried it and kept the code there, should it be useful in the future. 

Just run `main_braibreg.py`

After that, some outputs will be created in `FlexiVexi/brainreg`. Bear in mind that the paths are fixed to work on the cluster. 

You can open those outputs graphically in [the Napari plugin](https://brainglobe.info/tutorials/tutorial-whole-brain-registration.html) of brainreg, and use [the brainreg tutorials](https://brainglobe.info/tutorials/segmenting-1d-tracks.html) to register a neuropixels probe. 

For me, installing everything via command line (brainreg bundled with napari) did not work well. I reccommend following their instructions and installing Napari plugins via the napari GUI. Because  you need a GUI, doing this in the cluster is probably challenging, and also probably unnecessary. 

## Probe power spectrum pipeline
The IBL did a [nice brain-wide neuropixels mapping](https://viz.internationalbrainlab.org/app), and there they have a good sense of  how the power spectrum changes depending on the area of the brain you're recording from. They specifically look at delta power (from 0 to 4 Hz). 

This is a pipeline to plot maps of just that in the recordings for the flexivexi task, but it probably works for any other neuuropixels recordings through the OpenEphys GUI with minimal modifications. 

### Running the pipeline
Because it uses `spikeinterface`, it should run fine with the environment used for ephys processing. 

It is usually run as a batch job, because it takes a long time, from `probe_location.batch`. Please, edit the email address and switch it to your own. You  should also change the path to the `main_probe_location.py` script 

Parameters shold be edited in `main_probe_location.py`. It accepts a list of mouse names. You can calculate all the delta powers, and choose between re-calculating them all from scratch (if you made any changes) or skipping the ones that are already made. You can also only use the pipeline to produce whole-probe maps. 

If a recording has several segments to it (that is, within the recording folder there are several directories and several `.xml` files), the pipeline will iterate over all of them and indicate where each recording comes from in the final map. 

You can choose to use the welch method to calculate the fourier transform. It will take a 40'' chunk of recording between seconds 5 and 45, break it into four windows, compute the spectrogram and average it. 

You can also use the multitaper method to calculate the power spectrum over a snippet of 10s of probe. This is significantly slower. 

This is not what the IBL does: they seem to break the signal into nonoverlapping 3'' windows, high-pass filter them below 1 Hz, calculuate the Welch power spectrum and add all of the windows together to get an estimate of the total energy spectrum of the signal. This is weird, as Megan Lockwood and I expected them to normalise the power spectrum, to obtain a measure that is invariable over time. 

[This is how they calculate the energy spectrum](https://github.com/int-brain-lab/ibllib/blob/master/ibllib/ephys/ephysqc.py)  

[This is how they plot it](https://github.com/int-brain-lab/ibllib/blob/master/brainbox/ephys_plots.py#L11)

## Registering probe spectrum to brainreg data. 

This pipeline solves two issues. When you trace a track in brainreg, you get a nice `.csv` file which contains a thousand points, sampled from the spline, and their anatomical locations. You also  get a `.npy` file which contains the coordinates of each of these points in the Allen Brain Atlas space. How to translate  from this  to where a channel is within the probe is not trivial: some people have used the tip and the fact that they know the geometry  of the probe to infer  where different probes are. However:

- If the probes are deep, the tip can be lost or hard to find. Also, the dye can diffuse if the animals have been implanted for a lonng time, which makes locating the tip very noisy. 

- When you use brainreg to register you brainsaw data to the Allen Brain Atlas, you are warping your brain to fit the Allen Brain Atlas. Because your brain might be smaller or bigger than the reference brain, a micron in the reference brain does not neccessarily mean the same as a micron in your brainsaw volume. 

The idea behind this pipelinne, then, is to find a set of common points in your probe space (through delta power analysis) and in Allen Brain space (through brainreg tracks). 

In the `main_physiology_aligmnent` script, you'll find an intuitive way to run the code in `phyhsiology_alignment`. 

- Write down the positions of a shared feature in probe space and brainreg space. This could be the transition from cortex to striatum, or the transitions in-out of the dentate gyrus. If you have more than one transition point, write them as a list. The more transition points, the better. 

- The code will attempt to find a mapping between your channels on each session and positions along your brainreg track. With just one feature, it can only align the two tracks, but not correct for the warping. With more than one feature, it will fit a line to the two or more points and use it create a linear map from probe space to the brainreg track. That is:
  
```
brainreg_position = intercept + slope*probe_position

OR

brainreg_position = difference + probe_position
```

The end result looks like the `complete_probemap.csv` file generated in the `probe_location` pipeline. However, it contains the Allen Brain coordinates for each channel on each sessions. To make things easier, there is an `areas_per_session.csv` file, which shows which areas were spanned in each recording session. 

## Visualization

I've included a re-worked example from  the brainreg people to be able to visualize the probes and select structures in the Allen Brain space. You can include as many animals as you want, because they've all been registered to a reference brain. 