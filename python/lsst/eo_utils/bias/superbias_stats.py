"""Class to analyze the variation in the bias images"""

import os

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables,\
    get_run_config_table

from lsst.eo_utils.base.file_utils import SUPERBIAS_STAT_FORMATTER

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_raw_image, get_amp_list

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .meta_analysis import  SuperbiasRaftTableAnalysisConfig,\
    SuperbiasRaftTableAnalysisTask,\
    SuperbiasSummaryAnalysisConfig, SuperbiasSummaryAnalysisTask


class SuperbiasStatsConfig(SuperbiasRaftTableAnalysisConfig):
    """Configuration for SuperbiasStatsTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='')
    filekey = EOUtilOptions.clone_param('filekey', default='stats')
    stat = EOUtilOptions.clone_param('stat', default='stdevclip')


class SuperbiasStatsTask(SuperbiasRaftTableAnalysisTask):
    """Analyze the variation in the bias images"""

    ConfigClass = SuperbiasStatsConfig
    _DefaultName = "SuperbiasStatsTask"

    intablename_format = SUPERBIAS_STAT_FORMATTER

    plot_names = ['mean', 'std']

    def extract(self, butler, data, **kwargs):
        """Extract the statistics from the superbias frames

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
            The resulting data
        """
        self.safe_update(**kwargs)
        if butler is not None:
            self.log.warn("Ignoring butler")

        stats_data = {}

        self.log_info_raft_msg(self.config, "")

        slot_list = self.config.slots
        if slot_list is None:
            slot_list = ALL_SLOTS

        for islot, slot in enumerate(slot_list):

            superbias_file = data[slot]
            if self.config.stat is not None:
                superbias_file = superbias_file.replace('_superbias_', '_%s_' % self.config.stat)

            if not os.path.exists(superbias_file):
                self.log.warn("Skipping missing file for %s:%s" % (self.config.raft, slot))
                continue

            self.log_progress("  %s" % slot)

            mask_files = self.get_mask_files(slot=slot)

            try:
                superbias_frame = self.get_ccd(None, superbias_file, mask_files)
            except Exception:
                self.log.warn("Skipping %s:%s:%s" % (self.config.run, self.config.raft, slot))
                superbias_frame = None
            self.get_superbias_stats(superbias_frame, stats_data, islot)

        self.log_progress("Done!")

        if not stats_data:
            return None

        stats_data['slot'] = np.arange(9)

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, slot_list))
        dtables.make_datatable('stats', stats_data)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the stats on the superbias frames

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        data = dtables.get_table('stats')

        figs.plot_stat_color("mean", data['mean'], clabel="Mean of STD [ADU]")
        figs.plot_stat_color("std", data['std'], clabel="STD of STD [ADU]")


    @staticmethod
    def get_superbias_stats(superbias, stats_data, islot):
        """Get the serial overscan data

        Parameters
        ----------
        butler : `Butler`
            The data butler
        superbias : `MaskedCCD`
            The ccd we are getting data from
        stats_data : `dict`
            The data we are updating

        Keywords
        --------
        islot : `int`
            The slot index
        """
        if 'mean' not in stats_data:
            stats_data['mean'] = np.zeros((9, 16))
            stats_data['median'] = np.zeros((9, 16))
            stats_data['std'] = np.zeros((9, 16))
            stats_data['min'] = np.zeros((9, 16))
            stats_data['max'] = np.zeros((9, 16))

        if superbias is None:
            return

        amps = get_amp_list(superbias)
        for i, amp in enumerate(amps):

            img = get_raw_image(superbias, amp).image
            stats_data['mean'][islot, i] = img.array.mean()
            stats_data['median'][islot, i] = np.median(img.array)
            stats_data['std'][islot, i] = img.array.std()
            stats_data['min'][islot, i] = img.array.min()
            stats_data['max'][islot, i] = img.array.max()


class SuperbiasSummaryConfig(SuperbiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOScanSummaryTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='stats')
    filekey = EOUtilOptions.clone_param('filekey', default='sum')
    dataset = EOUtilOptions.clone_param('dataset')
    stat = EOUtilOptions.clone_param('stat', default='stdevclip')


class SuperbiasSummaryTask(SuperbiasSummaryAnalysisTask):
    """Summarize the results for the analysis of variations of the bias frames"""

    ConfigClass = SuperbiasSummaryConfig
    _DefaultName = "SuperbiasSummaryTask"

    plot_names = ['stats', 'stats_<RAFT>']

    def extract(self, butler, data, **kwargs):
        """Make a summary table of the superbias statistics

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
            The resulting data
        """
        self.safe_update(**kwargs)

        if butler is not None:
            self.log.warn("Ignoring butler")

        run_dict = dict(runs=[], rafts=[])
        for key, val in sorted(data.items()):
            run_dict['runs'].append(key[4:])
            run_dict['rafts'].append(key[0:3])
            data[key] = val.replace(self.config.filekey, self.config.infilekey)

        outtable = vstack_tables(data, tablename='stats')

        dtables = TableDict()
        dtables.add_datatable('stats', outtable)
        dtables.make_datatable('runs', run_dict)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the superbias statistics study

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

        #config_table = get_run_config_table(kwargs.get('config_table', 'seq_list.fits'), 'seq')
        config_table = get_run_config_table(kwargs.get('config_table', 'nbias_full_bot.fits'), 'nbias')

        sumtable = dtables['stats']
        if self.config.teststand == 'ts8':
            runtable = dtables['runs']
            yvals = sumtable['mean'].flatten().clip(0., 30.)
            yerrs = sumtable['std'].flatten().clip(0., 10.)
            runs = runtable['runs']
            figs.plot_run_chart("stats", runs, yvals, yerrs=yerrs, ylabel="Superbias STD [ADU]")
        elif self.config.teststand == 'bot':
            rafts = np.unique(sumtable['raft'].flatten())
            for raft in rafts:
                mask = sumtable['raft'].flatten() == raft
                subtable = sumtable[mask]
                figs.plot_run_chart_by_slot("stats_%s" % raft, subtable,
                                            "mean", #yerrs="std",
                                            ylabel="Superbias STD [ADU]",
                                            ymin=0., ymax=10.,
                                            raft='nbias',
                                            config_table=config_table)


EO_TASK_FACTORY.add_task_class('SuperbiasStats', SuperbiasStatsTask)
EO_TASK_FACTORY.add_task_class('SuperbiasSummary', SuperbiasSummaryTask)
