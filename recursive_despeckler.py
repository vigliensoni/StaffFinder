from optparse import OptionParser
import os
from gamera.core import *
init_gamera()

import logging
lg = logging.getLogger('despeckle')
f = logging.Formatter("%(levelname)s %(asctime)s On Line: %(lineno)d %(message)s")
h = logging.StreamHandler()
h.setFormatter(f)

lg.setLevel(logging.DEBUG)
lg.addHandler(h)

def process_directory(working_directory, cc_size, output_directory):
    """
        Performs all the directory processing and methods
    """
    print "\nProcessing directory {0}".format(working_directory)
    
    for dirpath, dirnames, filenames in os.walk(working_directory):
        for f in filenames:
            if f.split('.')[-1] == 'tif':
                img = load_image(os.path.join(dirpath, f))
                onebitimage = img.to_onebit()
                onebitimage.despeckle(int(cc_size))
                output_path = os.path.join(output_directory, f)
                # print onebitimage
                # print (os.path.join(dirpath, f.split('.')[0]+ '_NEW.' + f.split('.')[-1]))
                # onebitimage.save_tiff(os.path.join(dirpath, f.split('.')[0]+ '_NEW.' + f.split('.')[-1]))

                onebitimage.save_tiff(output_path)
                print output_path
            else:
                pass 

if __name__ == "__main__":
    usage = "usage: %prog [options] working_directory despeckle_cc_size output_directory"
    opts = OptionParser(usage = usage)
    options, args = opts.parse_args()
    init_gamera()

    
    if not args:
        opts.error("You must supply arguments to this script as \nworking_directory \ndespeckle_cc_size \noutput_directory")

    process_directory(args[0], args[1], args[2])

    print "\nDone!\n"