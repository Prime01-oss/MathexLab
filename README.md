# MathexLab Platform

**MathexLab** is a modular, high-fidelity scientific computing platform designed to unify various STEM workflows into a single, professional interface. It serves as a container for multiple research tools, combining the familiar syntax of legacy tools (like MATLAB) with the modern power of the **Python** ecosystem (NumPy, SciPy, SymPy).

Think of it as an **Operating System for Science**—a lightweight, extensible shell that runs specialized IDEs.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.11+-blue.svg) ![Status](https://img.shields.io/badge/status-Beta-orange.svg) ![Framework](https://img.shields.io/badge/GUI-PySide6-green.svg)

---

## 🚀 System Architecture: The "Platform" Approach

Unlike traditional monolithic editors, MathexLab is architected as a **Plugin-Based Platform**. This modular design allows different scientific languages to coexist within the same application window.

### 🏗️ Core Components

1.  **The Platform Shell (`app_platform`)**
    * **StemShell:** The main window container that manages the application lifecycle, windowing system, and global settings.
    * **Side Drawer:** A collapsible, professional navigation bar (similar to VS Code) that allows users to instantly switch between active tools (e.g., swapping from *MathexLab* to *Mathematica*).
    * **Shared Core (`shared`)**: A centralized repository of math engines and plotting libraries.
        * `shared.symbolic_core`: Unified access to SymPy and NumPy for all plugins.
        * `shared.plotting_engine`: A high-performance Matplotlib wrapper that handles figure docking and 2D/3D rendering for any connected tool.

2.  **The IDE Plugins (`ides`)**
    The platform currently hosts two powerful tools:

    * **📘 Tool 1: MathexLab (MATLAB® Compatible)**
        * A transcript-based IDE that runs `.m` files.
        * Features a dedicated **Workspace Inspector**, **Command Window**, and **Variable Viewer**.
        * Powered by a custom **Transpiler** that converts MATLAB syntax to Python on the fly.
    
    * **🐺 Tool 2: Mathematica (Mathematica® Style)**
        * A symbolic-first environment designed for high-level algebraic manipulation.
        * Integrates deep symbolic computation capabilities directly into the platform.

---

## 🛠️ Feature Deep Dive: The MathexLab Tool

The flagship tool of the platform is the **MathexLab IDE**, designed to replace MATLAB for PhD students and engineers.

### 🖥️ Layer 1: Professional UI (`ides.mathexlab.ui`)
The user interface is built with **PySide6**, strictly adhering to the "transcript model" familiar to MATLAB users.

#### **1. Command Window (`ui.console.ConsoleWidget`)**
* **What:** A specialized `QPlainTextEdit` widget that acts as the primary REPL.
* **Why:** Researchers need a persistent history where the prompt (`>>`) and past outputs are immutable (read-only), but current input is editable.
* **How:** * **Strict Transcript Modeling:** The console maintains a `locked_pos` index to block editing of history.
    * **Visual Distinction:** User input is **Grey** and system output is **White**, ensuring clarity.

#### **2. Workspace Inspector (`ui.workspace.WorkspaceWidget`)**
* **What:** An interactive data viewer that mirrors the MATLAB "Workspace" panel.
* **How:**
    * **Live Slicing:** Automatically generates 2D "Slice Views" (e.g., `[:,:,0]`) for 3D/4D arrays to prevent UI freezes.
    * **Bi-directional Sync:** Editing a cell in the table directly mutates the underlying `KernelSession` memory.

#### **3. Plot Dock (`ui.plotdock.PlotDock`)**
* **What:** A dedicated panel for managing matplotlib figures.
* **How:** Redirects `plt.show()` calls to a docked layout manager, organizing multiple figures into tabs.

---

### 🧠 Layer 2: Native Transpiler Engine (`ides.mathexlab.language`)
This is the core innovation. It translates MATLAB source code into optimized Python bytecode on the fly.

#### **1. The Tokenizer (`language.tokenizer`)**
* **What:** A lexical analyzer built specifically for MATLAB syntax (handling `'` ambiguity, `...` continuations, etc.).

#### **2. The AST Parser (`language.parser`)**
* **What:** A Recursive Descent Parser that builds an Abstract Syntax Tree (AST) to support complex structures like `switch-case` and `try-catch`.

#### **3. The Transpiler (`language.transpiler`)**
* **What:** Converts the AST into executable Python code.
* **Key Translations:**
    * **Indexing:** Converts 1-based (`A(1)`) to 0-based (`A[0]`).
    * **Matrix Math:** Maps `*` to matrix multiplication (`@`).
    * **Memory:** Injects "Copy-on-Write" behavior to emulate MATLAB's safety.

---

### 🔬 Layer 3: Research Toolboxes (`ides.mathexlab.toolbox`)

#### **1. Partial Differential Equations (`pde`)**
* **Function:** `pdepe(m, pdefun, icfun, bcfun, xmesh, tspan)`
* **What:** Solves 1D parabolic/elliptic PDEs using the Method of Lines.
* **Features:** Supports Slab, Cylindrical, and Spherical geometries ($m=0,1,2$).

#### **2. Control Systems (`control`)**
* **Function:** `tf`, `step`, `bode`, `rlocus`
* **What:** Represents LTI systems and solves characteristic equations ($1 + k \cdot G(s) = 0$) for stability analysis.

#### **3. Optimization (`optim`)**
* **Function:** `fmincon`
* **What:** Wraps `scipy.optimize.minimize` (SLSQP) to solve constrained non-linear optimization problems using MATLAB-style constraint functions.

---

## 💻 Tech Stack

MathexLab is built with high-performance Python technologies:

| Component | Technology | Role |
| :--- | :--- | :--- |
| **GUI Framework** | **PySide6 (Qt)** | Native OS integration, dark mode, and hardware acceleration. |
| **Runtime** | **Python 3.11+** | Selected for speed and advanced type hinting. |
| **Math Engine** | **NumPy & SciPy** | Powers the linear algebra, signal processing, and ODE solvers. |
| **Symbolic** | **SymPy** | Backend for the Mathematica tool and Symbolic Toolbox. |
| **Rendering** | **Matplotlib** | The engine behind the shared 2D/3D plotting system. |

---

## 📦 Installation & Setup

### Prerequisites
* Python 3.10 or higher.

### Steps

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/patarsamar/MathexLab.git](https://github.com/patarsamar/MathexLab.git)
    cd MathexLab
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Platform**
    ```bash
    python main.py
    ```

*Note: If you encounter import errors regarding `platform`, ensure you have run the `fix_imports.py` script included in the root directory to finalize the directory restructuring.*

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and create a pull request.

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