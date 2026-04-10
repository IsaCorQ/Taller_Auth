# ejercicio-auth (MySQL + Python)

Taller CE-1115: archivo de la **Unidad de Casos Especiales (UCE)** del TEC — constituida en **1971**, en paralelo a la creación de la institución. La app simula el acceso al expediente digital del campus Cartago: autenticación básica y **matriz de autorización rota** a propósito para el laboratorio.

Hay tres **frentes** (equipos): OVNI, Ghosts y Wizards (`teams` en `schema.sql`). Cada usuario pertenece a uno y, según la **matriz de acceso** de `Taller_Auth.md`, **debería** solo ver y agregar ítems de **su** tabla y **solo las notas con su** `team_id`. En la versión actual del `app.py`, **cualquier agente autenticado** puede ver y alterar todo (fallo grave que corrigen en la etapa 0–1).

## Requisitos

- MySQL 8+ (o 5.7+)
- Python 3.10+

## Puesta en marcha

```bash
cd Ejercicios/ejercicio-auth
mysql -u root -p < schema.sql
# Si ya existía la BD (sin tabla notas u otros cambios), borra y recrea:
# mysql -u root -p -e "DROP DATABASE IF EXISTS ejercicio_auth;" && mysql -u root -p < schema.sql
pip install -r requirements.txt
export MYSQL_USER=root MYSQL_PASSWORD=tu_clave   # si aplica
python app.py
```

La app pide **correo** y **contraseña** por consola. Usuarios demo (contraseña `demo123`):

| Correo              | Equipo   |
|---------------------|----------|
| `ovni@lab.local`    | ovni     |
| `ghosts@lab.local`  | ghosts   |
| `wizards@lab.local` | wizards  |

Variables opcionales: `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.

## Guía paso a paso del taller

Ver **[Taller_Auth.md](./Taller_Auth.md)** — UCE desde **1971**, marco teórico, etapas 0–3 y matriz (metas y criterios; el diseño de la solución lo define el equipo).

## Archivos

- `schema.sql` — base de datos y datos de prueba
- `app.py` — CLI mínima
- `requirements.txt` — dependencias
- `Taller_Auth.md` — guía del taller (metas y matriz)
