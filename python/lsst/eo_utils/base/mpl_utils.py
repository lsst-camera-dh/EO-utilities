#!/usr/bin/env python

# -*- python -*-

"""A standalone file with a function to initialize matplotlib that works for either
interactive or batch processing"""

import os

def init_matplotlib_backend(backend=None):
    """This function initializes the matplotlib backend.  When no
    DISPLAY is available the backend is automatically set to 'Agg'.

    Parameters
    ----------
    backend : `str`
        matplotlib backend name to use in interactive mode
    """

    import matplotlib

    if 'MPLBACKEND' in os.environ:
        return

    try:
        os.environ['DISPLAY']
    except KeyError:
        matplotlib.use('Agg')
    else:
        if backend is not None:
            matplotlib.use(backend)


def set_plt_ioff():
    """Set interactive plotting off"""
    import matplotlib.pyplot as plt
    plt.ioff()


init_matplotlib_backend()
