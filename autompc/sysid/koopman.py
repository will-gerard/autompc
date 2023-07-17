import numpy as np
import numpy.linalg as la
import scipy.linalg as sla
from pdb import set_trace
from sklearn.linear_model import  Lasso

from .model import Model, ModelFactory
from .stable_koopman import stabilize_discrete

import ConfigSpace as CS
import ConfigSpace.hyperparameters as CSH
import ConfigSpace.conditions as CSC

class KoopmanFactory(ModelFactory):
    """
    This class identifies Koopman models of the form :math:`\dot{\Psi}(x) = A\Psi(x) + Bu`. 
    Given states :math:`x \in \mathbb{R}^n`, :math:`\Psi(x) \in \mathbb{R}^N` ---termed Koopman 
    basis functions--- are used to lift the dynamics in a higher-dimensional space
    where nonlinear functions of the system states evolve linearly. The identification
    of the Koopman model, specified by the A and B matrices, can be done in various ways, 
    such as solving a least squares solution :math:`\|\dot{\Psi}(x) - [A, B][\Psi(x),u]^T\|`.
    
    The choice of the basis functions is an open research question. In this implementation, 
    we choose basis functions that depend only on the system states and not the control, 
    in order to derive a representation that is amenable for LQR control. 
    

    Hyperparameters:

    - *method* (Type: str, Choices: ["lstsq", "lasso", "stable"]): Method for training Koopman
      operator.
    - *lasso_alpha* (Type: float, Low: 10^-10, High: 10^2, Defalt: 1.0): α parameter for Lasso
      regression. (Conditioned on method="lasso").
    - *poly_basis* (Type: bool): Whether to use polynomial basis functions.
    - *poly_degree* (Type: int, Low: 2, High: 8, Default: 3): Maximum degree of polynomial basis
      functions. (Conditioned on poly_basis="true").
    - *trig_basis* (Type: bool): Whether to use trig basis functions.
    - *trig_freq* (Type: int, Low: 1, High: 8, Default: 1): Maximum frequency of trig functions.
    - *product_terms* (Type: bool): Whether to include cross-product terms.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Model = Koopman
        self.name = "Koopman"

    def get_configuration_space(self):
        cs = CS.ConfigurationSpace()
        method = CSH.CategoricalHyperparameter("method", choices=["lstsq", "lasso",
            "stable"])
        lasso_alpha = CSH.UniformFloatHyperparameter("lasso_alpha", 
                lower=1e-10, upper=1e2, default_value=1.0, log=True)
        use_lasso_alpha = CSC.InCondition(child=lasso_alpha, parent=method, 
                values=["lasso"])

        poly_basis = CSH.CategoricalHyperparameter("poly_basis", 
                choices=["true", "false"], default_value="false")
        poly_degree = CSH.UniformIntegerHyperparameter("poly_degree", lower=2, upper=8,
                default_value=3)
        use_poly_degree = CSC.InCondition(child=poly_degree, parent=poly_basis,
                values=["true"])

        trig_basis = CSH.CategoricalHyperparameter("trig_basis", 
                choices=["true", "false"], default_value="false")
        trig_freq = CSH.UniformIntegerHyperparameter("trig_freq", lower=1, upper=8,
                default_value=1)
        use_trig_freq = CSC.InCondition(child=trig_freq, parent=trig_basis,
                values=["true"])

        product_terms = CSH.CategoricalHyperparameter("product_terms",
                choices=["false"], default_value="false")


        cs.add_hyperparameters([method, poly_basis, poly_degree,
            trig_basis, trig_freq, product_terms, lasso_alpha])
        cs.add_conditions([use_poly_degree, use_trig_freq, use_lasso_alpha])

        return cs

class Koopman(Model):
    def __init__(self, system, method, lasso_alpha=None, poly_basis=False,
            poly_degree=1, trig_basis=False, trig_freq=1, product_terms=False,
            use_cuda=None):
        super().__init__(system)

        self.method = method
        if not lasso_alpha is None:
            self.lasso_alpha = lasso_alpha
        else:
            self.lasso_alpha = None
        if type(poly_basis) == str:
            poly_basis = True if poly_basis == "true" else False
        self.poly_basis = poly_basis
        self.poly_degree = poly_degree
        if type(trig_basis) == str:
            trig_basis = True if trig_basis == "true" else False
        self.trig_basis = trig_basis
        self.trig_freq = trig_freq
        if type(product_terms) == str:
            self.product_terms = True if product_terms == "true" else False

        self.basis_funcs = [lambda x: x]
        if self.poly_basis:
            self.basis_funcs += [lambda x: x**i for i in range(2, 1+self.poly_degree)]
        if self.trig_basis:
            for i in range(1, 1+self.poly_degree):
                self.basis_funcs += [lambda x: np.sin(i*x), lambda x : np.cos(i*x)]

    def _apply_basis(self, state):
        tr_state = [b(x) for b in self.basis_funcs for x in state]
        if self.product_terms:
            pr_terms = []
            for i, x in enumerate(tr_state):
                for j, y in enumerate(tr_state):
                    if i < j:
                        pr_terms.append(x*y)
            tr_state += pr_terms

        return np.array(tr_state)

    def _transform_observations(self, observations):
        return np.apply_along_axis(self._apply_basis, 1, observations)

    def traj_to_state(self, traj):
        return self._transform_observations(traj.obs[:])[-1,:]

    def traj_to_states(self, traj):
        return self._transform_observations(traj.obs[:])
    
    def update_state(self, state, new_ctrl, new_obs):
        return self._apply_basis(new_obs)

    @property
    def state_dim(self):
        return len(self.basis_funcs) * self.system.obs_dim

    def train(self, trajs, silent=False):
        trans_obs = [self._transform_observations(traj.obs[:]) for traj in trajs]
        X = np.concatenate([obs[:-1,:] for obs in trans_obs]).T
        Y = np.concatenate([obs[1:,:] for obs in trans_obs]).T
        U = np.concatenate([traj.ctrls[:-1,:] for traj in trajs]).T
        
        n = X.shape[0] # state dimension
        m = U.shape[0] # control dimension    
        
        XU = np.concatenate((X, U), axis = 0) # stack X and U together
        if self.method == "lstsq": # Least Squares Solution
            AB = np.dot(Y, sla.pinv(XU))
            A = AB[:n, :n]
            B = AB[:n, n:]
        elif self.method == "lasso":  # Call lasso regression on coefficients
            print("Call Lasso")
            clf = Lasso(alpha=self.lasso_alpha)
            clf.fit(XU.T, Y.T)
            AB = clf.coef_
            A = AB[:n, :n]
            B = AB[:n, n:]
        elif self.method == "stable": # Compute stable A, and B
            print("Compute Stable Koopman")
            # call function
            A, _, _, _, B, _ = stabilize_discrete(X, U, Y)
            A = np.real(A)
            B = np.real(B)

        self.A, self.B = A, B

    def pred(self, state, ctrl):
        xpred = self.A @ state + self.B @ ctrl
        return xpred

    def pred_batch(self, states, ctrls):
        statesnew = self.A @ states.T + self.B @ ctrls.T

        return statesnew.T

    def pred_diff(self, state, ctrl):
        xpred = self.A @ state + self.B @ ctrl

        return xpred, np.copy(self.A), np.copy(self.B)

    def to_linear(self):
        return np.copy(self.A), np.copy(self.B)

    def get_parameters(self):
        return {"A" : np.copy(self.A),
                "B" : np.copy(self.B)}

    def set_parameters(self, params):
        self.A = np.copy(params["A"])
        self.B = np.copy(params["B"])
