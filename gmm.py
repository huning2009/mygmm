#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GMM estimator.

"""
from __future__ import print_function, division

import numpy as np
from scipy import stats, linalg
from scipy.optimize import minimize
from hac import hac

class GMM(object):
    """GMM estimation class.

    """

    def __init__(self, theta, data):
        self.data = data
        self.theta = theta

        # Should check that the moment function exists!
        g, dg = self.moment(theta)

        # Dimensions:

        # Sample size
        self.T = g.shape[0]
        assert self.T > 0, 'Number of observations must be positive'
        # Number of moment restrictions and parameters
        self.q, self.k = dg.shape
        assert self.k == len(self.theta), 'The shape of the Jacobian is wrong,\
            the second dimension should coincide with number of parameters'
        # Degrees of freedom, scalar
        self.df = self.q - self.k
        assert self.df > 0, 'Degrees of freedom should be positive\
            for overidentification'

        # Default options:

        # Weighting matrix
        self.W = np.eye(self.q)
        # Number of GMM steps
        self.iter = 2
        # Maximum iterations for the optimizer
        self.maxiter = None
        # Optimization method
        self.method = 'BFGS'
        # Display convergence results
        self.disp = True
        # Use analytic Jacobian?
        self.use_jacob = True
        # HAC kernel type
        self.kernel = 'Bartlett'
        # HAC kernel bandwidth
        self.band = int(self.T**(1/3))
        # J-statistic
        self.J = None
        # Optimization results
        self.res = None
        # Standard errors
        self.se = None
        # T-statistics
        self.t = None
        # P-values
        self.pval = None

    def moment(self, theta):
        """Moment function.

        Computes moment restrictions and their gradients.
        Should be written for each specific problem.

        Parameters
        ----------
            theta: (k,) array
                Parameters

        Returns
        -------
            g : (T, q) array
                Matrix of moment restrictions
            dg : (q, k)
                Gradient of moment restrictions. Mean over observations

        """
        pass

    def print_results(self):
        """Print GMM estimation results.

        """
        np.set_printoptions(precision=3, suppress=True)

        print('-' * 60)
        print('The final results are')
        print(self.res.message)
        print('theta   = ', self.theta)
        print('s.e.    = ', self.se)
        print('t-stat  = ', self.t)
        print('J-stat  = %0.2f' % self.J)
        print('df      = ', self.df)
        print('p-value = %0.2f' % self.pval)
        print('-' * 60)


    def gmmest(self):
        """Multiple step GMM estimation procedure.

        """
        print('Theta 0 = ', self.theta)
        # First step GMM
        for i in range(self.iter):
            # Compute optimal weighting matrix
            # Only after the first step
            if i > 0:
                self.W = self.weights(self.theta)

            opt_options = {'disp' : self.disp, 'maxiter' : self.maxiter}
            self.res = minimize(self.gmmobjective, self.theta,
                                method=self.method,
                                jac=self.use_jacob,
                                options=opt_options)
            # Update parameter for the next step
            self.theta = self.res.x
            print('Theta', i+1, ' = ', self.theta)
            print('f', i+1, ' = ', self.res.fun * self.T)

        # k x k
        V = self.varest(self.theta)
        # J-statistic
        self.J = self.res.fun * self.T
        # p-value of the J-test, scalar
        self.pval = 1 - stats.chi2.cdf(self.J, self.df)
        # t-stat for each parameter, 1 x k
        self.se = np.diag(V)**.5
        # t-stat for each parameter, 1 x k
        self.t = self.theta / self.se

    def gmmobjective(self, theta):
        """GMM objective function and its gradient.

        Parameters
        ----------
            theta: (k,) array
                Parameters

        Returns
        -------
            f : float
                Value of objective function, see Hansen (2012, p.241)
            df : (k,) array
                Derivative of objective function.
                Depends on the switch 'use_jacob'
        """
        #theta = theta.flatten()
        # g - T x q, time x number of moments
        # dg - q x k, time x number of moments
        g, dg = self.moment(theta)
        # g - 1 x q, 1 x number of moments
        g = g.mean(0).flatten()
        # 1 x 1
        f = float(g.dot(self.W).dot(g.T))
        assert f >= 0, 'Objective function should be non-negative'

        if self.use_jacob:
            # 1 x k
            df = 2 * g.dot(self.W).dot(dg).flatten()

            return f, df
        else:
            return f

    def weights(self, theta):
        """
        Optimal weighting matrix

        Parameters
        ----------
            theta : (k,) array
                Parameters

        Returns
        -------
            invS : (q, q) array
                Inverse of moments covariance matrix

        """
        # g - T x q, time x number of moments
        # dg - q x k, time x number of moments
        g = self.moment(theta)[0]
        # q x q
        S = hac(g, self.kernel, self.band)
        # q x q
        invS = linalg.pinv(S)

        return invS

    def varest(self, theta):
        """Estimate variance matrix of parameters.

        Parameters
        ----------
            theta : (k,)
                Parameters

        Returns
        -------
            V : (k, k) array
                Variance matrix of parameters

        """
        # g - T x q, time x number of moments
        # dg - q x k, time x number of moments
        dg = self.moment(theta)[1]
        # q x q
        S = self.weights(theta)
        # k x k
        # What if k = 1?
        V = linalg.pinv(dg.T.dot(S).dot(dg)) / self.T

        return V

if __name__ == '__main__':
    import test_mygmm
    test_mygmm.test_mygmm()
