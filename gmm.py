import numpy as np
from scipy import stats, linalg
from scipy.optimize import minimize
from hac import hac
#from numba import autojit

class GMM(object):
    
    def __init__(self, theta, data):
        self.data = data
        self.theta = theta
        
        g, dg = self.moment(theta)
        # Dimensions:
        # Sample size
        self.T = g.shape[0]
        # Number of moment restrictions
        self.q = dg.shape[0]
        # Number of parameters
        self.k = len(self.theta)
        # Degrees of freedom, scalar
        self.df = self.q - self.k
        
        # Default options:
        self.W = np.eye(self.q)
        self.Iter = 2
        self.maxiter = 10
        self.method = 'BFGS'
        self.disp = True
        # Should be determined automatically by counting the number of returns
        self.use_jacob = True
        self.kernel = 'Bartlett'
        self.band = int(self.T**(1/3))
        
    def print_results(self):
        """Print results function.
        
        Does not return anything. Just prints.
        """
        np.set_printoptions(precision = 3, suppress = True)
        
        print('-' * 60)
        print('The final results are')
        print(self.res.message)
        print('theta   = ', self.res.x)
        print('s.e.    = ', self.res.se)
        print('t-stat  = ', self.res.t)
        print('J-stat  = ', '%0.2f' % self.res.fun)
        print('df      = ', self.df)
        print('p-value = ', '%0.2f' % self.res.pval)
        print('-' * 60)
    
    
    def gmmest(self):
        """Multiple step GMM estimation procedure.
        
        Args:
            theta : vector, 1 x k
            data : problem scpecific
            options : control of optimization, etc.
            
        Returns:
            gmm : object containing optimization results and statistics
            
        """
        print('Theta 0 = ', self.theta)
        # First step GMM
        for i in range(self.Iter):
            # Compute optimal weighting matrix
            # Only after the first step
            if i > 0:
                self.W = self.weights(self.theta)
            # i step GMM
            
            opt_options = {'disp' : self.disp,
                           'maxiter' : self.maxiter}
            self.res = minimize(self.gmmobjective, self.theta,
                                method = self.method,
                                jac = self.use_jacob,
                                options = opt_options)
            # Update parameter for the next step
            self.theta = self.res.x
            self.res.fun = self.T * self.res.fun
            print('Theta', i+1, ' = ', self.res.x)
            print('f', i+1, ' = ', self.res.fun)
        
        # k x k
        V = self.varest(self.theta)
        # p-value of the J-test, scalar
        self.res.pval = 1 - stats.chi2.cdf(self.res.fun, self.df)
        # t-stat for each parameter, 1 x k
        self.res.se = np.diag(V)**.5
        # t-stat for each parameter, 1 x k
        self.res.t = self.res.x / self.res.se
    
    def gmmobjective(self, theta):
        """GMM objective function and its gradient.
        
        Args:
            theta : vector, 1 x k
            data : problem scpecific
            options : control of optimization, etc.
        
        Returns:
            f : 1 x 1, value of objective function, see Hansen (2012, p.241)
            df : 1 x k, derivative of objective function, 1 x parameters
        """
        #theta = theta.flatten()
        # g - T x q, time x number of moments
        # dg - q x k, time x number of moments
        g, dg = self.moment(theta)
        # g - 1 x q, 1 x number of moments
        g = g.mean(0).flatten()
        # 1 x 1
        f = float(g.dot(self.W).dot(g.T))
        
        if self.use_jacob:
            # 1 x k    
            df = 2 * g.dot(self.W).dot(dg).flatten()
            
            return f, df
        else:
            return f
    
    def weights(self, theta):
        """
        Optimal weighting matrix
        
        Args:
            theta : vector, 1 x k
            data : problem scpecific
            options : control of optimization, etc.
            
        Returns:
            invS : q x q, moments x moments
            
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
        """Variance matrix of parameters.
        
        Args:
            theta : vector, 1 x k
            data : problem scpecific
            options : control of optimization, etc.
            
        Returns:
            V : k x k, parameters x parameters
            
        """
        # g - T x q, time x number of moments
        # dg - q x k, time x number of moments
        dg = self.moment(theta)[1]
        # q x q
        S = self.weights(theta)
        # k x k
        V = linalg.pinv(np.atleast_2d(dg.T.dot(S).dot(dg))) / self.T
        
        return V

if __name__ == '__main__':
    import test_mygmm
    test_mygmm.test_mygmm()