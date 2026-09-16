# IconMaker — các quy trình (pipeline). Chạy `make help` để xem danh sách.
#
# Layout: src/ (main.py + core/ + service/ + gui/ + tools/) — mọi lệnh python chạy từ
# thư mục gốc với PYTHONPATH=src (export bên dưới).
# input/ là đầu vào mặc định của tool; output/<tenTool>/ là đầu ra.
#
# Trên Windows CMD/PowerShell, make sẽ dùng shell là cmd.

ifeq ($(OS),Windows_NT)
    GUI_PYTHON = .venv/Scripts/pythonw.exe
    RM = rmdir /s /q
else
    GUI_PYTHON = .venv/bin/python
    RM = rm -rf
endif
UVRUN = uv run

export PYTHONPATH := src

INPUT_DIR  ?= input
SPRITES    ?= output/sprites
ICONS      ?= output/icons
LAUNCHER   = launcher/IconMakerLauncher

.PHONY: help all install test sprites icons export rounded resize foldericon junction launcher new-launcher build-launcher gui clean

help:
	@$(UVRUN) python -c "print('''IconMaker Makefile:\n  make all        install + test + sprites + icons\n  make install    tao .venv bang uv + cai Python deps (requirements.txt)\n  make test       chay toan bo pytest (uv run)\n  make sprites    tach sprite: $(INPUT_DIR)/ -> $(SPRITES)/\n  make icons      build ICO chat luong cao: $(SPRITES)/ -> $(ICONS)/ (1 tang, phang)\n  make export     xuat anh 1 vao -> jpg/png/webp/ico (SRC=... FMT=.ico QUALITY=100; bo trong = lay input/ -> output/export/)\n  make rounded    bo goc anh (RSRC=... RDEST=... RADIUS=...; bo trong = lay input/ -> output/rounded/)\n  make resize     resize vuong 16/48/128 (RSRC=... EXT=.png; bo trong = lay input/ -> output/resize/)\n  make foldericon dat icon cho thu muc (ICON=...ico FOLDER=... NAME=... STORE=...; bo ICON = lay ICO moi nhat output/icons/; bo NAME = giu ten goc)\n  make junction tao junction point (JLINK=<duong dan ao> JTARGET=<thu muc that>, JNO=1 de bo attrib +r /l)\n  make build-launcher build exe tray cho thu muc server (SERVER=... ICON=...ico NAME=... [MODE=framework|standalone])\n  make launcher   build launcher C# (can .NET 8+ SDK)\n  make new-launcher NAME=<TenApp> [ICON=...ico] sinh launcher moi theo khung tray-clone\n  make gui        mo GUI truc tiep bang pythonw trong .venv (khong hien console)\n  make clean      xoa output/ __pycache__ .pytest_cache (giu input/ .venv)''')"

all: install test sprites icons

install:
	uv venv --python 3.13
	uv pip install -r requirements.txt

test:
	$(UVRUN) python -m pytest

sprites:
	$(UVRUN) python -m service.sprites $(INPUT_DIR) $(SPRITES)

icons:
	$(UVRUN) python -m service.icons $(SPRITES) $(ICONS)

SRC ?=
FMT ?= .ico
QUALITY ?= 100
export:
	$(UVRUN) python -m service.export "$(SRC)" --fmt "$(FMT)" --quality $(QUALITY)

RSRC ?=
RDEST ?=
RADIUS ?= 64
rounded:
	$(UVRUN) python -m service.image_ops "$(RSRC)" "$(RDEST)" --radius $(RADIUS)

RSRC ?=
EXT ?= .png
RESTYPE ?= resize
resize:
	$(UVRUN) python -m service.resize "$(RSRC)" --ext "$(EXT)"

ICON ?=
FOLDER ?= .
NAME ?=
STORE ?=
foldericon:
	$(UVRUN) python -m service.foldericon "$(ICON)" "$(FOLDER)" $(if $(strip $(STORE)),--store "$(STORE)") $(if $(strip $(NAME)),--name "$(NAME)")

JLINK ?=
JTARGET ?=
JNO ?=
junction:
	$(UVRUN) python -m service.junction "$(JLINK)" "$(JTARGET)" $(if $(strip $(JNO)),--no-readonly)

launcher:
	dotnet build $(LAUNCHER) -c Release

NAME ?= MyLauncher
ICON ?=
new-launcher:
	powershell -ExecutionPolicy Bypass -File launcher/new-launcher.ps1 -Name $(NAME) $(if $(ICON),-Icon $(ICON))

SERVER ?=
ICON ?=
LNAME ?=
MODE ?= framework
build-launcher:
	$(UVRUN) python -m service.launcher "$(SERVER)" $(if $(strip $(ICON)),--icon "$(ICON)") $(if $(strip $(LNAME)),--name "$(LNAME)") --mode $(MODE)

gui:
	$(GUI_PYTHON) src/main.py

clean:
	-$(RM) output
	$(UVRUN) python -c "import shutil,glob,os; [shutil.rmtree(p,ignore_errors=True) for p in ['.pytest_cache']+glob.glob('**/__pycache__',recursive=True)]; [shutil.rmtree(d,ignore_errors=True) for d in ['$(LAUNCHER)/bin','$(LAUNCHER)/obj']]"
