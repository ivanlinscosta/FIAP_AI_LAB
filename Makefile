.PHONY: init up down logs provision test power-automate

init:
	cp -n .env.example .env || true
	python scripts/generate_secrets.py

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

provision:
	python scripts/provision_groups.py

test:
	python scripts/smoke_test.py

power-automate:
	@echo "Run: python scripts/render_power_automate_swagger.py https://YOUR-GATEWAY"
