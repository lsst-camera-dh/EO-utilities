"""This module manage the default settings for eo_utils module"""


# Location of various butler Repos
BUTLER_TS8_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/ts8'
BUTLER_BOT_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/bot'
BUTLER_TS8_NCSA_REPO = '/datasets/ts8/repo'
BUTLER_BOT_NCSA_REPO = '/datasets/bot/repo'

# Location of slac archive
ARCHIVE_SLAC = '/gpfs/slac/lsst/fs*/g/data/jobHarness/jh_archive*'

# Map the Butler repos to simple names
BUTLER_REPO_DICT = dict(TS8=BUTLER_TS8_REPO,
                        BOT=BUTLER_BOT_REPO,
                        TS8_NCSA=BUTLER_TS8_NCSA_REPO,
                        BOT_NCSA=BUTLER_BOT_NCSA_REPO)

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



# These are the standard input filenames
TS8_GLOB_STRING =\
    '{archive}/LCA-11021_RTM/LCA-11021_{raft}*/{run}/{testName}/v0/*/{slot}/*{imgtype}*.fits'
BOT_GLOB_STRING =\
    '{archive}/LCA-10134_Cryostat/LCA-10134_Cryostat-0001/{run}/' +\
    'BOT_acq/v0/*/{testName}*{imgtype}*/MC_C*{raft}_{slot}.fits'

# These strings define the standard output filenames
SLOT_FORMAT_STRING = '{outdir}/{fileType}/{raft}/{testType}/{raft}-{run}-{slot}{suffix}'
RAFT_FORMAT_STRING = '{outdir}/{fileType}/{raft}/{testType}/{raft}-{run}-RFT{suffix}'
SUMMARY_FORMAT_STRING = '{outdir}/{fileType}/summary/{testType}/{dataset}{suffix}'
SUPERBIAS_FORMAT_STRING =\
    '{outdir}/superbias/{raft}/{raft}-{run}-{slot}_superbias_b-{bias}{suffix}'
SUPERBIAS_STAT_FORMAT_STRING =\
    '{outdir}/superbias/{raft}/{raft}-{run}-{slot}_{stat}_b-{bias}{suffix}'




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


# Template to make superbias files
SBIAS_TEMPLATE = 'analysis/superbias/templates/sbias_template.fits'
SFLAT_TEMPLATE = 'analysis/superflat/templates/sflat_template.fits'
SDARK_TEMPLATE = 'analysis/superdark/templates/sdark_template.fits'


# Some default values
DEFAULT_OUTDIR = 'analysis'
DEFAULT_STAT_TYPE = 'median'
DEFAULT_BITPIX = -32
DEFAULT_BIAS_TYPE = 'spline'
DEFAULT_SUPERBIAS_TYPE = None
DEFAULT_LOGFILE = 'temp.log'
DEFAULT_NBINS = 100
DEFAULT_BATCH_ARGS = "-W 1200 -R bullet"
