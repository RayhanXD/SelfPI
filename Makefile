# SelfPI — run the stack
#
#   make            # ensure local Mongo + seed + API + frontend
#   make reset      # wipe changes/specs and re-seed demo + live APIs
#   make mongo      # start local mongod (portable binary)
#   make seed       # seed Stripe demo + live apis
#   make stop       # stop API/UI/local mongod

ROOT        := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
BACKEND     := $(ROOT)/backend
FRONTEND    := $(ROOT)/frontend
VENV        := $(BACKEND)/.venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
UVICORN     := $(VENV)/bin/uvicorn
TOOLS       := $(ROOT)/.tools
MONGODB_VER := 7.0.14
MONGODB_DIR := $(TOOLS)/mongodb-macos-aarch64-$(MONGODB_VER)
MONGOD      := $(MONGODB_DIR)/bin/mongod
MONGO_DATA  := $(TOOLS)/mongo-data
MONGO_LOG   := $(TOOLS)/mongod.log
API_PORT    ?= 8000
WEB_PORT    ?= 5173

.PHONY: all run setup ensure-mongo check-mongo mongo mongo-download seed reset backend frontend test stop help

all: run

help:
	@echo "SelfPI make targets:"
	@echo "  make / make run   Ensure Mongo, seed, start API + UI"
	@echo "  make reset        Wipe changes/specs and re-seed cleanly"
	@echo "  make mongo        Start local mongod on :27017"
	@echo "  make check-mongo  Ping MONGODB_URI"
	@echo "  make seed         Seed MongoDB"
	@echo "  make backend      API on :$(API_PORT)"
	@echo "  make frontend     UI on :$(WEB_PORT)"
	@echo "  make test         Backend pytest"
	@echo "  make stop         Stop API, UI, and local mongod"

# --- one command -----------------------------------------------------------

run: setup ensure-mongo
	@echo "→ Seeding MongoDB…"
	@cd $(BACKEND) && $(PYTHON) -m db.seed
	@echo "→ Starting API (:$(API_PORT)) + frontend (:$(WEB_PORT))"
	@echo "   UI:  http://localhost:$(WEB_PORT)"
	@echo "   API: http://localhost:$(API_PORT)/health"
	@echo "   Demo: open UI → Bump spec on Stripe (demo)"
	@echo "   Ctrl+C stops API + UI (Mongo keeps running; make stop to kill it)."
	@$(MAKE) -j2 backend frontend

# --- setup -----------------------------------------------------------------

setup: $(PYTHON) $(FRONTEND)/node_modules $(BACKEND)/.env
	@echo "→ Setup OK"

$(PYTHON):
	@echo "→ Creating backend venv…"
	python3 -m venv $(VENV)
	$(PIP) install -q -U pip
	$(PIP) install -q -e "$(BACKEND)[dev]"

$(FRONTEND)/node_modules: $(FRONTEND)/package.json
	@echo "→ Installing frontend deps…"
	cd $(FRONTEND) && npm install

$(BACKEND)/.env:
	@cp $(BACKEND)/.env.example $(BACKEND)/.env
	@echo "→ Created backend/.env (default: local Mongo on :27017)"

# --- mongo -----------------------------------------------------------------

ensure-mongo: $(PYTHON) $(BACKEND)/.env
	@if cd $(BACKEND) && $(PYTHON) -m db.check_mongo >/dev/null 2>&1; then \
		echo "→ MongoDB OK"; \
	else \
		echo "→ MongoDB not reachable — starting local mongod…"; \
		$(MAKE) mongo; \
		cd $(BACKEND) && $(PYTHON) -m db.check_mongo; \
	fi

check-mongo: $(PYTHON) $(BACKEND)/.env
	@cd $(BACKEND) && $(PYTHON) -m db.check_mongo

mongo: $(MONGOD)
	@mkdir -p $(MONGO_DATA)
	@if lsof -iTCP:27017 -sTCP:LISTEN >/dev/null 2>&1; then \
		echo "→ mongod already listening on :27017"; \
	else \
		echo "→ Starting local mongod…"; \
		$(MONGOD) --dbpath $(MONGO_DATA) --logpath $(MONGO_LOG) --fork --bind_ip 127.0.0.1; \
	fi

$(MONGOD):
	@$(MAKE) mongo-download

mongo-download:
	@mkdir -p $(TOOLS)
	@echo "→ Downloading MongoDB $(MONGODB_VER)…"
	@cd $(TOOLS) && curl -fsSL -o mongodb.tgz \
		"https://fastdl.mongodb.org/osx/mongodb-macos-arm64-$(MONGODB_VER).tgz" \
		&& tar -xzf mongodb.tgz && rm mongodb.tgz
	@echo "→ MongoDB binary ready at $(MONGOD)"

# --- data ------------------------------------------------------------------

seed: ensure-mongo
	@echo "→ Ensuring indexes (prod-style — no demo APIs)…"
	@cd $(BACKEND) && $(PYTHON) -m db.seed

seed-demo: ensure-mongo
	@echo "→ Bootstrapping demo-consumer + Stripe demo fixtures…"
	@python3 $(ROOT)/scripts/bootstrap_demo_consumer.py
	@cd $(BACKEND) && $(PYTHON) -m db.seed --demo --force

reset: ensure-mongo
	@echo "→ Resetting MongoDB to clean prod workspace…"
	@cd $(BACKEND) && $(PYTHON) -m db.reset

reset-demo: ensure-mongo
	@echo "→ Resetting with Stripe demo fixtures…"
	@python3 $(ROOT)/scripts/bootstrap_demo_consumer.py
	@cd $(BACKEND) && $(PYTHON) -m db.reset --demo

# --- apps ------------------------------------------------------------------

backend: $(PYTHON) $(BACKEND)/.env
	cd $(BACKEND) && $(UVICORN) api.main:app --reload --host 0.0.0.0 --port $(API_PORT)

frontend: $(FRONTEND)/node_modules
	cd $(FRONTEND) && npm run dev -- --host --port $(WEB_PORT)

test: $(PYTHON)
	cd $(BACKEND) && $(PYTHON) -m pytest -q

stop:
	@-pkill -f "uvicorn api.main:app" 2>/dev/null || true
	@-pkill -f "vite --host --port $(WEB_PORT)" 2>/dev/null || true
	@-pkill -f "$(MONGOD)" 2>/dev/null || true
	@echo "→ Stopped API/UI/local mongod (if they were running)"
