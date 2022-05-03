openapi:
	poetry run python -m documentation.openapi_yaml_generator

build:
	docker build --target build -t colab_ssh .

build_dev:
	DOCKER_BUILDKIT=1 docker build --target build_dev -t colab_ssh .

up:
	docker-compose up -d --build

down:
	docker-compose down

down_volume:
	docker-compose down -v

test:
	docker build --target test -t colab_ssh:test .

commit:
	cz commit

requirements:
	poetry export -o requirements.txt --dev
