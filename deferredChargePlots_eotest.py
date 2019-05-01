class EOTestPlots(object):

    band_pass = QE_Data.band_pass
    prnu_wls = (350, 450, 500, 620, 750, 870, 1000)

    def __init__(self, sensor_id, rootdir='.', output_dir='.',
                 interactive=False, results_file=None, xtalk_file=None):
        self.sensor_id = sensor_id
        self.rootdir = rootdir
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.interactive = interactive
        plot.pylab.interactive(interactive)
        if results_file is None:
            results_file = self._fullpath('%s_eotest_results.fits' % sensor_id)
        if not os.path.exists(results_file):
            raise RuntimeError("EOTestPlots: %s not found" % results_file)
        self.results = EOTestResults(results_file)
        self._qe_data = None
        self._qe_file = self._fullpath('%s_QE.fits' % self.sensor_id)
        self.specs = CcdSpecs(results_file, plotter=self,
                              xtalk_file=xtalk_file, prnu_wls=self.prnu_wls)
        self._linearity_results = None
        self.subplot = Subplot(len(self.results['AMP']))

    def cti_curves(self, maxflux=150000., overscan_file=None, figsize=(8, 6)):

        if overscan_file is None:
            overscan_file = self._fullpath('{0}_overscan_results.fits'.format(self.sensor_id))
        fig = plt.figure(figsize=figsize)

        with fits.open(overscan_file) as overscan:

            fig.add_subplot(1, 1, 1)
            for amp in range(1, 17):
                
                meanrow = overscan[amp].data['MEANROW']
                flux = overscan[amp].data.field['FLUX']
                offset = np.mean(meanrow[:, -20:], axis=1)
                overscan1 = meanrow[:, xmax] - offset
                overscan2 = meanrow[:, xmax+1] - offset
                lastpixel = meanrow[:, xmax-1] - offset
                cti = (overscan1+overscan2)/(xmax*lastpixel)
                index = np.argsort(flux)

                plt.plot(flux[index], cti[index], label='{0}'.format(amp))

            plt.ylim(bottom=5E-8, top=2E-4)
            plt.xlim(left=50.0)
            plt.grid(True, which='major', axis='both')
            plt.xlabel('flux (e-)', fontsize='small')
            plt.ylabel('cti', fontsize='small')
            plt.legend(fontsize='x-small', loc=2)
            plt.title('CTI from EPER, {0}'.format(sensor_id), fontsize='small')
        


        
