"""This module manage the default settings for eo_utils module"""

import os

import sys

# Package location
EO_PACKAGE_BASE = os.path.abspath(os.path.join(__file__, '..', '..', '..', '..', '..'))

DEFAULT_CALIB_FILE = os.path.join(EO_PACKAGE_BASE, 'templates', 'calib_flavor.yaml')


# SITE DEPENDENT STUFF
SITE = os.environ.get('EO_UTILS_SITE', 'slac')

if SITE == 'slac':
    BUTLER_TS8_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/ts8'
    BUTLER_BOT_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/bot_etu'
    BUTLER_GEN3_REPO = '/sdf/group/lsst/camera/IandT/repo_gen3/test/butler.yaml'
    ARCHIVE_DIR = '/gpfs/slac/lsst/fs*/g/data/jobHarness/jh_stage*'
    DEFAULT_DATA_SOURCE = os.environ.get('EO_DATA_SOURCE', 'glob')
    DEFAULT_BATCH_ARGS = '-W 1200 -R bubble'
    BATCH_SYSTEM = 'lsf'
elif SITE == 'rd':
    BUTLER_TS8_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/ts8'
    BUTLER_BOT_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/bot_etu'
    ARCHIVE_DIR = 'data_links'
    DEFAULT_DATA_SOURCE = os.environ.get('EO_DATA_SOURCE', 'glob')
    DEFAULT_BATCH_ARGS = '-W 1200 -R bubble'
    BATCH_SYSTEM = 'lsf'
elif SITE == 'ncsa':
    BUTLER_TS8_REPO = '/datasets/ts8/repo'
    BUTLER_BOT_REPO = '/project/production/tmpdataloc/BOT/gen2repo'
    ARCHIVE_DIR = None
    DEFAULT_BATCH_ARGS = ""
    DEFAULT_DATA_SOURCE = os.environ.get('EO_DATA_SOURCE', 'butler_file')
    BATCH_SYSTEM = 'slurm'
else:
    raise ValueError("Unknown site %s" % SITE)


# TEST
DEFAULT_TESTSTAND = os.environ.get('EO_TESTSTAND', 'bot')

if os.environ.get('EO_PRINT_OPTS', False):
    sys.stdout.write("SITE=%s\n" % SITE)
    sys.stdout.write("DEFAULT_TESTSTAND=%s\n" % DEFAULT_TESTSTAND)
    sys.stdout.write("DEFAULT_DATA_SOURCE=%s\n" % DEFAULT_DATA_SOURCE)



# Map the Butler repos to simple names
BUTLER_REPO_DICT = dict(ts8=BUTLER_TS8_REPO,
                        bot=BUTLER_BOT_REPO,
                        gen3=BUTLER_GEN3_REPO)

# The amps
ALL_AMPS = ['C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'C17',
            'C07', 'C06', 'C05', 'C04', 'C03', 'C02', 'C01', 'C00']

# The slots
ALL_SLOTS = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
CORNER_SLOTS = ['SG0', 'SG1', 'SW0', 'SW1']

# The rafts
ALL_RAFTS_BOT_ETU = ['R10', 'R22']
CORNER_RAFTS = ['R00', 'R04', 'R40', 'R44']
NINE_RAFTS = ['R01', 'R02', 'R10',
              'R11', 'R12', 'R20',
              'R21', 'R22', 'R30']
SCIENCE_RAFTS = ['R01', 'R02', 'R03',
                 'R10', 'R11', 'R12', 'R13', 'R14',
                 'R20', 'R21', 'R22', 'R23', 'R24',
                 'R30', 'R31', 'R32', 'R33', 'R34',
                 'R41', 'R42', 'R43']
NINE_AND_CORNER_RAFTS = NINE_RAFTS + CORNER_RAFTS
BOT_RAFTS = SCIENCE_RAFTS + CORNER_RAFTS

RAFT_NAMES_DICT = dict(bot_etu=ALL_RAFTS_BOT_ETU,
                       bot_9=NINE_RAFTS,
                       bot=BOT_RAFTS)

# Various types of tests
TS8_MASK_TEST_TYPES = ['bright_pixel_mask',
                       'dark_pixel_mask',
                       'rolloff_defects_mask',
                       'traps_mask']
BOT_MASK_TEST_TYPES = ['fe55_analysis_BOT',
                       'pixel_defects_BOT']


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
DEFAULT_OUTDIR = 'analysis'
DEFAULT_STAT_TYPE = 'median'
DEFAULT_BITPIX = -32
DEFAULT_BIAS_TYPE = 'spline'
DEFAULT_SUPERBIAS_TYPE = None
DEFAULT_LOGFILE = 'eo_util_log/temp.log'
DEFAULT_NBINS = 100


# Get the list of slots for a given raft
def getSlotList(raftName):
    if raftName in CORNER_RAFTS:
        return CORNER_SLOTS
    return ALL_SLOTS
