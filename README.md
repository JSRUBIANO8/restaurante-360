# Restaurante 360 | AA2 – Gestión del Software
Prototipo académico funcional de reservas y pedidos con FastAPI, SQLite y una interfaz responsive. Autor: Jhoan Sebastian Rubiano Moscoso.

## Ejecutar en Windows (PowerShell)
Con Python 3.12 instalado, abre la carpeta en VS Code y ejecuta:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:ADMIN_PASSWORD = 'CambiaEstaClaveLocal'
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```
Abre http://127.0.0.1:8000. La clave administrativa es la que configuraste; no está guardada en el repositorio. La documentación interactiva de la API está en http://127.0.0.1:8000/docs. SQLite crea automáticamente la base local. Cada mesa admite hasta cuatro personas; se usan cuatro franjas horarias fijas. Las confirmaciones se muestran en pantalla, no se envían correos.

## Pruebas locales
```powershell
.\.venv\Scripts\python.exe -m pytest -q --cov=app --cov-fail-under=80
.\.venv\Scripts\python.exe -m bandit -r app.py -ll
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
```
En `docs/pruebas-locales.txt` están los resultados de pytest ejecutados durante la preparación del proyecto, en Python 3.13.

## Subir a GitHub
1. Crea un repositorio vacío llamado `restaurante-360` en https://github.com/new (sin README inicial).
2. Desde esta carpeta, con Git instalado:
```bash
git init
git add .
git commit -m "feat: sistema restaurante y pipeline CI/CD"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/restaurante-360.git
git push -u origin main
```
3. Reemplaza TU-USUARIO por tu usuario real. En GitHub, abre Actions y selecciona Restaurante 360 CI-CD. El push dispara la ejecución. Si Actions está desactivado, actívalo en Settings > Actions. Si falla una auditoría, revisa el log y actualiza la dependencia vulnerable; no omitas la validación.
4. Descarga los artefactos `calidad` y `staging` y captura el resumen de ejecución.

## Demostrar un fallo y su corrección
Después de una ejecución inicial exitosa, crea una rama `demo/fallo` (`git switch -c demo/fallo`). En `tests/test_app.py`, cambia temporalmente la expectativa del segundo POST en `test_duplicate` de 409 a 201. Es una prueba negativa deliberada del bloqueo del pipeline, no un defecto real en la aplicación. Haz commit y push (`git push -u origin demo/fallo`). Captura el fallo de pytest y el job staging omitido. Revierte el commit (`git revert --no-edit HEAD`), vuelve a hacer push y captura el resultado. No fusiones el fallo a main.

## Docker local (si tienes Docker Desktop)
```powershell
docker build -t restaurante-360 .
docker run --rm -p 127.0.0.1:8000:8000 -e ADMIN_PASSWORD=CambiaEstaClaveLocal -v restaurante-data:/data restaurante-360
```

## Pipeline
Push / Pull request -> compilación Python y dependencias -> pytest + cobertura >=80% -> Bandit (bloquea severidad media/alta) -> pip-audit -> Docker build -> staging temporal -> health check -> Locust (50 usuarios, 30 segundos) -> puerta de calidad (p95 <500 ms y cero fallos) -> artefactos y limpieza. Un error en quality impide ejecutar staging. El staging vive únicamente durante la ejecución de Actions, no es un hosting permanente. El test de carga mide consultas de lectura; no demuestra disponibilidad de largo plazo. Los logs y métricas reales deben obtenerse en GitHub.

## Límites y evolución
Autenticación administrativa básica con contraseña de entorno y tokens en memoria de un único proceso. Para producción: autenticación individual, expiración de tokens, limitación de intentos, HTTPS, PostgreSQL, migraciones, gestión de secretos, imágenes versionadas, revisión obligatoria de PR y monitoreo. Los precios son ficticios; no hay cobros reales. Las dependencias tienen rangos de versión: para producción generar un lockfile auditado. El entorno de preparación no tenía Docker ni acceso a PyPI, por lo que el pipeline remoto, Bandit, pip-audit y Locust quedan pendientes de ejecución en GitHub.
