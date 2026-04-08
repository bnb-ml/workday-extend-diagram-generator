import json
import argparse
import sys
import os
import subprocess
import urllib.request
import logging
import zipfile
import shutil
from typing import List, Dict, Any, Set

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

class DiagramGenerationError(Exception):
    """Custom exception base class for diagram generation errors."""
    pass

class DependencyMissingError(DiagramGenerationError):
    """Raised when a required system dependency is missing."""
    pass

class DataLoadError(DiagramGenerationError):
    """Raised when data loading or parsing fails."""
    pass

class RenderError(DiagramGenerationError):
    """Raised when the rendering subprocess encounters an error."""
    pass

class DiagramGenerator:
    """
    A class to generate PlantUML Entity-Relationship diagrams from a JSON definition.
    """

    PLANTUML_JAR_URL = "https://github.com/plantuml/plantuml/releases/download/v1.2024.3/plantuml-1.2024.3.jar"
    PLANTUML_JAR_NAME = "plantuml.jar"

    def __init__(self, json_path: str, output_prefix: str) -> None:
        self.json_path = json_path
        self.output_prefix = output_prefix
        self.output_txt = f"{self.output_prefix}.txt"
        self.output_jpg = f"{self.output_prefix}.jpg"
        self.data: List[Dict[str, Any]] = []
        self.internal_entities: Set[str] = set()

    def _check_system_dependency(self, command: str) -> None:
        if not shutil.which(command):
            raise DependencyMissingError(f"Required system command '{command}' is not installed or not in PATH.")

    def _ensure_plantuml_jar(self) -> str:
        cache_dir = os.path.expanduser("~/.cache/workday-diagram")
        os.makedirs(cache_dir, exist_ok=True)
        jar_path = os.path.join(cache_dir, self.PLANTUML_JAR_NAME)
        if not os.path.exists(jar_path):
            logging.info("Downloading PlantUML jar to %s", jar_path)
            try:
                urllib.request.urlretrieve(self.PLANTUML_JAR_URL, jar_path)
            except Exception as e:
                raise DependencyMissingError(f"Failed to download PlantUML jar: {e}") from e
        return jar_path

    def _process_json_content(self, content: Any) -> None:
        if isinstance(content, list):
            self.data.extend(content)
        elif isinstance(content, dict):
            self.data.append(content)
        else:
            raise DataLoadError("Invalid JSON structure format: expected dict or list.")

    def _load_from_directory(self) -> None:
        for filename in os.listdir(self.json_path):
            if filename.endswith(".businessobject"):
                file_path = os.path.join(self.json_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self._process_json_content(json.load(f))
                except OSError as e:
                    raise DataLoadError(f"IO Error loading {filename}: {e}") from e
                except json.JSONDecodeError as e:
                    raise DataLoadError(f"JSON Parse Error in {filename}: {e}") from e

    def _load_from_zip(self) -> None:
        try:
            with zipfile.ZipFile(self.json_path, "r") as z:
                for filename in z.namelist():
                    if filename.endswith(".businessobject"):
                        with z.open(filename) as f:
                            self._process_json_content(json.loads(f.read().decode("utf-8")))
        except zipfile.BadZipFile as e:
            raise DataLoadError(f"Invalid ZIP file: {e}") from e
        except json.JSONDecodeError as e:
            raise DataLoadError(f"JSON Parse Error inside ZIP: {e}") from e
        except OSError as e:
            raise DataLoadError(f"Error loading from ZIP {self.json_path}: {e}") from e

    def _load_from_file(self) -> None:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self._process_json_content(json.load(f))
        except FileNotFoundError as e:
            raise DataLoadError(f"File not found: {self.json_path}") from e
        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in {self.json_path}: {e}") from e
        except OSError as e:
            raise DataLoadError(f"Error loading file {self.json_path}: {e}") from e

    def load_data(self) -> None:
        self.data.clear()
        
        if not os.path.exists(self.json_path):
            raise DataLoadError(f"Input path does not exist: {self.json_path}")

        if os.path.isdir(self.json_path):
            self._load_from_directory()
        elif self.json_path.lower().endswith(".zip"):
            self._load_from_zip()
        else:
            self._load_from_file()

        if not self.data:
            raise DataLoadError("No valid data loaded from the input source.")

        self.internal_entities = {
            entity.get("name") for entity in self.data if isinstance(entity, dict) and entity.get("name")
        }
        
    def generate_plantuml_code(self) -> str:
        lines: List[str] = [
            "@startuml",
            "!theme plain",
            "skinparam linetype ortho",
            "skinparam classBackgroundColor #F9F9F9",
            "skinparam classBorderColor #333333",
            "skinparam classArrowColor #333333",
            "hide methods",
            "hide circle",
            ""
        ]

        relationships: List[str] = []

        for entity in self.data:
            if not isinstance(entity, dict):
                continue
                
            entity_name = entity.get("name")
            if not entity_name or not isinstance(entity_name, str):
                continue
                
            entity_label = entity.get("label", entity_name)
            lines.append(f'entity "{entity_label}" as {entity_name} {{')

            fields = entity.get("fields")
            if not isinstance(fields, list):
                fields = []
                
            for field in fields:
                if not isinstance(field, dict):
                    continue
                    
                field_name = field.get("name", "Unknown")
                field_type = field.get("type", "TEXT")

                is_rel = field_type in ("SINGLE_INSTANCE", "MULTI_INSTANCE")
                target = field.get("target")

                if is_rel and target in self.internal_entities:
                    multiplicity_right = "1" if field_type == "SINGLE_INSTANCE" else "*"
                    relationships.append(f'{entity_name} --> "{multiplicity_right}" {target} : {field_name}')
                elif is_rel and target not in self.internal_entities:
                    multi_type = "Single Instance" if field_type == "SINGLE_INSTANCE" else "Multi Instance"
                    lines.append(f"  {field_name} : {target} <<Workday, {multi_type}>>")
                else:
                    lines.append(f"  {field_name} : {field_type}")

            lines.append("}")
            lines.append("")

        lines.extend(relationships)
        lines.append("@enduml")
        return "\n".join(lines)

    def save_diagram_source(self, puml_code: str) -> None:
        try:
            with open(self.output_txt, "w", encoding="utf-8") as f:
                f.write(puml_code)
        except OSError as e:
            raise RenderError(f"Failed writing PlantUML source to {self.output_txt}: {e}") from e

    def render_image(self) -> None:
        self._check_system_dependency("java")
        
        try:
            from PIL import Image
        except ImportError as e:
            raise DependencyMissingError(
                "The 'Pillow' library is required for cross-platform image processing. "
                "Please install it using: 'pip install Pillow' or 'pip install -r requirements.txt'"
            ) from e

        jar_path = self._ensure_plantuml_jar()

        try:
            command = ["java", "-jar", jar_path, "-tpng", self.output_txt]
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RenderError(f"PlantUML generation failed: {e.stderr}") from e

        output_png = f"{self.output_prefix}.png"
        
        if not os.path.exists(output_png):
            raise RenderError("PlantUML did not generate the expected PNG file.")

        try:
            with Image.open(output_png) as img:
                rgb_im = img.convert('RGB')
                rgb_im.save(self.output_jpg)
            
            if os.path.exists(output_png):
                os.remove(output_png)
        except Exception as e:
            raise RenderError(f"Error converting PNG to JPG using Pillow: {e}") from e

    def run(self) -> None:
        try:
            self.load_data()
            puml_code = self.generate_plantuml_code()
            self.save_diagram_source(puml_code)
            self.render_image()
            logging.info("Successfully generated %s", self.output_jpg)
        except DiagramGenerationError as e:
            logging.error("Generation aborted: %s", e)
            sys.exit(1)
        except Exception as e:
            logging.critical("An unexpected error occurred: %s", e, exc_info=True)
            sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ER Diagram via PlantUML from a JSON or ZIP descriptor"
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Path to the input JSON, ZIP file, or directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="diagram",
        help="Prefix for the output files (txt and jpg)",
    )

    args = parser.parse_args()

    generator = DiagramGenerator(json_path=args.input, output_prefix=args.output)
    generator.run()

if __name__ == "__main__":
    main()
