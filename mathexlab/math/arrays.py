from __future__ import annotations
import numpy as np
import scipy.linalg
import scipy.sparse
import scipy.sparse.linalg
from typing import Union

# Update types to include SciPy sparse matrices
ArrayLike = Union[
    np.ndarray, 
    scipy.sparse.spmatrix, 
    list, tuple, int, float, complex, 
    "MatlabArray"
]


# Dummy colon marker for runtime (true MATLAB : )
class ColonType:
    pass
colon = ColonType()


def _to_data(x):
    """
    Helper to extract underlying data (Dense or Sparse).
    Does NOT force conversion to dense numpy array.
    """
    if isinstance(x, MatlabArray):
        return x._data
    return x


def _to_numpy(x):
    """
    Helper to force data into a dense Numpy array.
    Used for indices or incompatible operations.
    """
    d = _to_data(x)
    if scipy.sparse.issparse(d):
        return d.toarray()
    return np.asarray(d)


class MatlabArray:
    """
    MATLAB-like numerical array.
    """

    # -----------------------------------------------------
    # CONSTRUCTOR
    # -----------------------------------------------------
    def __init__(self, data: ArrayLike):
        if isinstance(data, MatlabArray):
            self._data = data._data.copy()
        elif scipy.sparse.issparse(data):
            self._data = data
        elif isinstance(data, (list, tuple)):
            # [FIX] Check for strings to avoid np.block/scipy.sparse 'str has no attribute H' error
            has_str = any(isinstance(x, str) for x in data)
            if has_str:
                self._data = np.array(data)
            else:
                try:
                    def unwrap_rec(x):
                        if isinstance(x, MatlabArray):
                            return x._data
                        if isinstance(x, (list, tuple)):
                            return [unwrap_rec(i) for i in x]
                        return x
                    
                    unwrapped = unwrap_rec(data)
                    self._data = np.block(unwrapped)
                except Exception:
                    self._data = np.array(data)
        else:
            self._data = np.array(data)

        # [FIX] Only cast to complex if explicit string type, otherwise respect input
        if hasattr(self._data, 'dtype') and self._data.dtype.kind in ('U', 'S'):
            try:
                # Try casting to float first to avoid unnecessary complex promotion
                self._data = self._data.astype(float)
            except ValueError:
                try:
                    self._data = self._data.astype(complex)
                except Exception:
                    pass

        if not scipy.sparse.issparse(self._data):
            if self._data.ndim == 0:
                self._data = self._data.reshape(1, 1)
            elif self._data.ndim == 1:
                self._data = self._data.reshape(1, -1)

    # -----------------------------------------------------
    # PYTHON INTEROPERABILITY
    # -----------------------------------------------------
    def __array__(self, dtype=None):
        if self.is_sparse:
            return self._data.toarray()
        return np.asarray(self._data, dtype=dtype)
    
    def __float__(self):
        val = self._data.item()
        if isinstance(val, complex):
            return float(val.real)
        return float(val)

    def __int__(self):
        return int(self._data.item())
    
    # [FIX] Critical for if statements: Handle Truthiness correctly
    def __bool__(self):
        if self.size == 0:
            return False
        if self.size == 1:
            return bool(self._data.item())
        # MATLAB behavior: True only if ALL elements are non-zero
        if self.is_sparse:
             return self.nnz == self.size 
        return np.all(self._data).item()
    
    def __iter__(self):
        """
        Iterates over columns to match MATLAB 'for' loop behavior.
        """
        rows, cols = self.shape
        for c in range(cols):
            # Use slicing [:, c:c+1] to preserve 2D shape (M, 1)
            col_slice = self._data[:, c:c+1]
            yield MatlabArray(col_slice)

    # Attribute Access (for Structs)
    def __getattr__(self, name):
        """Allow s.field access if this array wraps a struct/object."""
        # Only allow if scalar and object type
        if not self.is_sparse and self.size == 1 and self._data.dtype == object:
            item = self._data.flat[0]
            # Delegate to the object (MatlabStruct)
            if hasattr(item, name):
                return getattr(item, name)
            # Or dict access
            if isinstance(item, dict) and name in item:
                return item[name]
        raise AttributeError(f"'MatlabArray' object has no attribute '{name}'")

    # -----------------------------------------------------
    # PROPERTIES
    # -----------------------------------------------------
    @property
    def is_sparse(self):
        return scipy.sparse.issparse(self._data)

    @property
    def shape(self):
        return self._data.shape

    @property
    def size(self):
        return self._data.size

    @property
    def nnz(self):
        if self.is_sparse:
            return self._data.nnz
        return np.count_nonzero(self._data)

    @property
    def T(self):
        return MatlabArray(self._data.T)

    @property
    def H(self):
        if self.is_sparse:
            return MatlabArray(self._data.conj().T)
        return MatlabArray(self._data.conj().T)

    def __len__(self):
        return max(self.shape)

    # -----------------------------------------------------
    # REPRESENTATION
    # -----------------------------------------------------
    def __repr__(self):
        if self.is_sparse:
            d = self._data.tocoo()
            if d.nnz == 0:
                return f"All zero sparse: {self.shape[0]}x{self.shape[1]}"
            limit = 20
            lines = [f"<Sparse {self.shape} with {d.nnz} stored elements>"]
            for i in range(min(d.nnz, limit)):
                lines.append(f"  ({d.row[i]+1}, {d.col[i]+1})\t{d.data[i]}")
            if d.nnz > limit:
                lines.append(f"  ... and {d.nnz - limit} more")
            return "\n".join(lines)

        if self.size == 0:
            return "[]"
        if self.size > 200:
            return f"<MatlabArray {self.shape}>"

        return np.array2string(
            self._data,
            separator=" ",
            max_line_width=120
        ).replace("[", " ").replace("]", " ")

    # -----------------------------------------------------
    # INDEXING: MATLAB Style ()
    # -----------------------------------------------------
    def __call__(self, *args):
        if not args:
            return self

        # CASE 1: Linear Indexing (A(k) or A(:))
        if len(args) == 1:
            arg = args[0]
            
            # Colon (: -> all elements flattened column-wise)
            if arg is colon:
                if self.is_sparse:
                    return MatlabArray(self._data.reshape((-1, 1)))
                return MatlabArray(self._data.flatten(order='F').reshape(-1, 1))
            
            # 'end'
            if isinstance(arg, str) and arg == 'end':
                # Return last element as scalar
                if self.is_sparse:
                    return MatlabArray(self._data.reshape((-1,1))[self.size-1, 0])
                return MatlabArray(self._data.flatten(order='F')[self.size - 1])
                
            # Numeric
            val = _to_numpy(arg)
            
            # Scalar Index A(i)
            if np.isscalar(val) or (isinstance(val, np.ndarray) and val.ndim == 0):
                idx = int(val) - 1
                if self.is_sparse:
                     d = self._data.reshape((-1, 1))
                     return MatlabArray(d[idx, 0])
                # Dense flat indexing
                return MatlabArray(self._data.flatten(order='F')[idx])

            # Array Linear Indexing A([1, 4, 10])
            arr = np.asarray(val)
            if arr.dtype == bool:
                idx = arr.flatten(order='F')
                if self.is_sparse:
                     d = self._data.reshape((-1, 1))
                     return MatlabArray(d[idx])
                return MatlabArray(self._data.flatten(order='F')[idx].reshape(-1, 1))
            else:
                idx = arr.astype(int) - 1
                if self.is_sparse:
                     d = self._data.reshape((-1, 1))
                     return MatlabArray(d[idx, 0])
                
                # Dense: flat indexing reshaped to input shape
                return MatlabArray(self._data.flatten(order='F')[idx].reshape(arr.shape))

        # CASE 2: N-Dimensional Indexing (A(i, j))
        grid_indices = []
        
        for i, arg in enumerate(args):
            # Determine dimension size
            dim_len = self.shape[i] if i < len(self.shape) else 1
            
            # --- Colon (:) ---
            if arg is colon:
                grid_indices.append(np.arange(dim_len))
                continue
                
            # --- 'end' ---
            if isinstance(arg, str) and arg == 'end':
                grid_indices.append(np.array([dim_len - 1]))
                continue
                
            # --- Values ---
            val = _to_numpy(arg)
            
            # Scalar
            if np.isscalar(val) or (isinstance(val, np.ndarray) and val.ndim == 0):
                grid_indices.append(np.array([int(val) - 1]))
                continue
                
            # Array
            arr = np.asarray(val)
            if arr.dtype == bool:
                grid_indices.append(np.nonzero(arr)[0])
            else:
                grid_indices.append(arr.astype(int) - 1)

        # Apply Indexing using Open Mesh (np.ix_)
        try:
            # Flatten indices for np.ix_ (it expects 1D sequences)
            ix_args = [x.flatten() for x in grid_indices]
            mesh = np.ix_(*ix_args)
            
            return MatlabArray(self._data[mesh])
            
        except IndexError:
            raise IndexError("Index out of bounds.")
        except Exception as e:
            # Fallback for weird dimension mismatches
            raise ValueError(f"Indexing failed: {str(e)}")

    # -----------------------------------------------------
    # INDEXED ASSIGNMENT SUPPORT (With Auto-Expansion)
    # -----------------------------------------------------
    def set_val(self, value, *args):
        """
        Supports 1-based indexed assignment: A(i) = v
        """
        py_indices = []
        required_shape = [] 
        is_linear = len(args) == 1
        
        # 1. Parse Arguments
        for i, arg in enumerate(args):
            if arg is colon:
                py_indices.append(slice(None))
                curr_dim = self.shape[i] if i < len(self.shape) else 1
                required_shape.append(curr_dim)
                continue
            
            if isinstance(arg, str) and arg == 'end':
                if is_linear:
                    idx = self.size - 1
                else:
                    idx = self.shape[i] - 1 if i < len(self.shape) else 0
                py_indices.append(idx)
                required_shape.append(idx + 1)
                continue

            val = _to_numpy(arg)
            
            if isinstance(val, np.ndarray) and val.dtype == bool:
                py_indices.append(val)
                required_shape.append(0) 
                continue

            if np.isscalar(val):
                idx = int(val) - 1
                if idx < 0: raise IndexError("Index must be positive.")
                py_indices.append(idx)
                required_shape.append(idx + 1)
                continue
                
            if isinstance(val, (list, tuple, np.ndarray)):
                arr = np.asarray(val)
                if arr.dtype == bool:
                     py_indices.append(arr)
                     required_shape.append(0)
                else:
                    int_idxs = arr.astype(int) - 1
                    if np.any(int_idxs < 0): raise IndexError("Index must be positive.")
                    py_indices.append(int_idxs)
                    
                    if int_idxs.size > 0:
                        required_shape.append(int_idxs.max() + 1)
                    else:
                        required_shape.append(0)
                continue
            
            raise TypeError(f"Invalid index type: {type(arg)}")

        val_data = _to_numpy(value)
        
        if isinstance(val_data, np.ndarray) and val_data.size == 1:
            val_data = val_data.item()

        # 2. Try Standard Assignment
        try:
            if len(py_indices) == 1 and not self.is_sparse and self._data.ndim == 2:
                idx = py_indices[0]
                if isinstance(idx, np.ndarray) and idx.dtype != bool: 
                    idx = idx.flatten()
                
                if isinstance(val_data, np.ndarray):
                    val_data = val_data.flatten()
                
                flat = self._data.flatten(order='F')
                flat[idx] = val_data
                self._data = flat.reshape(self.shape, order='F')
                return

            self._data[tuple(py_indices)] = val_data

        except IndexError:
            # 3. DYNAMIC EXPANSION LOGIC
            if self.is_sparse:
                raise IndexError("Sparse matrix dynamic expansion not yet supported.")
            
            if is_linear:
                 req_size = required_shape[0]
                 current_size = self.size
                 
                 if req_size > current_size:
                     flat_old = self._data.flatten(order='F')
                     flat_new = np.zeros(req_size, dtype=self._data.dtype)
                     flat_new[:current_size] = flat_old
                     
                     if self.shape[1] == 1 and self.shape[0] > 0:
                         self._data = flat_new.reshape(-1, 1, order='F')
                     else:
                         self._data = flat_new.reshape(1, -1, order='F')
                     
                     self.set_val(value, *args)
                     return

            current_shape = list(self.shape)
            new_shape = list(current_shape)

            while len(new_shape) < len(args):
                new_shape.append(1)

            for dim, req_max in enumerate(required_shape):
                if req_max > 0: 
                    if dim < len(new_shape):
                        new_shape[dim] = max(new_shape[dim], req_max)
                    else:
                        new_shape.append(req_max)
            
            expanded = np.zeros(new_shape, dtype=self._data.dtype)
            source_slices = tuple(slice(0, s) for s in current_shape)
            expanded[source_slices] = self._data
            self._data = expanded
            self.set_val(value, *args)

    # -----------------------------------------------------
    # Python Style: A[0, 0]
    # -----------------------------------------------------
    def __getitem__(self, key):
        if isinstance(key, MatlabArray):
            key = key._data
            if isinstance(key, np.ndarray) and key.ndim == 0:
                key = key.item()
        try:
            val = self._data[key]
        except IndexError:
            if np.isscalar(key) and self.size > key:
                return self._data.flatten()[key]
            raise
        if np.isscalar(val):
            return val
        return MatlabArray(val)

    def __setitem__(self, key, value):
        val = _to_numpy(value)
        if isinstance(key, MatlabArray):
            key = key._data
        self._data[key] = val

    # -----------------------------------------------------
    # ARITHMETIC
    # -----------------------------------------------------
    def __abs__(self):
        if self.is_sparse:
            return MatlabArray(abs(self._data))
        return MatlabArray(np.abs(self._data))

    def __add__(self, o):
        return MatlabArray(self._data + _to_data(o))
    
    def __radd__(self, o):
        return MatlabArray(_to_data(o) + self._data)

    def __sub__(self, o):
        return MatlabArray(self._data - _to_data(o))
    
    def __rsub__(self, o):
        return MatlabArray(_to_data(o) - self._data)

    def __neg__(self):
        return MatlabArray(-self._data)
    
    def __invert__(self): 
        if self.is_sparse:
             return MatlabArray((self._data != 0).toarray() == False)
        return MatlabArray(~self._data.astype(bool))

    def __mul__(self, o):
        """
        Matrix Multiplication (*)
        [FIX] Optimized to avoid np.matmul warning for scalar/scalar or scalar/matrix ops
        """
        A = self._data
        B = _to_data(o)
        
        dimA = A.ndim if hasattr(A, 'ndim') else 0
        dimB = B.ndim if hasattr(B, 'ndim') else 0

        # Optimization: If either is a scalar (size 1), use elementwise * # (This is mathematically equivalent to @ for 1x1 but faster/safer)
        is_scalar_A = (dimA == 0) or (hasattr(A, 'size') and A.size == 1)
        is_scalar_B = (dimB == 0) or (hasattr(B, 'size') and B.size == 1)

        if is_scalar_A or is_scalar_B:
             return MatlabArray(A * B)

        # True Matrix Multiplication for 2D matrices
        if dimA == 2 and dimB == 2:
            return MatlabArray(A @ B)
            
        return MatlabArray(A * B)
        
    __rmul__ = __mul__

    def __truediv__(self, o):
        B = _to_data(o)
        A = self._data
        if np.isscalar(B) or (hasattr(B, 'size') and B.size == 1):
            return MatlabArray(A / B)
        if hasattr(A, 'ndim') and A.ndim == 2 and hasattr(B, 'ndim') and B.ndim == 2:
            B_dense = B.toarray() if scipy.sparse.issparse(B) else B
            return MatlabArray(A @ scipy.linalg.pinv(B_dense))
        return MatlabArray(A / B)
    
    def __rtruediv__(self, o):
        return MatlabArray(_to_data(o) / self._data)

    def mldivide(self, o):
        b = _to_data(o)
        A = self._data
        if hasattr(A, 'ndim') and A.ndim == 2:
            try:
                if scipy.sparse.issparse(A):
                    x = scipy.sparse.linalg.spsolve(A, b)
                    if isinstance(x, np.ndarray) and x.ndim == 1:
                         if hasattr(b, 'shape') and len(b.shape) >= 2 and b.shape[1] == 1:
                             x = x.reshape(-1, 1)
                    return MatlabArray(x)
                return MatlabArray(scipy.linalg.solve(A, b))
            except Exception:
                if scipy.sparse.issparse(A):
                    A_dense = A.toarray()
                    x, _, _, _ = scipy.linalg.lstsq(A_dense, b)
                    return MatlabArray(x)
                else:
                    x, _, _, _ = scipy.linalg.lstsq(A, b)
                    return MatlabArray(x)
        return MatlabArray(b / A)

    def emul(self, o): 
        return MatlabArray(self._data.multiply(_to_data(o))) if self.is_sparse else MatlabArray(self._data * _to_data(o))
    
    def ediv(self, o): 
        return MatlabArray(self._data / _to_data(o))
    
    def epow(self, o): 
        if self.is_sparse:
             return MatlabArray(self._data.power(_to_data(o)))
        return MatlabArray(self._data ** _to_data(o))

    def __pow__(self, p):
        p = int(p)
        if self.is_sparse:
            return MatlabArray(self._data ** p) 
        return MatlabArray(np.linalg.matrix_power(self._data, p))

    def __lt__(self, o): return MatlabArray(self._data < _to_data(o))
    def __gt__(self, o): return MatlabArray(self._data > _to_data(o))
    def __eq__(self, o): return MatlabArray(self._data == _to_data(o))
    def __le__(self, o): return MatlabArray(self._data <= _to_data(o))
    def __ge__(self, o): return MatlabArray(self._data >= _to_data(o))
    def __ne__(self, o): return MatlabArray(self._data != _to_data(o))


# -----------------------------------------------------
# CONSTRUCTORS
# -----------------------------------------------------
def mat(data): return MatlabArray(data)
def zeros(*args): return MatlabArray(np.zeros(_shape(args)))
def ones(*args): return MatlabArray(np.ones(_shape(args)))
def eye(n): return MatlabArray(np.eye(int(n)))
def linspace(s, e, n=100): return MatlabArray(np.linspace(s, e, int(n)))

def arange(start, stop=None, step=1):
    """
    MATLAB-style range creation.
    Handles integer sequences explicitly to avoid '1. 2.' output.
    Uses float conversion to ensure robust execution when inputs are MatlabArrays.
    """
    # 1. Handle single argument case (stop only)
    if stop is None:
        stop, start = start, 0

    # 2. Explicitly cast to standard Python numbers (float)
    try:
        start_val = float(start)
        stop_val = float(stop)
        step_val = float(step)
    except Exception:
        # Fallback if casting fails (unlikely for numbers)
        start_val, stop_val, step_val = start, stop, step

    # 3. Check for integer-like values to preserve nice output (1, 2, 3 instead of 1., 2., 3.)
    if (float(start_val).is_integer() and 
        float(stop_val).is_integer() and 
        float(step_val).is_integer()):
        
        start_val = int(start_val)
        stop_val = int(stop_val)
        step_val = int(step_val)
        
        if step_val > 0:
            return MatlabArray(np.arange(start_val, stop_val + 1, step_val))
        else:
            return MatlabArray(np.arange(start_val, stop_val - 1, step_val))

    # 4. Standard float case
    return MatlabArray(np.arange(start_val, stop_val + 1e-12, step_val))

def cell(*args):
    """
    cell(N) -> Empty NxN cell
    cell([data]) -> Cell array wrapping data (from { } literals)
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        return MatlabArray(np.array(args[0], dtype=object))
    shape = _shape(args)
    return MatlabArray(np.empty(shape, dtype=object))

def sparse(i, j=None, v=None, m=None, n=None):
    if j is None and v is None:
        val = _to_data(i)
        if scipy.sparse.issparse(val):
            return MatlabArray(val)
        return MatlabArray(scipy.sparse.csr_matrix(val))

    idx_i = _to_numpy(i).flatten() - 1
    idx_j = _to_numpy(j).flatten() - 1
    vals  = _to_numpy(v).flatten()

    if m is None: m = int(idx_i.max()) + 1
    if n is None: n = int(idx_j.max()) + 1

    mat_data = scipy.sparse.csr_matrix(
        (vals, (idx_i, idx_j)), 
        shape=(int(m), int(n))
    )
    return MatlabArray(mat_data)

def full(A: MatlabArray):
    if not isinstance(A, MatlabArray):
        return MatlabArray(np.array(A))
    if not A.is_sparse:
        return A
    return MatlabArray(A._data.toarray())

def _shape(args):
    if len(args) == 1:
        arg = args[0]
        # Unwrap MatlabArray or sparse
        if hasattr(arg, '_data'):
            arg = arg._data
        
        # Force into a numpy array to easily check size/dimensions
        arg_arr = np.array(arg)
        
        # Case: zeros(3) -> 3x3 square matrix
        if arg_arr.size == 1:
            val = int(arg_arr.item())
            return (val, val)
        
        # Case: zeros([2, 5]) or zeros(size(x)) -> use vector elements as dims
        return tuple(int(x) for x in arg_arr.flatten())
    
    # Case: zeros(2, 5) -> multiple arguments
    return tuple(int(a) for a in args)