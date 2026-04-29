"""Tests for Docker/Compose extraction in extract_cmd."""
from __future__ import annotations

import textwrap

from llm_wiki_cli.commands.extract_cmd import (
    _parse_dockerfile,
    _parse_compose,
    _parse_inline_yaml_list,
    _looks_like_compose,
    get_docker_inventory,
)


# ── Dockerfile parsing ───────────────────────────────────────────────

class TestParseDockerfileBasic:
    def test_single_stage(self):
        text = textwrap.dedent("""\
            FROM python:3.12-slim
            WORKDIR /app
            COPY requirements.txt .
            RUN pip install -r requirements.txt
            COPY . .
            EXPOSE 8000
            CMD ["uvicorn", "main:app"]
        """)
        result = _parse_dockerfile(text)
        assert result["type"] == "dockerfile"
        assert len(result["stages"]) == 1
        assert result["stages"][0]["image"] == "python:3.12-slim"
        assert result["stages"][0]["alias"] == ""
        assert result["ports"] == ["8000"]
        assert result["workdir"] == "/app"
        assert '["uvicorn", "main:app"]' in result["cmd"]

    def test_env_vars(self):
        text = "FROM alpine\nENV APP_ENV=production\nENV DB_HOST postgres\n"
        result = _parse_dockerfile(text)
        assert len(result["env_vars"]) == 2
        assert result["env_vars"][0] == {"name": "APP_ENV", "default": "production"}
        assert result["env_vars"][1] == {"name": "DB_HOST", "default": "postgres"}

    def test_volumes(self):
        text = 'FROM alpine\nVOLUME ["/data", "/logs"]\n'
        result = _parse_dockerfile(text)
        assert result["volumes"] == ["/data", "/logs"]

    def test_build_args(self):
        text = "FROM alpine\nARG VERSION=1.0\nARG BUILD_DATE\n"
        result = _parse_dockerfile(text)
        assert len(result["build_args"]) == 2
        assert result["build_args"][0] == {"name": "VERSION", "default": "1.0"}
        assert result["build_args"][1] == {"name": "BUILD_DATE", "default": ""}

    def test_labels(self):
        text = 'FROM alpine\nLABEL maintainer="test@example.com" version="1.0"\n'
        result = _parse_dockerfile(text)
        assert result["labels"]["maintainer"] == "test@example.com"
        assert result["labels"]["version"] == "1.0"

    def test_entrypoint(self):
        text = 'FROM alpine\nENTRYPOINT ["python", "-m", "app"]\n'
        result = _parse_dockerfile(text)
        assert '["python", "-m", "app"]' in result["entrypoint"]

    def test_healthcheck(self):
        text = "FROM alpine\nHEALTHCHECK --interval=30s CMD curl -f http://localhost/ || exit 1\n"
        result = _parse_dockerfile(text)
        assert "curl" in result["healthcheck"]

    def test_comments_and_blank_lines_skipped(self):
        text = "# Comment\n\nFROM alpine\n# Another comment\nEXPOSE 80\n"
        result = _parse_dockerfile(text)
        assert len(result["stages"]) == 1
        assert result["ports"] == ["80"]


class TestParseDockerfileMultiStage:
    def test_multi_stage_build(self):
        text = textwrap.dedent("""\
            FROM python:3.12 AS builder
            WORKDIR /build
            COPY requirements.txt .
            RUN pip install -r requirements.txt

            FROM python:3.12-slim AS runtime
            WORKDIR /app
            COPY --from=builder /build /app
            COPY . .
            EXPOSE 8000
            CMD ["python", "main.py"]
        """)
        result = _parse_dockerfile(text)
        assert len(result["stages"]) == 2
        assert result["stages"][0]["image"] == "python:3.12"
        assert result["stages"][0]["alias"] == "builder"
        assert result["stages"][1]["image"] == "python:3.12-slim"
        assert result["stages"][1]["alias"] == "runtime"
        # COPY --from=builder
        from_copies = [c for c in result["copies"] if c["from_stage"]]
        assert len(from_copies) == 1
        assert from_copies[0]["from_stage"] == "builder"

    def test_continuation_lines(self):
        text = "FROM alpine\nRUN apt-get update && \\\n    apt-get install -y curl\nEXPOSE 80\n"
        result = _parse_dockerfile(text)
        assert result["ports"] == ["80"]

    def test_copy_add(self):
        text = "FROM alpine\nCOPY src/ /app/src/\nADD config.tar.gz /app/\n"
        result = _parse_dockerfile(text)
        assert len(result["copies"]) == 2
        assert result["copies"][0]["instruction"] == "COPY"
        assert result["copies"][1]["instruction"] == "ADD"


class TestParseDockerfileEmpty:
    def test_empty_file(self):
        result = _parse_dockerfile("")
        assert result["type"] == "dockerfile"
        assert result["stages"] == []
        assert result["ports"] == []


# ── docker-compose parsing ───────────────────────────────────────────

class TestParseCompose:
    def test_basic_services(self):
        text = textwrap.dedent("""\
            version: "3.8"
            services:
              web:
                build: .
                ports:
                  - "8000:8000"
                depends_on:
                  - db
              db:
                image: postgres:16
                ports:
                  - "5432:5432"
        """)
        result = _parse_compose(text)
        assert result["type"] == "compose"
        assert "web" in result["services"]
        assert "db" in result["services"]
        assert result["services"]["web"]["build"] == "."
        assert result["services"]["web"]["ports"] == ["8000:8000"]
        assert result["services"]["web"]["depends_on"] == ["db"]
        assert result["services"]["db"]["image"] == "postgres:16"

    def test_environment_and_volumes(self):
        text = textwrap.dedent("""\
            services:
              app:
                image: myapp:latest
                environment:
                  - DATABASE_URL=postgres://localhost/db
                  - REDIS_URL=redis://localhost:6379
                volumes:
                  - ./data:/app/data
                  - cache:/tmp/cache
        """)
        result = _parse_compose(text)
        svc = result["services"]["app"]
        assert svc["image"] == "myapp:latest"
        assert len(svc["environment"]) == 2
        assert len(svc["volumes"]) == 2

    def test_networks_and_volumes(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
            networks:
              frontend:
              backend:
            volumes:
              pgdata:
              redis_data:
        """)
        result = _parse_compose(text)
        assert "frontend" in result["networks"]
        assert "backend" in result["networks"]
        assert "pgdata" in result["volumes"]
        assert "redis_data" in result["volumes"]

    def test_empty_compose(self):
        result = _parse_compose("")
        assert result["type"] == "compose"
        assert result["services"] == {}

    def test_command(self):
        text = textwrap.dedent("""\
            services:
              worker:
                image: celery:latest
                command: celery -A app worker --loglevel=info
        """)
        result = _parse_compose(text)
        assert "celery" in result["services"]["worker"]["command"]


# ── get_docker_inventory ─────────────────────────────────────────────

class TestGetDockerInventory:
    def test_discovers_dockerfile(self, tmp_path):
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\nEXPOSE 8000\n")
        inv = get_docker_inventory(str(tmp_path))
        assert "Dockerfile" in inv
        assert inv["Dockerfile"]["type"] == "dockerfile"

    def test_discovers_compose(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text("services:\n  web:\n    image: nginx\n")
        inv = get_docker_inventory(str(tmp_path))
        assert "docker-compose.yml" in inv
        assert inv["docker-compose.yml"]["type"] == "compose"

    def test_discovers_compose_yaml(self, tmp_path):
        (tmp_path / "compose.yaml").write_text("services:\n  web:\n    image: nginx\n")
        inv = get_docker_inventory(str(tmp_path))
        assert "compose.yaml" in inv

    def test_discovers_named_dockerfile(self, tmp_path):
        (tmp_path / "Dockerfile.dev").write_text("FROM python:3.12\n")
        inv = get_docker_inventory(str(tmp_path))
        assert "Dockerfile.dev" in inv

    def test_empty_dir(self, tmp_path):
        inv = get_docker_inventory(str(tmp_path))
        assert inv == {}

    def test_both_dockerfile_and_compose(self, tmp_path):
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
        (tmp_path / "docker-compose.yml").write_text("services:\n  web:\n    build: .\n")
        inv = get_docker_inventory(str(tmp_path))
        assert len(inv) == 2
        assert inv["Dockerfile"]["type"] == "dockerfile"
        assert inv["docker-compose.yml"]["type"] == "compose"


# ── Compose deep nesting / env-as-dict ───────────────────────────────

class TestParseComposeDeepNesting:
    def test_environment_as_dict(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
                environment:
                  VAULT_ADDR: http://vault:8200
                  APP_ENV: production
                  DATABASE_URL: postgresql://admin:pass@db:5432/mydb
        """)
        result = _parse_compose(text)
        env = result["services"]["web"]["environment"]
        assert isinstance(env, dict)
        assert env["VAULT_ADDR"] == "http://vault:8200"
        assert env["APP_ENV"] == "production"
        assert env["DATABASE_URL"] == "postgresql://admin:pass@db:5432/mydb"

    def test_build_context_and_dockerfile(self):
        text = textwrap.dedent("""\
            services:
              app:
                build:
                  context: ..
                  dockerfile: services/app/Dockerfile
        """)
        result = _parse_compose(text)
        build = result["services"]["app"]["build"]
        assert isinstance(build, dict)
        assert build["context"] == ".."
        assert build["dockerfile"] == "services/app/Dockerfile"

    def test_depends_on_with_conditions(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
                depends_on:
                  postgres:
                    condition: service_healthy
                  redis:
                    condition: service_started
        """)
        result = _parse_compose(text)
        deps = result["services"]["web"]["depends_on"]
        assert isinstance(deps, dict)
        assert deps["postgres"]["condition"] == "service_healthy"
        assert deps["redis"]["condition"] == "service_started"

    def test_healthcheck_with_subkeys(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
                healthcheck:
                  test: ["CMD", "curl", "-f", "http://localhost/health"]
                  interval: 30s
                  timeout: 10s
                  retries: 3
                  start_period: 40s
        """)
        result = _parse_compose(text)
        hc = result["services"]["web"]["healthcheck"]
        assert isinstance(hc, dict)
        assert hc["test"] == ["CMD", "curl", "-f", "http://localhost/health"]
        assert hc["interval"] == "30s"
        assert hc["timeout"] == "10s"
        assert hc["retries"] == "3"

    def test_deploy_resources(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
                deploy:
                  resources:
                    limits:
                      memory: 512M
                      cpus: '1.0'
                    reservations:
                      memory: 256M
                      cpus: '0.5'
        """)
        result = _parse_compose(text)
        deploy = result["services"]["web"]["deploy"]
        assert deploy["resources"]["limits"]["memory"] == "512M"
        assert deploy["resources"]["limits"]["cpus"] == "1.0"
        assert deploy["resources"]["reservations"]["memory"] == "256M"

    def test_deploy_placement_constraints(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
                deploy:
                  mode: replicated
                  replicas: 3
                  placement:
                    constraints:
                      - node.labels.role == core
        """)
        result = _parse_compose(text)
        deploy = result["services"]["web"]["deploy"]
        assert deploy["mode"] == "replicated"
        assert deploy["replicas"] == "3"
        assert deploy["placement"]["constraints"] == ["node.labels.role == core"]

    def test_container_name_and_restart(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
                container_name: my_web
                restart: unless-stopped
                read_only: true
        """)
        result = _parse_compose(text)
        svc = result["services"]["web"]
        assert svc["container_name"] == "my_web"
        assert svc["restart"] == "unless-stopped"
        assert svc["read_only"] == "true"

    def test_security_opts_and_tmpfs(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
                tmpfs:
                  - /tmp:rw,noexec,nosuid,size=50m
                security_opt:
                  - no-new-privileges:true
                cap_add:
                  - IPC_LOCK
        """)
        result = _parse_compose(text)
        svc = result["services"]["web"]
        assert svc["tmpfs"] == ["/tmp:rw,noexec,nosuid,size=50m"]
        assert svc["security_opt"] == ["no-new-privileges:true"]
        assert svc["cap_add"] == ["IPC_LOCK"]


# ── Inline YAML lists ────────────────────────────────────────────────

class TestParseInlineYamlList:
    def test_basic_list(self):
        assert _parse_inline_yaml_list('["a", "b", "c"]') == ["a", "b", "c"]

    def test_cmd_list(self):
        result = _parse_inline_yaml_list('["CMD", "curl", "-f", "http://localhost/"]')
        assert result == ["CMD", "curl", "-f", "http://localhost/"]

    def test_single_item(self):
        assert _parse_inline_yaml_list("[infra]") == ["infra"]

    def test_not_a_list(self):
        assert _parse_inline_yaml_list("just a string") is None

    def test_empty_list(self):
        assert _parse_inline_yaml_list("[]") == []

    def test_profiles_inline(self):
        text = textwrap.dedent("""\
            services:
              db:
                profiles: [infra]
              web:
                profiles: [core, ml]
        """)
        result = _parse_compose(text)
        assert result["services"]["db"]["profiles"] == ["infra"]
        assert result["services"]["web"]["profiles"] == ["core", "ml"]

    def test_healthcheck_inline_list(self):
        text = textwrap.dedent("""\
            services:
              web:
                healthcheck:
                  test: ["CMD", "wget", "--spider", "http://localhost/"]
        """)
        result = _parse_compose(text)
        assert result["services"]["web"]["healthcheck"]["test"] == [
            "CMD", "wget", "--spider", "http://localhost/"
        ]


# ── _looks_like_compose ──────────────────────────────────────────────

class TestLooksLikeCompose:
    def test_real_compose(self):
        text = "services:\n  web:\n    image: nginx\n"
        assert _looks_like_compose(text) is True

    def test_vault_config_not_compose(self):
        text = "global:\n  JWT_ALGO: HS256\nservices:\n  admin-service:\n    JWT_KEY: secret\n"
        assert _looks_like_compose(text) is False

    def test_compose_with_build(self):
        text = "services:\n  web:\n    build: .\n"
        assert _looks_like_compose(text) is True

    def test_no_services_key(self):
        text = "networks:\n  frontend:\nvolumes:\n  pgdata:\n"
        assert _looks_like_compose(text) is False

    def test_empty_file(self):
        assert _looks_like_compose("") is False


# ── Recursive discovery ──────────────────────────────────────────────

class TestRecursiveDiscovery:
    def test_finds_dockerfile_in_subdirectory(self, tmp_path):
        sub = tmp_path / "services" / "web"
        sub.mkdir(parents=True)
        (sub / "Dockerfile").write_text("FROM python:3.12\n")
        inv = get_docker_inventory(str(tmp_path))
        assert "services/web/Dockerfile" in inv

    def test_finds_compose_in_subdirectory(self, tmp_path):
        sub = tmp_path / "compose"
        sub.mkdir()
        (sub / "docker-compose.yml").write_text("services:\n  web:\n    image: nginx\n")
        inv = get_docker_inventory(str(tmp_path))
        assert "compose/docker-compose.yml" in inv

    def test_content_based_compose_detection(self, tmp_path):
        sub = tmp_path / "compose"
        sub.mkdir()
        (sub / "core.yml").write_text("services:\n  web:\n    image: nginx\n    ports:\n      - 8000:8000\n")
        inv = get_docker_inventory(str(tmp_path))
        assert "compose/core.yml" in inv
        assert inv["compose/core.yml"]["type"] == "compose"

    def test_skips_non_compose_yaml(self, tmp_path):
        (tmp_path / "config.yml").write_text("database:\n  host: localhost\n  port: 5432\n")
        inv = get_docker_inventory(str(tmp_path))
        assert "config.yml" not in inv

    def test_skips_excluded_dirs(self, tmp_path):
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "Dockerfile").write_text("FROM python:3.12\n")
        inv = get_docker_inventory(str(tmp_path))
        assert inv == {}

    def test_skips_virtualenv_layout_with_custom_name(self, tmp_path):
        site_packages = (
            tmp_path / "custom-python" / "lib" / "python3.13" / "site-packages"
        )
        site_packages.mkdir(parents=True)
        (site_packages / "Dockerfile").write_text("FROM python:3.12\n")
        inv = get_docker_inventory(str(tmp_path))
        assert inv == {}

    def test_mixed_deep_tree(self, tmp_path):
        # Dockerfile at root
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
        # Dockerfiles in service dirs
        svc = tmp_path / "services" / "api"
        svc.mkdir(parents=True)
        (svc / "Dockerfile").write_text("FROM node:20\n")
        # Non-standard compose
        compose = tmp_path / "compose"
        compose.mkdir()
        (compose / "infra.yml").write_text("services:\n  db:\n    image: postgres\n    ports:\n      - 5432:5432\n")
        # Standard compose at root
        (tmp_path / "docker-compose.yml").write_text("services:\n  web:\n    build: .\n")
        inv = get_docker_inventory(str(tmp_path))
        assert len(inv) == 4
        assert inv["Dockerfile"]["type"] == "dockerfile"
        assert inv["services/api/Dockerfile"]["type"] == "dockerfile"
        assert inv["compose/infra.yml"]["type"] == "compose"
        assert inv["docker-compose.yml"]["type"] == "compose"
