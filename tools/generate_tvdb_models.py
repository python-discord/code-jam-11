import subprocess
import sys


def _run_datamodel_codegen() -> None:
    command = [
        "poetry",
        "run",
        "datamodel-codegen",
        "--url",
        "https://thetvdb.github.io/v4-api/swagger.yml",
        "--input-file-type",
        "openapi",
        "--output",
        r"./src/tvdb/generated_models.py",
        "--output-model-type",
        "pydantic_v2.BaseModel",
    ]
    try:
        subprocess.run(command, check=True)  # noqa: S603
        print("Code generation completed successfully.")  # noqa: T201
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running datamodel-codegen: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)


def main() -> None:
    """The main entry point for the script.

    :return:
    """
    _run_datamodel_codegen()


if __name__ == "__main__":
    main()
