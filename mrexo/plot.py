import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
import os
from scipy.stats.mstats import mquantiles
from astropy.table import Table


def plot_m_given_r_relation(result_dir):
    """
    Use to plot the conditional relationship of mass given radius.
    \nINPUTS:
        result_dir : Directory generated by the fitting function.
            Example: result_dir = '~/mrexo_working/trial_result'

    EXAMPLE:
        
        # Sample script to plot M-R data and fit.
        from mrexo import plot_mr_relation
        import os

        pwd = '~/mrexo_working/'
        result_dir = os.path.join(pwd,'Results_deg_12')

        _ = plot_m_given_r_relation(result_dir)

    """

    input_location = os.path.join(result_dir, 'input')
    output_location = os.path.join(result_dir, 'output')

    t = Table.read(os.path.join(input_location, 'MR_inputs.csv'))
    Mass = t['pl_masse']
    Mass_sigma = t['pl_masseerr1']
    Radius = t['pl_rade']
    Radius_sigma = t['pl_radeerr1']

    Mass_min, Mass_max = np.loadtxt(os.path.join(input_location, 'Mass_bounds.txt'))
    Radius_min, Radius_max = np.loadtxt(os.path.join(input_location, 'Radius_bounds.txt'))

    R_points = np.loadtxt(os.path.join(output_location, 'R_points.txt'))
    M_cond_R = np.loadtxt(os.path.join(output_location, 'M_cond_R.txt'))
    M_cond_R_upper = np.loadtxt(os.path.join(output_location, 'M_cond_R_upper.txt'))
    M_cond_R_lower = np.loadtxt(os.path.join(output_location, 'M_cond_R_lower.txt'))

    weights_boot = np.loadtxt(os.path.join(output_location, 'weights_boot.txt'))
    M_cond_R_boot = np.loadtxt(os.path.join(output_location, 'M_cond_R_boot.txt'))

    n_boot = np.shape(weights_boot)[0]
    deg_choose = int(np.sqrt(np.shape(weights_boot[1])))

    mr_lower_boot, mr_upper_boot = mquantiles(M_cond_R_boot,prob=[0.16, 0.84],axis = 0,alphap=1,betap=1).data

    fig = plt.figure(figsize=(8.5,7))
    plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=20)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=20)    # fontsize of the tick labels
    ax1 = fig.add_subplot(1,1,1)

    ax1.errorbar(x=Radius, y=Mass, xerr=Radius_sigma, yerr=Mass_sigma,fmt='k.',markersize=3, elinewidth=0.3)
    ax1.plot(10**R_points, 10**M_cond_R,  color='maroon', lw=2) # Full dataset run
    ax1.fill_between(10**R_points, 10**M_cond_R_lower, 10**M_cond_R_upper,alpha=0.3, color='lightsalmon') # Full dataset run
    ax1.fill_between(10**R_points, 10**mr_lower_boot, 10**mr_upper_boot,alpha=0.3, color='r') # Bootstrap result

    mr_median_line = Line2D([0], [0], color='maroon', lw=2,label='Median of f(m$|$r) from full dataset run')
    mr_full = mpatches.Patch(color='lightsalmon', alpha=0.3,  label=r'Quantiles of f(m$|$r) from full dataset run  ')
    mr_boot = mpatches.Patch(color='r', alpha=0.3, label=r'Quantiles of the median of the f(m$|$r) from bootstrap')

    handles = [mr_median_line, mr_full, mr_boot]


    ax1.set_xlabel('Radius ($R_{\oplus}$)')
    ax1.set_ylabel('Mass ($M_{\oplus}$)')
    ax1.set_title('f(m$|$r) with degree {}, and {} bootstraps'.format(deg_choose, n_boot), pad=5)
    ax1.set_yscale('log')
    ax1.set_xscale('log')

    plt.show(block=False)
    plt.ylim(10**Mass_min, 10**Mass_max)
    plt.xlim(10**Radius_min, 10**Radius_max)
    import matplotlib
    matplotlib.rc('text', usetex=True) #use latex for text
    plt.legend(handles = handles, prop={'size': 15})



    return fig, ax1, handles


def plot_r_given_m_relation(result_dir):
    """
    Use to plot the conditional relationship of radius given mass.
    \nINPUTS:
        result_dir : Directory generated by the fitting function.
            Example: result_dir = '~/mrexo_working/trial_result'

    EXAMPLE:
        
        # Sample script to plot M-R data and fit.
        from mrexo import plot_mr_relation
        import os

        pwd = '~/mrexo_working/'
        result_dir = os.path.join(pwd,'Results_deg_12')

        _ = plot_r_given_m_relation(result_dir)

    """

    input_location = os.path.join(result_dir, 'input')
    output_location = os.path.join(result_dir, 'output')

    t = Table.read(os.path.join(input_location, 'MR_inputs.csv'))
    Mass = t['pl_masse']
    Mass_sigma = t['pl_masseerr1']
    Radius = t['pl_rade']
    Radius_sigma = t['pl_radeerr1']

    Mass_min, Mass_max = np.loadtxt(os.path.join(input_location, 'Mass_bounds.txt'))
    Radius_min, Radius_max = np.loadtxt(os.path.join(input_location, 'Radius_bounds.txt'))

    R_points = np.loadtxt(os.path.join(output_location, 'R_points.txt'))
    M_points = np.loadtxt(os.path.join(output_location, 'M_points.txt'))
    R_cond_M = np.loadtxt(os.path.join(output_location, 'R_cond_M.txt'))
    R_cond_M_upper = np.loadtxt(os.path.join(output_location, 'R_cond_M_upper.txt'))
    R_cond_M_lower = np.loadtxt(os.path.join(output_location, 'R_cond_M_lower.txt'))

    weights_boot = np.loadtxt(os.path.join(output_location, 'weights_boot.txt'))
    R_cond_M_boot = np.loadtxt(os.path.join(output_location, 'R_cond_M_boot.txt'))

    n_boot = np.shape(weights_boot)[0]
    deg_choose = int(np.sqrt(np.shape(weights_boot[1])))

    rm_lower_boot, rm_upper_boot = mquantiles(R_cond_M_boot,prob=[0.16, 0.84],axis=0,alphap=1,betap=1).data

    fig = plt.figure(figsize=(8.5,7))
    plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=20)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=20)    # fontsize of the tick labels
    ax1 = fig.add_subplot(1,1,1)

    ax1.errorbar(y=Radius, x=Mass, yerr=Radius_sigma, xerr=Mass_sigma,fmt='k.',markersize=3, elinewidth=0.3)
    ax1.plot(10**M_points, 10**R_cond_M,  color='midnightblue', lw=2) # Full dataset run
    ax1.fill_between(10**M_points, 10**R_cond_M_lower, 10**R_cond_M_upper, alpha=0.3, color='cornflowerblue') # Full dataset run
    ax1.fill_between(10**M_points, 10**rm_lower_boot, 10**rm_upper_boot, alpha=0.3, color='b') # Bootstrap result


    rm_median_line = Line2D([0], [0], color='midnightblue', lw=2,label=r'Median of f(r$|$m) from full dataset run')
    rm_full = mpatches.Patch(color='cornflowerblue', alpha=0.3,  label=r'Quantiles of f(r$|$m) from full dataset run  ')
    rm_boot = mpatches.Patch(color='b', alpha=0.3, label=r'Quantiles of the median of the f(r$|$m) from bootstrap')
    handles = [rm_median_line, rm_full, rm_boot]

    plt.legend(handles=handles, prop={'size': 15})
    ax1.set_ylabel('Radius ($R_{\oplus}$)')
    ax1.set_xlabel('Mass ($M_{\oplus}$)')

    ax1.set_title(r'f(r$|$m) with degree {}, and {} bootstraps'.format(deg_choose, n_boot), pad=5)
    ax1.set_yscale('log')
    ax1.set_xscale('log')

    plt.show(block=False)
    plt.xlim(10**Mass_min, 10**Mass_max)
    plt.ylim(10**Radius_min, 10**Radius_max)

    return fig, ax1, handles

def plot_mr_and_rm(result_dir):
    """
    Use to plot the conditional relationship of radius given mass, as well as and mass given radius.
    Fig 3 (a,c) from Kanodia et al. 2019

    \nINPUTS:
        result_dir : Directory generated by the fitting function.
            Example: result_dir = '~/mrexo_working/trial_result'

    EXAMPLE:
        
        # Sample script to plot M-R data and fit.
        from mrexo import plot_mr_relation
        import os

        pwd = '~/mrexo_working/'
        result_dir = os.path.join(pwd,'Results_deg_12')

        _ = plot_mr_and_rm(result_dir)

    """

    input_location = os.path.join(result_dir, 'input')
    output_location = os.path.join(result_dir, 'output')

    t = Table.read(os.path.join(input_location, 'MR_inputs.csv'))
    Mass = t['pl_masse']
    Mass_sigma = t['pl_masseerr1']
    Radius = t['pl_rade']
    Radius_sigma = t['pl_radeerr1']

    Mass_min, Mass_max = np.loadtxt(os.path.join(input_location, 'Mass_bounds.txt'))
    Radius_min, Radius_max = np.loadtxt(os.path.join(input_location, 'Radius_bounds.txt'))

    R_points = np.loadtxt(os.path.join(output_location, 'R_points.txt'))
    M_points = np.loadtxt(os.path.join(output_location, 'M_points.txt'))

    M_cond_R = np.loadtxt(os.path.join(output_location, 'M_cond_R.txt'))
    M_cond_R_upper = np.loadtxt(os.path.join(output_location, 'M_cond_R_upper.txt'))
    M_cond_R_lower = np.loadtxt(os.path.join(output_location, 'M_cond_R_lower.txt'))
    R_cond_M = np.loadtxt(os.path.join(output_location, 'R_cond_M.txt'))
    R_cond_M_upper = np.loadtxt(os.path.join(output_location, 'R_cond_M_upper.txt'))
    R_cond_M_lower = np.loadtxt(os.path.join(output_location, 'R_cond_M_lower.txt'))

    weights_boot = np.loadtxt(os.path.join(output_location, 'weights_boot.txt'))
    M_cond_R_boot = np.loadtxt(os.path.join(output_location, 'M_cond_R_boot.txt'))
    R_cond_M_boot = np.loadtxt(os.path.join(output_location, 'R_cond_M_boot.txt'))

    n_boot = np.shape(weights_boot)[0]
    deg_choose = int(np.sqrt(np.shape(weights_boot[1])))


    mr_lower_boot, mr_upper_boot = mquantiles(M_cond_R_boot,prob=[0.16, 0.84],axis=0,alphap=1,betap=1).data
    rm_lower_boot, rm_upper_boot = mquantiles(R_cond_M_boot,prob=[0.16, 0.84],axis=0,alphap=1,betap=1).data

    fig = plt.figure(figsize=(8.5,6.5))
    plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=20)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=20)    # fontsize of the tick labels
    ax1 = fig.add_subplot(1,1,1)

    ax1.errorbar(x=Radius, y=Mass, xerr=Radius_sigma, yerr=Mass_sigma,fmt='k.', markersize=3, elinewidth=0.3)

    ax1.plot(10**R_points, 10**M_cond_R,  color='maroon', lw=2) # Full dataset run
    ax1.fill_between(10**R_points, 10**M_cond_R_lower, 10**M_cond_R_upper, alpha=0.3, color='lightsalmon') # Full dataset run
    ax1.fill_between(10**R_points, 10**mr_lower_boot, 10**mr_upper_boot, alpha=0.3, color='r') # Bootstrap result

    ax1.plot(10**R_cond_M, 10**M_points,  color='midnightblue', lw=2) # Full dataset run
    ax1.fill_betweenx(10**M_points, 10**R_cond_M_lower, 10**R_cond_M_upper, alpha=0.3, color='cornflowerblue') # Full dataset run
    ax1.fill_betweenx(10**M_points,10**rm_lower_boot,10**rm_upper_boot, alpha=0.3, color='b') # Bootstrap result

    mr_median_line = Line2D([0], [0], color='maroon', lw=2,label=r'Median of f(m$|$r) from full dataset run')
    mr_full = mpatches.Patch(color='lightsalmon', alpha=0.3,  label=r'Quantiles of f(m$|$r) from full dataset run  ')
    mr_boot = mpatches.Patch(color='r', alpha=0.3, label=r'Quantiles of median of f(m$|$r) from bootstrap')

    rm_median_line = Line2D([0], [0], color='midnightblue', lw=2,label=r'Median of f(r$|$m) from full dataset run')
    rm_full = mpatches.Patch(color='cornflowerblue', alpha=0.3,  label=r'Quantiles of f(r$|$m) from full dataset run  ')
    rm_boot = mpatches.Patch(color='b', alpha=0.3, label=r'Quantiles of median of f(r$|$m) from bootstrap')

    handles = [mr_median_line, mr_full, mr_boot, rm_median_line, rm_full, rm_boot]

    ax1.set_xlabel(' Radius ($R_{\oplus}$)', fontsize = 20)
    ax1.set_ylabel(' Mass ($M_{\oplus}$)', fontsize = 20)
    ax1.set_yscale('log')
    ax1.set_xscale('log')

    plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=20)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=20)    # fontsize of the tick labels

    plt.show(block=False)
    plt.ylim(10**Mass_min, 10**Mass_max)
    plt.xlim(10**Radius_min, 10**Radius_max)
    import matplotlib
    matplotlib.rc('text', usetex=True) #use latex for text
    plt.legend(handles = handles, loc=4, prop={'size': 15})

    return fig, ax1, handles


def plot_joint_mr_distribution(result_dir):
    """
    Use to plot joint distribution of mass AND radius.
    Fig 3 (b,d) from Kanodia et al. 2019

    \nINPUTS:
        result_dir : Directory generated by the fitting function.
            Example: result_dir = '~/mrexo_working/trial_result'

    EXAMPLE:
        
        # Sample script to plot M-R data and fit.
        from mrexo import plot_mr_relation
        import os

        pwd = '~/mrexo_working/'
        result_dir = os.path.join(pwd,'Results_deg_12')

        _ = plot_joint_mr_distribution(result_dir)

    """

    input_location = os.path.join(result_dir, 'input')
    output_location = os.path.join(result_dir, 'output')

    t = Table.read(os.path.join(input_location, 'MR_inputs.csv'))
    Mass = t['pl_masse']
    Mass_sigma = t['pl_masseerr1']
    Radius = t['pl_rade']
    Radius_sigma = t['pl_radeerr1']

    logMass = np.log10(Mass)
    logRadius = np.log10(Radius)
    logMass_sigma = 0.434 * Mass_sigma/Mass
    logRadius_sigma = 0.434 * Radius_sigma/Radius

    Mass_min, Mass_max = np.loadtxt(os.path.join(input_location, 'Mass_bounds.txt'))
    Radius_min, Radius_max = np.loadtxt(os.path.join(input_location, 'Radius_bounds.txt'))

    joint = np.loadtxt(os.path.join(output_location,'joint_distribution.txt'))

    fig = plt.figure(figsize=(8.5,6.5))
    ax1 = fig.add_subplot(1,1,1)
    ax1.errorbar(x=logRadius, y=logMass, xerr=logRadius_sigma, yerr=logMass_sigma,fmt='k.',markersize=3, elinewidth=0.3)


    plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=20)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=20)    # fontsize of the tick labels

    ax1.tick_params(which = 'both',  labeltop = False, top = False, labelright = False, right = False, labelsize = 22)

    im = ax1.imshow(joint, cmap = 'coolwarm', extent=[Radius_min, Radius_max, Mass_min, Mass_max], origin = 'lower', aspect = 'auto')
    cbar = fig.colorbar(im, ticks=[np.min(joint), np.max(joint)], fraction=0.037, pad=0.04)
    cbar.ax.set_yticklabels(['Min', 'Max'])

    x_ticks = ax1.get_xticks().tolist()
    x_tick_labels = [np.round(10**i,3) for i in x_ticks]
    ax1.set_xticklabels(x_tick_labels, size = 18)

    y_ticks = ax1.get_yticks().tolist()
    y_tick_labels = [np.round(10**i,2) for i in y_ticks]
    ax1.set_yticklabels(y_tick_labels, size = 18)


    plt.ylim(Mass_min, Mass_max)
    plt.xlim(Radius_min, Radius_max)

    plt.xlabel('Radius ($R_{\oplus}$)', fontsize = 20)
    plt.ylabel('Mass ($M_{\oplus}$)', fontsize = 20)

    plt.show(block=False)

    return fig, ax1



def plot_mle_weights(result_dir):
    """
    Function to plot MLE weights, similar to Fig 2 from Kanodia et al. 2019
    \nINPUTS:
        result_dir = Directory created by fitting procedure. See ~/mrexo/mrexo/datasets/M_dwarfs_20181214 for example

    OUTPUTS:

        Displays plot. No outputs

    """
    output_location = os.path.join(result_dir, 'output')

    weights_mle = np.loadtxt(os.path.join(output_location,'weights.txt'))

    size = int(np.sqrt(len(weights_mle)))

    plt.imshow(np.reshape(weights_mle , [size, size]), extent = [0, size, 0, size], origin = 'left', cmap = 'viridis')
    plt.xticks(np.arange(0,size), *[np.arange(0,size)])
    plt.yticks(np.arange(0,size), *[np.arange(0,size)])

    plt.colorbar()
    plt.title('Polynomial weights with {} degrees'.format(size))
    plt.show()
