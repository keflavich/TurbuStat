# Licensed under an MIT open source license - see LICENSE


'''

Function for calculating statistics for sensitivity analysis

'''


import numpy as np
from turbustat.io import fromfits
import sys
import os
from datetime import datetime

keywords = {"centroid", "centroid_error", "integrated_intensity",
            "integrated_intensity_error", "linewidth",
            "linewidth_error", "moment0", "moment0_error", "cube"}

## Load each statistic in

from turbustat.statistics import Wavelet_Distance

from turbustat.statistics import MVC_distance

from turbustat.statistics import PSpec_Distance, BiSpectrum_Distance

from turbustat.statistics import GenusDistance

from turbustat.statistics import DeltaVariance_Distance

from turbustat.statistics import VCA_Distance, VCS_Distance

from turbustat.statistics import Tsallis_Distance

from turbustat.statistics import StatMomentsDistance

from turbustat.statistics import PCA_Distance

from turbustat.statistics import SCF_Distance

from turbustat.statistics import Cramer_Distance

from turbustat.statistics import DendroDistance


## Wrapper function
def wrapper(dataset1, dataset2, fiducial_models=None,
            statistics=None, multicore=False, filenames=None):

    if statistics is None:  # Run them all
        statistics = ["Wavelet", "MVC", "PSpec", "Bispectrum", "DeltaVariance",
                      "Genus", "VCS", "VCA", "VCS_Density", "VCS_Velocity",
                      "Tsallis", "PCA", "SCF", "Cramer", "Skewness",
                      "Kurtosis", "SCF", "PCA", "Dendrogram_Hist",
                      "Dendrogram_Num"]

    distances = {}

    # Calculate the fiducial case and return it for later use
    if fiducial_models is None:

        fiducial_models = {}

        if any("Wavelet" in s for s in statistics):
            wavelet_distance = \
                Wavelet_Distance(dataset1["integrated_intensity"],
                                 dataset2["integrated_intensity"]).distance_metric()
            distances["Wavelet"] = wavelet_distance.distance
            if not multicore:
                fiducial_models["Wavelet"] = wavelet_distance.wt1

        if any("MVC" in s for s in statistics):
            mvc_distance = MVC_distance(dataset1, dataset2).distance_metric()
            distances["MVC"] = mvc_distance.distance
            if not multicore:
                fiducial_models["MVC"] = mvc_distance.mvc1

        if any("PSpec" in s for s in statistics):
            pspec_distance = PSpec_Distance(dataset1,
                                            dataset2).distance_metric()
            distances["PSpec"] = pspec_distance.distance
            if not multicore:
                fiducial_models["PSpec"] = pspec_distance.pspec1

        if any("Bispectrum" in s for s in statistics):
            bispec_distance = \
                BiSpectrum_Distance(dataset1["integrated_intensity"],
                                    dataset2["integrated_intensity"]).distance_metric()
            distances["Bispectrum"] = bispec_distance.distance
            if not multicore:
                fiducial_models["Bispectrum"] = bispec_distance.bispec1

        if any("DeltaVariance" in s for s in statistics):
            delvar_distance = \
                DeltaVariance_Distance(dataset1["integrated_intensity"],
                                       dataset1["integrated_intensity_error"][0],
                                       dataset2["integrated_intensity"],
                                       dataset2["integrated_intensity_error"][0]).distance_metric()
            distances["DeltaVariance"] = delvar_distance.distance
            if not multicore:
                fiducial_models["DeltaVariance"] = delvar_distance.delvar1

        if any("Genus" in s for s in statistics):
            genus_distance = \
                GenusDistance(dataset1["integrated_intensity"][0],
                              dataset2["integrated_intensity"][0]).distance_metric()
            distances["Genus"] = genus_distance.distance
            if not multicore:
                fiducial_models["Genus"] = genus_distance.genus1

        if any("VCS" in s for s in statistics):
            vcs_distance = VCS_Distance(dataset1["cube"],
                                        dataset2["cube"]).distance_metric()
            distances["VCS"] = vcs_distance.distance
            distances["VCS_Density"] = vcs_distance.density_distance
            distances["VCS_Velocity"] = vcs_distance.velocity_distance
            if not multicore:
                fiducial_models["VCS"] = vcs_distance.vcs1

        if any("VCA" in s for s in statistics):
            vca_distance = VCA_Distance(dataset1["cube"],
                                        dataset2["cube"]).distance_metric()
            distances["VCA"] = vca_distance.distance
            if not multicore:
                fiducial_models["VCA"] = vca_distance.vca1

        if any("Tsallis" in s for s in statistics):
            tsallis_distance = \
                Tsallis_Distance(dataset1["integrated_intensity"][0],
                                 dataset2["integrated_intensity"][0]).distance_metric()
            distances["Tsallis"] = tsallis_distance.distance
            if not multicore:
                fiducial_models["Tsallis"] = tsallis_distance.tsallis1

        if any("Skewness" in s for s in statistics) or\
           any("Kurtosis" in s for s in statistics):
            moment_distance = \
                StatMomentsDistance(dataset1["integrated_intensity"][0],
                                    dataset2["integrated_intensity"][0], 5).distance_metric()
            distances["Skewness"] = moment_distance.skewness_distance
            distances["Kurtosis"] = moment_distance.kurtosis_distance
            if not multicore:
                fiducial_models["stat_moments"] = moment_distance.moments1

        if any("PCA" in s for s in statistics):
            pca_distance = \
                PCA_Distance(dataset1["cube"][0],
                             dataset2["cube"][0]).distance_metric()
            distances["PCA"] = pca_distance.distance
            if not multicore:
                fiducial_models["PCA"] = pca_distance.pca1

        if any("SCF" in s for s in statistics):
            scf_distance = \
                SCF_Distance(dataset1["cube"][0],
                             dataset2["cube"][0]).distance_metric()
            distances["SCF"] = scf_distance.distance
            if not multicore:
                fiducial_models["SCF"] = scf_distance.scf1

        if any("Cramer" in s for s in statistics):
            cramer_distance = \
                Cramer_Distance(dataset1["cube"][0],
                                dataset2["cube"][0]).distance_metric()
            distances["Cramer"] = cramer_distance.distance

        if any("Dendrogram_Hist" in s for s in statistics) or \
           any("Dendrogram_Num" in s for s in statistics):
            dendro_distance = DendroDistance(dataset1["cube"][0],
                                             dataset2["cube"][0])
            dendro_distance.distance_metric()

            distances["Dendrogram_Hist"] = dendro_distance.histogram_distance
            distances["Dendrogram_Num"] = dendro_distance.num_distance
            if not multicore:
                fiducial_models["Dendrogram"] = dendro_distance.dendro1

        if multicore:
            return distances
        else:
            return distances, fiducial_models

    else:

        if any("Wavelet" in s for s in statistics):
            wavelet_distance = \
                Wavelet_Distance(dataset1["integrated_intensity"],
                                 dataset2["integrated_intensity"],
                                 fiducial_model=fiducial_models["Wavelet"]).distance_metric()
            distances["Wavelet"] = wavelet_distance.distance

        if any("MVC" in s for s in statistics):
            mvc_distance = \
                MVC_distance(dataset1,
                             dataset2,
                             fiducial_model=fiducial_models["MVC"]).distance_metric()
            distances["MVC"] = mvc_distance.distance

        if any("PSpec" in s for s in statistics):
            pspec_distance = \
                PSpec_Distance(dataset1,
                               dataset2,
                               fiducial_model=fiducial_models["PSpec"]).distance_metric()
            distances["PSpec"] = pspec_distance.distance

        if any("Bispectrum" in s for s in statistics):
            bispec_distance = \
                BiSpectrum_Distance(dataset1["integrated_intensity"],
                                    dataset2["integrated_intensity"],
                                    fiducial_model=fiducial_models["Bispectrum"]).distance_metric()
            distances["Bispectrum"] = bispec_distance.distance

        if any("DeltaVariance" in s for s in statistics):
            delvar_distance = \
                DeltaVariance_Distance(dataset1["integrated_intensity"],
                                       dataset1["integrated_intensity_error"][0], \
                                       dataset2["integrated_intensity"],
                                       dataset2["integrated_intensity_error"][0],
                                       fiducial_model=fiducial_models["DeltaVariance"]).distance_metric()
            distances["DeltaVariance"] = delvar_distance.distance

        if any("Genus" in s for s in statistics):
            genus_distance = \
                GenusDistance(dataset1["integrated_intensity"][0],
                              dataset2["integrated_intensity"][0],
                              fiducial_model=fiducial_models["Genus"]).distance_metric()
            distances["Genus"] = genus_distance.distance

        if any("VCS" in s for s in statistics):
            vcs_distance = \
                VCS_Distance(dataset1["cube"],
                             dataset2["cube"],
                             fiducial_model=fiducial_models["VCS"]).distance_metric()
            distances["VCS_Density"] = vcs_distance.density_distance
            distances["VCS_Velocity"] = vcs_distance.velocity_distance
            distances["VCS"] = vcs_distance.distance

        if any("VCA" in s for s in statistics):
            vca_distance = \
                VCA_Distance(dataset1["cube"],
                             dataset2["cube"],
                             fiducial_model=fiducial_models["VCA"]).distance_metric()
            distances["VCA"] = vca_distance.distance

        if any("Tsallis" in s for s in statistics):
            tsallis_distance= \
                Tsallis_Distance(dataset1["integrated_intensity"][0],
                                 dataset2["integrated_intensity"][0],
                                 fiducial_model=fiducial_models["Tsallis"]).distance_metric()
            distances["Tsallis"] = tsallis_distance.distance

        if any("Skewness" in s for s in statistics) or any("Kurtosis" in s for s in statistics):
            moment_distance = \
                StatMomentsDistance(dataset1["integrated_intensity"][0],
                                    dataset2["integrated_intensity"][0],
                                    5,
                                    fiducial_model=fiducial_models["stat_moments"]).distance_metric()
            distances["Skewness"] = moment_distance.skewness_distance
            distances["Kurtosis"] = moment_distance.kurtosis_distance

        if any("PCA" in s for s in statistics):
            pca_distance = \
                PCA_Distance(dataset1["cube"][0],
                             dataset2["cube"][0],
                             fiducial_model=fiducial_models["PCA"]).distance_metric()
            distances["PCA"] = pca_distance.distance

        if any("SCF" in s for s in statistics):
            scf_distance = \
                SCF_Distance(dataset1["cube"][0],
                             dataset2["cube"][0],
                             fiducial_model=fiducial_models["SCF"]).distance_metric()
            distances["SCF"] = scf_distance.distance

        if any("Cramer" in s for s in statistics):
            cramer_distance = \
                Cramer_Distance(dataset1["cube"][0],
                                dataset2["cube"][0]).distance_metric()
            distances["Cramer"] = cramer_distance.distance

        if any("Dendrogram_Hist" in s for s in statistics) or \
           any("Dendrogram_Num" in s for s in statistics):
            dendro_distance = DendroDistance(dataset1["cube"][0],
                                             dataset2["cube"][0],
                                             fiducial_model=fiducial_models["Dendrogram"])
            dendro_distance.distance_metric()

            distances["Dendrogram_Hist"] = dendro_distance.histogram_distance
            distances["Dendrogram_Num"] = dendro_distance.num_distance

        return distances


def timestep_wrapper(fiducial, design, statistics):
    keywords = {"centroid", "centroid_error", "integrated_intensity",
                "integrated_intensity_error", "linewidth",
                "linewidth_error", "moment0", "moment0_error", "cube"}

    fiducial_dataset = fromfits(fiducial, keywords)
    design_dataset = fromfits(design, keywords)

    distances = wrapper(fiducial_dataset, design_dataset,
                        statistics=statistics, multicore=True,
                        filenames=[fiducial, design])
    return distances


def single_input(a):
    return timestep_wrapper(*a)


def run_all(fiducial, simulation_runs, face, statistics, savename,
            multicore=True, ncores=10, verbose=True):

    if verbose:
        print "Simulation runs to be analyzed: %s" % (simulation_runs)
        print "Started at "+str(datetime.now())

    # Distances will be stored in an array of dimensions
    # # statistics x # sim runs x # timesteps
    # The +1 in the second dimensions is to include the
    # fiducial case against itself.
    distances_storage = np.zeros((len(statistics),
                                  len(simulation_runs)))

    if multicore:
        pool = Pool(processes=ncores)
        distances = pool.map(single_input, izip(repeat(fiducial),
                                                simulation_runs,
                                                repeat(statistics)))
        pool.close()
        pool.join()
        distances_storage = sort_distances(statistics, distances).T

    else:
        for i, design in enumerate(simulation_runs):
            fiducial_dataset = fromfits(fiducial, keywords)
            testing_dataset = fromfits(design, keywords)
            if i == 0:
                distances, fiducial_models = \
                    wrapper(fiducial_dataset, testing_dataset,
                            statistics=statistics,
                            filenames=[fiducial, design])
                all_fiducial_models = fiducial_models
            else:
                distances = \
                    wrapper(fiducial_dataset, testing_dataset,
                            fiducial_models=all_fiducial_models,
                            statistics=statistics,
                            filenames=[fiducial, design])
            distances = [distances]
            distances_storage[:, i:i+1] = \
                sort_distances(statistics, distances).T

    return distances_storage


def sort_distances(statistics, distances):
    if len(statistics) > 1:
        distance_array = np.empty((len(distances), len(statistics)))
    elif len(statistics) == 1:
        distance_array = np.empty((len(distances), 1))

    for j, dist in enumerate(distances):
        distance_array[j, :] = [distances[j][stat] for stat in statistics]

    return distance_array

if __name__ == "__main__":

    from multiprocessing import Pool
    from itertools import izip, repeat

    INTERACT = False  # Will prompt you for inputs if True
    PREFIX = "/srv/astro/erickoch/enzo_sims/full_factorial/"

    os.chdir(PREFIX)

    statistics = ["Wavelet", "MVC", "PSpec", "Bispectrum", "DeltaVariance",
                  "Genus", "VCS", "VCA", "Tsallis", "PCA", "SCF", "Cramer",
                  "Skewness", "Kurtosis", "VCS_Density", "VCS_Velocity",
                  "Dendrogram_Hist", "Dendrogram_Num"]
    print "Statistics to run: %s" % (statistics)
    num_statistics = len(statistics)

    if INTERACT:
        fiducial = str(raw_input("Input folder of fiducial: "))
        face = str(raw_input("Which face? (0 or 1 or 2): "))
        save_name = str(raw_input("Save Name: "))
        MULTICORE = bool(raw_input("Run on multiple cores? (T or blank): "))

        if MULTICORE:
            NCORES = int(raw_input("How many cores to use? "))
    else:
        fiducial = str(sys.argv[1])
        face = str(sys.argv[2])
        save_name = str(sys.argv[3])
        MULTICORE = str(sys.argv[4])
        if MULTICORE == "T":
            MULTICORE = True
        else:
            MULTICORE = False
            NCORES = 1  # Placeholder to pass into run_all
        if MULTICORE:
            NCORES = int(sys.argv[5])

    if fiducial == "fid_comp":  # Run all the comparisons of fiducials
        if INTERACT:
            cross_comp = str(raw_input("Cross comparison? "))
        else:
            cross_comp = str(sys.argv[6])

        if cross_comp == "F":
            cross_comp = False
        else:
            cross_comp = True

        if cross_comp:
            if face == "0":
                comp_face = "2"
            elif face == "2":
                comp_face = "0"
        else:
            comp_face = face

        fiducials = [x for x in os.listdir(".") if os.path.isdir(x)
                     and x[:8] == "Fiducial" and x[-3] == comp_face]
        fiducials = np.sort(fiducials)

        fiducials_comp = [x for x in os.listdir(".") if os.path.isdir(x)
                          and x[:8] == "Fiducial" and x[-3] == face]
        fiducials_comp = np.sort(fiducials_comp)

        print "Fiducials to compare %s" % (fiducials)
        fiducial_labels = []
        # number of comparisons b/w all fiducials
        num_comp = (len(fiducials)**2. - len(fiducials))/2
        # Change dim 2 to match number of time steps
        distances_storage = np.zeros((num_statistics, num_comp))
        posn = 0
        prev = 0
        # no need to loop over the last one
        for fid, i in zip(fiducials[:-1], np.arange(len(fiducials)-1, 0, -1)):
            #### THIS NEED TO BE CHANGED BASED ON THE FIDUCIAL NUMBERING!!!!!!!
            fid_num = int(fid[-5]) + 1
            posn += i
            partial_distances = \
                run_all(fiducials[fid_num-1], fiducials_comp[fid_num:],
                        face, statistics, save_name, multicore=MULTICORE,
                        ncores=NCORES)
            distances_storage[:, prev:posn] = partial_distances
            prev += i
            fiducial_labels.extend([f + "to" + fid for f in
                                    fiducials_comp[fid_num:]])

        # consistent naming with non-fiducial case
        simulation_runs = fiducial_labels
        face = comp_face
    else:  # Normal case of comparing to single fiducial

        simulation_runs = [x for x in os.listdir(".") if os.path.isdir(x)
                           and x[:6] == "Design" and x[-3] == face]
        simulation_runs = np.sort(simulation_runs)

        distances_storage = \
            run_all(fiducial, simulation_runs,
                    face, statistics, save_name,
                    multicore=MULTICORE, ncores=NCORES)

        simulation_runs = [sim+"to"+fiducial for sim in simulation_runs]

    filename = save_name + "_" + face + "_distance_results.h5"
    print filename
    from pandas import DataFrame, HDFStore, concat

    ## Save data for each statistic in a dataframe.
    ## Each dataframe is saved in a single hdf5 file

    store = HDFStore("results/"+filename)

    for i in range(num_statistics):
        df = DataFrame(distances_storage[i, :], index=simulation_runs,
                       columns=[fiducial])
        if statistics[i] in store:
            existing_df = store[statistics[i]]
            if len(existing_df.index) == len(df.index):
                store[statistics[i]] = df
            else:  # Append on
                for ind in df.index:
                    if ind in list(existing_df.index):
                        existing_df.ix[ind] = df.ix[ind]
                    else:
                        existing_df = concat([existing_df, df])
                    store[statistics[i]] = existing_df
        else:
            store[statistics[i]] = df

    store.close()

    print "Done at " + str(datetime.now())
