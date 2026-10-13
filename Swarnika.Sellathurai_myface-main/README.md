# “MyFace” Example Project (INF226, 2025)

The tasks are [here](https://git.app.uib.no/inf226/25h/inf226-25h/-/wikis/portfolio-2/myface).

-   Flask docs: https://flask.palletsprojects.com/en/3.0.x/
-   Flask login docs: https://flask-login.readthedocs.io/en/latest/
-   Using "Log in with _social network_": https://python-social-auth.readthedocs.io/en/latest/configuration/flask.html

## To Use

### Set up virtual environment and install dependencies

Use the [`venv`](https://docs.python.org/3/library/venv.html) command to create a virtual environment. E.g., on Unix (see web page for how to use it on Windows and with non-Bourne-like shells):

```sh
cd assignment-2
python -m venv .venv  # or possibly python3
. .venv/bin/activate  # yes there's a dot at the beginning of the line
pip install -r requirements.txt
```

You can exit the virtual environment with the command `deactivate`.

### Run it

To run the dev server, start Flask:

```sh
flask -A myface run --debug
```

and then navigate to [http://localhost:5000/](http://localhost:5000/).

If you want to experiment using the Python command line, you can start the Flask shell:

```sh
flask -A myface shell
```

### Running with Docker

```sh
# this is where data files will be stored, same as `instance/` when running on the dev server
DATA_DIR=docker-instance

# create the data dir, make it owned by the user used inside the container (222 by default)
# you only need to do this once
mkdir -p $DATA_DIR && chmod g+s $DATA_DIR && sudo chown 222 $DATA_DIR

# do this whenever the source code has changed
docker build -t myface .

# do this to run the container
docker run --init --rm --name myface -p 8000:8000 -v $DATA_DIR:/srv/myface/instance -it  myface

# or you can run it "live" from the working directory, so you don't have to rebuild the
# docker image whenever you change the source code – this will also reload changed files automatically
docker run --init --rm --name myface -p 8000:8000 -v .:/srv/myface:ro -v $DATA_DIR:/srv/myface/instance -it  myface
```

## Copyright

-   `unknown.png` – from [OpenMoji](https://openmoji.org/about/) ([Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/))
-   `favicon.(png|ico)` – from [Game Icons](https://game-icons.net/1x1/skoll/knockout.html) ([CC BY 3.0](http://creativecommons.org/licenses/by/3.0/))
-   `_uhtml.js` – from [µHTML](https://github.com/WebReflection/uhtml) (Copyright (c) 2020, Andrea Giammarchi, [ISC License](https://opensource.org/license/isc-license-txt/))
-   Base code by Anya
