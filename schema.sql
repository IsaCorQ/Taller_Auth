-- CE-1115 — ejercicio-auth (MySQL)
-- Archivo digital — Unidad de Casos Especiales (UCE), línea operativa desde 1971 (fundación del TEC).
-- Ejecutar: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS ejercicio_auth CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ejercicio_auth;

-- Frentes de la UCE. Cada agente pertenece a un solo frente.
CREATE TABLE teams (
  id TINYINT UNSIGNED PRIMARY KEY,
  code VARCHAR(32) NOT NULL UNIQUE,
  display_name VARCHAR(80) NOT NULL
);

INSERT INTO teams (id, code, display_name) VALUES
  (1, 'ovni', 'UCE — Frente OVNI (desde 1971)'),
  (2, 'ghosts', 'UCE — Frente Espectral (desde 1971)'),
  (3, 'wizards', 'UCE — Frente Arcano (desde 1971)');

-- Contraseña con hash bcrypt (taller etapa 2).
-- Login en la app: correo + contraseña; se verifica con bcrypt.checkpw().
CREATE TABLE users (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  team_id TINYINT UNSIGNED NOT NULL,
  FOREIGN KEY (team_id) REFERENCES teams (id)
);

-- Tres catálogos separados (matriz: cada equipo debería ver/solo escribir el suyo).
CREATE TABLE ovnis (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL
);

CREATE TABLE ghosts (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL
);

CREATE TABLE wizards (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL
);

-- Notas de investigación por equipo (taller RLS: cada equipo debería ver solo las suyas).
CREATE TABLE notas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  team_id TINYINT UNSIGNED NOT NULL,
  contenido VARCHAR(500) NOT NULL,
  FOREIGN KEY (team_id) REFERENCES teams (id)
);

-- Usuarios demo (misma contraseña: demo123)
-- Hash generado con: bcrypt.hashpw(b'demo123', bcrypt.gensalt()).decode()
INSERT INTO users (email, password_hash, team_id) VALUES
  ('alejimenezc92@gmail.com', '$2b$12$KW2tZpsEShUMQYav9pMqqeFXTDnC5SbYzpaA6m6yis3jB0CWdQTJe', 1),
  ('ghosts@lab.local', '$2b$12$KW2tZpsEShUMQYav9pMqqeFXTDnC5SbYzpaA6m6yis3jB0CWdQTJe', 2),
  ('wizards@lab.local', '$2b$12$KW2tZpsEShUMQYav9pMqqeFXTDnC5SbYzpaA6m6yis3jB0CWdQTJe', 3);

-- Registros “ocultos” inspirados en lugares y datos públicos del Campus Central Cartago (ficción de taller).
INSERT INTO ovnis (name) VALUES
  ('L-TEC-001: luces en silencio sobre canchas — sin drones registrados'),
  ('L-TEC-002: mancha térmica circular — Biblioteca JFF, techo remodelado 2024–2025'),
  ('L-TEC-003: destello sobre bosque del campus — correlación con neblina a 1435 msnm');
INSERT INTO ghosts (name) VALUES
  ('E-TEC-01: pasos en pasillos tras cierre — edificio de servicios académicos'),
  ('E-TEC-02: sombra en ventanales BJF — piso alto, sin movimiento HVAC'),
  ('E-TEC-03: “eco de silbato” gimnasio — sin entrenamiento en agenda');
INSERT INTO wizards (name) VALUES
  ('A-TEC-α: anomalía de horario — examen que “cambia” de aula en SIGA (leyenda)'),
  ('A-TEC-β: círculo de tesis — tres citas idénticas, tres décadas distintas'),
  ('A-TEC-γ: donación simbólica 2012 — bronce cerca del comedor; archivo sellado');

INSERT INTO notas (team_id, contenido) VALUES
  (1, 'Testigo (anónimo): objeto estático sobre el perfil del campus; sin ruido de rotor; viento del Este.'),
  (1, 'Nota de correlación: aves nocturnas descartadas; mapache fuera de ventana; no explica trayectoria recta.'),
  (1, 'Biblioteca JFF: revisar cámaras post-remodelación; fibra nueva; falso positivo por reflejo aún no descartado.'),
  (2, 'Patrón: incidentes suben en semanas de neblina densa en Cartago; campus 88 ha; bordes con bosque.'),
  (2, 'Audio de campo — pasos + agua; correlación con lluvia fina; sensor de puerta sin apertura registrada.'),
  (2, 'Gimnasio: custodia confirma alarma OK; sensación de “presencia” reportada por 2 brigadas distintas.'),
  (3, 'Archivo fundacional 1971: acta interna UCE — alineación cronológica con constitución del TEC; sello de archivo restringido.'),
  (3, 'Índice simbólico: estatua donada por Asociación Mundial de Confucio CR; punto de referencia; “mapa” antiguo superpuesto (ficción).'),
  (3, 'Fauna campus: inventario oficial menciona sapos comunes; broma interna: “los verdaderos custodios del TEC” — no clasificar como OVNI.');
