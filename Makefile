# IconMaker — các quy trình (pipeline). Chạy `make help` để xem danh sách.
#
# Trên Windows CMD/PowerShell, make sẽ dùng shell là cmd; nếu có sh/bash
# (Git Bash, MSYS) thì dùng trực tiếp được. Biến bên dưới tự thích ứng.

ifeq ($(OS),Windows_NT)
    PYTHONPATH_CMD = set "PYTHONPATH=src" &
    RM = -rmdir /s /q
else
    PYTHONPATH_CMD = env PYTHONPATH=src
    RM = rm -rf
endif

INPUT_DIR  ?= input
SPRITES    ?= sprites_out
ICONS      ?= icon_out
LAUNCHER   = launcher/IconMakerLauncher
LAUNCHER_EXE = $(LAUNCHER)/bin/Release/net8.0-windows/IconMakerLauncher.exe

.PHONY: help all install test sprites icons ico foldericon launcher run clean

help:
	@$(PYTHONPATH_CMD) python -c "print('''IconMaker Makefile:\n  make all        install + test + sprites + icons\n  make install    cai Python deps (requirements.txt)\n  make test       chay toan bo pytest\n  make sprites    tach sprite: $(INPUT_DIR)/ -> $(SPRITES)/\n  make icons      build ICO chat luong cao: $(SPRITES)/ -> $(ICONS)/ (1 tang, phang)\n  make ico        goi converter truc tiep (SRC=...png DEST=...ico)\n  make foldericon dat icon cho thu muc (ICON=...ico FOLDER=...)\n  make launcher   build launcher C# (can .NET 8+ SDK)\n  make run        mo GUI qua launcher\n  make clean      xoa sprites_out/ icon_out/ __pycache__ .pytest_cache (giu input/)''')"

all: install test sprites icons

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest

sprites:
	$(PYTHONPATH_CMD) python -m iconmaker.sprites $(INPUT_DIR) $(SPRITES)

icons:
	$(PYTHONPATH_CMD) python -m iconmaker.icons $(SPRITES) $(ICONS)

SRC ?= input/0.png
DEST ?= $(ICONS)/manual.ico
ico:
	$(PYTHONPATH_CMD) python -m iconmaker.cli "$(SRC)" "$(DEST)"

ICON ?= $(ICONS)/manual.ico
FOLDER ?= .
foldericon:
	$(PYTHONPATH_CMD) python -m iconmaker.foldericon "$(ICON)" "$(FOLDER)"

launcher:
	dotnet build $(LAUNCHER) -c Release

run: launcher
	"$(LAUNCHER_EXE)"

clean:
	$(RM) $(SPRITES) $(ICONS)
	$(PYTHONPATH_CMD) python -c "import shutil,glob,os; [shutil.rmtree(p,ignore_errors=True) for p in ['.pytest_cache']+glob.glob('**/__pycache__',recursive=True)]; [shutil.rmtree(d,ignore_errors=True) for d in ['$(LAUNCHER)/bin','$(LAUNCHER)/obj']]"
