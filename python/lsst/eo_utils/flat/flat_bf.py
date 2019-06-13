"""Class to analyze the FFT of the bias frames"""

import sys

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

from lsst.eotest.sensor.BFTask import crossCorrelate_images

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_amp_list,\
    get_geom_regions, get_raw_image, unbias_amp

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.flat.file_utils import SLOT_FLAT_TABLE_FORMATTER,\
    RAFT_FLAT_TABLE_FORMATTER, RAFT_FLAT_PLOT_FORMATTER

from lsst.eo_utils.flat.analysis import FlatAnalysisConfig, FlatAnalysisTask


class BFConfig(FlatAnalysisConfig):
    """Configuration for BFTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='bf')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    maxLag = EOUtilOptions.clone_param('maxLag')
    nSigmaClip = EOUtilOptions.clone_param('nSigmaClip')
    backgroundBinSize = EOUtilOptions.clone_param('backgroundBinSize')


class BFTask(FlatAnalysisTask):
    """Analyze some flat data"""

    ConfigClass = BFConfig
    _DefaultName = "BFTask"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        FlatAnalysisTask.__init__(self, **kwargs)
        self.stat_ctrl = afwMath.StatisticsControl()

    def mean(self, img):
        """Return the mean of an image"""
        return afwMath.makeStatistics(img, afwMath.MEAN, self.stat_ctrl).getValue()

    def extract(self, butler, data, **kwargs):
        """Extract data

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            Output data tables
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        flat1_files = data['FLAT1']
        flat2_files = data['FLAT2']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        gains = None

        sys.stdout.write("Working on %s, %i files: " % (slot, len(flat1_files)))
        sys.stdout.flush()

        # This is a dictionary of dictionaries to store all the
        # data you extract from the flat_files
        data_dict = {}
        for i in range(1, 17):
            data_dict['AMP%02i_MEAN' % i] = []
            data_dict['AMP%02i_XCORR' % i] = []
            data_dict['AMP%02i_YCORR' % i] = []
            data_dict['AMP%02i_XCORR_ERR' % i] = []
            data_dict['AMP%02i_YCORR_ERR' % i] = []

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        for i, (id_1, id_2) in enumerate(zip(flat1_files, flat2_files)):
            
            if i > 2:
                break
            if i % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            flat_1 = get_ccd_from_id(butler, id_1, [])
            flat_2 = get_ccd_from_id(butler, id_2, [])

            amps = get_amp_list(butler, flat_1)

            for i, amp in enumerate(amps):
                regions = get_geom_regions(butler, flat_1, amp)
                serial_oscan = regions['serial_overscan']
                imaging = regions['imaging']
                #imaging.grow(-20)
                im_1 = get_raw_image(butler, flat_1, amp)
                im_2 = get_raw_image(butler, flat_2, amp)

                if superbias_frame is not None:
                    if butler is not None:
                        superbias_im = get_raw_image(None, superbias_frame, amp+1)
                    else:
                        superbias_im = get_raw_image(None, superbias_frame, amp)
                else:
                    superbias_im = None

                image_1 = unbias_amp(im_1, serial_oscan, bias_type=self.config.bias,
                                     superbias_im=superbias_im, region=imaging)
                image_2 = unbias_amp(im_2, serial_oscan, bias_type=self.config.bias,
                                     superbias_im=superbias_im, region=imaging)

                avemean = (self.mean(image_1) + self.mean(image_2)) / 2.

                corr, corr_err = crossCorrelate_images(image_1, image_2,
                                                       self.config.maxLag,
                                                       self.config.nSigmaClip,
                                                       self.config.backgroundBinSize)
                                
                data_dict['AMP%02i_MEAN' % (i+1)].append(avemean)
                data_dict['AMP%02i_XCORR' % (i+1)].append(corr[1][0]/corr[0][0])
                data_dict['AMP%02i_YCORR' % (i+1)].append(corr[0][1]/corr[0][0])
                data_dict['AMP%02i_XCORR_ERR' % (i+1)].append(corr_err[1][0])
                data_dict['AMP%02i_YCORR_ERR' % (i+1)].append(corr_err[0][1])

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, flat1_files + flat2_files))
        dtables.make_datatable('bf', data_dict)

        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots 

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """        
        self.safe_update(**kwargs)

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


class BFStatsConfig(FlatAnalysisConfig):
    """Configuration for BFStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='bf')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='bf_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class BFStatsTask(FlatAnalysisTask):
    """Extract summary statistics from the data"""

    ConfigClass = BFStatsConfig
    _DefaultName = "BFStatsTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_FLAT_TABLE_FORMATTER
    tablename_format = RAFT_FLAT_TABLE_FORMATTER
    plotname_format = RAFT_FLAT_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        FlatAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Extract data

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            Output data tables
        """
        self.safe_update(**kwargs)

        # You should expand this to include space for the data you want to extract
        data_dict = dict(slot=[],
                         amp=[])

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace(self.config.outsuffix, self.config.insuffix)

            dtables = TableDict(datapath)

            for amp in range(16):

                # Here you can get the data out for each amp and append it to the
                # data_dict

                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("bf", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data 

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


EO_TASK_FACTORY.add_task_class('BF', BFTask)
EO_TASK_FACTORY.add_task_class('BFStats', BFStatsTask)
