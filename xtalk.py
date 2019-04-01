import argparse
from lsst.eotest.sensor.crosstalkTask import CrosstalkTask
from os.path import join, basename
import glob
from lsst.eotest.raft.raft_crosstalk import CrosstalkButler


def main(results_dir, output_dir='./'):

    sensor_list = [('S00', ['024', '025', '030', '031']), 
                   ('S01', ['012', '013', '018', '019']), 
                   ('S02', ['000', '001', '006', '007']), 
                   ('S10', ['026', '027', '032', '033']), 
                   ('S11', ['014', '015', '020', '021']), 
                   ('S12', ['002', '003', '008', '009']), 
                   ('S20', ['028', '029', '034', '035']),
                   ('S21', ['016', '017', '022', '023']), 
                   ('S22', ['004', '005', '010', '011'])]

    sensor_ids = [x[0] for x in sensor_list]
    butler = CrosstalkButler(sensor_ids, output_dir)

    for sensor_id, sensor_pos_keys in sensor_list:

        infiles = sorted(glob.glob(join(results_dir, sensor_id, '{0}_xtalk*.fits'.format(sensor_id))))

        image_dict = {}
        for infile in infiles:
            pos = str(basename(infile).split('_')[-1][:3])
            image_dict[pos] = infile
                  
        gains = {i+1 : 1.0 for i in range(16)}

        butler.sensor_ingest(sensor_id, sensor_pos_keys, image_dict, gains)

    butler.run_all()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('results_dir', type=str)
    parser.add_argument('-o', '--output_dir', default='./', type=str)
    args = parser.parse_args()

    results_dir = args.results_dir
    output_dir = args.output_dir

    main(results_dir, output_dir=output_dir)

    


