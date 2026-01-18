import os
import ast
from mathexlab.io.mfile import read_mfile
from mathexlab.language.transpiler import transpile
from mathexlab.kernel.path_manager import path_manager
from mathexlab.language.functions import registry, FunctionEntry

def load_and_register(name: str):
    """
    Attempts to find, transpile, and register a function named 'name'.
    Strictly handles .m files only.
    """
    # 1. Resolve File Path (Strict .m lookup via PathManager)
    filepath = path_manager.resolve(name)
    if not filepath:
        return False

    try:
        # 2. Read & Transpile
        code = read_mfile(filepath)
        if code is None: 
            return False

        # Unpack the tuple returned by transpile
        py_code, _ = transpile(code)
        
        # 3. Detect Type (Function vs Script) WITHOUT Executing
        try:
            tree = ast.parse(py_code)
        except SyntaxError as e:
            print(f"Syntax Error in {os.path.basename(filepath)}: {e}")
            return False

        is_function = False
        func_name_in_code = name

        if tree.body and isinstance(tree.body[0], ast.FunctionDef):
            is_function = True
            func_name_in_code = tree.body[0].name

        # -------------------------------------------------------
        # CASE A: FUNCTION (function y = f(x))
        # -------------------------------------------------------
        if is_function:
            scope = {}
            # Execute definition into a temporary scope to create the function object
            exec(py_code, scope)
            
            # Retrieve the function object 
            # Note: We look for the name DEFINED in the file, not necessarily the filename
            func_obj = scope.get(func_name_in_code)
            
            if func_obj and callable(func_obj):
                # Register under the REQUESTED name 'name' so executor can find it
                entry = FunctionEntry(name=name, func=func_obj, source=py_code, source_file=filepath)
                registry.register(entry)
                return True

        # -------------------------------------------------------
        # CASE B: SCRIPT (Commands that modify the workspace)
        # -------------------------------------------------------
        # We create a runner that executes the RAW python code 
        # inside the USER'S globals (the Console Workspace).
        
        def script_runner(globals_dict=None):
            if globals_dict is None:
                # Should not happen in Executor, but failsafe
                globals_dict = {}
            
            # [CRITICAL FIX] Execute code DIRECTLY into the session globals
            # This ensures 'x=1' sticks in the workspace.
            exec(py_code, globals_dict)

        # Flags for Executor
        script_runner.__mathexlab_command__ = True
        script_runner.__mathexlab_script__ = True 
        
        entry = FunctionEntry(name=name, func=script_runner, source=py_code, source_file=filepath)
        registry.register(entry)
        return True

    except Exception as e:
        print(f"Error loading {name}: {e}")
        return False
        
    return False