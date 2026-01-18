import ast
import traceback
import sys
from mathexlab.language.transpiler import transpile
from mathexlab.kernel.session import KernelSession
from mathexlab.kernel.loader import load_and_register
from mathexlab.language.functions import registry

# -----------------------------------------------------------
# MAIN EXECUTOR (PURE MATLAB)
# -----------------------------------------------------------
def execute(code: str, session: KernelSession):
    """
    MATLAB execution semantics (PRINT-BASED):
    - Executes statements
    - Prints output (KernelWorker captures it)
    - Returns None on success, or the Exception object on failure.
    """

    code = code.strip()
    if not code:
        return None

    suppress = code.endswith(";")
    if suppress:
        code = code[:-1].strip()

    try:
        # [FIX] Unpack tuple: (python_code, line_number_map)
        py, line_map = transpile(code)
        
        tree = ast.parse(py, mode="exec")

        # ------------------------------------------------
        # FUNCTION DEFINITIONS
        # ------------------------------------------------
        if tree.body and isinstance(tree.body[0], ast.FunctionDef):
            exec(py, session.globals)
            return None

        # ------------------------------------------------
        # FINAL EXPRESSION
        # ------------------------------------------------
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last = tree.body[-1]
            body = tree.body[:-1]

            if body:
                exec(
                    compile(ast.Module(body=body, type_ignores=[]), "<ml>", "exec"),
                    session.globals,
                )

            value = eval(
                compile(ast.Expression(last.value), "<ml>", "eval"),
                session.globals,
            )

            # ------------------------------
            # MATLAB COMMAND EXECUTION
            # ------------------------------
            # 1. Check for explicit command flag (e.g. clc, clear, user scripts)
            is_cmd = getattr(value, "__mathexlab_command__", False)

            # 2. [CRITICAL FIX] Implicit Call Strategy
            # If the user typed a bare Name (e.g. "comet3", "sin") and it resulted 
            # in a callable, we treat it as a command request.
            if not is_cmd and callable(value) and isinstance(last.value, ast.Name):
                is_cmd = True

            if callable(value) and is_cmd:
                try:
                    # [FIX] Check if it is a SCRIPT that needs the workspace
                    if getattr(value, "__mathexlab_script__", False):
                        # Pass the SESSION GLOBALS so variables stick!
                        value(session.globals)
                    else:
                        # Standard function/command call
                        try:
                            value()
                        except TypeError as e:
                            # [CRITICAL FIX] Handle "Not enough input arguments" gracefully
                            # If calling comet3() fails because it needs args, we print a MATLAB error
                            # instead of crashing the Python kernel.
                            msg = str(e)
                            if "required" in msg or "missing" in msg or "argument" in msg:
                                print(f"Error: Not enough input arguments.")
                                return None
                            raise e
                            
                    return None
                except Exception as e:
                    # Allow error to propagate to the main error handler
                    raise e

            # ------------------------------
            # PLOTTING CALL (DO NOT PRINT)
            # ------------------------------
            if hasattr(value, "__class__") and value.__class__.__name__.endswith("Handle"):
                session.globals["ans"] = value
                return None

            # ------------------------------
            # NORMAL EXPRESSION
            # ------------------------------
            if value is not None:
                session.globals["ans"] = value
                if not suppress:
                    if hasattr(value, "_data"):
                        print(f"ans =\n{value}")
                    else:
                        print(f"ans = {value}")
            return None

        # ------------------------------------------------
        # STATEMENTS ONLY
        # ------------------------------------------------
        exec(py, session.globals)

        if (
            not suppress
            and len(tree.body) == 1
            and isinstance(tree.body[0], ast.Assign)
        ):
            target = tree.body[0].targets[0]
            if isinstance(target, ast.Name):
                name = target.id
                val = session.globals.get(name)
                if hasattr(val, "_data"):
                    print(f"{name} =\n{val}")
                else:
                    print(f"{name} = {val}")

    except NameError as e:
        # ==========================================================
        # MAGIC: Auto-Discovery & Lazy Loading
        # ==========================================================
        try:
            var_name = str(e).split("'")[1]
            if load_and_register(var_name):
                entry = registry.get(var_name)
                if entry:
                    session.globals[var_name] = entry.func
                    # Recursively execute now that it's loaded
                    # [FIX] Return the result of the recursive call to propagate errors/success
                    return execute(code, session)
        except Exception:
            pass
        
        l_map = locals().get('line_map', {})
        _handle_matlab_error(e, code, l_map)
        return e 

    except Exception as e:
        l_map = locals().get('line_map', {})
        _handle_matlab_error(e, code, l_map)
        return e 
    
    return None


def _handle_matlab_error(e, code, line_map=None):
    """
    Translates Python exceptions to MATLAB error messages.
    """
    if line_map is None:
        line_map = {}

    # ------------------------------------------------------------------
    # 1. Determine Location (Line Number Mapping)
    # ------------------------------------------------------------------
    _, _, tb = sys.exc_info()
    py_line = -1
    
    for frame in traceback.extract_tb(tb):
        if frame.filename in ("<ml>", "<string>"):
            py_line = frame.lineno
    
    matlab_line_str = ""
    if py_line > 0:
        m_line = line_map.get(py_line, "?")
        matlab_line_str = f" (Line {m_line})"

    # ------------------------------------------------------------------
    # 2. User Facing Error Message
    # ------------------------------------------------------------------
    msg = str(e)
    exc_type = type(e).__name__
    
    prefix = f"Error{matlab_line_str}:"

    if "SyntaxError" in exc_type:
        print(f"{prefix} Invalid syntax near '{code.strip()}'")
        return

    if isinstance(e, NameError):
        try:
            var_name = str(e).split("'")[1]
            print(f"{prefix} Undefined function or variable '{var_name}'.")
        except IndexError:
            print(f"{prefix} Undefined function or variable.")
        return

    if isinstance(e, IndexError):
        print(f"{prefix} Index exceeds the number of array elements.")
        return

    if isinstance(e, ValueError):
        if "broadcast" in msg or "shape" in msg:
            print(f"{prefix} Matrix dimensions must agree.")
            return

    print(f"{prefix} {msg}")