# IconMaker — các quy trình (pipeline). Chạy `make help` để xem danh sách.
#
# Layout: src/ (main.py + core/ + service/ + gui/ + tools/) — mọi lệnh python chạy từ
# thư mục gốc với PYTHONPATH=src (export bên dưới).
# input/ là đầu vào mặc định của tool; output/<tenTool>/ là đầu ra.
#
# Trên Windows CMD/PowerShell, make sẽ dùng shell là cmd.

ifeq ($(OS),Windows_NT)
    GUI_PYTHON = pythonw
    RM = rmdir /s /q
else
    GUI_PYTHON = python3
    RM = rm -rf
endif

export PYTHONPATH := src

INPUT_DIR  ?= input
SPRITES    ?= output/sprites
ICONS      ?= output/icons
LAUNCHER   = launcher/IconMakerLauncher

.PHONY: help all install test sprites icons ico rounded resize convfmt foldericon junction launcher new-launcher gui clean

help:
	@python -c "print('''IconMaker Makefile:\n  make all        install + test + sprites + icons\n  make install    cai Python deps (requirements.txt)\n  make test       chay toan bo pytest\n  make sprites    tach sprite: $(INPUT_DIR)/ -> $(SPRITES)/\n  make icons      build ICO chat luong cao: $(SPRITES)/ -> $(ICONS)/ (1 tang, phang)\n  make ico        convert truc tiep (SRC=...png DEST=...ico; bo trong = lay input/ -> output/convert/)\n  make rounded    bo goc anh (RSRC=... RDEST=... RADIUS=...; bo trong = lay input/ -> output/rounded/)\n  make resize     resize vuong 16/48/128 (RSRC=... EXT=.png; bo trong = lay input/ -> output/resize/)\n  make convfmt    doi dinh dang png/jpg/webp (FSRC=... FMT=.webp QUALITY=100; bo trong = lay input/ -> output/convert_format/)\n  make foldericon dat icon cho thu muc (ICON=...ico FOLDER=... NAME=... STORE=...; bo ICON = lay ICO moi nhat output/icons/; bo NAME = giu ten goc)\n  make junction tao junction point (JLINK=<duong dan ao> JTARGET=<thu muc that>, JNO=1 de bo attrib +r /l)\n  make launcher   build launcher C# (can .NET 8+ SDK)\n  make new-launcher NAME=<TenApp> [ICON=...ico] sinh launcher moi theo khung tray-clone\n  make gui        mo GUI truc tiep bang pythonw (khong hien console)\n  make clean      xoa output/ __pycache__ .pytest_cache (giu input/)''')"

all: install test sprites icons

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest

sprites:
	python -m service.sprites $(INPUT_DIR) $(SPRITES)

icons:
	python -m service.icons $(SPRITES) $(ICONS)

SRC ?=
DEST ?= $(ICONS)/manual.ico
ico:
	python -m service.convert "$(SRC)" "$(DEST)"

RSRC ?=
RDEST ?=
RADIUS ?= 64
rounded:
	python -m service.image_ops "$(RSRC)" "$(RDEST)" --radius $(RADIUS)

RSRC ?=
EXT ?= .png
RESTYPE ?= resize
resize:
	python -m service.resize "$(RSRC)" --ext "$(EXT)"

FSRC ?=
FMT ?= .webp
QUALITY ?= 100
convfmt:
	python -m service.format_convert "$(FSRC)" --fmt "$(FMT)" --quality $(QUALITY)

ICON ?=
FOLDER ?= .
NAME ?=
STORE ?=
foldericon:
	python -m service.foldericon "$(ICON)" "$(FOLDER)" $(if $(strip $(STORE)),--store "$(STORE)") $(if $(strip $(NAME)),--name "$(NAME)")

JLINK ?=
JTARGET ?=
JNO ?=
junction:
	python -m service.junction "$(JLINK)" "$(JTARGET)" $(if $(strip $(JNO)),--no-readonly)

launcher:
	dotnet build $(LAUNCHER) -c Release

NAME ?= MyLauncher
ICON ?=
new-launcher:
	powershell -ExecutionPolicy Bypass -File launcher/new-launcher.ps1 -Name $(NAME) $(if $(ICON),-Icon $(ICON))

gui:
	$(GUI_PYTHON) src/main.py

clean:
	-$(RM) output
	python -c "import shutil,glob,os; [shutil.rmtree(p,ignore_errors=True) for p in ['.pytest_cache']+glob.glob('**/__pycache__',recursive=True)]; [shutil.rmtree(d,ignore_errors=True) for d in ['$(LAUNCHER)/bin','$(LAUNCHER)/obj']]"
