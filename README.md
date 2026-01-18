# MathexLab

**MathexLab** is a high-fidelity scientific computing environment designed to replace MATLAB for PhD students, researchers, and engineers. It combines the familiar syntax of MATLAB (`.m` files) with the robust, open-source power of the **Python** scientific ecosystem (NumPy, SciPy, SymPy)—all wrapped in a professional **PySide6 (Qt)** interface.

Think of it as a free, lightweight MATLAB built on the modern Python stack.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.11+-blue.svg) ![Status](https://img.shields.io/badge/status-Beta-orange.svg)

---

## 🚀 Key Features

### 🖥️ Professional IDE Interface
A unified workspace designed for serious research:
* **Command Window**: A "MATLAB-grade" console with strict transcript modeling, history navigation (Up/Down), and color-coded input/output (Grey/White).
* **Workspace Inspector**: An Excel-like variable viewer supporting **live editing** of scalars and matrices, with automatic slicing for 3D+ arrays.
* **Code Editor**: specialized script editor with syntax highlighting, line numbers, and intelligent indentation.
* **Plot Dock**: Integrated figure management for 2D/3D plots and animations.

### 🧠 Native Transpiler Engine
MathexLab doesn't just call Python; it *understands* MATLAB:
* **Real-time Transpilation**: Custom Tokenizer and Parser convert MATLAB syntax to Python AST on the fly.
* **Language Support**: Full support for Control Flow (`if`, `for`, `switch/case`), Object-Oriented Programming (`classdef`), and Matrix Math (1-based indexing, slicing).
* **Script Execution**: Run legacy `.m` scripts directly without modification.

### 🔬 Specialized Research Toolboxes
Built-in libraries that rival commercial alternatives:
* **Partial Differential Equations (`pde`)**: Solve 1D parabolic/elliptic PDEs using the `pdepe` solver with support for slab, cylindrical, and spherical geometries.
* **Control Systems (`control`)**: Analyze systems with Transfer Functions, `bode` plots, `step` responses, and high-visibility `rlocus` (Root Locus) plots.
* **Optimization (`optim`)**: Perform unconstrained (`fminsearch`) and constrained (`fmincon`) non-linear optimization.
* **Symbolic Math (`symbolic`)**: Perform derivations, integrals, and simplifications using a SymPy backend (`syms`, `diff`, `int`, `solve`).

### 📊 Advanced Visualization
* **2D & 3D Plotting**: Powered by Matplotlib, supporting lines, scatter plots, surfaces, and meshes.
* **Animation**: Create complex animations for physics simulations (e.g., traveling waves, ripples).
* **Interactivity**: Pan, zoom, and inspect data directly within the Plot Dock.

---

## 🛠️ Tech Stack

MathexLab is built with high-performance Python technologies:

* **Core**: [Python 3.11+](https://www.python.org/)
* **GUI Framework**: [PySide6 (Qt)](https://doc.qt.io/qtforpython/)
* **Linear Algebra**: [NumPy](https://numpy.org/)
* **Scientific Computing**: [SciPy](https://scipy.org/)
* **Symbolic Math**: [SymPy](https://www.sympy.org/)
* **Plotting**: [Matplotlib](https://matplotlib.org/)

---

## 📦 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/patarsamar/MathexLab.git](https://github.com/patarsamar/MathexLab.git)
    cd MathexLab
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**
    ```bash
    python main.py
    ```

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and create a pull request for any features, bug fixes, or documentation improvements.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## Author Details
**Samarjit Patar** 📧 patarsamar123abc@gmail.com