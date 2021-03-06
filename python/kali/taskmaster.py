import math
import cmath
import numpy as np
import sys
import os
import psutil
import time
import re
import platform
import types
import cPickle as pickle
import matplotlib.pyplot as plt
import brewer2mpl
import pdb

try:
    import kali.lc
except ImportError:
    print 'Could not import kali.lc! kali may not be setup. Setup kali by sourcing bin/setup.sh'
    sys.exit(1)

try:
    import kali.util.triangle
except ImportError:
    print 'Could not import kali.util.triangle! kali may not be setup. Setup kali by sourcing bin/setup.sh'
    sys.exit(1)


class taskmaster(object):
    """!
\anchor taskmaster_

\brief Fit a set of light curves with a set of models

\section kali_taskmaster_taskmaster_Contents Contents
  - \ref kali_taskmaster_taskmaster_Purpose
  - \ref kali_taskmaster_taskmaster_Initialize
  - \ref kali_taskmaster_taskmaster_Run

  - \ref kali_taskmaster_taskmaster_Example

\section kali_taskmaster_taskmaster_Purpose	Description

\copybrief taskmaster_

The objects that implement CARMA, MBHB, etc... fitting are designed to be reused with multiple different light
curves. taskmaster objects are designed to fit multiple light curves to multiple models, reusing each model
repeatedly

\section kali_taskmaster_taskmaster_Initialize       Initialization
\copydoc \_\_init\_\_

\section kali_taskmaster_taskmaster_Run       Invoking the Task
\copydoc run

\section kali_taskmaster_taskmaster_Example	A complete example of using taskmaster


    """

    def __init__(self, lcs, models=['carma(1,0)'], widthT=0.25, widthF=0.25,
                 save=True, plot=True, ext=None, pdf=False, rerun=False, dpi=300, numoverlay=3,
                 nthreads=psutil.cpu_count(logical=True),
                 nwalkers=25*psutil.cpu_count(logical=False), nsteps=10000,
                 maxEvals=10000, xTol=0.001, mcmcA=2.0):
        self.widthT = widthT
        self.widthF = widthF
        self._save = save
        self._plot = plot
        if ext is None:
            System = platform.system()
            if System == 'Linux':
                self._ext = 'jpg'
            elif System == 'Darwin':
                self._ext = 'png'
        else:
            self._ext = ext
        self._pdf = pdf
        self._rerun = rerun
        self._dpi = dpi
        if numoverlay <= 9:
            self._numoverlay = numoverlay
        else:
            raise ValueError('Cannot overlay more than 9 model fits on lc!')  # colorbrewer only has 9 paired
            # color choices!
        self._lclist = list()
        self._init_models(models, nthreads=nthreads, nwalkers=nwalkers, nsteps=nsteps, maxEvals=maxEvals,
                          xTol=xTol, mcmcA=mcmcA)
        self._init_lcs(lcs)

    @property
    def models(self):
        return self._models

    @property
    def lcs(self):
        return self._lcs

    @property
    def save(self):
        return self._save

    @save.setter
    def save(self, value):
        if isinstance(value, types.BooleanType):
            self._save = value

    @property
    def ext(self):
        return self._ext

    @ext.setter
    def ext(self, value):
        if isinstance(value, types.StringType):
            self._ext = value

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, value):
        if isinstance(value, types.BooleanType):
            self._plot = value

    @property
    def pdf(self):
        return self._pdf

    @pdf.setter
    def pdf(self, value):
        if isinstance(value, types.BooleanType):
            self._pdf = value

    @property
    def rerun(self):
        return self._rerun

    @rerun.setter
    def rerun(self, value):
        if isinstance(value, types.BooleanType):
            self._rerun = value

    @property
    def dpi(self):
        return self._dpi

    @dpi.setter
    def dpi(self, value):
        if isinstance(value, types.IntType):
            self._dpi = value

    @property
    def numoverlay(self):
        return self._numoverlay

    @numoverlay.setter
    def numoverlay(self, value):
        if isinstance(value, types.IntType):
            if value <= 9:
                self._numoverlay = value
            else:
                raise ValueError('Cannot overlay more than 9 model fits on lc!')  # colorbrewer only has 9
                # paired color choices!

    def _init_models(self, models, nthreads, nwalkers, nsteps, maxEvals, xTol, mcmcA):
        if not models:
            raise ValueError('No models specified!')
        self._models = list()
        for model in models:
            model = model.lower()
            kaliRegex = re.compile('kali\.')
            res = re.findall(kaliRegex, model)
            if res:
                model = model.split('.')[1]
            orderRegEx = re.compile('[0-9]+')
            orderList = re.findall(orderRegEx, model)
            if len(orderList) == 2:
                model = model.split('(')[0]
                orderP = int(orderList[0])
                orderQList = [int(orderList[1])]
            elif len(orderList) == 1:
                model = model.split('(')[0]
                orderP = int(orderList[0])
                orderQList = [i for i in xrange(orderP)]
            elif len(orderList) == 0:
                if model != 'mbhb':
                    raise ValueError('Model %s could not be interpreted!'%(original))
                else:
                    orderP = 0
                    orderQList = [0]
            elif len(orderList) > 2:
                raise ValueError('Model %s could not be interpreted!'%(original))
            modulename = 'kali.' + model
            if modulename not in sys.modules:
                try:
                    exec('import ' + modulename)
                except ImportError:
                    print 'Could not import kali.%s! kali may not be setup. \
                    Setup kali by sourcing bin/setup.sh'%(model)
                    sys.exit(1)

            for orderQ in orderQList:
                self._models.append('kali.%s.%sTask(p=%d,q=%d, \
                nthreads=%d, nwalkers=%d, nsteps=%d, \
                maxEvals=%d, xTol=%f, mcmcA=%f)'%(model, model.upper(), orderP, orderQ,
                                                  nthreads, nwalkers, nsteps,
                                                  maxEvals, xTol, mcmcA))

    def _init_lcs(self, lcs):
        self._lcs = list()
        self.lclist = list()
        for lc in lcs:
            if not isinstance(lc, kali.lc.lc):
                raise ValueError('No light curve supplied!')
            else:
                self._lcs.append(lc)
                self._lclist.append(lc.id)
                if not os.path.isdir(os.path.join(lc.path, lc.id)):
                    os.mkdir(os.path.join(lc.path, lc.id))
                with open(os.path.join(lc.path, lc.id, 'kali.res.dat'), 'wb') as f:
                    f.write('Light curve: %s; Band: %s; Redshift: %s\n'%(lc.name, lc.band, lc.z))
                if self.save:
                    with open(os.path.join(lc.path, lc.id, 'kali.lc.pkl'), 'wb') as out:
                        pickle.dump(lc, out)
                if self.plot:
                    lcplot = lc.plot(colory=r'#000000')
                    lcplot.savefig(os.path.join(lc.path, lc.id, 'kali.lc.%s'%(self.ext)), dpi=self.dpi)
                    if self.pdf:
                        lcplot.savefig(os.path.join(lc.path, lc.id, 'kali.lc.pdf'), dpi=self.dpi)
                    plt.close(lcplot)
                    periodplot = lc.plotperiodogram(colory=r'#000000')
                    periodplot.savefig(os.path.join(lc.path, lc.id, 'kali.periodogram.%s'%(self.ext)),
                                       dpi=self.dpi)
                    if self.pdf:
                        periodplot.savefig(os.path.join(lc.path, lc.name, 'kali.periodogram.pdf'),
                                           dpi=self.dpi)
                    plt.close(periodplot)

    def _fit(self, lc, model):
        print 'Fitting lc %s at z = %f to model %s ...'%(lc.id, lc.z, model.id)
        model.clear()
        startTask = time.time()
        model.fit(lc, widthT=self.widthT, widthF=self.widthF)
        stopTask = time.time()
        timeTask = stopTask - startTask
        print 'Fitting took %4.3f s = %4.3f min = %4.3f hrs'%(timeTask,
                                                              timeTask/60.0,
                                                              timeTask/3600.0)
        if self.save:
            pickle.dump(model, open(os.path.join(lc.path, lc.id, '%s.pkl'%(model.id)), 'wb'))
        return model

    def _restore(self, lc, model):
        print 'Restoring fit of lc %s at z = %f to model %s ...'%(lc.id, lc.z, model.id)
        startTask = time.time()
        model = pickle.load(open(os.path.join(lc.path, lc.id, '%s.pkl'%(model.id)), 'rb'))
        stopTask = time.time()
        timeTask = stopTask - startTask
        print 'Restoration took %4.3f s = %4.3f min = %4.3f hrs'%(timeTask,
                                                                  timeTask/60.0,
                                                                  timeTask/3600.0)
        return model

    @staticmethod
    def relativeLikelihood(best, model):
        return math.exp((best - model)/2.0)

    def _reorder(self):
        for lc in self.lcs:
            print 'Re-ordering models based on relative likelihood for lc %s'%(lc.id)
            dicDict = dict()
            dicList = list()
            with open(os.path.join(lc.path, lc.id, 'kali.res.dat'), 'rb') as f:
                f.readline()
                for line in f:
                    words = line.rstrip('\n').split(' ')
                    dicDict[words[1].split(';')[0]] = float(words[3])
                    dicList.append(float(words[3]))
            bestDIC = sorted(dicList)[0]
            with open(os.path.join(lc.path, lc.id, 'kali.res.dat'), 'wb') as f:
                f.write('Light curve: %s; Band: %s; Redshift: %s\n'%(lc.name, lc.band, lc.z))
                for w in sorted(dicDict, key=dicDict.get):
                    relLike = self.relativeLikelihood(bestDIC, dicDict[w])
                    f.write('Model: %s; DIC: %+4.3e; Relative Likelihood: %+4.3e\n'%(w, dicDict[w], relLike))

    def _plotbestfits(self):
        primary = brewer2mpl.get_map('Set1', 'Qualitative', self.numoverlay).hex_colors
        secondary = brewer2mpl.get_map('Pastel1', 'Qualitative', self.numoverlay).hex_colors
        for lc in self.lcs:
            print 'Plotting %d-best overlaid light curves for lc %s'%(self.numoverlay, lc.id)
            lc.removesmooth()
            lcplot = lc.plot(fig=100, colory=r'#000000')
            with open(os.path.join(lc.path, lc.id, 'kali.res.dat'), 'r') as f:
                f.readline()
                linecounter = 0
                for line in f:
                    if linecounter == self.numoverlay:
                        break
                    words = line.rstrip('\n').split(' ')
                    infile = os.path.join(lc.path, lc.id, '%s.pkl'%(words[1].split(';')[0]))
                    if os.path.isfile(infile):
                        model = pickle.load(open(infile, 'rb'))
                        print 'Plotting overlaid light curve for model %s'%(model.id)
                        model.set(lc.dt, model.bestTheta)
                        model.smooth(lc, stopT=(lc.t[-1] + lc.T*0.5))
                        lc.plot(fig=100, colory=r'#000000',
                                colors=[primary[linecounter], secondary[linecounter]], labely='none',
                                labels=r'%s fit'%(model.id), clearFig=False)
                    linecounter += 1
            if self.plot:
                if not os.path.isfile(os.path.join(lc.path, lc.id, 'kali.comp.%s'%(self.ext))):
                    lcplot.savefig(os.path.join(lc.path, lc.id, 'kali.comp.%s'%(self.ext)),
                                   dpi=self.dpi)
                if self.pdf:
                    if not os.path.isfile(os.path.join(lc.path, lc.id, 'kali.comp.pdf')):
                        lcplot.savefig(os.path.join(lc.path, lc.id, 'kali.comp.pdf'),
                                       dpi=self.dpi)
            plt.close(lcplot)

    def run(self):
        for modelexec in self.models:
            exec('model = %s'%(modelexec))
            for lc in self.lcs:
                if self.rerun:
                    model = self._fit(lc, model)
                else:
                    outfile = os.path.join(lc.path, lc.id, '%s.pkl'%(model.id))
                    if os.path.isfile(outfile):
                        model = self._restore(lc, model)
                    else:
                        model = self._fit(lc, model)
                with open(os.path.join(lc.path, lc.id, 'kali.res.dat'), 'ab') as f:
                    f.write('Model: %s; DIC: %+17.16e\n'%(model.id, model.dic))
                model.set(lc.dt, model.bestTheta)
                model.smooth(lc)
                if self.save:
                    if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_kali.lc.pkl'%(model.id))):
                        with open(os.path.join(lc.path, lc.id, '%s_kali.lc.pkl'%(model.id)), 'wb') as out:
                            pickle.dump(lc, out)
                if self.plot:
                    lcplot = lc.plot(colory=r'#000000')
                    if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_kali.lc.%s'%(model.id, self.ext))):
                        lcplot.savefig(os.path.join(lc.path, lc.id, '%s_kali.lc.%s'%(model.id, self.ext)),
                                       dpi=self.dpi)
                    if self.pdf:
                        if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_kali.lc.pdf'%(model.id))):
                            lcplot.savefig(os.path.join(lc.path, lc.id, '%s_kali.lc.pdf'%(model.id)),
                                           dpi=self.dpi)
                    plt.close(lcplot)
                    res = model.plottriangle()
                    if len(res) == 1:
                        if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_sto.%s'%(model.id, self.ext))):
                            res[0][0].savefig(os.path.join(lc.path, lc.id, '%s_sto.%s'%(model.id, self.ext)),
                                              dpi=self.dpi)
                        if self.pdf:
                            if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_sto.pdf'%(model.id))):
                                res[0][0].savefig(os.path.join(lc.path, lc.id, '%s_sto.pdf'%(model.id)),
                                                  dpi=self.dpi)
                        plt.close(res[0][0])
                    elif len(res) == 2:
                        if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_orb.%s'%(model.id, self.ext))):
                            res[0][0].savefig(os.path.join(lc.path, lc.id, '%s_orb.%s'%(model.id, self.ext)),
                                              dpi=self.dpi)
                        if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_aux.%s'%(model.id, self.ext))):
                            res[1][0].savefig(os.path.join(lc.path, lc.id, '%s_aux.%s'%(model.id, self.ext)),
                                              dpi=self.dpi)
                        if self.pdf:
                            if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_orb.pdf'%(model.id))):
                                res[0][0].savefig(os.path.join(lc.path, lc.id, '%s_orb.pdf'%(model.id)),
                                                  dpi=self.dpi)
                            if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_aux.pdf'%(model.id))):
                                res[1][0].savefig(os.path.join(lc.path, lc.id, '%s_aux.pdf'%(model.id)),
                                                  dpi=self.dpi)
                        plt.close(res[0][0])
                        plt.close(res[1][0])
                    elif len(res) == 3:
                        if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_sto.%s'%(model.id, self.ext))):
                            res[0][0].savefig(os.path.join(lc.path, lc.id, '%s_sto.%s'%(model.id, self.ext)),
                                              dpi=self.dpi)
                        if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_orb.%s'%(model.id, self.ext))):
                            res[1][0].savefig(os.path.join(lc.path, lc.id, '%s_orb.%s'%(model.id, self.ext)),
                                              dpi=self.dpi)
                        if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_aux.%s'%(model.id, self.ext))):
                            res[2][0].savefig(os.path.join(lc.path, lc.id, '%s_aux.%s'%(model.id, self.ext)),
                                              dpi=self.dpi)
                        if self.pdf:
                            if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_sto.pdf'%(model.id))):
                                res[0][0].savefig(os.path.join(lc.path, lc.id, '%s_sto.pdf'%(model.id)),
                                                  dpi=self.dpi)
                            if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_orb.pdf'%(model.id))):
                                res[1][0].savefig(os.path.join(lc.path, lc.id, '%s_orb.pdf'%(model.id)),
                                                  dpi=self.dpi)
                            if not os.path.isfile(os.path.join(lc.path, lc.id, '%s_aux.pdf'%(model.id))):
                                res[2][0].savefig(os.path.join(lc.path, lc.id, '%s_aux.pdf'%(model.id)),
                                                  dpi=self.dpi)
                        plt.close(res[0][0])
                        plt.close(res[1][0])
                        plt.close(res[2][0])
            del model
        self._reorder()
        self._plotbestfits()
