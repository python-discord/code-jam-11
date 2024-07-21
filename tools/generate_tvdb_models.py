import subprocess
from pathlib import Path
from urllib.parse import ParseResult, urlparse

from datamodel_code_generator import DataModelType, InputFileType, OpenAPIScope, PythonVersion, generate

HEADER: str = """# ruff: noqa: D101, ERA001, E501
"""


def _generate_models() -> Path:
    output = Path("./src/tvdb/generated_models.py")
    url: ParseResult = urlparse("https://thetvdb.github.io/v4-api/swagger.yml")
    generate(
        url,
        input_file_type=InputFileType.OpenAPI,
        input_filename="swagger.yml",
        output=output,
        output_model_type=DataModelType.PydanticV2BaseModel,
        field_constraints=True,
        snake_case_field=True,
        target_python_version=PythonVersion.PY_312,
        use_default_kwarg=True,
        use_union_operator=True,
        reuse_model=True,
        field_include_all_keys=True,
        strict_nullable=True,
        use_schema_description=True,
        keep_model_order=True,
        enable_version_header=True,
        openapi_scopes=[OpenAPIScope.Schemas, OpenAPIScope.Paths],
    )
    with output.open("r") as f:
        contents = f.read()
    contents = contents.replace("’", "'")  # noqa: RUF001
    with output.open("w") as f:
        f.write(HEADER + contents)
        f.truncate()
    return output


def _run_ruff(file_path: Path) -> None:
    subprocess.run(["poetry", "run", "ruff", "check", "--fix", "--unsafe-fixes", str(file_path)], check=True)  # noqa: S603, S607


def main() -> None:
    """The main entry point for the script."""
    generated_file = _generate_models()
    _run_ruff(generated_file)


if __name__ == "__main__":
    main()
