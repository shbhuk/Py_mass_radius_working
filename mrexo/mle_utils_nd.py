import numpy as np
from scipy.stats import beta,norm
import scipy
from scipy.integrate import quad
from scipy.optimize import brentq as root
from scipy.interpolate import interpn
import datetime,os
from multiprocessing import current_process


from .utils import _logging
from .Optimizers import optimizer


########################################
##### Main function: MLE_fit() #########
########################################

# Ndim - 20201130
def InputData(ListofDictionaries):
	'''
	Input List of Dictionaries, where each dictionary corresponds to a dimension
	Example dictionary
	RadiusDict = {'Data': Radius, 'Sigma': Radius_sigma,
		'Max':None, 'Min':None,
		'Label':'Radius', 'Char':'r'}
	MassDict = {'Data': Mass, 'Sigma': Mass_sigma,
		'Max':None, 'Min':None,
		'Label':'Mass', 'Char':'m'}

	The number of 'Data' entries and 'Sigma' entries in each dictionary must be equal
	
	Output:
		DataDict with attributes - 
			'ndim_data', 'ndim_sigma', 'ndim_bounds', 'ndim_char', 'ndim_label'
		
	'''
	
	ndim = len(ListofDictionaries)
	ndim_data = np.zeros((ndim, len(ListofDictionaries[0]['Data'])))
	ndim_sigmaL  = np.zeros((ndim, len(ListofDictionaries[0]['SigmaLower'])))
	ndim_sigmaU  = np.zeros((ndim, len(ListofDictionaries[0]['SigmaUpper'])))
	ndim_sigma = np.zeros((ndim, len(ListofDictionaries[0]['SigmaUpper'])))
	ndim_bounds = np.zeros((ndim, 2))
	ndim_char = []
	ndim_label = []
	
	for d in range(len(ListofDictionaries)):
		assert len(ListofDictionaries[d]['Data']) == np.shape(ndim_data)[1], "Data entered for dimension {} does not match length for dimension 0".format(d)
		assert len(ListofDictionaries[d]['SigmaLower']) == np.shape(ndim_sigmaL)[1], "Length of Sigma Lower entered for dimension {} does not match length for dimension 0".format(d)
		assert len(ListofDictionaries[d]['SigmaUpper']) == np.shape(ndim_sigmaU)[1], "Length of Sigma Upper entered for dimension {} does not match length for dimension 0".format(d)
		assert len(ListofDictionaries[d]['SigmaUpper']) == len(ListofDictionaries[d]['SigmaLower']), "Length of Sigma Upper entered for dimension {} does not match length for Sigma Lower".format(d)
		assert len(ListofDictionaries[d]['Data']) == len(ListofDictionaries[d]['SigmaLower']), 'Data and Sigma for dimension {} are not of same length'.format(d)
		
		ndim_data[d] = ListofDictionaries[d]['Data']
		ndim_sigmaL[d] = ListofDictionaries[d]['SigmaLower']
		ndim_sigmaU[d] = ListofDictionaries[d]['SigmaUpper']
		ndim_sigma[d] = np.average([np.abs(ndim_sigmaL[d]), np.abs(ndim_sigmaU[d])], axis=0)
		ndim_char.append(ListofDictionaries[d]['Char'])
		ndim_label.append(ListofDictionaries[d]['Label'])
		
		if not np.isfinite(ListofDictionaries[d]['Min']):
			Min = np.log10(0.9*np.min(np.abs(ndim_data[d] - ndim_sigma[d])))
		else:
			Min = ListofDictionaries[d]['Min']
			
		if not np.isfinite(ListofDictionaries[d]['Max']):
			Max = np.log10(1.1*np.max(ndim_data[d] + ndim_sigma[d]))
		else:
			Max = ListofDictionaries[d]['Max']
			 
		ndim_bounds[d] = [Min, Max]
		
	DataDict = {"ndim_data":ndim_data, 
						"ndim_sigma":ndim_sigma,
						"ndim_sigmaL":ndim_sigmaL,
						"ndim_sigmaU":ndim_sigmaU,
						"ndim_bounds":ndim_bounds,
						"ndim_char":ndim_char,
						"ndim_label":ndim_label,
						"ndim":ndim,
						"DataLength":np.shape(ndim_data)[1]}

	return DataDict


def MLE_fit(DataDict, deg_per_dim, 
			Log=True, abs_tol=1e-8, 
			output_weights_only=False, calc_joint_dist = False, 
			save_path=None, verbose=2):
	'''
	Perform maximum likelihood estimation to find the weights for the beta density basis functions.
	Also, use those weights to calculate the conditional density distributions.
	Ning et al. 2018 Sec 2.2, Eq 9.

	'''
	starttime = datetime.datetime.now()
	if save_path is None:
		save_path = os.path.dirname(__file__)

	message = '=========\nStarted MLE run at {}'.format(starttime)
	_ = _logging(message=message, filepath=save_path, verbose=verbose, append=True)

	ndim = DataDict["ndim"]
	DataLength = DataDict["DataLength"]
	
	########################################################################
	# Integration to find C matrix (input for log likelihood maximization.)
	########################################################################

	# C_pdf is of shape n x deg_product where deg_product = Product of (deg_i - 2) for i in ndim
	C_pdf = calc_C_matrix(DataDict=DataDict, 
		deg_per_dim=deg_per_dim, 
		abs_tol=abs_tol, 
		save_path=save_path, 
		Log=Log, 
		verbose=verbose, 
		SaveCMatrix=True)

	message = 'Finished Integration at {}. \nCalculated the PDF for Integrated beta and normal density.'.format(datetime.datetime.now())
	_ = _logging(message=message, filepath=save_path, verbose=verbose, append=True)

	###########################################################
	# Run optimization to find the weights
	###########################################################

	# Weights are a 1D vector of length deg_product where deg_product = Product of (deg_i - 2) for i in ndim
	# They can be reshaped into an `ndim` dimensional array 
	unpadded_weight, n_log_lik = optimizer(C_pdf=C_pdf, deg_per_dim=deg_per_dim,
		verbose=verbose, save_path=save_path)
	# print("AAAAAAAAAAAAAAAA   {}".format(n_log_lik))
	# rand = np.random.randn()
	# np.savetxt(os.path.join(save_path, 'loglikelihoodtest{:.3f}.txt'.format(rand)), [n_log_lik])
	# np.savetxt(os.path.join(save_path, 'Cpdf{:.3f}.txt'.format(rand)), C_pdf)
	# np.savetxt(os.path.join(save_path, 'IntermediateWeight{:.3f}.txt'.format(rand)), w_hat)


	# Pad the weight array with zeros for the
	w_sq = np.reshape(unpadded_weight, np.array(deg_per_dim)-2)
	w_sq_padded = np.zeros(deg_per_dim)
	w_sq_padded[[slice(1,-1) for i in range(ndim)]] = w_sq
	w_hat = w_sq_padded.flatten()


	if output_weights_only == True:
		return unpadded_weight, n_log_lik

	else:
		# Calculate AIC and BIC
		# aic = -n_log_lik*2 + 2*(deg**2 - 1)
		# aic = -n_log_lik*2 + 2*(rank_FI_matrix(C_pdf, unpadded_weight)/n)
		# bic = -n_log_lik*2 + np.log(n)*(deg**2 - 1)
		
		DataSeq = np.zeros((ndim, 100))
		for dim in range(ndim):
			DataSeq[dim] = np.linspace(DataDict['ndim_bounds'][dim][0], DataDict['ndim_bounds'][dim][1], DataSeq.shape[1]) 
		
		DataDict['DataSequence'] = DataSeq
		
		output = {"UnpaddedWeights":unpadded_weight, "Weights":w_hat,
				"deg_per_dim":deg_per_dim,
				"DataSequence":DataSeq}
	
		JointDist, indv_pdf_per_dim = calculate_joint_distribution(DataDict=DataDict, 
			weights=w_hat, 
			deg_per_dim=deg_per_dim, 
			save_path=save_path, verbose=verbose, abs_tol=abs_tol)
			
		output['JointDist'] = JointDist
			
		"""
		Y_seq = np.linspace(Y_min,Y_max,100)
		X_seq = np.linspace(X_min,X_max,100)

		output = {'weights': w_hat,
				  'aic': aic,
				  'bic': bic,
				  'Y_points': Y_seq,
				  'X_points': X_seq}


		deg_vec = np.arange(1,deg+1)

		Y_cond_X_median, Y_cond_X_var, Y_cond_X_quantile = [], [], []
		X_cond_Y_median, X_cond_Y_var, X_cond_Y_quantile = [], [], []

		for i in range(0,len(X_seq)):
			# Conditional Densities with 16% and 84% quantile
			Y_cond_X = cond_density_quantile(a = X_seq[i], a_max = X_max, a_min = X_min,
							b_max = Y_max, b_min = Y_min, deg = deg, deg_vec = deg_vec, w_hat = w_hat, qtl = [0.5,0.16,0.84])[0:3]
			Y_cond_X_median.append(Y_cond_X[2][0])
			Y_cond_X_var.append(Y_cond_X[1])
			Y_cond_X_quantile.append(Y_cond_X[2][1:])

			X_cond_Y = cond_density_quantile(a = Y_seq[i], a_max=Y_max, a_min=Y_min,
								b_max=X_max, b_min=X_min, deg=deg, deg_vec = deg_vec,
								w_hat=np.reshape(w_hat,(deg,deg)).T.flatten(), qtl = [0.5,0.16,0.84])[0:3]
			X_cond_Y_median.append(X_cond_Y[2][0])
			X_cond_Y_var.append(X_cond_Y[1])
			X_cond_Y_quantile.append(X_cond_Y[2][1:])



		# Output everything as dictionary

		output['Y_cond_X'] = Y_cond_X_median
		output['Y_cond_X_var'] = Y_cond_X_var
		output['Y_cond_X_quantile'] = np.array(Y_cond_X_quantile)
		output['X_cond_Y'] = X_cond_Y_median
		output['X_cond_Y_var'] = X_cond_Y_var
		output['X_cond_Y_quantile'] = np.array(X_cond_Y_quantile)
		"""


		
		return output

# Ndim - 20201130
def calc_C_matrix(DataDict, deg_per_dim,
		abs_tol, save_path, Log, verbose, SaveCMatrix=False):
	'''
	Integrate the product of the normal and beta distributions for Y and X and then take the Kronecker product.

	Refer to Ning et al. 2018 Sec 2.2 Eq 8 and 9.
	'''
	ndim = DataDict['ndim']
	n = DataDict['DataLength']
	# For degree 'd', actually using d-2 since the boundaries are zero padded.
	deg_vec_per_dim = [np.arange(1, deg-1) for deg in deg_per_dim] 
	indv_pdf_per_dim = [np.zeros((n, deg-2)) for deg in deg_per_dim]
	
	# Product of degrees (deg-2 since zero padded)
	deg_product = 1
	for deg in deg_per_dim:
		deg_product *= deg-2
		
	C_pdf = np.zeros((n, deg_product))
	
	message = 'Started Integration at {}'.format(datetime.datetime.now())
	_ = _logging(message=message, filepath=save_path, verbose=verbose, append=True)

	# Loop across each data point.
	for i in range(0,n):
		kron_temp = 1
		for dim in range(0,ndim):
			indv_pdf_per_dim[dim][i,:] = _find_indv_pdf(a=DataDict["ndim_data"][dim][i], 
															a_std=DataDict["ndim_sigma"][dim][i],
															deg=deg_per_dim[dim], deg_vec=deg_vec_per_dim[dim],
															a_max=DataDict["ndim_bounds"][dim][1], 
															a_min=DataDict["ndim_bounds"][dim][0], 
															Log=Log)
			
			kron_temp = np.kron(indv_pdf_per_dim[dim][i,:], kron_temp)
		C_pdf[i,:] = kron_temp

	C_pdf = C_pdf.T

	# Log of 0 throws weird errors
	C_pdf[C_pdf == 0] = 1e-300
	C_pdf[np.where(np.isnan(C_pdf))] = 1e-300

	if SaveCMatrix:
		np.savetxt(os.path.join(save_path, 'C_pdf.txt'), C_pdf)
	return C_pdf


def _norm_pdf(a, loc, scale):
	'''
	Find the PDF for a normal distribution. Identical to scipy.stats.norm.pdf.
	Runs much quicker without the generic function handling.
	'''
	N = (a - loc)/scale
	return np.exp(-N*N/2)/(np.sqrt(2*np.pi))/scale

def _int_gamma(a):
	return scipy.math.factorial(a-1)


def _beta_pdf(x,a,b):
	f = (_int_gamma(a+b) * x**(a-1)*(1-x)**(b-1))/(_int_gamma(a)*_int_gamma(b))
	return f

# Ndim - 20201130
def _pdfnorm_beta(a, a_obs, a_std, a_max, a_min, shape1, shape2, Log=True):
	'''
	Product of normal and beta distribution

	Refer to Ning et al. 2018 Sec 2.2, Eq 8.
	'''

	if Log == True:
		norm_beta = _norm_pdf(a_obs, loc=10**a, scale=a_std) * _beta_pdf((a - a_min)/(a_max - a_min), a=shape1, b=shape2)/(a_max - a_min)
	else:
		norm_beta = _norm_pdf(a_obs, loc=a, scale=a_std) * _beta_pdf((a - a_min)/(a_max - a_min), a=shape1, b=shape2)/(a_max - a_min)
	return norm_beta

# Ndim - 20201130
def integrate_function(data, data_std, deg, degree, a_max, a_min, Log=False, abs_tol=1e-8):
	'''
	Integrate the product of the normal and beta distribution.

	Refer to Ning et al. 2018 Sec 2.2, Eq 8.
	'''
	a_obs = data
	a_std = data_std
	shape1 = degree
	shape2 = deg - degree + 1
	Log = Log

	integration_product = quad(_pdfnorm_beta, a=a_min, b=a_max,
						  args=(a_obs, a_std, a_max, a_min, shape1, shape2, Log), epsabs = abs_tol, epsrel = 1e-8)
	return integration_product[0]

# Ndim - 20201130
def _find_indv_pdf(a, deg, deg_vec, a_max, a_min, a_std=np.nan, abs_tol=1e-8, Log=False):
	'''
	Find the individual probability density Function for a variable.
	If the data has uncertainty, the joint distribution is modelled using a
	convolution of beta and normal distributions.

	Refer to Ning et al. 2018 Sec 2.2, Eq 8.

	Always use with Log=False
	'''


	if np.isnan(a_std):
		if Log:
			a_std = (np.log10(a) - a_min)/(a_max - a_min)
		else:
			a_std = (a - a_min)/(a_max - a_min)
		a_beta_indv = np.array([_beta_pdf(a_std, a=d, b=deg - d + 1)/(a_max - a_min) for d in deg_vec])
	else:
		a_beta_indv = np.array([integrate_function(data=a, data_std=a_std, deg=deg, degree=d, a_max=a_max, a_min=a_min, abs_tol=abs_tol, Log=Log) for d in deg_vec])
	return a_beta_indv


def calculate_conditional_distribution(ConditionString, DataDict, 
		weights, deg_per_dim, 
		JointDist,
		MeasurementDict):
	'''
	
	INPUTS:
		ConditionString = Example 'x|y,z' or 'x,y|z', or 'm|r,p'
		JointDist = An n-dimensional cube with each dimension of same length. Typically 100.
		weights = Padded weights with dimensionality (1 x (d1 x d2 x d3 x .. x dn)) where di are the degrees per dimension
		indv_pdf_per_dim = This is the individual PDF for each point in the sequence . 
			It is a list of 1-D vectors, where the number of elements in the list = ndim.
			The number of elements in each vector is the number of degrees for that dimension
		MeasurementDict: Example:
			MeasurementDict = {}
			MeasurementDict['r'] = [[1,2,3],[0.1, 0.2, 0.3]] # Vector of radius measurements, vector of radius measurement uncertainties
			MeasurementDict['p'] = [[10, 20, 30], [1e-3, 1e-3, 1e-3]] # Likewise for period
			
			MeasurementDict['r'] = [[4], [np.nan]]
			MeasurementDict['p'] = [[0.9999], [np.nan]]
			
		MeasurementDict assumes linear values
	'''
	
	# Assuming it is x|y,z, i.e. there is only one dimension on the LHS
	
	Alphabets = [chr(i) for i in range(105,123)] # Lower case ASCII characters
	
	# NPoints = len(DataDict['DataSequence'][0])
	Condition = ConditionString.split('|')
	LHSTerms = Condition[0].split(',')
	RHSTerms = Condition[1].split(',')
	deg_vec_per_dim = [np.arange(1, deg+1) for deg in deg_per_dim] 
	
	LHSDimensions = np.arange(DataDict['ndim'])[np.isin(DataDict['ndim_char'] , LHSTerms)]
	RHSDimensions = np.arange(DataDict['ndim'])[np.isin(DataDict['ndim_char'] , RHSTerms)]
	####################################

	# Need to finalize exact structure of input
	RHSMeasurements = []
	RHSUncertainties = []
	_ = [RHSMeasurements.append(MeasurementDict[i][0]) for i in RHSTerms]
	_ = [RHSUncertainties.append(MeasurementDict[i][1]) for i in RHSTerms]
	
	i=0 # Working on ith element of measurements
	
	NPoints = len(RHSMeasurements[0])
	Denominator = np.zeros(NPoints)
	Numerator = np.zeros(NPoints)
	
	# Initial values
	ReshapedWeights = np.reshape(weights, deg_per_dim)

	ldim = LHSDimensions
	rdim = RHSDimensions
	
	RHSSequence = DataDict['DataSequence'][rdim]
	LHSSequence = DataDict['DataSequence'][ldim]
	NSeq = len(RHSSequence[0])
	
	Indices = [slice(0, None) for _ in range(DataDict['ndim'])]
	InterpSlices = np.copy(DataDict['DataSequence'])
	for j in range(len(RHSTerms)):
		# jth RHS dimension, 0 refers to measurement (1 is uncertainty), and taking a slice of the ith measurement input
		InterpSlices[RHSDimensions[j]] = np.repeat(np.log10(MeasurementDict[RHSTerms[j]][0][i]), NSeq)
		
	# 20201215 - only works for 1 LHS Dimensions
	SliceofJoint = interpn(tuple(DataDict['DataSequence']), JointDist, np.dstack(InterpSlices))
	
	
	# RHSMeasurements = 10**RHSSequence[50]
	# RHSIndex = np.argmin(np.abs(RHSSequence - np.log10(RHSMeasurements)))
	
	# Hardcoded 20201209
	# Take a slice of the joitn distribution (in reality would perhaps need to interpolate this
	# Slice is taken at the radius value that we're finding mass for
	# Then calculate denominator by taking matrix multiplication
	# Ratio of the two gives the PDF
	# Expectation value of this PDF matches the mean from old (Ning et al. 2018) method
	# Integral(conditionaldist * MassSequence) / Integral(conditionaldist) = Mean(f(m|r)) = Expectation value
	# SliceofJoint = JointDist[RHSIndex, :]
	
	
	temp_denominator = ReshapedWeights
	InputIndices = ''.join(Alphabets[0:DataDict['ndim']])
	
	for j in range(len(RHSTerms)):
		rdim = RHSDimensions[j]
		indv_pdf = _find_indv_pdf(a=np.log10(MeasurementDict[RHSTerms[j]][0][i]), 
					a_std=MeasurementDict[RHSTerms[j]][1][i]/MeasurementDict[RHSTerms[j]][0][i]/np.log(10),
					deg=deg_per_dim[rdim], deg_vec=deg_vec_per_dim[rdim],
					a_max=DataDict["ndim_bounds"][rdim][1], 
					a_min=DataDict["ndim_bounds"][rdim][0], 
					Log=False) 

		ProductIndices = InputIndices.replace(Alphabets[rdim], '')
		Subscripts = InputIndices+',' +''.join(Alphabets[rdim]) + '->' + ProductIndices

		temp_denominator = TensorMultiplication(temp_denominator, indv_pdf, Subscripts=Subscripts)
		InputIndices = ProductIndices

	# Denominator = np.sum(weights * np.kron(np.ones(deg_per_dim[ldim]), indv_pdf))
	# Denominator = np.sum(np.matmul(ReshapedWeights, indv_pdf))
	
	ConditionalDist = SliceofJoint/np.sum(temp_denominator)
	
	from scipy.interpolate import UnivariateSpline	
	"""
	Radius has d' degrees
	Mass has d degrees
	weights is a 2D matrix of shape d, d'
	indv_pdf is a 1D matrix of shape 1,d'
	
	weights*indv_pdf = (1xd') x (d' x d) = (dx1)
	f(r|theta) = np.sum((dx1))
	"""
	
	
	return Numerator, Denominator


def _marginal_density(a, a_max, a_min, deg, w_hat):
	'''
	Calculate the marginal density

	Refer to Ning et al. 2018 Sec 2.2, Eq 10
	'''
	if type(a) == list:
		a = np.array(a)

	deg_vec = np.arange(1,deg+1)
	x_beta_indv = _find_indv_pdf(a,deg, deg_vec, a_max, a_min)
	x__beta_pdf = np.kron(x_beta_indv, np.repeat(1,deg))

	marg_x = np.sum(w_hat * x__beta_pdf)

	return marg_x

def cond_density_quantile(a, a_max, a_min, b_max, b_min, deg, deg_vec, w_hat, a_std=np.nan, qtl=[0.16,0.84], abs_tol=1e-8):
	'''
	Calculate 16% and 84% quantiles of a conditional density, along with the mean and variance.

	Refer to Ning et al. 2018 Sec 2.2, Eq 10

	b/a
	'''
	if type(a) == list:
		a = np.array(a)

	a_beta_indv = _find_indv_pdf(a=a, deg=deg, deg_vec=deg_vec, a_max=a_max, a_min=a_min, a_std=a_std, abs_tol=abs_tol, Log=False)
	a_beta_pdf = np.kron(np.repeat(1,np.max(deg_vec)),a_beta_indv)

	# Equation 10b Ning et al 2018
	denominator = np.sum(w_hat * a_beta_pdf)

	if denominator == 0:
		denominator = np.nan

	# Mean
	mean_beta_indv = (deg_vec * (b_max - b_min) / (deg + 1)) + b_min
	mean_beta = np.kron(mean_beta_indv,a_beta_indv)
	mean_numerator = np.sum(w_hat * mean_beta)
	mean = mean_numerator / denominator

	# Variance
	var_beta_indv = (deg_vec * (deg - deg_vec + 1) * (b_max - b_min)**2 / ((deg + 2)*(deg + 1)**2))
	var_beta = np.kron(var_beta_indv,a_beta_indv)
	var_numerator = np.sum(w_hat * var_beta)
	var = var_numerator / denominator

	# Quantile

	def pbeta_conditional_density(j):
		if type(j) == np.ndarray:
			j = j[0]
		b_indv_cdf = np.array([beta.cdf((j - b_min)/(b_max - b_min), a=d, b=deg - d + 1) for d in deg_vec])
		quantile_numerator = np.sum(w_hat * np.kron(b_indv_cdf,a_beta_indv))
		p_beta = quantile_numerator / denominator

		return p_beta


	def conditional_quantile(q):
		def g(x):
			return pbeta_conditional_density(x) - q
		return root(g, a=b_min, b=b_max, xtol=1e-8, rtol=1e-12)


	if np.size(qtl) == 1:
		qtl = [qtl]
	quantile = [conditional_quantile(i) for i in qtl]

	return mean, var, quantile, denominator, a_beta_indv


def calculate_joint_distribution(DataDict, weights, deg_per_dim, save_path, verbose, abs_tol):
	'''
	# X_points, X_min, X_max, Y_points, Y_min, Y_max, weights, abs_tol):
	Calculcate the joint distribution of Y and X (Y and X) : f(y,x|w,d,d')
	Refer to Ning et al. 2018 Sec 2.1, Eq 7
	
	INPUT:
	weights = Padded weights with dimensionality (1 x (d1 x d2 x d3 x .. x dn)) where di are the degrees per dimension
	
	OUTPUT:
	joint distribution = 
	indv_pdf_per_dim = This is the individual PDF for each point in the sequence . 
		It is a list of 1-D vectors, where the number of elements in the list = ndim.
		The number of elements in each vector is the number of degrees for that dimension
	'''
	
	message = 'Calculating Joint Distribution at {}'.format(datetime.datetime.now())
	_ = _logging(message=message, filepath=save_path, verbose=verbose, append=True)

	
	# DataSequence is a uniformly distributed (in log space) sequence of equal size for each dimension (typically 100).
	NPoints = len(DataDict['DataSequence'][0])
	deg_vec_per_dim = [np.arange(1, deg+1) for deg in deg_per_dim] 
	ndim = DataDict['ndim']

	joint = np.zeros([NPoints for i in range(ndim)])
	indv_pdf_per_dim = [np.zeros((NPoints, deg)) for deg in deg_per_dim]
	Indices = np.zeros(ndim, dtype=int)
	
	def JointRecursiveMess(dim):
		for i in range(NPoints):
			Indices[dim] =  i
			
			# Here log is false, since the measurements are drawn from DataSequence which is uniformly 
			# distributed in log space (between Max and Min)
			indv_pdf_per_dim[dim][i,:] = _find_indv_pdf(a=DataDict["DataSequence"][dim][i], 
				a_std=np.nan,
				deg=deg_per_dim[dim], deg_vec=deg_vec_per_dim[dim],
				a_max=DataDict["ndim_bounds"][dim][1], 
				a_min=DataDict["ndim_bounds"][dim][0], 
				Log=False)
				
			# print(Indices, dim, np.sum(indv_pdf_per_dim[dim][i,:]))
				
			if dim == ndim-1:
				temporary = np.reshape(weights, deg_per_dim)
				# print('-----')
				# Perform matrix multiplication to multiply the individual PDFs with the weights and obtain the Joint Distribution
				for dd in range(ndim):
					# print(Indices, dd, np.sum(indv_pdf_per_dim[dd][Indices[dd],:]), np.sum(temporary), joint[tuple(Indices)])
					temporary = TensorMultiplication(indv_pdf_per_dim[dd][Indices[dd],:], temporary)
					if dd == ndim-1:
						joint[tuple(Indices)] = temporary
						# print(joint[tuple(Indices)])
			else:
				# print("Init next loop for ", Indices, dim+1)
				JointRecursiveMess(dim+1)
				
	JointRecursiveMess(0)

	return joint, indv_pdf_per_dim


def TensorMultiplication(A, B, Subscripts=None):
	"""
	Calculate the tensor contraction of A and B.
	If Subscripts = None: Calculate along the last dimension of A, and the first dimension of B 
		which must match in size.
		C[i,j,...,l,...,n] = A[i,j,...,k] * B[k,l,...n]
		NOTE: if dimension n is length 1, C is reshaped to reduce that dimension.
	else:
		Provide Subscripts example: 'ijk,klm -> ijlm'
	"""
	
	
	Alphabets = [chr(i) for i in range(105,123)] # Lower case ASCII characters
	NdimA = A.ndim
	NdimB = B.ndim
	
	if Subscripts is None:
		Subscripts = ''.join(Alphabets[0:NdimA])+ ',' +\
			''.join(Alphabets[NdimA-1:NdimA+NdimB-1]) + '->' +\
			 ''.join(Alphabets[0:NdimA-1]+Alphabets[NdimA:NdimA+NdimB-1])
	return np.einsum(Subscripts, A, B)


def rank_FI_matrix(C_pdf, w):
	"""
	INPUT:
		C_pdf: 2d array with [n, (deg-2)^2]
		w: 2D array with [deg-2, deg-2]

	"""
	n = np.shape(C_pdf)[1] # number of data points

	score = C_pdf/np.matmul(C_pdf.T, w)
	FI = np.matmul(score, score.T/n)
	Rank = np.linalg.matrix_rank(FI)

	return Rank




def _rank_FI_matrix(C_pdf, w):
	"""
	INPUT:
	C_pdf: 2d array with [n, (deg-2)^2]
	w: 2D array with [deg-2, deg-2]

	"""
	n = np.shape(C_pdf)[1] # number of data points
	deg_min2_sq = np.shape(C_pdf)[0]

	#C_pdf_transpose = transpose(C_pdf)

	F = np.zeros((deg_min2_sq, deg_min2_sq))

	start = datetime.datetime.now()
	for i in range(n):
		F += np.outer(C_pdf[:,i], C_pdf[:,i].T) / ((C_pdf[:,i].T * w)**2)
	end = datetime.datetime.now()
	print(end-start)
   	#F += reshape(kron(C_pdf[:,i], C_pdf_transpose[i,:]), (deg_min2_sq, deg_min2_sq)) / sum(C_pdf_transpose[i,:] .* w)^2
   	#println(i)

	F = F/n
	return F
