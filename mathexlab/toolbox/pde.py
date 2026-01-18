import numpy as np
import scipy.integrate
from mathexlab.math.arrays import MatlabArray

# ==========================================================
# HELPER: Broadcasting (Pure NumPy)
# ==========================================================
def _broadcast_to_array(val, shape_ref):
    """Ensures scalar returns from pdefun become arrays."""
    # Fast path for scalars
    if np.ndim(val) == 0:
        return np.full_like(shape_ref, val, dtype=np.float64)
    return np.asarray(val, dtype=np.float64)

# ==========================================================
# PDE KERNEL (Pure Python + Optimized NumPy)
# ==========================================================
# Note: We removed @jit because passing Python callbacks (pdefun) 
# into a Numba function triggers TypingErrors. 
# Pure NumPy is sufficiently fast (Vectorized) for this N=1000 workload.

def _pde_loop_kernel_vectorized(t, u, x, m, pdefun, bcfun):
    """
    Vectorized Kernel.
    Calculates du/dt for the entire mesh in one pass using NumPy.
    """
    N = len(x)
    
    # -----------------------------------------------------
    # 1. VECTORIZED PREP
    # -----------------------------------------------------
    # Views (No copy)
    x_mid = x[1:-1]
    u_mid = u[1:-1]
    
    # Precompute grid spacing
    dx_left  = x[1:-1] - x[0:-2]
    dx_right = x[2:]   - x[1:-1]
    dx_avg   = dx_right + dx_left  # 2 * avg_dx
    
    # Gradient Estimate at Interior Nodes (Central Difference-ish)
    # Note: pdepe usually expects approximations. 
    # We use: (u_right - u_left) / (x_right - x_left)
    dudx_i = (u[2:] - u[0:-2]) / dx_avg
    
    # -----------------------------------------------------
    # 2. CALL USER FUNCTION (Python Speed)
    # -----------------------------------------------------
    # This runs once per time step. O(1) Python overhead.
    res_c, res_f, res_s = pdefun(x_mid, t, u_mid, dudx_i)
    
    c = _broadcast_to_array(res_c, x_mid)
    f = _broadcast_to_array(res_f, x_mid)
    s = _broadcast_to_array(res_s, x_mid)
    
    # -----------------------------------------------------
    # 3. FLUX & DIVERGENCE
    # -----------------------------------------------------
    # To get accurate flux divergence, we need flux at the boundaries too.
    # We calculate boundary gradients and call pdefun for endpoints.
    
    # Left Boundary (x[0])
    dudx_L = (u[1] - u[0]) / (x[1] - x[0])
    _, res_fL, _ = pdefun(x[0], t, u[0], dudx_L)
    # Handle scalar return
    f_L = float(res_fL) if np.ndim(res_fL) == 0 else res_fL[0]
    
    # Right Boundary (x[-1])
    dudx_R = (u[-1] - u[-2]) / (x[-1] - x[-2])
    _, res_fR, _ = pdefun(x[-1], t, u[-1], dudx_R)
    f_R = float(res_fR) if np.ndim(res_fR) == 0 else res_fR[0]
    
    # Construct Full Flux Array
    # This allows vectorized differentiation
    f_full = np.empty(N)
    f_full[0] = f_L
    f_full[-1] = f_R
    f_full[1:-1] = f
    
    # Divergence: (f[i+1] - f[i-1]) / 2dx
    # Using the same dx_avg from above
    dfdx = (f_full[2:] - f_full[0:-2]) / dx_avg
    
    # Geometric term (Spherical/Cylindrical)
    # Vectorized masking (No loops)
    if m > 0:
        geom = np.zeros_like(x_mid)
        # Avoid division by zero at r=0
        mask = np.abs(x_mid) > 1e-12
        geom[mask] = (m / x_mid[mask]) * f[mask]
        dfdx += geom

    # Calculate Interior du/dt
    # Prevent division by zero in c
    c = np.where(np.abs(c) < 1e-9, 1.0, c)
    
    dudt = np.zeros(N)
    dudt[1:-1] = (dfdx + s) / c

    # -----------------------------------------------------
    # 4. BOUNDARY CONDITIONS
    # -----------------------------------------------------
    res_bc = bcfun(x[0], u[0], x[-1], u[-1], t)
    pl, ql, pr, qr = res_bc
    
    # Left BC
    if abs(ql) < 1e-9:
        dudt[0] = 0.0 # Dirichlet (Approx)
    else:
        # Neumann/Robin: In pdepe, this often maps to matching the flux
        # For simple benchmarks, we copy the neighbor derivative or 0
        dudt[0] = dudt[1] 
        
    # Right BC
    if abs(qr) < 1e-9:
        dudt[-1] = 0.0
    else:
        dudt[-1] = dudt[-2]

    return dudt

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

    # BDF is required for Stiff equations (like Heat Eq)
    sol = scipy.integrate.solve_ivp(odefun, (t[0], t[-1]), y0, t_eval=t, method='BDF')
    
    return MatlabArray(sol.y.T)