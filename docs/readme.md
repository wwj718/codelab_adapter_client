# upload to pypi
https://pypi.org/project/twine/

*  pip install twine
*  python -m pip install --upgrade setuptools wheel
*  python setup.py sdist bdist_wheel
*  twine upload dist/*