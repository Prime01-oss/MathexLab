# import numpy as np
# import scipy.integrate
# import scipy.signal
# import scipy.fft
# import scipy.optimize
# import scipy.interpolate
# from .arrays import MatlabArray

# # ==========================================================
# # HELPER: ODE Solution Struct
# # ==========================================================
# class ODESolution:
#     """Emulates a MATLAB struct for ODE results (sol.x, sol.y, sol.te, sol.ye, sol.ie)."""
#     def __init__(self, t, y, te=None, ye=None, ie=None):
#         self.x = MatlabArray(t)   # Independent var
#         self.y = MatlabArray(y)
#         self.t = self.x 
        
#         # Events support
#         self.te = MatlabArray(te) if te is not None else MatlabArray([])
#         self.ye = MatlabArray(ye) if ye is not None else MatlabArray([])
#         self.ie = MatlabArray(ie) if ie is not None else MatlabArray([])
    
#     def __repr__(self):
#         base = f"<Structure with fields: x {self.x.shape}, y {self.y.shape}"
#         if self.te.size > 0:
#             base += f", te {self.te.shape}"
#         return base + ">"
    
#     def __iter__(self):
#         """
#         Support unpacking: [t, y] = ode45(...)
#         Only yield the primary outputs (t, y) to match the 2-variable expectation.
#         Events must be accessed via struct fields (sol.te) if needed.
#         """
#         yield self.x
#         yield self.y

#     def __getitem__(self, key):
#         # Handle Integer Indexing (legacy or specific index access)
#         if isinstance(key, int):
#             if key == 0: return self.x
#             if key == 1: return self.y
#             # Stop iteration for unpacking at 2 elements if __iter__ wasn't defined
#             if key == 2: return self.te
#             if key == 3: return self.ye
#             if key == 4: return self.ie
#             raise IndexError(f"ODESolution index {key} out of range")

#         # Handle String Indexing (struct fields)
#         if key in ('x', 't'): return self.x
#         if key == 'y': return self.y
#         if key == 'te': return self.te
#         if key == 'ye': return self.ye
#         if key == 'ie': return self.ie
#         raise KeyError(f"Field '{key}' not found in solution structure.")

# def _wrap_ode_func(fun):
#     """Wraps a MathexLab function @(t,y) to work with SciPy."""
#     def wrapper(t, y):
#         # [FIX] Ensure y is a column vector (Nx1) so y[i] indexing works as expected (returning scalar rows)
#         # scipy passes y as (N,). MatlabArray((N,)) becomes (1, N).
#         # We need (N, 1).
#         y_col = y.reshape(-1, 1) 
#         res = fun(t, MatlabArray(y_col))
        
#         # Case 1: Function returns a single MatlabArray (e.g. column vector)
#         if isinstance(res, MatlabArray):
#             return res._data.flatten()
            
#         # Case 2: Function returns a list/tuple (e.g. [y(2), -y(1)])
#         # Each element might be a 1x1 MatlabArray object, which crashes np.asarray(float)
#         if isinstance(res, (list, tuple)):
#             # Robustly convert each element to float
#             return np.array([float(x) for x in res])
            
#         return np.asarray(res).flatten()
#     return wrapper

# # ==========================================================
# # DIFFERENTIAL EQUATION SOLVERS (ODE)
# # ==========================================================

# def ode45(fun, tspan, y0, events=None):
#     """RK45 Solver. Supports 'events' (SciPy style)."""
#     return _solve_ivp_generic(fun, tspan, y0, method='RK45', events=events)

# def ode23(fun, tspan, y0, events=None):
#     """RK23 Solver."""
#     return _solve_ivp_generic(fun, tspan, y0, method='RK23', events=events)

# def ode15s(fun, tspan, y0, events=None):
#     """BDF Solver (Stiff)."""
#     return _solve_ivp_generic(fun, tspan, y0, method='BDF', events=events)

# def _solve_ivp_generic(fun, tspan, y0, method, events=None):
#     # 1. Handle Time Span
#     if isinstance(tspan, MatlabArray):
#         ts = tspan._data
#     else:
#         ts = np.array(tspan)
#     ts = ts.flatten()
#     t_start, t_end = float(ts[0]), float(ts[-1])

#     # Determine t_eval (if tspan has specific points)
#     t_eval = None
#     if ts.size > 2:
#         t_eval = ts

#     # 2. Handle Initial Conditions
#     if isinstance(y0, MatlabArray):
#         y0_val = y0._data.flatten()
#     else:
#         y0_val = np.asarray(y0).flatten()
    
#     # 3. Run Solver
#     sol = scipy.integrate.solve_ivp(
#         _wrap_ode_func(fun), 
#         (t_start, t_end), 
#         y0_val, 
#         method=method,
#         events=events,
#         t_eval=t_eval
#     )
    
#     # Extract event data if present
#     te, ye, ie = None, None, None
#     if sol.t_events is not None and len(sol.t_events) > 0:
#         flat_te = []
#         flat_ye = []
#         flat_ie = []
#         for i, (t_ev, y_ev) in enumerate(zip(sol.t_events, sol.y_events)):
#             if t_ev.size > 0:
#                 flat_te.append(t_ev)
#                 flat_ye.append(y_ev)
#                 flat_ie.append(np.full(t_ev.shape, i+1))
        
#         if flat_te:
#             te = np.concatenate(flat_te)
#             ye = np.concatenate(flat_ye)
#             ie = np.concatenate(flat_ie)
            
#             idx = np.argsort(te)
#             te = te[idx]
#             ye = ye[idx]
#             ie = ie[idx]

#     # [FIX] Transpose y to shape (Time, States) and ensure t is a column vector
#     # SciPy returns y as (States, Time). MATLAB expects [Time, States].
#     t_out = sol.t.reshape(-1, 1)
#     y_out = sol.y.T

#     return ODESolution(t_out, y_out, te, ye, ie)

# def bvp4c(ode_fun, bc_fun, solinit):
#     """Boundary Value Problems."""
#     x_mesh = solinit.x._data if isinstance(solinit.x, MatlabArray) else solinit.x
#     y_guess = solinit.y._data if isinstance(solinit.y, MatlabArray) else solinit.y
    
#     def wrapped_ode(x, y):
#         res = ode_fun(MatlabArray(x), MatlabArray(y))
#         return res._data if isinstance(res, MatlabArray) else np.asarray(res)

#     def wrapped_bc(ya, yb):
#         res = bc_fun(MatlabArray(ya), MatlabArray(yb))
#         return res._data.flatten() if isinstance(res, MatlabArray) else np.asarray(res).flatten()

#     res = scipy.integrate.solve_bvp(wrapped_ode, wrapped_bc, x_mesh, y_guess)
#     return ODESolution(res.x, res.y)

# # ==========================================================
# # PARTIAL DIFFERENTIAL EQUATIONS (PDE)
# # ==========================================================

# def pdepe(m, pdefun, icfun, bcfun, xmesh, tspan):
#     """
#     sol = pdepe(m, pdefun, icfun, bcfun, xmesh, tspan)
    
#     1D PDE Solver using Method of Lines.
#     Solves: c * du/dt = x^-m * d/dx(x^m * f) + s
#     Supports m=0 (Slab), m=1 (Cylindrical), m=2 (Spherical).
#     """
#     x = np.asarray(xmesh).flatten()
#     t = np.asarray(tspan).flatten()
#     N = len(x)
#     m = float(m)
    
#     # 1. Initial Conditions
#     y0 = np.zeros(N)
#     for i in range(N):
#         res = icfun(x[i])
#         y0[i] = float(res)

#     # 2. ODE System (Method of Lines Discretization)
#     def odefun(time, u):
#         dudt = np.zeros_like(u)
        
#         # Loop interior points
#         for i in range(1, N-1):
#             # Mesh data
#             dx_left = x[i] - x[i-1]
#             dx_right = x[i+1] - x[i]
            
#             # Solution values
#             ui = u[i]
#             u_left = u[i-1]
#             u_right = u[i+1]
            
#             # Gradient approx for calling pdefun
#             dudx_i = (u_right - u_left) / (dx_right + dx_left)
            
#             # Get PDE coefficients: [c, f, s] = pdefun(x, t, u, dudx)
#             c, f, s = pdefun(x[i], time, ui, dudx_i)
#             c, f, s = float(c), float(f), float(s)
            
#             # --- Geometric Flux Term: x^-m * d/dx(x^m * f) ---
#             # This expands to: df/dx + (m/x)*f
            
#             # 1. Calculate flux 'f' at boundaries (left and right midpoints)
#             # Estimate u and dudx at i+1/2 and i-1/2
            
#             # Right neighbor props
#             u_R = u[min(i+1, N-1)]
#             dudx_R_est = (u_R - ui) / dx_right
#             cR, fR, sR = pdefun(x[i+1], time, u_R, dudx_R_est)
            
#             # Left neighbor props
#             u_L = u[max(0, i-1)]
#             dudx_L_est = (ui - u_L) / dx_left
#             cL, fL, sL = pdefun(x[i-1], time, u_L, dudx_L_est)

#             # Central difference of flux f
#             fR = float(fR); fL = float(fL)
#             dfdx = (fR - fL) / (dx_right + dx_left) # Simplified central
            
#             # 2. Geometric source term
#             geom_term = 0.0
#             if m > 0 and abs(x[i]) > 1e-12:
#                 geom_term = (m / x[i]) * f
            
#             if abs(c) < 1e-9: c = 1.0 # Prevent division by zero
            
#             dudt[i] = (dfdx + geom_term + s) / c

#         # Boundaries
#         # [pl, ql, pr, qr] = bcfun(xl, ul, xr, ur, t)
#         res = bcfun(x[0], u[0], x[-1], u[-1], time)
#         pl, ql, pr, qr = [float(z) for z in res]
        
#         # Left BC: pl + ql * f = 0
#         if abs(ql) < 1e-9:
#             dudt[0] = 0 # Dirichlet (fixed u)
#         else:
#             dudt[0] = dudt[1] # Approx Neumann
            
#         # Right BC: pr + qr * f = 0
#         if abs(qr) < 1e-9:
#             dudt[-1] = 0
#         else:
#             dudt[-1] = dudt[-2]

#         return dudt

#     # 3. Solve using stiff solver (ODEs from PDEs are usually stiff)
#     sol = scipy.integrate.solve_ivp(odefun, (t[0], t[-1]), y0, t_eval=t, method='BDF')
    
#     # Return shape: [Time, Space] (MATLAB convention)
#     return MatlabArray(sol.y.T)

# # ==========================================================
# # INTERPOLATION & GRIDDING
# # ==========================================================

# def interp1(x, y, xi, method='linear', extrap=None):
#     """
#     yi = interp1(x, y, xi, method)
#     Methods: 'linear', 'nearest', 'cubic', 'spline'
#     """
#     x_d = np.asarray(x).flatten()
#     y_d = np.asarray(y)
#     xi_d = np.asarray(xi)

#     # [FIX] Handle Row Vectors (1xN) which are standard in MathexLab
#     if y_d.ndim == 2 and (y_d.shape[0] == 1 or y_d.shape[1] == 1) and y_d.size == x_d.size:
#         y_d = y_d.flatten()

#     fill_value = "extrapolate" if extrap is None else extrap
    
#     # Use CubicSpline for robust spline interpolation
#     if method in ('spline', 'cubic', 'pchip'):
#         cs = scipy.interpolate.CubicSpline(x_d, y_d, extrapolate=True if extrap is None else False)
#         return MatlabArray(cs(xi_d))
    
#     f = scipy.interpolate.interp1d(x_d, y_d, kind=method, fill_value=fill_value, bounds_error=False)
#     return MatlabArray(f(xi_d))

# def interp2(X, Y, Z, Xi, Yi, method='linear'):
#     """
#     zi = interp2(X, Y, Z, Xi, Yi)
#     """
#     # Prepare grid axes
#     x_edge = np.asarray(X)[0, :]
#     y_edge = np.asarray(Y)[:, 0]
#     z_data = np.asarray(Z)
    
#     # RegularGridInterpolator expects (points_1, points_2) corresponding to matrix indexing (ij)
#     # MATLAB meshgrid(x,y) produces X (rows vary x) and Y (cols vary y).
#     # We must match SciPy's expectation.
#     interp = scipy.interpolate.RegularGridInterpolator(
#         (y_edge, x_edge), z_data, method=method, bounds_error=False, fill_value=None
#     )
    
#     # Stack query points
#     Xi_d = np.asarray(Xi)
#     Yi_d = np.asarray(Yi)
#     pts = np.stack((Yi_d.flatten(), Xi_d.flatten()), axis=-1)
    
#     vals = interp(pts)
#     return MatlabArray(vals.reshape(Xi_d.shape))

# def griddata(x, y, v, xq, yq, method='linear'):
#     """
#     zq = griddata(x, y, v, xq, yq, method)
#     Fits a surface to scattered data.
#     """
#     points = np.stack((np.asarray(x).flatten(), np.asarray(y).flatten()), axis=-1)
#     values = np.asarray(v).flatten()
#     xi = (np.asarray(xq), np.asarray(yq))
    
#     res = scipy.interpolate.griddata(points, values, xi, method=method)
#     return MatlabArray(res)

# # ==========================================================
# # NUMERICAL INTEGRATION
# # ==========================================================

# def trapz(y, x=None):
#     """Trapezoidal numerical integration."""
#     y_data = y._data if isinstance(y, MatlabArray) else np.array(y)
    
#     if x is None:
#         return MatlabArray(scipy.integrate.trapezoid(y_data))
    
#     x_data = x._data if isinstance(x, MatlabArray) else np.array(x)
#     return MatlabArray(scipy.integrate.trapezoid(y_data, x_data))

# def cumtrapz(y, x=None):
#     """Cumulative trapezoidal numerical integration."""
#     y_data = y._data if isinstance(y, MatlabArray) else np.array(y)
    
#     if x is None:
#         res = scipy.integrate.cumulative_trapezoid(y_data, initial=0)
#     else:
#         x_data = x._data if isinstance(x, MatlabArray) else np.array(x)
#         res = scipy.integrate.cumulative_trapezoid(y_data, x_data, initial=0)
        
#     return MatlabArray(res)

# def integral(fun, xmin, xmax):
#     """
#     Adaptive Quadrature (like MATLAB 'integral').
#     q = integral(fun, xmin, xmax)
#     """
#     xmin = float(xmin._data) if isinstance(xmin, MatlabArray) else float(xmin)
#     xmax = float(xmax._data) if isinstance(xmax, MatlabArray) else float(xmax)
    
#     def wrapped(x):
#         res = fun(x)
#         return float(res._data) if isinstance(res, MatlabArray) else float(res)

#     val, err = scipy.integrate.quad(wrapped, xmin, xmax)
#     return MatlabArray(val)

# # ==========================================================
# # SIGNAL PROCESSING & TRANSFORMS
# # ==========================================================
# def fft(x, n=None, dim=-1):
#     data = x._data if isinstance(x, MatlabArray) else x
#     return MatlabArray(scipy.fft.fft(data, n=n, axis=dim))

# def ifft(x, n=None, dim=-1):
#     data = x._data if isinstance(x, MatlabArray) else x
#     return MatlabArray(scipy.fft.ifft(data, n=n, axis=dim))

# def fftshift(x, axes=None):
#     data = x._data if isinstance(x, MatlabArray) else np.array(x)
#     return MatlabArray(np.fft.fftshift(data, axes=axes))

# def ifftshift(x, axes=None):
#     data = x._data if isinstance(x, MatlabArray) else np.array(x)
#     return MatlabArray(np.fft.ifftshift(data, axes=axes))

# def spectrogram(x, window=None, noverlap=None, nfft=None, fs=1.0):
#     """
#     [S, F, T] = spectrogram(x, window, noverlap, nfft, fs)
#     """
#     x_data = np.asarray(x).flatten()
    
#     if nfft is None: nfft = 256
    
#     f, t, Sxx = scipy.signal.spectrogram(
#         x_data, fs=fs, window=('hann' if window is None else window),
#         nperseg=nfft, noverlap=noverlap
#     )
#     # Return as [S, F, T] to match common usage
#     return MatlabArray(Sxx), MatlabArray(f), MatlabArray(t)

# def pwelch(x, window='hann', noverlap=None, nfft=None, fs=1.0):
#     """
#     [pxx, f] = pwelch(x, window, noverlap, nfft, fs)
#     Power spectral density estimate (Welch's method).
#     """
#     x_data = np.asarray(x).flatten()
    
#     if nfft is None: nfft = 256
    
#     f, Pxx = scipy.signal.welch(
#         x_data, fs=fs, window=window, 
#         nperseg=nfft, noverlap=noverlap
#     )
#     return MatlabArray(Pxx), MatlabArray(f)

# def findpeaks(data, **kwargs):
#     """
#     [pks, locs] = findpeaks(data)
#     Wrapper for scipy.signal.find_peaks.
    
#     Returns peaks (pks) and their locations (locs).
#     """
#     x = np.asarray(data).flatten()
#     if isinstance(data, MatlabArray):
#         x = data._data.flatten()
        
#     # Wrapper maps common kwargs if needed, or passes through
#     idxs, properties = scipy.signal.find_peaks(x, **kwargs)
    
#     pks = x[idxs]
#     # Return 1-based indices for MATLAB compatibility
#     return MatlabArray(pks), MatlabArray(idxs + 1)

# def roots(p):
#     coeffs = p._data.flatten() if isinstance(p, MatlabArray) else np.array(p).flatten()
#     return MatlabArray(np.roots(coeffs))

# def polyval(p, x):
#     coeffs = p._data.flatten() if isinstance(p, MatlabArray) else np.array(p).flatten()
#     val_x = x._data if isinstance(x, MatlabArray) else x
#     return MatlabArray(np.polyval(coeffs, val_x))

# # ==========================================================
# # GEOMETRY
# # ==========================================================

# # [FIX] meshgrid: Make 'y' optional to support meshgrid(x) -> meshgrid(x,x)
# def meshgrid(x, y=None):
#     x_data = x._data if isinstance(x, MatlabArray) else np.array(x)
    
#     if y is None:
#         y_data = x_data
#     else:
#         y_data = y._data if isinstance(y, MatlabArray) else np.array(y)
        
#     X, Y = np.meshgrid(x_data, y_data)
#     return MatlabArray(X), MatlabArray(Y)

# def sphere(n=20):
#     theta = np.linspace(0, 2*np.pi, int(n)+1)
#     phi = np.linspace(0, np.pi, int(n)+1)
#     theta, phi = np.meshgrid(theta, phi)
#     x = np.sin(phi) * np.cos(theta)
#     y = np.sin(phi) * np.sin(theta)
#     z = np.cos(phi)
#     return MatlabArray(x), MatlabArray(y), MatlabArray(z)

# def cylinder(r=1, n=20):
#     theta = np.linspace(0, 2*np.pi, int(n)+1)
#     x = r * np.cos(theta)
#     y = r * np.sin(theta)
#     X = np.array([x, x])
#     Y = np.array([y, y])
#     Z = np.array([np.zeros_like(x), np.ones_like(x)])
#     return MatlabArray(X), MatlabArray(Y), MatlabArray(Z)

# def gradient(f, *varargs):
#     data = f._data if isinstance(f, MatlabArray) else f
#     grads = np.gradient(data, *varargs)
#     if isinstance(grads, list):
#         return tuple(MatlabArray(g) for g in grads)
#     return MatlabArray(grads)

# def cross(a, b):
#     val_a = a._data if isinstance(a, MatlabArray) else a
#     val_b = b._data if isinstance(b, MatlabArray) else b
#     return MatlabArray(np.cross(val_a, val_b))

# def dot(a, b):
#     val_a = a._data if isinstance(a, MatlabArray) else a
#     val_b = b._data if isinstance(b, MatlabArray) else b
#     return MatlabArray(np.vdot(val_a, val_b))