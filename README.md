# get it up and running

``python -m venv .venv``

``.venv\Scripts\activate``

``pip install Flask``

``pip install .\dependency\coro_context_manager-0.2.0-py2.py3-none-any.whl``

``pip install .\dependency\pydapper-0.10.0-py2.py3-none-any.whl``

``pip install mariadb``

# init db
``flask --app flaskr init-db ``

# test run
``flask --app flaskr run --debug``

# to test
``pip install pytest coverage``

``pytest``

``coverage run -m pytest``

``coverage report``

``coverage html``

# build
``pip install build``

``python -m build --wheel``

```
You can find the file in dist/flaskr-**.whl.

set up a new virtualenv, then install the file with pip.
```

``pip install flaskr-1.0.0-py3-none-any.whl``
