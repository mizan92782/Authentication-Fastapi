#!/bin/bash

set -e

COMPOSE="docker compose -f docker-compose.dev.yml"
SERVICE="api"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           🌱  SEEDING DATABASE           ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Pass --flush to wipe everything before seeding
FLUSH_FLAG=""
if [[ "$1" == "--flush" ]]; then
  FLUSH_FLAG="--flush"
  echo "⚠️  Flush mode ON — all existing data will be wiped"
  echo ""
fi

echo "▶  Step 1/2 — Seeding catalog (categories + products)..."
$COMPOSE exec $SERVICE python -m app.scripts.seed_catalog $FLUSH_FLAG

echo ""
echo "▶  Step 2/2 — Seeding users + orders..."
$COMPOSE exec $SERVICE python -m app.scripts.seed_orders $FLUSH_FLAG

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         ✅  ALL SEEDS COMPLETE           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
