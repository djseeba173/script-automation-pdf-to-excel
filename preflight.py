"""
Preflight check — verifica el entorno antes de correr el batch.
No llama a Azure Document Intelligence ni consume páginas.
Sí verifica conectividad con Graph API/OneDrive si está habilitado.

Uso:
    python preflight.py --config config/settings.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

OK    = "[OK]"
WARN  = "[WARN]"
FAIL  = "[FAIL]"

errors = 0
warnings = 0


def ok(msg: str) -> None:
    print(f"  {OK}    {msg}")


def warn(msg: str) -> None:
    global warnings
    warnings += 1
    print(f"  {WARN}  {msg}")


def fail(msg: str) -> None:
    global errors
    errors += 1
    print(f"  {FAIL}  {msg}")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_python_version() -> None:
    print("\n[1] Python")
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 11):
        ok(f"Python {major}.{minor}")
    else:
        fail(f"Python {major}.{minor} — se requiere 3.11+")


def check_dependencies() -> None:
    print("\n[2] Dependencias")

    deps = {
        "openpyxl": "openpyxl",
        "azure.ai.formrecognizer": "azure-ai-formrecognizer",
        "azure.core": "azure-core",
        "dotenv": "python-dotenv",
    }
    for module, package in deps.items():
        try:
            __import__(module)
            ok(package)
        except ImportError:
            fail(f"{package} no instalado — ejecutar: pip install {package}")


def check_env(env_path: Path) -> dict:
    print("\n[3] Variables de entorno (.env)")

    if not env_path.exists():
        warn(f".env no encontrado en {env_path} — las variables deben estar en el entorno del sistema")
    else:
        ok(f".env encontrado: {env_path}")
        from dotenv import load_dotenv
        load_dotenv(env_path)

    required = [
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
        "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    ]
    found = {}
    for var in required:
        value = os.getenv(var, "")
        if value:
            ok(f"{var} presente")
            found[var] = value
        else:
            fail(f"{var} no definida o vacía")

    optional = "AZURE_DOCUMENT_MODEL_ID"
    model = os.getenv(optional, "prebuilt-invoice")
    ok(f"{optional} = {model}")

    return found


def check_config(config_path: Path) -> dict | None:
    print("\n[4] Configuración (settings.json)")

    if not config_path.exists():
        fail(f"No existe: {config_path}")
        return None

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        ok(f"JSON válido: {config_path}")
    except json.JSONDecodeError as e:
        fail(f"JSON inválido: {e}")
        return None

    # paths requeridos
    paths_raw = raw.get("paths", {})
    required_paths = ["input_dir", "working_dir", "processed_dir", "error_dir", "output_dir", "log_dir"]
    root = config_path.resolve().parent.parent
    for key in required_paths:
        if key not in paths_raw:
            fail(f"paths.{key} no definido en settings.json")
        else:
            p = Path(paths_raw[key])
            resolved = p if p.is_absolute() else root / p
            ok(f"paths.{key} = {resolved}")

    # azure.pages
    azure_raw = raw.get("azure", {})
    pages = azure_raw.get("pages")
    if pages:
        ok(f"azure.pages = \"{pages}\" (lectura limitada a páginas {pages})")
    else:
        warn("azure.pages no definido — se leerán TODAS las páginas de cada PDF")

    return raw


def check_inbox(config_path: Path, raw: dict) -> None:
    print("\n[5] Archivos en inbox")

    if raw.get("onedrive", {}).get("enabled", False):
        ok("OneDrive habilitado — los PDFs se leen desde Pendientes (inbox local no aplica)")
        return

    paths_raw = raw.get("paths", {})
    root = config_path.resolve().parent.parent
    input_raw = paths_raw.get("input_dir", "data/inbox")
    input_dir = Path(input_raw) if Path(input_raw).is_absolute() else root / input_raw

    if not input_dir.exists():
        fail(f"Directorio inbox no existe: {input_dir}")
        return

    extensions = {e.lower() for e in raw.get("processing", {}).get("supported_extensions", [".pdf"])}
    files = [f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in extensions]

    if not files:
        warn(f"No hay archivos PDF en inbox: {input_dir}")
    else:
        ok(f"{len(files)} archivo(s) encontrado(s) en {input_dir}")
        for f in sorted(files):
            ok(f"  → {f.name}")


def check_write_permissions(config_path: Path, raw: dict) -> None:
    print("\n[6] Permisos de escritura")

    paths_raw = raw.get("paths", {})
    root = config_path.resolve().parent.parent

    for key in ["output_dir", "log_dir", "working_dir"]:
        raw_path = paths_raw.get(key, f"data/{key.replace('_dir','')}")
        resolved = Path(raw_path) if Path(raw_path).is_absolute() else root / raw_path
        try:
            resolved.mkdir(parents=True, exist_ok=True)
            test_file = resolved / ".preflight_test"
            test_file.write_text("ok")
            test_file.unlink()
            ok(f"{key} escribible: {resolved}")
        except Exception as e:
            fail(f"{key} no escribible: {e}")


def check_onedrive(raw: dict) -> None:
    print("\n[7] OneDrive")

    od = raw.get("onedrive", {})
    if not od.get("enabled", False):
        ok("OneDrive deshabilitado — se omite validación")
        return

    user_email = od.get("user_email", "")
    folder_path = od.get("folder_path", "")

    if not user_email or not folder_path:
        fail("onedrive.user_email y onedrive.folder_path son requeridos cuando enabled=true")
        return

    try:
        import requests as req
    except ImportError:
        fail("requests no instalado — ejecutar: pip install requests")
        return

    tenant_id = os.getenv("GRAPH_TENANT_ID", "")
    client_id = os.getenv("GRAPH_CLIENT_ID", "")
    client_secret = os.getenv("GRAPH_CLIENT_SECRET", "")

    if not all([tenant_id, client_id, client_secret]):
        fail("Faltan variables GRAPH_TENANT_ID / GRAPH_CLIENT_ID / GRAPH_CLIENT_SECRET")
        return

    # Obtener token
    try:
        token_resp = req.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        token = token_resp.json()["access_token"]
        ok("Autenticación Graph API exitosa")
    except Exception as e:
        fail(f"No se pudo obtener token de Graph API: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    base_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/"

    # Verificar carpeta raíz del proyecto
    try:
        folder_resp = req.get(f"{base_url}{folder_path}", headers=headers, timeout=15)
        if folder_resp.status_code == 200:
            ok(f"Carpeta raíz encontrada: {folder_path} ({user_email})")
        elif folder_resp.status_code == 404:
            fail(f"Carpeta no encontrada en OneDrive: '{folder_path}'")
            try:
                root_resp = req.get(
                    f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root/children",
                    headers=headers,
                    params={"$select": "name,folder", "$top": "20"},
                    timeout=15,
                )
                if root_resp.status_code == 200:
                    items = root_resp.json().get("value", [])
                    folders = [i["name"] for i in items if "folder" in i]
                    print(f"         Carpetas en la raíz del OneDrive de {user_email}:")
                    for f in folders:
                        print(f"           → {f}")
            except Exception:
                pass
            return
        else:
            fail(f"Error al verificar carpeta raíz OneDrive: HTTP {folder_resp.status_code}")
            return
    except Exception as e:
        fail(f"No se pudo verificar carpeta OneDrive: {e}")
        return

    # Verificar subcarpetas operativas
    pending_folder   = od.get("pending_folder",   "Pendientes")
    processed_folder = od.get("processed_folder", "Procesados")
    error_folder     = od.get("error_folder",      "Errores")
    subfolders = [
        pending_folder,
        processed_folder,
        error_folder,
        "Facturas",
        "Notas de Crédito",
        "Notas de Débito",
    ]
    for sub in subfolders:
        sub_path = f"{folder_path}/{sub}"
        try:
            sub_resp = req.get(f"{base_url}{sub_path}", headers=headers, timeout=15)
            if sub_resp.status_code == 200:
                ok(f"Subcarpeta encontrada: {sub}")
            elif sub_resp.status_code == 404:
                warn(f"Subcarpeta no existe (se creará al correr): {sub}")
            else:
                warn(f"No se pudo verificar subcarpeta '{sub}': HTTP {sub_resp.status_code}")
        except Exception as e:
            warn(f"No se pudo verificar subcarpeta '{sub}': {e}")


def check_invoice_batch_importable() -> None:
    print("\n[8] Módulo invoice_batch")
    try:
        import invoice_batch  # noqa: F401
        ok("invoice_batch importable")
    except ImportError as e:
        fail(f"invoice_batch no importable: {e} — ejecutar: pip install -e .")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight check para invoice_batch.")
    parser.add_argument("--config", default="config/settings.json")
    parser.add_argument("--env", default=".env")
    args = parser.parse_args()

    config_path = Path(args.config)
    env_path = Path(args.env)

    print("=" * 55)
    print("  INVOICE BATCH — PREFLIGHT CHECK")
    print("=" * 55)

    check_python_version()
    check_dependencies()
    check_env(env_path)
    raw = check_config(config_path)
    if raw:
        check_inbox(config_path, raw)
        check_write_permissions(config_path, raw)
        check_onedrive(raw)
    check_invoice_batch_importable()

    print("\n" + "=" * 55)
    if errors:
        print(f"  RESULTADO: {errors} error(s), {warnings} advertencia(s) — NO correr hasta resolver los errores.")
    elif warnings:
        print(f"  RESULTADO: {warnings} advertencia(s) — revisar antes de correr.")
    else:
        print("  RESULTADO: todo OK — listo para correr.")
    print("=" * 55)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
