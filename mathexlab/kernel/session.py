import time
import os
import numpy as np
from mathexlab.language import builtins
from mathexlab.kernel.path_manager import path_manager
from mathexlab.kernel.loader import load_and_register
from mathexlab.language.functions import registry

# [FIX] Explicitly import constants to ensure they exist in session
from mathexlab.math.physics import (
    physconst, constants_struct, PhysicalConstants,
    convtemp, convlength, convmass, convforce, convpres, convenergy,
    c, G, h, k, g  # Imported directly from physics.py
)
try:
    from PySide6.QtWidgets import QApplication
except Exception:
    QApplication = None

# ------------------------------------------------------------
# Core Math Engine
# ------------------------------------------------------------
from mathexlab.math import functions as _mlfun
from mathexlab.math.arrays import (
    MatlabArray, mat, zeros, ones, eye, linspace, arange,
    sparse, full, colon, cell, _shape
)

# ------------------------------------------------------------
# Linear Algebra
# ------------------------------------------------------------
from mathexlab.math.linalg import (
    inv, det, eig, rank, norm, lu,
    svd, qr, pinv, null, orth,
    expm, sqrtm, hess, schur, chol,
    gmres, pcg, cond, eigs
)

# ------------------------------------------------------------
# Statistics & Calculus
# ------------------------------------------------------------
from mathexlab.math.statistics import (
    mean, std, max_func, min_func, sum_func,
    corrcoef, cov, histcounts, nlinfit
)

# ------------------------------------------------------------
# Optimization
# ------------------------------------------------------------
try:
    from mathexlab.math.optim import (
        fminsearch, fzero, lsqcurvefit,
        fmincon, linprog
    )
except ImportError:
    fminsearch = fzero = lsqcurvefit = fmincon = linprog = None

# ------------------------------------------------------------
# Advanced Toolbox
# ------------------------------------------------------------
from mathexlab.toolbox import (
    meshgrid, sphere, cylinder,
    gradient, cross, dot,
    ode45, ode23, ode15s, bvp4c,
    fft, ifft,
    roots, polyval, trapz, cumtrapz, integral,
    interp1, interp2, griddata,
    fftshift, ifftshift, spectrogram,
    pdepe,
    # [NEW] Import new signal tools
    fft2, ifft2, filter
)

# ------------------------------------------------------------
# Plotting
# ------------------------------------------------------------
import mathexlab.plotting as _plt_mod
from mathexlab.plotting.state import plot_manager
from mathexlab.plotting.engine import PlotEngine

# ------------------------------------------------------------
# I/O & Structs
# ------------------------------------------------------------
from mathexlab.io import (
    save_workspace, load_workspace, writematrix, saveas,
    readtable, readmatrix, csvread
)
from mathexlab.math.structs import MatlabStruct

# ------------------------------------------------------------
# Symbolic Math
# ------------------------------------------------------------
from mathexlab.math.symbolic import (
    syms, diff, int_func, expand, simplify, factor, solve, subs, limit
)

# ============================================================
# Helpers & Commands
# ============================================================

def rand(*args):
    shape = _shape(args)
    return MatlabArray(np.random.rand(*shape))

def randn(*args):
    shape = _shape(args)
    return MatlabArray(np.random.randn(*shape))

_tic_timer = 0.0

def tic():
    global _tic_timer
    _tic_timer = time.time()

def toc():
    global _tic_timer
    val = time.time() - _tic_timer
    print(f"Elapsed time is {val:.6f} seconds.")
    return val

def addpath(p):
    path_manager.add_path(p)

def rmpath(p):
    path_manager.remove_path(p)

def cd(p=None):
    if p is None:
        print(os.getcwd())
        return
    try:
        os.chdir(str(p))
        print(os.getcwd())
    except Exception as e:
        print(f"Error: {str(e)}")

def pwd():
    cwd = os.getcwd()
    print(cwd)
    return cwd

def ls(p='.'):
    try:
        items = os.listdir(str(p))
        print("\n".join(sorted(items)))
    except Exception as e:
        print(str(e))

# IMPORTANT: Mark these as commands so they execute without parentheses in CLI
cd.__mathexlab_command__ = True
pwd.__mathexlab_command__ = True
ls.__mathexlab_command__ = True

# ============================================================
# Kernel Session
# ============================================================

class KernelSession:
    """
    MATLAB-style execution kernel.
    """

    def __init__(self):
        self.globals = {}
        # We need to know what keys are "System Builtins" so we don't delete them on 'clear'
        self._builtins_set = set() 
        self.reset()

    def reset(self):
        self.globals = {}

        if getattr(plot_manager, "widget", None):
            try:
                plot_manager.set_widget(plot_manager.widget)
            except Exception:
                pass

        # Constants
        self.globals.update({
            "pi": np.pi,
            "e": np.e,
            "i": 1j,
            "j": 1j,
            "nan": np.nan,
            "inf": np.inf,
            "ans": 0,
        })

        # Arrays
        self.globals.update({
            "MatlabArray": MatlabArray,
            "mat": mat,
            "zeros": zeros,
            "ones": ones,
            "eye": eye,
            "linspace": linspace,
            "arange": arange,
            "rand": rand,
            "randn": randn,
            "sparse": sparse,
            "full": full,
            "colon": colon,
            "cell": cell,
        })

        # Helpers
        self.globals.update({
            "size": builtins.size,
            "length": builtins.length,
            "numel": builtins.numel,
            "tic": tic,
            "toc": toc,
            "struct": builtins.struct,
            "MatlabStruct": MatlabStruct,
            "deal": builtins.deal,
            "num2str": builtins.num2str,
        })

        # Path & File System
        self.globals.update({
            "addpath": addpath,
            "rmpath": rmpath,
            "cd": cd,
            "pwd": pwd,
            "ls": ls,
            "dir": ls,
        })

        # Linear Algebra
        self.globals.update({
            "inv": inv, "det": det, "eig": eig, "rank": rank, "norm": norm,
            "lu": lu, "svd": svd, "qr": qr, "pinv": pinv, "null": null, "orth": orth,
            "expm": expm, "sqrtm": sqrtm, "hess": hess, "schur": schur, "chol": chol,
            "gmres": gmres, "pcg": pcg, "cond": cond, 
            "eigs": eigs,
        })

        # Statistics
        self.globals.update({
            "mean": mean, "std": std, "max": max_func, "min": min_func, "sum": sum_func,
            "corrcoef": corrcoef, "cov": cov, "histcounts": histcounts, 
            "nlinfit": nlinfit,
        })

        # Symbolic & Calculus
        self.globals.update({
            "syms": syms,
            "diff": diff,
            "int": int_func,
            "expand": expand,
            "simplify": simplify,
            "factor": factor,
            "solve": solve,
            "subs": subs,
            "limit": limit,
        })
        
        # Physics Constants & Converters
        hbar_val = getattr(constants_struct, 'hbar', None)
        if hbar_val is None:
             hbar_val = constants_struct.h / (2 * np.pi)

        # [FIX] Use explicit imports for c, G, h, k to guarantee availability
        self.globals.update({
            "physconst": physconst,
            "PhysicalConstants": constants_struct,
            "c": c,       # From explicit import
            "G": G,       # From explicit import
            "h": h,       # From explicit import
            "hbar": hbar_val,
            "k": k,       # From explicit import
            "g": g,       # From explicit import
            "convtemp": convtemp,
            "convlength": convlength,
            "convmass": convmass,
            "convforce": convforce,
            "convpres": convpres,
            "convenergy": convenergy,
        })

        # Optimization
        if fminsearch:
            self.globals.update({
                "fminsearch": fminsearch,
                "fzero": fzero,
                "lsqcurvefit": lsqcurvefit,
                "fmincon": fmincon,
                "linprog": linprog,
            })

        # Toolbox
        self.globals.update({
            "meshgrid": meshgrid, "sphere": sphere, "cylinder": cylinder,
            "gradient": gradient, "cross": cross, "dot": dot,
            "ode45": ode45, "ode23": ode23, "ode15s": ode15s, "bvp4c": bvp4c,
            "fft": fft, "ifft": ifft, "roots": roots, "polyval": polyval,
            "trapz": trapz, "cumtrapz": cumtrapz, "integral": integral,
            "interp1": interp1, "interp2": interp2, "griddata": griddata,
            "fftshift": fftshift, "ifftshift": ifftshift, "spectrogram": spectrogram,
            "pdepe": pdepe,
            # [NEW] Register Signal Tools
            "fft2": fft2,
            "ifft2": ifft2,
            "filter": filter,
        })

        # [CRITICAL FIX] Manually register core math functions.
        # This guarantees they exist and are protected from 'clear'.
        self.globals.update({
            "sin": _mlfun.sin, "cos": _mlfun.cos, "tan": _mlfun.tan,
            "asin": _mlfun.asin, "acos": _mlfun.acos, "atan": _mlfun.atan, "atan2": _mlfun.atan2,
            "sinh": _mlfun.sinh, "cosh": _mlfun.cosh, "tanh": _mlfun.tanh,
            "exp": _mlfun.exp, "log": _mlfun.log, "log10": _mlfun.log10, "sqrt": _mlfun.sqrt,
            "abs": _mlfun.abs, "sign": _mlfun.sign,
            "floor": _mlfun.floor, "ceil": _mlfun.ceil, "round": _mlfun.round, "fix": _mlfun.fix,
            "mod": _mlfun.mod, "rem": _mlfun.rem,
            
            # COMPLEX NUMBER SUPPORT
            "angle": _mlfun.angle,
            "real": _mlfun.real,
            "imag": _mlfun.imag,
            "conj": _mlfun.conj,
            "diag": _mlfun.diag,
        })

        # Auto-import remaining functions (backup)
        try:
            for name in dir(_mlfun):
                if not name.startswith("_") and name not in self.globals and name not in ("MatlabArray", "scipy", "np", "sympy"):
                    self.globals[name] = getattr(_mlfun, name)
        except Exception:
            pass

        # Plotting API
        for name in dir(_plt_mod):
            if not name.startswith("_"):
                try:
                    self.globals[name] = getattr(_plt_mod, name)
                except Exception:
                    pass

        self.globals.update({
            "clf": lambda: plot_manager.clf(),
            "cla": self._cla,
            "hold": lambda mode=True: plot_manager.hold(mode),
        })

        # I/O
        self.globals.update({
            "save": lambda f="workspace.mat": save_workspace(self, f),
            "load": lambda f="workspace.mat": load_workspace(self, f),
            "writematrix": writematrix,
            "readmatrix": readmatrix,
            "readtable": readtable,
            "csvread": csvread,
            "saveas": saveas,
            "disp": builtins.disp,
            "clear": self._clear_user,
            "clc": builtins.clc,
            "pause": time.sleep,
            "who": lambda: builtins.who(self.globals),
            "whos": lambda: builtins.whos(self.globals),
            "exist": lambda n, k=None: builtins.exist(n, k, self.globals),
        })
        
        # Control Toolbox
        try:
            from mathexlab.toolbox.control import (
                tf, step, impulse, bode, series, parallel, feedback,
                rlocus 
            )
            self.globals.update({
                "tf": tf, "step": step, "impulse": impulse,
                "bode": bode, "series": series, "parallel": parallel,
                "feedback": feedback, "rlocus": rlocus,
            })
        except ImportError:
            pass
        
        # Snapshot built-ins to protect them from 'clear'
        self._builtins_set = set(self.globals.keys())

    def execute(self, code: str):
        from mathexlab.kernel.executor import execute as _exec
        try:
            _exec(code, self)
        finally:
            self._after_execute()

    def _after_execute(self):
        try:
            PlotEngine.show()
        except Exception:
            pass
        try:
            if QApplication:
                QApplication.processEvents()
        except Exception:
            pass

    def _drawnow(self):
        self._after_execute()

    def _cla(self):
        ax = plot_manager.gca()
        if ax:
            ax.clear()

    def _clear_user(self, *args):
        """
        Clears USER variables, but preserves SYSTEM built-ins.
        """
        should_clear_all = False
        vars_to_clear = []

        if not args:
            should_clear_all = True
        else:
            for a in args:
                s = str(a)
                if s == 'all':
                    should_clear_all = True
                    break
                if s not in ('classes', 'functions', 'import'):
                    vars_to_clear.append(s)

        if should_clear_all:
            # [FIX] Iterate over a COPY of the keys
            for k in list(self.globals.keys()):
                if k in self._builtins_set:
                    continue
                if k == "ans": 
                    self.globals[k] = 0
                    continue
                try:
                    del self.globals[k]
                except Exception:
                    pass
            return

        for name in vars_to_clear:
             if name in self.globals and name not in self._builtins_set:
                 try: del self.globals[name]
                 except: pass