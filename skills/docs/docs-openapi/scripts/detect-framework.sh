#!/usr/bin/env bash
# Detecta el framework backend del proyecto actual.
# Salida: una línea con el framework detectado.
# Códigos: spring-boot | nestjs | express | fastapi | gin | unknown

set -euo pipefail

ROOT="${1:-.}"

detect() {
  # Spring Boot
  if [ -f "$ROOT/pom.xml" ] || [ -f "$ROOT/build.gradle" ] || [ -f "$ROOT/build.gradle.kts" ]; then
    if grep -qr "spring-boot" "$ROOT/pom.xml" "$ROOT/build.gradle" "$ROOT/build.gradle.kts" 2>/dev/null; then
      echo "spring-boot"
      return
    fi
  fi

  # Go / Gin
  if [ -f "$ROOT/go.mod" ]; then
    if grep -q "gin-gonic/gin\|labstack/echo" "$ROOT/go.mod" 2>/dev/null; then
      echo "gin"
      return
    fi
  fi

  # Node — NestJS antes que Express (NestJS usa Express por debajo)
  if [ -f "$ROOT/package.json" ]; then
    if grep -q '"@nestjs/core"' "$ROOT/package.json" 2>/dev/null; then
      echo "nestjs"
      return
    fi
    if grep -q '"express"' "$ROOT/package.json" 2>/dev/null; then
      echo "express"
      return
    fi
    if grep -q '"fastify"' "$ROOT/package.json" 2>/dev/null; then
      echo "fastify"
      return
    fi
  fi

  # Python — FastAPI / Flask / Django
  for dep_file in "$ROOT/requirements.txt" "$ROOT/pyproject.toml" "$ROOT/Pipfile"; do
    if [ -f "$dep_file" ]; then
      if grep -qi "fastapi" "$dep_file" 2>/dev/null; then
        echo "fastapi"
        return
      fi
      if grep -qi "flask" "$dep_file" 2>/dev/null; then
        echo "flask"
        return
      fi
      if grep -qi "django" "$dep_file" 2>/dev/null; then
        echo "django"
        return
      fi
    fi
  done

  echo "unknown"
}

FRAMEWORK=$(detect)
echo "$FRAMEWORK"

# Feedback visual adicional a stderr
case "$FRAMEWORK" in
  spring-boot)   echo "[docs-openapi] Framework detectado: Spring Boot (springdoc-openapi)" >&2 ;;
  nestjs)        echo "[docs-openapi] Framework detectado: NestJS (@nestjs/swagger)" >&2 ;;
  express)       echo "[docs-openapi] Framework detectado: Express (swagger-jsdoc)" >&2 ;;
  fastapi)       echo "[docs-openapi] Framework detectado: FastAPI (built-in docs)" >&2 ;;
  gin)           echo "[docs-openapi] Framework detectado: Gin (swaggo/swag)" >&2 ;;
  fastify)       echo "[docs-openapi] Framework detectado: Fastify (@fastify/swagger)" >&2 ;;
  flask)         echo "[docs-openapi] Framework detectado: Flask (flask-openapi3 / flasgger)" >&2 ;;
  django)        echo "[docs-openapi] Framework detectado: Django (drf-spectacular / drf-yasg)" >&2 ;;
  *)             echo "[docs-openapi] Framework no detectado. Especifica el stack manualmente." >&2 ;;
esac
