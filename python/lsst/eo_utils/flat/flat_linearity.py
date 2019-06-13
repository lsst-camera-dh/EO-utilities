"""Class to analyze the FFT of the bias frames"""

import sys

from lsst.eotest.sensor.DetectorResponse import DetectorResponse

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.flat.file_utils import SLOT_FLAT_TABLE_FORMATTER,\
    RAFT_FLAT_TABLE_FORMATTER, RAFT_FLAT_PLOT_FORMATTER

from lsst.eo_utils.flat.analysis import FlatAnalysisConfig, FlatAnalysisTask


class FlatLinearityConfig(FlatAnalysisConfig):
    """Configuration for FlatLinearityTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='flat')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='flat_lin')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class FlatLinearityTask(FlatAnalysisTask):
    """Extract summary statistics from the data"""

    ConfigClass = FlatLinearityConfig
    _DefaultName = "FlatLinearityTask"
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
                         amp=[],
                         full_well=[],
                         max_dev=[])

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace(self.config.outsuffix, self.config.insuffix)

            detresp = DetectorResponse(datapath, hdu_name='flat')

            for amp in range(1, 17):

                # Here you can get the data out for each amp and append it to the
                # data_dict

                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)
                linearity_data = detresp.linearity(amp)
                full_well_data = detresp.full_well(amp)

                data_dict['full_well'].append(full_well_data[0])
                data_dict['max_dev'].append(linearity_data[0])

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("flat_lin", data_dict)
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


EO_TASK_FACTORY.add_task_class('FlatLinearity', FlatLinearityTask)
