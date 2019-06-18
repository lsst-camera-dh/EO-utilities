"""Class to analyze the FFT of the bias frames"""

from lsst.eotest.sensor.DetectorResponse import DetectorResponse

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .meta_analysis import FlatRaftTableAnalysisConfig, FlatRaftTableAnalysisTask


class FlatLinearityConfig(FlatRaftTableAnalysisConfig):
    """Configuration for FlatLinearityTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='flat')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='flat_lin')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class FlatLinearityTask(FlatRaftTableAnalysisTask):
    """Extract summary statistics from the data"""

    ConfigClass = FlatLinearityConfig
    _DefaultName = "FlatLinearityTask"

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

        self.log_info_raft_msg(self.config, "")

        for islot, slot in enumerate(ALL_SLOTS):

            self.log_progress("  %s" % slot)

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

        self.log_progress("Done!")

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
