import yaml

from app.main import app


def generate_documentation() -> None:
    """Geneerates custom openapi.yaml SWAGGER documentation from fastapi app.

    :return: None.
    """
    with open("./documentation/openapi.yaml", "w") as openapi_file:
        yaml.dump(app.openapi(), openapi_file, sort_keys=False)


if __name__ == "__main__":
    generate_documentation()
