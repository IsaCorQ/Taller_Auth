#!/usr/bin/env python3
"""
CE-1115 — ejercicio-auth (CLI + MySQL)
Acceso al archivo digital de la Unidad de Casos Especiales (UCE) del TEC — operativa
desde 1971 (año de fundación del TEC). Ver Taller_Auth.md para el relato y la matriz.

Qué hace este archivo en una frase: pide correo y contraseña, y si coinciden con la
tabla `users`, deja consultar y modificar catálogos y notas.

Profesor / nota de clase:
  - Esto implementa bien la *identidad* (autenticación: ¿quién eres?).
  - A propósito NO implementa la *matriz de permisos* (autorización: ¿qué puedes tocar?).
    Por eso un usuario ovni puede leer fantasmas o escribir notas de wizards: lean Taller_Auth.md.

Buenas prácticas que sí debe copiar el equipo:
  - Valores de login en consultas con %s (parametrizado) → mitiga inyección SQL.
  - Nombres de tabla para SELECT/INSERT de catálogo solo desde lista blanca (_CATALOG_TABLES).
  - Credenciales de MySQL desde variables de entorno, no pegadas en el código.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

import pymysql

# ---------------------------------------------------------------------------
# Variables de entorno — nombres en constantes para no equivocarse al escribir
# ---------------------------------------------------------------------------
# Profesor: si mañana cambian el nombre de la variable, solo tocan aquí.
_ENV_MYSQL_HOST: Final = "MYSQL_HOST"
_ENV_MYSQL_USER: Final = "MYSQL_USER"
_ENV_MYSQL_PASSWORD: Final = "MYSQL_PASSWORD"
_ENV_MYSQL_DATABASE: Final = "MYSQL_DATABASE"

_DEFAULT_MYSQL_HOST: Final = "127.0.0.1"
_DEFAULT_MYSQL_USER: Final = "root"
_DEFAULT_MYSQL_PASSWORD: Final = ""
_DEFAULT_MYSQL_DATABASE: Final = "ejercicio_auth"
_DEFAULT_CHARSET: Final = "utf8mb4"

# ---------------------------------------------------------------------------
# Tablas físicas en MySQL
# ---------------------------------------------------------------------------
# Profesor: el riesgo de SQL dinámico es concatenar input del usuario en el SQL.
# Aquí el nombre de tabla solo puede ser uno de estos (validado en _assert_catalog_table).


class Table:
    OVNIS: Final = "ovnis"
    GHOSTS: Final = "ghosts"
    WIZARDS: Final = "wizards"
    NOTAS: Final = "notas"
    USERS: Final = "users"
    TEAMS: Final = "teams"


_CATALOG_TABLES: Final[frozenset[str]] = frozenset({Table.OVNIS, Table.GHOSTS, Table.WIZARDS})

# ---------------------------------------------------------------------------
# SQL — plantillas
# ---------------------------------------------------------------------------
# Profesor: %s = huecos para datos del usuario (siempre vía execute(..., tupla)).
# {table} en _SQL_SELECT_CATALOG solo se rellena DESPUÉS de validar contra _CATALOG_TABLES;
# nunca pongan ahí un string que venga del input() sin validar.

_SQL_LOGIN: Final[str] = (
    "SELECT u.id, u.email, t.code AS team_code, t.display_name AS team_name "
    "FROM users u JOIN teams t ON t.id = u.team_id "
    "WHERE u.email = %s AND u.password_plain = %s"
)
_SQL_SELECT_CATALOG: Final[str] = "SELECT id, name FROM {table} ORDER BY id"
_SQL_INSERT_CATALOG: Final[str] = "INSERT INTO {table} (name) VALUES (%s)"
_SQL_LIST_NOTAS_ALL: Final[str] = (
    "SELECT n.id, n.contenido, t.display_name AS equipo "
    "FROM notas n JOIN teams t ON t.id = n.team_id "
    "ORDER BY t.id, n.id"
)
_SQL_INSERT_NOTA: Final[str] = "INSERT INTO notas (team_id, contenido) VALUES (%s, %s)"

_TITLE_NOTAS_TODAS: Final[str] = "Notas de investigación (todos los equipos)"

# ---------------------------------------------------------------------------
# Menú — Enum evita comparar contra "1", "2" esparcidos en todo el archivo
# ---------------------------------------------------------------------------
class MenuOption(str, Enum):
    """Valores que el usuario escribe en consola (coinciden con el texto del menú)."""

    SALIR = "0"
    LISTAR_OVNIS = "1"
    LISTAR_GHOSTS = "2"
    LISTAR_WIZARDS = "3"
    AGREGAR_CATALOGO = "4"
    LISTAR_NOTAS_TODAS = "5"
    AGREGAR_NOTA_CUALQUIER_EQUIPO = "6"


@dataclass(frozen=True)
class CatalogView:
    """Empareja nombre de tabla MySQL con título amigable en pantalla."""

    table: str
    title: str


_CATALOG_BY_MENU: Final[dict[MenuOption, CatalogView]] = {
    MenuOption.LISTAR_OVNIS: CatalogView(Table.OVNIS, "OVNIs"),
    MenuOption.LISTAR_GHOSTS: CatalogView(Table.GHOSTS, "Fantasmas"),
    MenuOption.LISTAR_WIZARDS: CatalogView(Table.WIZARDS, "Magos / Wizards"),
}

_CATALOG_BY_LIST_KEY: Final[dict[str, CatalogView]] = {
    MenuOption.LISTAR_OVNIS.value: _CATALOG_BY_MENU[MenuOption.LISTAR_OVNIS],
    MenuOption.LISTAR_GHOSTS.value: _CATALOG_BY_MENU[MenuOption.LISTAR_GHOSTS],
    MenuOption.LISTAR_WIZARDS.value: _CATALOG_BY_MENU[MenuOption.LISTAR_WIZARDS],
}

# Mapeo menú 1/2/3 → team_id en la tabla `notas` (coincide con teams.id en schema.sql).
_TEAM_ID_BY_LIST_KEY: Final[dict[str, int]] = {
    MenuOption.LISTAR_OVNIS.value: 1,
    MenuOption.LISTAR_GHOSTS.value: 2,
    MenuOption.LISTAR_WIZARDS.value: 3,
}

# Matriz objetivo del taller (Taller_Auth.md). El código actual NO la aplica.
# team_code | ovnis | ghosts | wizards | notas.team_id
# ovni      | sí    | no     | no      | solo 1
# ghosts    | no    | sí     | no      | solo 2
# wizards   | no    | no     | sí      | solo 3


def _mysql_config() -> dict[str, Any]:
    """Arma el dict que espera pymysql.connect."""
    return {
        "host": os.environ.get(_ENV_MYSQL_HOST, _DEFAULT_MYSQL_HOST),
        "user": os.environ.get(_ENV_MYSQL_USER, _DEFAULT_MYSQL_USER),
        "password": os.environ.get(_ENV_MYSQL_PASSWORD, _DEFAULT_MYSQL_PASSWORD),
        "database": os.environ.get(_ENV_MYSQL_DATABASE, _DEFAULT_MYSQL_DATABASE),
        "charset": _DEFAULT_CHARSET,
        "cursorclass": pymysql.cursors.DictCursor,
    }


def connect() -> pymysql.connections.Connection:
    """Abre una sesión con el servidor MySQL (red + autenticación del *usuario de BD*)."""
    return pymysql.connect(**_mysql_config())


def login(conn: pymysql.connections.Connection) -> dict[str, Any] | None:
    """
    Autenticación (AuthN): comprueba correo + contraseña contra `users`.

    Devuelve un dict con email y datos del equipo si hay coincidencia; si no, None.
    Profesor: observe que la contraseña hoy está en texto plano en la BD — eso es
    vulnerabilidad de diseño (etapa 2 del taller: hash).
    """
    print("--- Inicio de sesión ---")
    email = input("Correo: ").strip().lower()
    password = input("Contraseña: ").strip()
    with conn.cursor() as cur:
        cur.execute(_SQL_LOGIN, (email, password))
        return cur.fetchone()


def _assert_catalog_table(table: str) -> None:
    """Evita que por error se ejecute SQL sobre una tabla no prevista."""
    if table not in _CATALOG_TABLES:
        raise ValueError(f"Tabla de catálogo no permitida: {table!r}")


def list_catalog(conn: pymysql.connections.Connection, spec: CatalogView) -> None:
    """
    Lista *toda* la tabla de catálogo elegida.

    Profesor: aquí debería existir una comprobación del tipo
    if user['team_code'] != 'ovni' and spec.table == Table.OVNIS: denegar
    según la matriz. Hoy no se pasa `user` a esta función: es el bug pedagógico.
    """
    _assert_catalog_table(spec.table)
    sql = _SQL_SELECT_CATALOG.format(table=spec.table)
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    print(f"\n--- {spec.title} ---")
    for row in rows:
        print(f"  [{row['id']}] {row['name']}")
    if not rows:
        print("  (vacío)")


def add_catalog_item(conn: pymysql.connections.Connection, spec: CatalogView) -> None:
    """
    INSERT en catálogo. Profesor: igual que list_catalog — falta cruzar con el equipo del usuario.
    """
    _assert_catalog_table(spec.table)
    name = input("Nombre del ítem: ").strip()
    if not name:
        print("Cancelado.")
        return
    sql = _SQL_INSERT_CATALOG.format(table=spec.table)
    with conn.cursor() as cur:
        cur.execute(sql, (name,))
    conn.commit()  # Confirma la transacción; sin esto otro cliente podría no ver el cambio.
    print("Guardado.")


def list_notas_all_teams(conn: pymysql.connections.Connection) -> None:
    """
    Lista notas de *todos* los equipos.

    Profesor: en producción esto sería la filtración por RLS o WHERE team_id = %s del usuario.
    """
    with conn.cursor() as cur:
        cur.execute(_SQL_LIST_NOTAS_ALL)
        rows = cur.fetchall()
    print(f"\n--- {_TITLE_NOTAS_TODAS} ---")
    for row in rows:
        print(f"  [{row['id']}] [{row['equipo']}] {row['contenido']}")
    if not rows:
        print("  (vacío)")


def add_nota_any_team(conn: pymysql.connections.Connection) -> None:
    """
    INSERT en `notas` con team_id elegido por quien usa la app.

    Profesor: en la matriz correcta, team_id debería ser siempre user['team_id'], sin preguntar.
    """
    prompt = (
        f"¿Equipo de la nota? {MenuOption.LISTAR_OVNIS.value}=OVNI "
        f"{MenuOption.LISTAR_GHOSTS.value}=Ghosts {MenuOption.LISTAR_WIZARDS.value}=Wizards: "
    )
    key = input(prompt).strip()
    team_id = _TEAM_ID_BY_LIST_KEY.get(key)
    if team_id is None:
        print("Opción inválida.")
        return
    texto = input("Contenido de la nota: ").strip()
    if not texto:
        print("Cancelado.")
        return
    with conn.cursor() as cur:
        cur.execute(_SQL_INSERT_NOTA, (team_id, texto))
    conn.commit()
    print("Nota guardada.")


def _print_menu(user: dict[str, Any]) -> None:
    # Mostramos el equipo solo para que ustedes vean la contradicción: sabe el rol y aun así el menú permite todo.
    print(f"\nSesión: {user['email']} | Equipo: {user['team_name']} ({user['team_code']})")
    print(
        f"{MenuOption.LISTAR_OVNIS.value}) Listar OVNIs   "
        f"{MenuOption.LISTAR_GHOSTS.value}) Listar fantasmas   "
        f"{MenuOption.LISTAR_WIZARDS.value}) Listar wizards"
    )
    print(f"{MenuOption.AGREGAR_CATALOGO.value}) Agregar ítem a cualquier lista")
    print(
        f"{MenuOption.LISTAR_NOTAS_TODAS.value}) Ver notas de todos los equipos   "
        f"{MenuOption.AGREGAR_NOTA_CUALQUIER_EQUIPO.value}) Agregar nota a cualquier equipo"
    )
    print(f"{MenuOption.SALIR.value}) Salir")


def run_menu(conn: pymysql.connections.Connection, user: dict[str, Any]) -> None:
    """
    Bucle principal post-login.

    Profesor: para la etapa 1, casi todas las ramas necesitan recibir `user` y consultar
    la matriz antes de llamar a list_catalog / add_* , o filtrar el SQL con team_id.
    """
    while True:
        _print_menu(user)
        raw = input("Opción: ").strip()
        try:
            choice = MenuOption(raw)
        except ValueError:
            print("Opción inválida.")
            continue

        if choice == MenuOption.SALIR:
            break
        if choice in _CATALOG_BY_MENU:
            list_catalog(conn, _CATALOG_BY_MENU[choice])
        elif choice == MenuOption.AGREGAR_CATALOGO:
            sub = input("¿Lista? 1=ovnis 2=ghosts 3=wizards: ").strip()
            spec = _CATALOG_BY_LIST_KEY.get(sub)
            if spec is None:
                print("Opción inválida.")
            else:
                add_catalog_item(conn, spec)
        elif choice == MenuOption.LISTAR_NOTAS_TODAS:
            list_notas_all_teams(conn)
        elif choice == MenuOption.AGREGAR_NOTA_CUALQUIER_EQUIPO:
            add_nota_any_team(conn)


def main() -> int:
    """
    Punto de entrada: conectar → login → menú → cerrar.

    Profesor: el `finally: conn.close()` libera el socket aunque haya error o Ctrl+C
    en algunos entornos; es hábito sano con bases de datos.
    """
    try:
        conn = connect()
    except pymysql.Error as e:
        print("No se pudo conectar a MySQL:", e, file=sys.stderr)
        return 1

    try:
        user = login(conn)
        if not user:
            print("Credenciales inválidas.")
            return 1
        run_menu(conn, user)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
