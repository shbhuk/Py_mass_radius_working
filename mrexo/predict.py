import numpy as np
import os

from .mle_utils import cond_density_quantile




def predict_m_given_r(Radius, weights_mle, Radius_sigma = None, posterior_sample = False,
                                qtl = [0.16,0.84], islog = False,Radius_min = -0.3,
                                Radius_max = 1.357,Mass_min = -1,Mass_max = 3.809):
    '''
    INPUT:
        Radius = The radius for which Mass is being predicted. [Earth Radii]
        weights_mle = The weights as generated by the MLE code.
        Radius_sigma = 1 sigma error on radius [Earth Radii]
        posterior_sample = If the input is a posterior sample. Default is False
        qtl = Quantile values returned. Default is 0.16 and 0.84
        islog = Whether the radius given is in log scale or not. Default is False. The Radius_sigma is always in original units
        Radius, Mass = upper bounds and lower bounds used in the Bernstein polynomial model in log10 scale
    '''

    degrees = int(np.sqrt(len(weights_mle)))
    print(degrees)

    if islog == False:
        logRadius = np.log10(Radius)
    else:
        logRadius = Radius


    if posterior_sample == False:
        predicted_value = cond_density_quantile(y = logRadius, y_std = Radius_sigma, y_max = Radius_max, y_min = Radius_min,
                                                      x_max = Mass_max, x_min = Mass_min, deg = degrees,
                                                      w_hat = weights_mle, qtl = qtl)
        predicted_mean = predicted_value[0]
        predicted_lower_quantile = predicted_value[2]
        predicted_upper_quantile = predicted_value[3]

        outputs = [predicted_mean,predicted_lower_quantile,predicted_upper_quantile]

    elif posterior_sample == True:

        n = np.size(Radius)
        mean_sample = np.zeros(n)
        random_quantile = np.zeros(n)

        if len(logRadius) != len(Radius_sigma):
            print('Length of Radius array is not equal to length of Radius_sigma array. CHECK!!!!!!!')
            return 0

        for i in range(0,n):
            qtl_check = np.random.random()
            print(qtl_check)
            results = cond_density_quantile(y = logRadius[i], y_std = Radius_sigma[i], y_max = Radius_max, y_min = Radius_min,
                                                      x_max = Mass_max, x_min = Mass_min, deg = degrees,
                                                      w_hat = weights_mle, qtl = [qtl_check,0.5])

            mean_sample[i] = results[0]
            random_quantile[i] = results[2]

        outputs = [mean_sample,random_quantile]

    if islog:
        return outputs
    else:
        #return outputs
        return [10**x for x in outputs]
