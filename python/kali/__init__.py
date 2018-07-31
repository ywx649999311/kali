"""Init file."""
import os
from shutil import copy
import matplotlib as mpl
import matplotlib.style
import matplotlib.pyplot
from kali.util.mpl_settings import plot_params

# mpl style path
confi_dir = mpl.get_configdir()
kali_dir = os.environ['KALI']
style_path = os.path.join(confi_dir, 'stylelib/')

# check path exists, if not, create
if not os.path.exists(style_path):
    os.makedirs(style_path)

# check if style copied, if not, copy and update library
if not os.path.exists(os.path.join(style_path, 'kali.mplstyle')):
    copy(os.path.join(kali_dir, 'python/kali/util/kali.mplstyle'), style_path)
    mpl.pyplot.style.reload_library()

# default to use 'kali' style
mpl.style.use('kali')
