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

Parameters shold be edited in `main_probe_location.py`. It accepts a list of mouse names. You can calculate all the delta powers, annd choose between re-calculating them all from scratch (if you made any changes) or skipping the ones that are already made. You can also only use the pipeline to produce whole-probe maps. 

You can choose to use the welch method to calculate the fourier transform. It will take a 40'' chunk of recording between seconds 5 and 45, break it into four windows, compute the spectrogram and average it. 

You can also use the multitaper method to calculate the power spectrum over a snippet of 10s of probe. This is significantly slower. 

This is not what the IBL does: they seem to break the signal into nonoverlapping 3'' windows, high-pass filter them below 1 Hz, calculuate the Welch power spectrum and add all of the windows together to get an estimate of the total energy spectrum of the signal. This is weird, as Megan Lockwood and I expected them to normalise the power spectrum, to obtain a measure that is invariable over time. 

[This is how they calculate the energy spectrum](https://github.com/int-brain-lab/ibllib/blob/master/ibllib/ephys/ephysqc.py)  

[This is how they plot it](https://github.com/int-brain-lab/ibllib/blob/master/brainbox/ephys_plots.py#L11)
