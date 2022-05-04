### Project description

**This application allows you to upload files into minio storage bucket and upload files from minio storage directly to colab.
Furthermore, you will be able to remotely execute scripts on colab and dynamically download script output files back to 
minio storage in synchronization mode (rsync-like approach).**


### Prerequisites

* Make sure that you have installed the latest versions of `python` and `pip` on your computer. 
  Also, you have to install [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/).


* This project by default uses [poetry](https://python-poetry.org/) for dependency and virtual environment management.
  Make sure to install it too.


* Make sure to provide all required environment variables (via `.env` file, `export` command, secrets, etc.) before running application.


### Development tools

1) For managing pre-commit hooks this project uses [pre-commit](https://pre-commit.com/).


2) For import sorting this project uses [isort](https://pycqa.github.io/isort/).


3) For code format checking this project uses [black](https://github.com/psf/black).


4) For code linting this project uses [flake8](https://flake8.pycqa.org/en/latest/) and [pylint](https://pypi.org/project/pylint/).


5) For type checking his project uses [mypy](https://github.com/python/mypy)


6) For create commits and lint commit messages this project uses [commitizen](https://commitizen-tools.github.io/commitizen/).
   Run `make commit` to use commitizen during commits.


7) There is special `build_dev` stage in Docker file to build dev version of application image.


### CI/CD

This project involves [github actions](https://docs.github.com/en/actions) to run all checks and unit-tests on `push` to remote repository.


### Make commands

There are lots of useful commands in `Makefile` included into this project's repo. Use `make <some_command>` syntax to run each of them. 
If your system doesn't support make commands - you may copy commands from `Makefile` directly into terminal.


### Installation

1) To install all the required dependencies and set up a virtual environment run in the cloned repository directory use:

    `poetry install`

    You can also install project dependencies using `pip install -r requirements.txt`.


2) To config pre-commit hooks for code linting, code format checking and linting commit messages run in the cloned directory:

    `poetry run pre-commit install`


3) Build app image using

    `make build`

    To build reloadable application locally use `make build_dev` to build image in development environment.


4) Run Docker containers using

    `make up`
    
    *Note: this will also create and attach persistent named volume `logs` for Docker container. 
    Container will use this volume to store application `app.log` file.*


5) Stop and remove Docker containers using

    `make down`

    If you also want to remove log volume use `make down_volume`


### Running app

1) By default, application will be accessible at http://localhost:8080, minio storage console - at http://localhost:9001. 
   You can try all endpoints with SWAGGER documentation at http://localhost:8080/docs


2) Use `/files/upload_minio` resource to upload files to colab. You should provide minio bucket name in header. 
   Request uses multipart/form-data to upload one or multiple files to minio storage. You should also specify key prefix 
   that will be added to all uploaded files (in directory-like way) e.g.: `files/main/`. If there are existing files with 
   the same prefix - they will be removed from storage.
   ![/files/upload_minio](https://user-images.githubusercontent.com/79688463/166653150-59630f31-6887-4b77-8e5c-8f93c1cac344.png)


3) Copy script from `documentation/colab_ssh_config_script.ipynb` to your colab account.
   Register at [ngrok](https://ngrok.com/). Run this cell on colab. Provide ngrok [auth token](https://dashboard.ngrok.com/auth) 
   to prompt. Tunel will be created with connection credentials at `/content/ssh_config/credentials` file.
   ![documentation/colab_ssh_config_script.ipynb](https://user-images.githubusercontent.com/79688463/166653155-ebb91292-e985-48fe-b806-a75d2f5f559f.png)


4) Use `/files/upload_colab` to send files from minio storage to colab. Files will be saved at colab's `/content/uploaded/` directory.
   Specify files key prefix in request body keys_prefix field (in directory-like way) - all files with such prefix will be uploaded to colab.
   To connect colab you must provide all credentials (i.e. username, password, host and port) from `/content/ssh_config/credentials` file.
   Files will be streamed to colab directly. If script_name specified - this script will be executed on colab. 
   If jupiter notebook provided as script (e.g. file with .ipynb extension). It will be converted to python script 
   (e.g. file with .py extension) on colab before execution. *Note: make sure to save script outputs at `/content/uploaded/output/` 
   in order to make them available to further download from colab to minio.*
   ![/files/upload_colab](https://user-images.githubusercontent.com/79688463/166653158-8fcea5c0-ca4b-459a-abfb-0d20beb72cbb.png)


5) Use `/files/download_colab` to download script results from colab directory `/content/uploaded/output/` to minio storage. 
   Specified key prefix will be added to each object in minio (in directory-like way). Files are streamed directly from colab to minio
   (i.e. without equally stored in application local storage) using sshfs protocol, which will mount colab remote directory 
   to temporary created application local directory. This action uses aws CLI sync under the hood, so it can be used to synchronise 
   minio storage files with dynamically created/updated/deleted by colab script files (i.e. this means that if new file was 
   created/updated/deleted on colab directory - it will be uploaded/updated/deleted in minio respectively. If file didn't change - 
   it won't be modified in minio.)
   ![/files/download_colab](https://user-images.githubusercontent.com/79688463/166653159-92709243-b2c9-4dc6-930d-0a5470337599.png)


### Documentation

* Description of all project's endpoints and API may be viewed without running any services from `documentation/openapi.yaml` file


* You can update openapi.yaml documentation for API at any time by using `make openapi` command.


* All warnings and info messages will be shown in container's stdout and saved in `app.log` file.


* Use `colab_ssh_config_script.ipynb` on colab session side to open ssh connection tunnel.


* You may use `test_script.py` or `test_script.ipynb` files from `documentation/` as examples of scripts to upload, 
  run on colab and get remote outputs.


### Running tests.

* Use `make test` to run build image and run all linters checks and unit-tests. 
  

* After all tests [coverage report](https://pytest-cov.readthedocs.io/en/latest/) will be also shown.

* Staged changes will be checked during commits via pre-commit hook.

* All checks and tests will run on code push to remote repository as part of github actions.
