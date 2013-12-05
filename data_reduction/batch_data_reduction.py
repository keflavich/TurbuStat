
'''

Runs data_reduc on all data cubes in the file.
Creates a folder for each data cube and its products
Run from folder containing data cubes

'''

from data_reduc import *
from astropy.io.fits import getdata
import os
import sys
import errno
import shutil
from datetime import datetime

## Read files in the folder
data_cubes = [x for x in os.listdir(".") if os.path.isfile(x) and x[-4:]=="fits"]
print data_cubes

logfile = open("".join([data_cubes[0][:-14],"_reductionlog",".txt"]), "w+")

for fitscube in data_cubes:

    filestr = "Reducing %s \n" % (fitscube)
    print filestr
    print str(datetime.now())
    logfile.write(filestr)
    logfile.write("".join([str(datetime.now()),"\n"]))

    try:
        os.makedirs(fitscube[:-5])
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            logfile.write(OSError)
            logfile.close()
            raise


    shutil.move(fitscube, fitscube[:-5])
    os.chdir(fitscube[:-5])

    cube, header = getdata(fitscube, header=True)

    # if np.isnan(cube.sum(axis=0)[:,cube.shape[2]]).shape[1] == cube.shape[2]:
    cube[:,:,cube.shape[2]-1] = cube[:,:,0]
    # elif np.isnan(cube.sum(axis=0)[cube.shape[1],:]).shape[1] == cube.shape[1]:
    cube[:,cube.shape[1]-1,:] = cube[:,0,:]

    reduction = property_arrays((cube,header), rms_noise=0.001, save_name=fitscube[:-5])

    reduction.return_all()


    ## Clean up
    cube, header = None, None
    reduction = None
    os.chdir("..")

print "Done!\n  "
print str(datetime.now())
logfile.write("Done!")
logfile.write("".join([str(datetime.now()),"\n"]))
logfile.close()
