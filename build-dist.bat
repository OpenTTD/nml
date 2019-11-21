python .\setup.py build_py
python .\setup.py build_ext --inplace
pyinstaller .\nmlc.spec
