.PHONY: help build-lambda bootstrap-dev bootstrap-prod \
        deploy-dev deploy-prod destroy-dev fmt validate \
        test test-unit test-integration

ENVIRONMENT  ?= dev
INFRA_DIR    := infra/environments/$(ENVIRONMENT)
ARTIFACTS_DIR := artifacts

help: 
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

# ── Build ─────────────────────────────────────────────────────────────────────

build-lambda: 
	./scripts/build_lambda.sh

# ── Bootstrap ─────────────────────────────────────────────────────────────────

bootstrap-dev: 
	./scripts/bootstrap_backend.sh dev

bootstrap-prod: 
	./scripts/bootstrap_backend.sh prod

# ── Terraform ─────────────────────────────────────────────────────────────────

fmt: 
	terraform -chdir=infra fmt -recursive

validate: 
	terraform -chdir=$(INFRA_DIR) init -backend=false -input=false -reconfigure
	terraform -chdir=$(INFRA_DIR) validate

deploy-dev: build-lambda 
	terraform -chdir=infra/environments/dev init -input=false
	terraform -chdir=infra/environments/dev apply -var-file=terraform.tfvars -auto-approve

deploy-prod: build-lambda 
	terraform -chdir=infra/environments/prod init -input=false
	terraform -chdir=infra/environments/prod apply -var-file=terraform.tfvars

destroy-dev: 
	terraform -chdir=infra/environments/dev destroy -var-file=terraform.tfvars

# ── Tests ─────────────────────────────────────────────────────────────────────

test-unit: 
	pytest -m "not integration" --tb=short -q

test-integration: 
	pytest -m integration --tb=short -q

test: test-unit 
