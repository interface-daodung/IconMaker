# IconMaker — app GUI (CustomTkinter). Chỉ còn 2 target: `run` và `cls`.
#
# Chạy bằng shortcut Windows (không cần make, không cần PYTHONPATH):
#   Target:  pythonw "C:\Users\inter\Project\MyHub\IconMaker\src\main.py"
# (main.py tự thêm src/ vào sys.path và neo cwd về gốc project.)

ifeq ($(OS),Windows_NT)
    GUI_PYTHON := $(if $(wildcard .venv/Scripts/pythonw.exe),.venv\Scripts\pythonw.exe,pythonw)
    PY := $(if $(wildcard .venv/Scripts/python.exe),.venv\Scripts\python.exe,python)
else
    GUI_PYTHON := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
    PY := $(GUI_PYTHON)
endif

.PHONY: run cls

run:
	$(GUI_PYTHON) src/main.py

cls:
	$(PY) -c "import glob,shutil; [shutil.rmtree(p,ignore_errors=True) for p in ['.pytest_cache']+glob.glob('**/__pycache__',recursive=True)]"
