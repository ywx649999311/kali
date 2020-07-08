#!/bin/bash
source /opt/intel/mkl/bin/mklvars.sh intel64
source /home/kali/bin/setup.sh
jupyter lab --ip=0.0.0.0 --NotebookApp.token='' --no-browser --allow-root
