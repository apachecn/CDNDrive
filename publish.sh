rm -rf dist
python setup.py sdist bdist_wheel
twine upload dist/* -u $(pip config get pypi.username) -p $(pip config get pypi.password)