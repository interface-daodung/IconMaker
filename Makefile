# IconMaker — các quy trình (pipeline). Chạy `make help` để xem danh sách.
#
# Layout gốc: core/ (logic) + gui/ + tools/ + main.py — chạy trực tiếp từ
# thư mục gốc, không cần PYTHONPATH.
#
# Trên Windows CMD/PowerShell, make sẽ dùng shell là cmd.

ifeq ($(OS),Windows_NT)
GUI_PYTHON = pythonw
RM = rmdir /s /q
else
GUI_PYTHON = python3
RM = rm -rf
endif

INPUT_DIR  ?= input
SPRITES    ?= sprites_out
ICONS      ?= icon_out
LAUNCHER   = launcher/IconMakerLauncher
LAUNCHER_EXE = $(LAUNCHER)/bin/Release/net8.0-windows/IconMakerLauncher.exe

.PHONY: help all install test sprites icons ico rounded foldericon launcher new-launcher gui run clean

help:
	@python -c "print('''IconMaker Makefile:\n  make all        install + test + sprites + icons\n  make install    cai Python deps (requirements.txt)\n  make test       chay toan bo pytest\n  make sprites    tach sprite: $(INPUT_DIR)/ -> $(SPRITES)/\n  make icons      build ICO chat luong cao: $(SPRITES)/ -> $(ICONS)/ (1 tang, phang)\n  make ico        convert truc tiep (SRC=...png DEST=...ico)\n  make rounded    bo goc anh (SRC=... DEST=... RADIUS=...)\n  make foldericon dat icon cho thu muc (ICON=...ico FOLDER=...)\n  make launcher   build launcher C# (can .NET 8+ SDK)\n  make new-launcher NAME=<TenApp> [ICON=...ico] sinh launcher moi theo khung tray-clone\n  make gui        mo GUI truc tiep bang pythonw (khong hien console)\n  make run        mo GUI qua launcher (launcher tu goi pythonw)\n  make clean      xoa sprites_out/ icon_out/ __pycache__ .pytest_cache (giu input/)''')"

all: install test sprites icons

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest

sprites:
	python -m core.sprites $(INPUT_DIR) $(SPRITES)

icons:
	python -m core.icons $(SPRITES) $(ICONS)

SRC ?= input/0.png
DEST ?= $(ICONS)/manual.ico
ico:
	python -m core.convert "$(SRC)" "$(DEST)"

RSRC ?= input/0.png
RDEST ?= $(ICONS)/rounded.png
RADIUS ?= 64
rounded:
	python -m core.image_ops "$(RSRC)" "$(RDEST)" --radius $(RADIUS)

ICON ?= $(ICONS)/manual.ico
FOLDER ?= .
foldericon:
	python -m core.foldericon "$(ICON)" "$(FOLDER)"

launcher:
	dotnet build $(LAUNCHER) -c Release

NAME ?= MyLauncher
ICON ?=
new-launcher:
	powershell -ExecutionPolicy Bypass -File launcher/new-launcher.ps1 -Name $(NAME) $(if $(ICON),-Icon $(ICON))

gui:
	$(GUI_PYTHON) main.py

run: launcher
	"$(LAUNCHER_EXE)"

clean:
	-$(RM) $(SPRITES) $(ICONS)
	python -c "import shutil,glob,os; [shutil.rmtree(p,ignore_errors=True) for p in ['.pytest_cache']+glob.glob('**/__pycache__',recursive=True)]; [shutil.rmtree(d,ignore_errors=True) for d in ['$(LAUNCHER)/bin','$(LAUNCHER)/obj']]"
