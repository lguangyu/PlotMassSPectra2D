# SYNOPSIS

This script plots mass spectral data in a 2-D heatmap.

# DEPENDENCIES

Python2 is deprecated. We follows the trend so this script requires python
version >= 3.0. In addition, below external dependency python libraries are
also required:

```
numpy
matplotlib
```

They must be pre-installed. The easiest way to install them is probably using
`pip` from command-line (or called terminal):

```
pip install numpy matplotlib # for Linux/MacOS
```

On Windows, the above command also works but only after some extra efforts in
configuring the environment. Also note that on Windows python is not natively
installed; one may find it necessary to download and install python first.

# BASIC EXAMPLE

The script needs to be executed from command-line interface (CLI), e.g. in
a terminal. A simple example may look like:

```
./plot_mass_spectra_2d.py spectra.mzdata.xml -p spectra.mzdata.xml.png
```

This will plot the data in spectra.mzdata.xml and save into a png image.

# ARGUMENTS

The argument option format follows the Linux convention.
`./plot_mass_spectra_2d.py --help` will show all available options and their
acceptable value format.

## input

The input spectra filename. The file is expected to be in mzdata xml format.
Note if the filename includes and special character (anything other than
alphabetical (a-z and A-Z) digits (0-9) and underscore (_)), it must be wrapped
in quote marks. For example:

```
./plot_mass_spectra_2d.py spectra mzdata.xml -p spectra.png # NOT ok
./plot_mass_spectra_2d.py "spectra mzdata.xml" -p spectra.png # ok
```

## --from-time/--till-time

These two arguments select the time range for plotting, for example:

```
./plot_mass_spectra_2d.py spectra.mzdata.xml -p spectra.mzdata.xml.png --from-time 5 --till-time 30
```

will plot the data between 5-30 min range. By default (if these arguments are
not set) the whole range will be plotted

## --mz-min/--mz-max

These two arguments select the M/Z range for plotting, for example:

```
./plot_mass_spectra_2d.py spectra.mzdata.xml -p spectra.mzdata.xml.png --mz-min 200 --mz-max 1000
```

will plot the data between 200-1000 M/Z range. The default is 0-1000.

## --title

To provide a title for the figure. If not set, the input mzdata xml filename
will be used. Note if the title includes and special character (anything other
than alphabetical (a-z and A-Z) digits (0-9) and underscore (_)), it must be
wrapped in quote marks. For example:

```
./plot_mass_spectra_2d.py spectra.mzdata.xml -p spectra.mzdata.xml.png --title my title # NOT ok
./plot_mass_spectra_2d.py spectra.mzdata.xml -p spectra.mzdata.xml.png --title "my title" # ok
```

## --dpi

Set output image resolution. default is 300; common values are 72, 100, 150, 300, 600.

## --plot

Set the output file name. If the filename includes and special character
(anything other than alphabetical (a-z and A-Z) digits (0-9) and underscore (_)),
it must be wrapped in quote marks. For example:

```
./plot_mass_spectra_2d.py spectra.mzdata.xml -p spectra plot.png # NOT ok
./plot_mass_spectra_2d.py spectra.mzdata.xml -p "spectra plot.png" # ok
```
