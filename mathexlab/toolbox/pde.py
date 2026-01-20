import numpy as np
import scipy.integrate
from numba import jit
from mathexlab.math.arrays import MatlabArray

# ==========================================================
# HELPER: Broadcasting
# ==========================================================
def _broadcast_to_array(val, shape_ref):
    """Ensures scalar returns from pdefun become arrays."""
    if np.ndim(val) == 0:
        return np.full_like(shape_ref, val, dtype=np.float64)
    return np.asarray(val, dtype=np.float64)

# ==========================================================
# JIT KERNEL (The "Heavy Lifting")
# ==========================================================
@jit(nopython=True, cache=True)
def _core_pde_solver(t, u, x, m, c, f, s, f_L, f_R, ql, qr):
    """
    Compiled Numerics Kernel.
    Handles Flux Divergence, Geometric Singularities (m=1,2), and BCs.
    """
    N = len(x)
    
    # 1. Prepare Views
    x_mid = x[1:-1]
    
    # 2. Grid Spacing
    dx_left  = x[1:-1] - x[0:-2]
    dx_right = x[2:]   - x[1:-1]
    dx_avg   = dx_right + dx_left 
    
    # 3. Construct Full Flux Array
    # We build a temporary array to allow vectorized differentiation
    f_full = np.empty(N, dtype=np.float64)
    f_full[0] = f_L
    f_full[-1] = f_R
    f_full[1:-1] = f
    
    # 4. Divergence: (f[i+1] - f[i-1]) / 2dx
    dfdx = (f_full[2:] - f_full[0:-2]) / dx_avg
    
    # 5. Geometric Term (Spherical/Cylindrical Symmetry)
    # Singular at x=0, handled via masking
    if m > 0:
        # Equivalent to: geom = (m / x) * f
        # Numba handles this loop efficiently
        for i in range(len(x_mid)):
            xi = x_mid[i]
            if np.abs(xi) > 1e-12:
                dfdx[i] += (m / xi) * f[i]

    # 6. Assemble Time Derivatives (du/dt)
    dudt = np.zeros(N, dtype=np.float64)
    
    # Prevent division by zero in 'c' (heat capacity)
    # In-place fix for stability
    for i in range(len(c)):
        if np.abs(c[i]) < 1e-9:
            c[i] = 1.0
            
    dudt[1:-1] = (dfdx + s) / c

    # 7. Apply Boundary Conditions
    # Left BC
    if np.abs(ql) < 1e-9:
        dudt[0] = 0.0 # Dirichlet
    else:
        dudt[0] = dudt[1] # Neumann approximation
        
    # Right BC
    if np.abs(qr) < 1e-9:
        dudt[-1] = 0.0
    else:
        dudt[-1] = dudt[-2]

    return dudt

# ==========================================================
# PYTHON ORCHESTRATOR (The "Dispatcher")
# ==========================================================
def _pde_loop_kernel_vectorized(t, u, x, m, pdefun, bcfun):
    """
    Python wrapper that calls user callbacks, then passes raw data to JIT.
    """
    # -----------------------------------------------------
    # 1. PRE-CALCULATIONS (Gradient Estimate for User Function)
    # -----------------------------------------------------
    dx_left  = x[1:-1] - x[0:-2]
    dx_right = x[2:]   - x[1:-1]
    dx_avg   = dx_right + dx_left
    
    # Central difference estimate for dudx passed to pdefun
    dudx_i = (u[2:] - u[0:-2]) / dx_avg
    
    x_mid = x[1:-1]
    u_mid = u[1:-1]

    # -----------------------------------------------------
    # 2. CALL USER FUNCTIONS (Python Domain)
    # -----------------------------------------------------
    # Interior
    res_c, res_f, res_s = pdefun(x_mid, t, u_mid, dudx_i)
    c = _broadcast_to_array(res_c, x_mid)
    f = _broadcast_to_array(res_f, x_mid)
    s = _broadcast_to_array(res_s, x_mid)
    
    # Left Boundary Flux
    dudx_L = (u[1] - u[0]) / (x[1] - x[0])
    _, res_fL, _ = pdefun(x[0], t, u[0], dudx_L)
    f_L = float(res_fL) if np.ndim(res_fL) == 0 else res_fL[0]
    
    # Right Boundary Flux
    dudx_R = (u[-1] - u[-2]) / (x[-1] - x[-2])
    _, res_fR, _ = pdefun(x[-1], t, u[-1], dudx_R)
    f_R = float(res_fR) if np.ndim(res_fR) == 0 else res_fR[0]

    # Boundary Conditions
    res_bc = bcfun(x[0], u[0], x[-1], u[-1], t)
    _, ql, _, qr = res_bc

    # -----------------------------------------------------
    # 3. CALL JIT KERNEL (Compiled Domain)
    # -----------------------------------------------------
    # We pass only arrays and scalars here. No functions.
    return _core_pde_solver(t, u, x, m, c, f, s, f_L, f_R, ql, qr)

# ==========================================================
# MAIN SOLVER
# ==========================================================
def pdepe(m, pdefun, icfun, bcfun, xmesh, tspan):
    x = np.asarray(xmesh, dtype=np.float64).flatten()
    t = np.asarray(tspan, dtype=np.float64).flatten()
    N = len(x)
    m = float(m)
    
    # Initial Conditions
    y0 = np.zeros(N)
    for i in range(N):
        y0[i] = float(icfun(x[i]))

    def odefun(time, u):
        return _pde_loop_kernel_vectorized(time, u, x, m, pdefun, bcfun)

    # Solve
    sol = scipy.integrate.solve_ivp(odefun, (t[0], t[-1]), y0, t_eval=t, method='BDF')
    
    return MatlabArray(sol.y.T)