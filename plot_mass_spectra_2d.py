#!/usr/bin/env  python3

import argparse
import base64
import matplotlib
import matplotlib.pyplot
import numpy
import sys
import xml.etree.ElementTree
# custom lib
import mpllayout
#import pylib


def get_args():
	ap = argparse.ArgumentParser()
	ap.add_argument("input", type = str,
		help = "input spectral data in MZData xml format")
	ap.add_argument("--from-time", type = NonNegFloat,
		default = NonNegFloat(0), metavar = "min",
		help = "extract data from this time point (default: 0.0)")
	ap.add_argument("--till-time", type = NonNegFloat,
		default = numpy.inf, metavar = "min",
		help = "extract data till this time point (default: <unlimited>)")
	ap.add_argument("--mz-min", type = NonNegFloat,
		default = NonNegFloat(0), metavar = "float",
		help = "min m/z to extract and plot (default: 0.0)")
	ap.add_argument("--mz-max", type = NonNegFloat,
		default = NonNegFloat(1000), metavar = "float",
		help = "max m/z to extract and plot (default: 1000.0)")
	ap.add_argument("--plot", "-p", type = str, default = "-",
		metavar = "png",
		help = "output image name (default: <stdout>)")
	ap.add_argument("--title", type = str,
		metavar = "str",
		help = "title to show in the plot; by default, the input filename will "
			"be used")
	ap.add_argument("--dpi", type = PosInt, default = 300,
		metavar = "int",
		help = "output image dpi (default: 300)")

	# parse and refine args
	args = ap.parse_args()
	if args.plot == "-":
		args.plot = sys.stdout.buffer
	return args


def main():
	args = get_args()
	plot_spectrum_2d(args.plot, args.input,
		from_time = args.from_time,
		till_time = args.till_time,
		mz_min = args.mz_min,
		mz_max = args.mz_max,
		title = args.title or args.input,
		dpi = args.dpi,
	)
	return


class PosInt(int):
	def __new__(cls, *ka, **kw):
		new = super().__new__(cls, *ka, **kw)
		if new <= 0:
			raise ValueError("%s cannot be 0 or negative, got '%d'"\
				% (cls.__name__, new))
		return new


class NonNegFloat(float):
	def __new__(cls, *ka, **kw):
		new = super().__new__(cls, *ka, **kw)
		if new < 0:
			raise ValueError("%s cannot be negative, got '%f'"\
				% (cls.__name__, new))
		return new


def itersearch_xml_path(node: xml.etree.ElementTree.Element, *tags)\
		-> xml.etree.ElementTree.Element:
	"""
	descends into node children path based on a list of node *tags; report all
	nodes that fit the *tags order;
	"""
	if not tags:
		yield node
	else:
		next_tag, *other_tags = tags
		for c in node:
			if c.tag == next_tag:
				yield from itersearch_xml_path(c, *other_tags)
	return


class MzDataSpectrum(object):
	def __init__(self, id, time: float, mz, inten, *ka, **kw):
		super().__init__(*ka, **kw)
		self.id		= id
		self.time	= time
		if len(mz) != len(inten):
			raise ValueError("mz and intensity must be of the same length")
		self.mz		= numpy.asarray(mz, dtype = float) # ensure dtype
		self.inten	= numpy.asarray(inten, dtype = float) # ensure dtype
		return

	def __len__(self):
		return len(self.mz)

	@classmethod
	def from_etree_node(cls, node: xml.etree.ElementTree.Element):
		if node.tag != "spectrum":
			raise ValueError("input node must be spectra, not '%s'" % node.tag)
		time = cls._etree_node_parse_time(node)
		mz, inten = cls._etree_node_parse_spectrum_data(node)
		ret = cls(
			id		= int(node.get("id")),
			time	= time,
			mz		= mz,
			inten	= inten,
		)
		return ret

	@classmethod
	def _etree_node_parse_time(cls, node: xml.etree.ElementTree.Element):
		for c in itersearch_xml_path(node, "spectrumDesc", "spectrumSettings",
				"spectrumInstrument", "cvParam"):
			if c.get("name") == "TimeInMinutes":
				ret = float(c.get("value"))
				break
		else:
			ret = numpy.nan
		return ret

	@staticmethod
	def _etree_node_decode_mzdata_base64(data_node) -> numpy.ndarray:
		attrib = data_node.attrib
		b = base64.decodebytes(bytes(data_node.text, encoding = "ascii"))
		if attrib["precision"] == "32":
			arr = numpy.frombuffer(b, dtype = numpy.float32)
		elif attrib["precision"] == "64":
			arr = numpy.frombuffer(b, dtype = numpy.float64)
		if len(arr) != int(attrib["length"]):
			raise RuntimeError("expect parsed array length of %s, got %u"\
				% (attrib["length"], len(arr)))
		return numpy.asarray(arr, dtype = float)

	@classmethod
	def _etree_node_parse_spectrum_data(cls, node) -> "mz_array, inten_array":
		for c in itersearch_xml_path(node, "mzArrayBinary", "data"):
			mz		= cls._etree_node_decode_mzdata_base64(c)
		for c in itersearch_xml_path(node, "intenArrayBinary", "data"):
			inten	= cls._etree_node_decode_mzdata_base64(c)
		return mz, inten


class MzDataXML(object):
	def __init__(self, etree: xml.etree.ElementTree.ElementTree, *ka, **kw):
		super().__init__(*ka, **kw)
		self.etree	= etree
		self._assign_main_childrens()
		return

	@classmethod
	def parse(cls, fname):
		new = cls(etree = xml.etree.ElementTree.parse(fname))
		return new
	@property
	def root(self):
		return self.etree.getroot()

	def _assign_main_childrens(self):
		for c in self.root:
			# check for name confliction
			if hasattr(self, c.tag):
				raise RuntimeError("attribute name '%s' has already been used"\
					% c.tag)
			setattr(self, c.tag, c)
		return


def get_all_mzdata_xml_spectra(fname: "mzData.xml") -> list:
	mzdata = MzDataXML.parse(fname)
	ret = list()
	for node in mzdata.spectrumList:
		mz_spec = MzDataSpectrum.from_etree_node(node)
		ret.append(mz_spec)
	return ret

def get_spectra_2d_data(fname, *, time_min, time_max, mz_min, mz_max,
		mz_resolution = 0.5):
	mz = numpy.arange(numpy.floor(mz_min), numpy.ceil(mz_max), mz_resolution)
	# result data
	time_list = list()
	sum_inten = list()
	mzdata_spectra = get_all_mzdata_xml_spectra(fname)
	# this is 'proto' because we may have less rows based on time range
	inten_2d_proto = numpy.empty((len(mzdata_spectra), len(mz)), dtype = float)
	for s in mzdata_spectra:
		# check if in expected time range
		if (s.time < time_min) or (s.time > time_max):
			continue

		inten_2d_proto[len(time_list)] = numpy.interp(mz, xp = s.mz,
			fp = s.inten - s.inten.min())
		time_list.append(s.time)
		sum_inten.append(s.inten.sum())
	# remove unsed data section
	time = numpy.asarray(time_list, dtype = float)
	inten_2d = inten_2d_proto[:len(time_list)]
	assert inten_2d.shape == (len(time), len(mz))

	ret = dict(
		time = time,
		mz = mz,
		inten_2d = inten_2d,
		sum_inten = numpy.array(sum_inten, dtype = float),
	)
	return ret


def create_layout():
	lc = mpllayout.LayoutCreator(
		left_margin		= 0.8,
		right_margin	= 0.2,
		top_margin		= 0.6,
		bottom_margin	= 0.8,
	)

	colorbar_height = 0.2
	colorbar = lc.add_frame("colorbar")
	colorbar.set_anchor("bottomleft")
	colorbar.set_size(8, colorbar_height)

	heatmap_height = 6
	heatmap = lc.add_frame("heatmap")
	heatmap.set_anchor("bottomleft", ref_frame = colorbar,
		ref_anchor = "topleft", offsets = (0, 0.6))
	heatmap.set_anchor("topright", ref_frame = colorbar,
		ref_anchor = "topright", offsets = (0, 0.6 + heatmap_height))

	sum_inten_width = 1
	sum_inten = lc.add_frame("sum_inten")
	sum_inten.set_anchor("bottomleft", ref_frame = heatmap,
		ref_anchor = "bottomright", offsets = (0.2, 0))
	sum_inten.set_anchor("topright", ref_frame = heatmap,
		ref_anchor = "topright", offsets = (0.2 + sum_inten_width, 0))

	# create layout
	layout = lc.create_figure_layout()

	layout["heatmap"].tick_params(
		left = True, labelleft = True,
		right = False, labelright = False,
		bottom = True, labelbottom = True,
		top = False, labeltop = False)

	layout["sum_inten"].tick_params(
		left = True, labelleft = False,
		right = False, labelright = False,
		bottom = False, labelbottom = False,
		top = False, labeltop = False)

	return layout


def plot_spectrum_2d(png, spec_xml, *, from_time, till_time, mz_min, mz_max,
		mz_resolution = 0.5, title = None, dpi = 300):
	# load data
	spectra_data = get_spectra_2d_data(fname = spec_xml,
		time_min = from_time, time_max = till_time,
		mz_min = mz_min, mz_max = mz_max, mz_resolution = mz_resolution
	)
	color = "#00cc1b" # the color shown in the total-intensity-time curve

	# create layout
	layout = create_layout()
	figure = layout["figure"]

	# plot heatmap
	axes = layout["heatmap"]
	s_mz = spectra_data["mz"]
	s_time = spectra_data["time"]
	cmap = matplotlib.pyplot.get_cmap("jet")
	c = numpy.log10(spectra_data["inten_2d"][:-1, :-1])
	pcolor = axes.pcolor(s_mz, s_time, c, cmap = cmap, vmin = 3, vmax = 7)
	# misc
	axes.set_xlim(s_mz.min(), s_mz.max())
	axes.set_ylim(s_time.min(), s_time.max())
	axes.set_xlabel("M/Z", fontsize = 12)
	axes.set_ylabel("retention time (min)", fontsize = 12)

	if title:
		axes.set_title(title, fontsize = 16, color = "#606060")

	# colorbar
	axes = layout["colorbar"]
	cbar = figure.colorbar(pcolor, cax = axes, orientation = "horizontal")
	cbar.outline.set_visible(False)
	cbar.set_label(r"log$_{10}$ intensity", fontsize = 12)

	# sum-inten spectra
	s_sum_inten = spectra_data["sum_inten"]
	axes = layout["sum_inten"]
	axes.plot(s_sum_inten, s_time, linestyle = "-", linewidth = 0.5,
		color = color, zorder = 3)
	axes.fill_betweenx(s_time, 0, s_sum_inten, edgecolor = "none",
		facecolor = color + "40", zorder = 2)
	# misc
	axes.set_xlim(0, s_sum_inten.max() * 1.10)
	axes.set_ylim(s_time.min(), s_time.max())

	# savefig and clean-up
	figure.savefig(png, dpi = dpi)
	matplotlib.pyplot.close()
	return


if __name__ == "__main__":
	main()
