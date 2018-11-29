import os
from astropy.table import Table
import numpy as np
from multiprocessing import cpu_count

from mrexo import fit_mr_relation


pwd = os.path.dirname(__file__)

t = Table.read(os.path.join(pwd,'MR_Kepler_170605_noanalytTTV_noupplim.csv'))

# Symmetrical errorbars
Mass_sigma = (abs(t['pl_masseerr1']) + abs(t['pl_masseerr2']))/2
Radius_sigma = (abs(t['pl_radeerr1']) + abs(t['pl_radeerr2']))/2

# In Earth units
Mass = np.array(t['pl_masse'])
Radius = np.array(t['pl_rade'])

# Directory to store results in 
result_dir = os.path.join(pwd,'Kepler_CV_run')


initialfit_result, bootstrap_results = fit_mr_relation(Mass = Mass, Mass_sigma = Mass_sigma,
                                        Radius = Radius, Radius_sigma = Radius_sigma,
                                        save_path = result_dir, select_deg = 'cv', 
                                        num_boot = 100, cores = cpu_count())
