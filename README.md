# MathexLab

**MathexLab** is a high-fidelity scientific computing environment designed to replace MATLAB for PhD students, researchers, and engineers. It combines the familiar syntax of MATLAB (`.m` files) with the robust, open-source power of the **Python** scientific ecosystem (NumPy, SciPy, SymPy)—all wrapped in a professional **PySide6 (Qt)** interface.

Think of it as a free, lightweight MATLAB built on the modern Python stack.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.11+-blue.svg) ![Status](https://img.shields.io/badge/status-Beta-orange.svg)

---

## 🚀 Key Features & System Architecture

MathexLab is not just a text editor; it is a complete language runtime environment. The system is architected into four distinct layers: **UI**, **Kernel**, **Transpiler**, and **Toolboxes**.

### 🖥️ Layer 1: Professional IDE Interface (`mathexlab.ui`)
The user interface is built with **PySide6**, strictly adhering to the "transcript model" familiar to MATLAB users.

#### **1. Command Window (`ui.console.ConsoleWidget`)**
* **What:** A specialized `QPlainTextEdit` widget that acts as the primary REPL (Read-Eval-Print Loop).
* **Why:** Standard Python consoles do not behave like MATLAB. Researchers need a persistent history where the prompt (`>>`) and past outputs are immutable (read-only), but current input is editable.
* **How:** * **Strict Transcript Modeling:** The console maintains a `locked_pos` index. Any keystroke attempting to edit text before the current prompt is blocked via event filtering.
    * **Visual Distinction:** Implements a rigorous color-coding system where user input is **Grey (`#aaaaaa`)** and system output/prompts are **White (`#ffffff`)**, ensuring visual clarity during long sessions.
    * **History Navigation:** Intercepts `Up`/`Down` keys to cycle through a session-specific command buffer, automatically handling multi-line inputs (`...` continuations).

#### **2. Workspace Inspector (`ui.workspace.WorkspaceWidget`)**
* **What:** An interactive data viewer that mirrors the MATLAB "Workspace" panel.
* **Why:** Complex simulations involve large matrices. Debugging them via `print()` statements is inefficient. Users need to see dimensions, types, and values at a glance.
* **How:**
    * **Live Slicing:** For variables with dimensions $N > 2$ (e.g., 3D MRI data or time-series grids), the inspector automatically generates a 2D "Slice View" (e.g., `[:,:,0]`), preventing UI freezes when trying to render million-element arrays.
    * **Bi-directional Sync:** Editing a cell in the table emits a signal that directly mutates the underlying `KernelSession` memory, allowing for "runtime patching" of simulation parameters.

#### **3. Plot Dock (`ui.plotdock.PlotDock`)**
* **What:** A dedicated panel for managing matplotlib figures.
* **Why:** Floating windows get lost behind code editors. A docked panel keeps visualizations contextually relevant.
* **How:** Integrates a custom Matplotlib backend that redirects `plt.show()` calls to a layout manager within the main window, organizing multiple figures into tabs or grid layouts.

---

### 🧠 Layer 2: Native Transpiler Engine (`mathexlab.language`)
This is the core innovation of MathexLab. It translates MATLAB source code into optimized Python bytecode on the fly.

#### **1. The Tokenizer (`language.tokenizer.Tokenizer`)**
* **What:** A lexical analyzer built specifically for MATLAB syntax.
* **Why:** MATLAB has unique parsing rules that standard regex parsers fail on (e.g., the single quote `'` can mean "String" OR "Hermitian Transpose" depending on context).
* **How:** It uses a context-aware state machine to distinguish between `matrix` definitions (`[1 2; 3 4]`), `cell` arrays (`{1, 2}`), and `continuations` (`...`). It handles the automatic insertion of semicolons/commas where they are implied by newlines.

#### **2. The AST Parser (`language.parser.Parser`)**
* **What:** A Recursive Descent Parser that builds an Abstract Syntax Tree (AST).
* **Why:** To support complex structures like nested `if-elseif-else` blocks, `switch` statements with cell-array cases, and `try-catch` blocks which have no direct 1-to-1 mapping in simple regex replacement.
* **How:** It recursively constructs nodes (`FunctionDef`, `ForLoop`, `BinOp`) that represent the logical flow of the program, completely independent of the Python syntax.

#### **3. The Transpiler (`language.transpiler.ASTCompiler`)**
* **What:** The compiler that converts the AST into executable Python code.
* **Why:** MATLAB uses 1-based indexing (`A(1)`) while Python uses 0-based (`A[0]`). MATLAB passes arrays by value; Python passes by reference. These discrepancies must be reconciled.
* **How:** * **Indexing Translation:** Automatically converts `A(i)` calls into `A[i-1]` accessors or `A.set_val()` calls for assignments.
    * **Matrix Math:** Maps `*` to matrix multiplication (`@`) and `.*` to element-wise multiplication.
    * **Auto-Copy:** Detects assignments to variables and injects `.copy()` calls to emulate MATLAB's "Copy-on-Write" behavior, ensuring safe mutation inside loops.

---

### 🔬 Layer 3: Specialized Research Toolboxes (`mathexlab.toolbox`)
These libraries provide the domain-specific functionality required for PhD-level work.

#### **1. Partial Differential Equations (`toolbox.pde`)**
* **Function:** `pdepe(m, pdefun, icfun, bcfun, xmesh, tspan)`
* **What:** A solver for systems of 1D parabolic and elliptic PDEs.
* **Why:** Essential for Heat Transfer, Diffusion, and Electrostatics research.
* **How:**
    * **Method of Lines:** Discretizes the spatial derivatives ($x$) to convert the PDE into a system of Ordinary Differential Equations (ODEs) regarding time ($t$).
    * **Geometric Support ($m$):** The solver kernel explicitly handles the singular term $x^{-m} \frac{\partial}{\partial x}(x^m f)$ for Slab ($m=0$), Cylindrical ($m=1$), and Spherical ($m=2$) coordinates.
    * **Vectorization:** The internal residual calculation is fully vectorized using NumPy, avoiding slow Python loops during the mesh iteration.

#### **2. Control Systems (`toolbox.control`)**
* **Class:** `TransferFunction(num, den)`
* **What:** Represents Linear Time-Invariant (LTI) systems in the Laplace domain ($s$).
* **Why:** Control engineers need to treat systems as algebraic objects (`G = P * C / (1 + P * C)`).
* **How:** Implements Python operator overloading (`__mul__`, `__add__`, `__pow__`) to perform polynomial convolution on numerators/denominators automatically.
* **Function:** `rlocus(sys)`
* **How:** Solves the characteristic equation $1 + k \cdot G(s) = 0$ for a logarithmically spaced vector of gains $k$, calculating roots using `np.roots()` and plotting the trajectories to visualize system stability.

#### **3. Optimization (`toolbox.optim`)**
* **Function:** `fmincon(fun, x0, A, b, Aeq, beq, lb, ub, nonlcon)`
* **What:** Finds the minimum of a constrained non-linear multivariable function.
* **Why:** Fundamental for Engineering Design Optimization (e.g., minimizing weight subject to stress constraints).
* **How:** Wraps `scipy.optimize.minimize` with the `SLSQP` (Sequential Least SQuares Programming) method. It creates wrapper closures to map MATLAB-style constraint functions (returning `c, ceq`) into SciPy's dictionary-based constraint definitions.

#### **4. Symbolic Math (`math.symbolic`)**
* **Function:** `syms`, `diff`, `int`, `solve`
* **What:** A Computer Algebra System (CAS) integration.
* **How:** Dynamically injects `sympy.Symbol` objects into the user's workspace. Wrappers like `diff(f)` check the input type: if it is a numeric array, it performs finite difference (`np.diff`); if it is a symbol, it performs analytical differentiation (`sympy.diff`).

---

## 🛠️ Tech Stack

MathexLab is built with high-performance Python technologies:

* **Core Runtime**: [Python 3.11+](https://www.python.org/) - Selected for its improved error tracebacks and speed.
* **GUI Framework**: [PySide6 (Qt)](https://doc.qt.io/qtforpython/) - Provides native OS integration and hardware-accelerated rendering.
* **Linear Algebra**: [NumPy](https://numpy.org/) - The engine behind all matrix operations.
* **Scientific Computing**: [SciPy](https://scipy.org/) - Powers the ODE solvers, Optimization algorithms, and Signal Processing.
* **Symbolic Math**: [SymPy](https://www.sympy.org/) - The backend for the symbolic toolbox.
* **Plotting**: [Matplotlib](https://matplotlib.org/) - The rendering engine for 2D/3D plots.

---

## 📦 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/patarsamar/MathexLab.git](https://github.com/patarsamar/MathexLab.git)
    cd MathexLab
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**
    ```bash
    python main.py
    ```

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and create a pull request for any features, bug fixes, or documentation improvements.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## Author Details
**Samarjit Patar** 📧 patarsamar123abc@gmail.com