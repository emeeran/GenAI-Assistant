import subprocess
import tomli
import tomli_w
from pathlib import Path


def get_packages(src_dir="src"):
    """Retrieve package names from the specified directory."""
    src = Path(src_dir)
    if not src.exists():
        raise FileNotFoundError(f"Source directory '{src_dir}' not found.")
    return [d.name for d in src.iterdir() if d.is_dir() and not d.name.startswith(".")]


def sync_dependencies(
    requirements_file="requirements.txt", pyproject_path="pyproject.toml"
):
    """
    Synchronize project dependencies and update pyproject.toml.
    """
    try:
        # Generate requirements.txt using 'pip freeze | grep -v ^-e > requirements.txt'
        subprocess.run(
            ["pip", "freeze", "|", "grep", "-v", "^-e"],
            stdout=open(requirements_file, "w"),
            check=True,
        )

        # Update pyproject.toml
        pyproject_path = Path(pyproject_path)
        if pyproject_path.exists():
            with pyproject_path.open("rb") as f:
                pyproject = tomli.load(f)

            pyproject.setdefault("project", {})
            pyproject["project"].setdefault("dependencies", [])

            with open(requirements_file) as req_file:
                for line in req_file:
                    name, version = line.strip().split("==")
                    pyproject["project"]["dependencies"].append(f"{name}=={version}")

            pyproject.setdefault("tool", {})
            pyproject["tool"].setdefault("setuptools", {})
            pyproject["tool"]["setuptools"]["packages"] = get_packages()

            with pyproject_path.open("wb") as f:
                tomli_w.dump(pyproject, f)

        return True

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to generate requirements.txt - {str(e)}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    sync_dependencies()
