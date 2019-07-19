"""This module manage the default settings for eo_utils module"""

import os

# Package location
EO_PACKAGE_BASE = os.path.abspath(os.path.join(__file__, '..', '..', '..', '..', '..'))

# SITE DEPENDENT STUFF
SITE = os.environ.get('EO_UTILS_SITE', 'slac')

if SITE == 'slac':
    BUTLER_TS8_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/ts8'
    BUTLER_BOT_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/bot'
    ARCHIVE_DIR = '/gpfs/slac/lsst/fs*/g/data/jobHarness/jh_archive*'
    DEFAULT_BATCH_ARGS = '-W 1200 -R bullet'
    BATCH_SYSTEM = 'lsf'
elif SITE == 'ncsa':
    BUTLER_TS8_REPO = '/datasets/ts8/repo'
    BUTLER_BOT_REPO = '/project/production/tmpdataloc/BOT/gen2repo'
    ARCHIVE_DIR = None
    DEFAULT_BATCH_ARGS = ""
    BATCH_SYSTEM = 'slurm'

# Map the Butler repos to simple names
BUTLER_REPO_DICT = dict(TS8=BUTLER_TS8_REPO,
                        BOT=BUTLER_BOT_REPO)

# The slots
ALL_SLOTS = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
# The rafts
ALL_RAFTS = ["R10", "R22"]


# Various types of tests
TS8_MASK_TEST_TYPES = ['bright_pixel_mask',
                       'dark_pixel_mask',
                       'rolloff_defects_mask',
                       'traps_mask']
BOT_MASK_TEST_TYPES = ['fe55_analysis_BOT',
                       'pixel_defects_BOT']


BUTLER_TEST_TYPES = ['DARK', 'FLAT', 'FE55', 'PPUMP', 'SFLAT', 'LAMBDA', 'TRAP']
DATACAT_TS8_TEST_TYPES = ['fe55_raft_acq',
                          'flat_pair_raft_acq',
                          'sflat_raft_acq',
                          'qe_raft_acq',
                          'dark_raft_acq']
DATACAT_BOT_TEST_TYPES = ['DARK', 'FLAT', 'FE55', 'PPUMP', 'SFLAT', 'LAMBDA', 'TRAP']




# These readout times, in seconds
T_SERIAL = 2e-06
T_PARALLEL = 40e-06

# Plot the different test types differently
TESTCOLORMAP = dict(DARK="black",
                    FLAT="blue",
                    TRAP="red",
                    LAMBDA="magenta",
                    SFLAT="green",
                    SFLAT_500="green",
                    FE55="cyan")


# Some default values
DEFAULT_OUTDIR = 'analysis/ts8'
DEFAULT_STAT_TYPE = 'median'
DEFAULT_BITPIX = -32
DEFAULT_BIAS_TYPE = 'spline'
DEFAULT_SUPERBIAS_TYPE = None
DEFAULT_LOGFILE = 'temp.log'
DEFAULT_NBINS = 100
