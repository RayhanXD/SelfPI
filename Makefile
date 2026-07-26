# SelfPI — run the stack
#
#   make            # ensure local Mongo + seed + API + frontend
#   make mongo      # start local mongod (portable binary; Docker if available)
#   make seed       # seed Stripe api + spec
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

.PHONY: all run setup ensure-mongo check-mongo mongo mongo-download seed backend frontend test stop help

all: run

help:
	@echo "SelfPI make targets:"
	@echo "  make / make run   Ensure Mongo, seed, start API + UI"
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
	@echo "   Demo: open UI → Bump spec on Stripe"
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
	cd $(BACKEND) && $(PYTHON) -m db.check_mongo

mongo-download: $(MONGOD)

$(MONGOD):
	@echo "→ Downloading portable MongoDB $(MONGODB_VER) for macOS arm64…"
	@mkdir -p $(TOOLS)
	@curl -fsSL -o $(TOOLS)/mongodb.tgz \
		"https://fastdl.mongodb.org/osx/mongodb-macos-arm64-$(MONGODB_VER).tgz"
	@tar -xzf $(TOOLS)/mongodb.tgz -C $(TOOLS)
	@test -x $(MONGOD)
	@echo "→ mongod ready at $(MONGOD)"

mongo: mongo-download
	@mkdir -p $(MONGO_DATA)
	@if lsof -ti tcp:27017 >/dev/null 2>&1; then \
		echo "→ Mongo already listening on :27017"; \
	else \
		echo "→ Starting local mongod on :27017…"; \
		$(MONGOD) --dbpath $(MONGO_DATA) --port 27017 --bind_ip 127.0.0.1 \
			--fork --logpath $(MONGO_LOG); \
		sleep 1; \
		echo "→ Local mongod started (log: $(MONGO_LOG))"; \
	fi
	@# Point .env at local if it still references Atlas and local is what we started
	@if grep -qE '^[[:space:]]*MONGODB_URI=mongodb\+srv://' $(BACKEND)/.env 2>/dev/null; then \
		echo "→ Note: backend/.env still has an Atlas URI."; \
		echo "  For local mongod set: MONGODB_URI=mongodb://localhost:27017"; \
	fi

seed: ensure-mongo
	cd $(BACKEND) && $(PYTHON) -m db.seed

# --- processes -------------------------------------------------------------

backend: $(PYTHON) $(BACKEND)/.env
	cd $(BACKEND) && $(UVICORN) api.main:app --reload --host 0.0.0.0 --port $(API_PORT)

frontend: $(FRONTEND)/node_modules
	cd $(FRONTEND) && npm run dev -- --host --port $(WEB_PORT)

test: $(PYTHON)
	cd $(BACKEND) && $(VENV)/bin/pytest -q

stop:
	@-lsof -ti tcp:$(API_PORT) | xargs kill -9 2>/dev/null || true
	@-lsof -ti tcp:$(WEB_PORT) | xargs kill -9 2>/dev/null || true
	@-lsof -ti tcp:27017 | xargs kill -9 2>/dev/null || true
	@-docker compose -f $(ROOT)/docker-compose.yml down 2>/dev/null || true
	@echo "→ Stopped API (:$(API_PORT)), UI (:$(WEB_PORT)), mongod (:27017)"
