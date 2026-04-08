# Workday Extend ER Diagram Generator

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![PlantUML](https://img.shields.io/badge/PlantUML-Supported-brightgreen)
![Cross-Platform](https://img.shields.io/badge/os-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

**Workday Extend ER Diagram Generator** is a robust command-line tool written in Python. It automatically analyzes Workday Extend Business Object definitions (`.businessobject` or aggregated `.json` files) and generates high-quality Entity-Relationship (ER) diagrams using PlantUML.

This tool is specifically designed to understand the relationship semantics of Workday Extend. It differentiates between internal custom business objects (rendering them as relational connections) and native Workday objects (rendering them as strongly-typed attributes with multiplicity indicators).

## Features

- **Multi-Format Parsing**: Point the tool directly to a `.zip` archive, an extracted `/model` directory, or a standalone `.json` array containing your business objects. No manual extraction required!
- **Workday Object Awareness**: Automatically segregates internal application entities from native Workday references (e.g., `WORKER`, `LEARNING_CONTENT`), marking the latter explicitly as `<<Workday, Single/Multi Instance>>`.
- **Zero-Configuration Rendering**: The tool automatically fetches the PlantUML binary if it's not present globally, generates the PlantUML source code, and directly renders a high-quality `.jpg` diagram.
- **Robust Error Handling**: Impeccable exception management, strict type hinting, and system validations ensure a smooth execution pipeline.

## Prerequisites

This tool is a Python-based wrapper that orchestrates Java (for the PlantUML engine) and Graphviz (for layout calculation). To ensure a smooth experience, please verify that your environment meets the following requirements:

| Dependency  | Purpose                | Link                                            |
| :---------- | :--------------------- | :---------------------------------------------- |
| Python 3.7+ | Core tool logic        | [python.org](https://www.python.org/downloads/) |
| Java (JRE)  | Executes PlantUML      | [java.com](https://www.java.com/en/download/)   |
| Graphviz    | Renders diagram layout | [graphviz.org](https://graphviz.org/download/)  |

<details>
<summary>Prerequisites Install Guide</summary>

### Prerequisites Install Guide

Depending on your Operating System, you can install all dependencies at once using these commands:

#### 🍎 macOS (Homebrew)

```bash
brew install python openjdk graphviz pipx
pipx ensurepath
# Note: You may need to symlink openjdk for the system to find it:
sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk
```

#### 🐧 Ubuntu / Debian / WSL

```bash
sudo apt update
sudo apt install -y python3 python3-pip default-jre graphviz pipx
pipx ensurepath
```

#### 🪟 Windows (winget)

```powershell
winget install Python.Python.3.12 OpenJDK.OpenJDK.21 Graphviz.Graphviz pipx
pipx ensurepath
```

---

### Verify Your Environment

Before installing the generator, you can run this single command to ensure all system dependencies are correctly mapped in your `PATH`:

```bash
python3 --version && java -version && dot -V
```

If all three commands return a version number, you are ready to proceed to the **Installation** section!

</details>

## Installation

### Option 1: Using pipx (Recommended)

To avoid conflicts with system Python packages and bypass "externally-managed-environment" errors, use [pipx](https://pypa.github.io/pipx/).

```bash
pipx install git+https://github.com/bnb-ml/workday-extend-diagram-generator.git
```

### Option 2: Using a Virtual Environment

If you prefer standard pip, always use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/bnb-ml/workday-extend-diagram-generator.git
```

## Obtaining the Source Files

The generator requires your Workday Extend Business Objects as input. Here is how you can obtain them safely:

### Method 1: Exporting the App Package (Recommended)

1. Log in to your **Workday Extend Developer Console**.
2. Navigate to your application.
3. Choose the option to **Export** or **Download** the app source code.
4. You will receive a `.zip` file (e.g., `myApp_qxbfwx.zip`).
5. You can pass this `.zip` file directly to the generator! The tool will automatically look for the `model/` directory inside the archive and parse all `.businessobject` files.

### Method 2: Extracting the Archive

If you are already working with a local clone or an extracted version of your Workday Extend application, locate the `model/` directory. This folder typically contains all your custom `.businessobject` JSON definitions.
You can pass the path to this `model/` directory directly to the tool.

### Method 3: Manual JSON Array

If you prefer, you can manually assemble a single `.json` file containing a JSON Array `[]` of the business objects you want to diagram.

## ️ Usage

Run the generator from your terminal using the globally installed `workday-diagram` command:

```bash
workday-diagram --input <INPUT_PATH> --output <OUTPUT_PREFIX>
```

### Examples

**1. Generating from a ZIP archive (Automatically parses the `model/` directory inside):**

```bash
workday-diagram --input myApp_export.zip --output my_diagram
```

**2. Generating from an extracted `model/` folder:**

```bash
workday-diagram --input path/to/app/model --output my_diagram
```

**3. Generating from a consolidated JSON file:**

```bash
workday-diagram --input business_objects.json --output my_diagram
```

### Output

The execution will yield two files in your current directory:

- `my_diagram.txt`: The declarative PlantUML source code.
- `my_diagram.jpg`: The fully rendered ER Diagram image.

## Architecture & Best Practices

This tool has been built following Clean Code and solid software engineering principles:

- **Modular Parsing Pipeline**: Data ingestion is strictly typed and decoupled from rendering logic.
- **System Validations**: Pre-flight checks ensure `java` is installed and core dependencies like `Pillow` are present before heavy processing.
- **Automated Artifact Management**: The required `plantuml.jar` is intelligently downloaded into your user's cache directory (`~/.cache/workday-diagram/`) exclusively if it isn't found, preventing permission issues when installed globally.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## License

This project is open-source and available under the MIT License.

## Troubleshooting

### "Externally Managed Environment" Error

If you see an error regarding `PEP 668`, it means your OS is protecting its system Python. Use **Option 1 (pipx)** in the installation section to resolve this.

### "Command 'java' not found"

The tool uses PlantUML, which is a Java application. Ensure you can run `java -version` in your terminal. If not, install the JRE (see Prerequisites).

### Diagrams looking "broken" or missing lines

This usually happens if **Graphviz** is missing. Ensure the `dot` command is available in your PATH by installing Graphviz.
