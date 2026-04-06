# Licium Backend — Módulos de Práctica

> Colección de módulos personalizados para el framework **Licium**: entorno Dockerizado con **FastAPI** en el backend, **PostgreSQL** como capa de persistencia y un frontend **Nuxt** que renderiza interfaces declaradas en YAML.

---

## Índice

- [Arquitectura de un Módulo](#arquitectura-de-un-módulo)
- [Módulos Incluidos](#módulos-incluidos)
- [Módulo: Feedback & Moderación](#módulo-feedback--moderación)
- [Módulo: Community Events](#módulo-community-events)
- [Puesta en Marcha](#puesta-en-marcha)
- [Cómo Ejecutar los Tests](#cómo-ejecutar-los-tests)
- [Notas para Desarrolladores](#notas-para-desarrolladores)
- [Estructura del Repositorio](#estructura-del-repositorio)

---

## Arquitectura de un Módulo

Cada módulo sigue una separación estricta en capas:

```
modules/mi_modulo/
├── __init__.py              # Registro del módulo
├── __manifest__.yaml        # Metadatos, dependencias y orden de carga de datos
├── models/                  # Capa de datos — Tablas SQLAlchemy
│   ├── __init__.py
│   └── mi_modelo.py
├── services/                # Capa de negocio — Lógica, validaciones y acciones expuestas
│   ├── __init__.py
│   └── mi_servicio.py
├── views/                   # Capa de presentación — UI declarativa en YAML
│   ├── views.yml
│   └── menu.yml
└── data/                    # Seguridad y configuración
    ├── groups.yml
    ├── acl_rules.yml
    └── ui_modules.yml
```

### Flujo de una petición

```
     HTTP Request
          │
          ▼
  ┌───────────────┐     ┌─────────────────┐     ┌──────────────────┐
  │  FastAPI Route │────▶│  Service Layer   │────▶│  Model (ORM)     │
  │  (auto-gen)    │     │  @exposed_action │     │  SQLAlchemy Base │
  └───────────────┘     └─────────────────┘     └──────────────────┘
          │                      │                        │
          │               ACL + Groups              PostgreSQL
          ▼
  ┌───────────────┐
  │  Frontend UI   │  ◄── views.yml + menu.yml (declarativo)
  │  (Nuxt, auto)  │
  └───────────────┘
```

---

## Módulos Incluidos

| Módulo | Nivel | Descripción |
|--------|:-----:|-------------|
| `practice_checklist` | 1 | Gestor de tareas y checklists con apertura/cierre automático e internacionalización |
| `asset_lending` | 2 | Inventario de activos, ubicaciones y ciclo de vida de préstamos |
| `feedback_moderation` | 3 | Moderación de sugerencias y comentarios con máquina de estados y relaciones M2M |
| `community_events` | 4 | Eventos comunitarios con control de aforo, listas de espera y check-in |

---

## Módulo: Feedback & Moderación

### Qué hace

Gestiona el ciclo de vida de **sugerencias y comentarios ciudadanos**. Cualquier usuario puede enviar una sugerencia; el equipo moderador la revisa y decide si publicarla, rechazarla o fusionarla con otra existente. Solo el contenido aprobado y marcado como público es visible para usuarios sin rol de moderador.

### Modelos

| Modelo | Descripción |
|--------|-------------|
| `Suggestion` | Entidad central. Almacena `title`, `content`, `author_email`, el estado de moderación (`pending` → `published` / `rejected` / `merged`) y `is_public`. Registra quién revisó la sugerencia (`reviewed_by_id`) y cuándo se publicó (`published_at`). |
| `Comment` | Comentario asociado a una sugerencia. Pasa por el mismo flujo de moderación independiente (`pending` → `published` / `rejected`). |
| `Tag` | Etiqueta de categorización (`name`, `slug`, `color`) vinculada a las sugerencias mediante una tabla de asociación Many-to-Many. |

### Acciones de servicio (`@exposed_action`)

Todas las acciones de moderación requieren el grupo `feedback_group_moderator` o `core_group_superadmin`:

| Acción | Descripción |
|--------|-------------|
| `publish(id, note?, pin?)` | Cambia el estado a `published`, marca `is_public=True` y registra la nota y el moderador. |
| `reject(id, note)` | Cambia el estado a `rejected`, mantiene `is_public=False` y guarda la nota obligatoria. |
| `merge(id, target_id, note?)` | Fusiona la sugerencia con otra. Valida que origen y destino sean distintos. |
| `reopen(id)` | Devuelve una sugerencia rechazada o fusionada al estado `pending`. |
| `publish_comment(id, note?)` | Publica un comentario pendiente. |
| `reject_comment(id, note?)` | Rechaza un comentario y lo oculta del público. |

> **Regla de creación**: Al crear una sugerencia o comentario el servicio fuerza siempre `status="pending"` e `is_public=False`, sin importar el payload recibido.

### Seguridad

| Grupo | Permisos |
|-------|----------|
| `feedback_group_viewer` | Lectura del contenido publicado |
| `feedback_group_moderator` | Lectura + escritura completa (hereda de Viewer) |
| `core_group_public` | Puede crear sugerencias y leer las que sean `published` e `is_public=true` |

### Hitos técnicos

| Hito | Detalle |
|------|---------|
| Relación Many-to-Many | `Suggestion` ↔ `Tag` con tabla de asociación explícita y `back_populates` |
| Seguridad dinámica | Domain en ACL pública: filtra a nivel de base de datos por `status` e `is_public` |
| UUID en Foreign Keys | `reviewed_by_id` apunta a `core_user.id` — debe ser `UUID`, no `Integer` |
| UI declarativa | `row_actions` en la vista de lista para ejecutar `publish`, `reject` y `merge` desde un clic |

---

## Módulo: Community Events

### Qué hace

Gestiona el ciclo de vida completo de **eventos comunitarios**: desde la creación en borrador y su publicación, hasta la inscripción de asistentes con control automático de aforo. Incluye sesiones internas por evento (talleres, ponencias), listas de espera cuando se supera la capacidad, y check-in con marca temporal el día del evento.

### Modelos

| Modelo | Descripción |
|--------|-------------|
| `Event` | Entidad maestra. Campos principales: `title`, `slug`, `status` (`draft` / `published` / `closed` / `cancelled`), `is_public`, `capacity_total`, fechas (`start_at`, `end_at`) y `organizer_user_id`. Tiene relaciones One-to-Many con `Session` y `Registration` con cascade. |
| `Session` | Segmento o charla dentro de un evento (`event_id`). Almacena `speaker_name`, `room`, tiempos propios y `capacity` limitada. |
| `Registration` | Inscripción de un asistente a un evento o sesión. Estados: `pending` / `confirmed` / `waitlist` / `cancelled`. Registra `registered_at`, `checkin_at` y `attendee_email`. |

### Acciones de servicio (`@exposed_action`)

Requieren el grupo `community_events_group_staff` o `core_group_superadmin`:

| Servicio | Acción | Descripción |
|----------|--------|-------------|
| `EventService` | `publish_event(id, note?)` | Pasa el evento a `published` y lo hace visible al público. |
| `EventService` | `close_registration(id, reason?)` | Cierra el evento a nuevas inscripciones (`closed`). |
| `EventService` | `cancel_event(id, reason)` | Cancela el evento y lo oculta (`is_public=False`). |
| `EventService` | `reopen_event(id)` | Reactiva un evento cerrado o cancelado a `published`. |
| `RegistrationService` | `confirm(id, note?)` | Confirma una inscripción pendiente o en lista de espera. |
| `RegistrationService` | `checkin(id, source?)` | Registra el acceso al evento con timestamp UTC. Bloquea con HTTP 400 si el estado no es `confirmed`. |

> **Regla de creación**: Al crear una inscripción se inyecta automáticamente `registered_at` con la fecha UTC actual y se establece `status="pending"` si no se indica otro.

> **Sanitización de fechas**: El `EventService` detecta y convierte fechas en formato `dd/mm/yyyy` al formato ISO con timezone UTC antes de persistirlas.

### Seguridad

| Grupo | Permisos |
|-------|----------|
| `community_events_group_viewer` | Lectura de eventos (hereda de `core_group_internal_user`) |
| `community_events_group_staff` | CRUD completo sobre todos los modelos del módulo (`community_events.*`) |
| `core_group_public` | Lectura de eventos donde `status='published'` Y `is_public=true`; creación de inscripciones |

### Hitos técnicos

| Hito | Detalle |
|------|---------|
| Control de aforo | La lógica de confirmación/waitlist se gestiona en el servicio sin lógica en el modelo |
| Cascade relacional | Borrar un `Event` elimina en cascada sus `Session` y `Registration` asociadas |
| FK tipadas correctamente | `organizer_user_id` y `attendee_user_id` → `UUID`; `event_id` / `session_id` → `Integer` |
| Sesiones anidadas | Un evento puede tener múltiples sesiones, cada una con su propia capacidad y ponente |

---

## Puesta en Marcha

### Requisitos previos

- **Docker** y **Docker Compose v2+** instalados en el sistema.
- Puertos `8000` (backend), `3000` (frontend) y `5432` (PostgreSQL) disponibles.

### 1. Levantar los contenedores

```bash
git clone <url-del-repositorio>
cd backend

docker compose -f docker-compose.backend-dev.yml up -d
```

| Servicio | Contenedor | Puerto |
|----------|-----------|--------|
| PostgreSQL 17 | `licium-postgres-dev` | `5432` |
| Backend FastAPI | `licium-backend-dev` | `8000` |
| Frontend Nuxt | `licium-frontend-dev` | `3000` |

### 2. Instalación base del framework

Con los contenedores activos, abrir en el navegador:

```
http://localhost:8000/api/install
```

Esto inicializa las tablas del core, los grupos de administración y el usuario inicial.

### 3. Instalar los módulos

```bash
# Feedback & Moderación
docker exec -it licium-backend-dev \
  python -m app.cli.module install modules/feedback_moderation -y

# Community Events
docker exec -it licium-backend-dev \
  python -m app.cli.module install modules/community_events -y
```

### 4. Acceder al frontend

```
http://localhost:3000
```

---

## Cómo Ejecutar los Tests

Los tests unitarios de cada módulo usan `pytest` con `MagicMock` para aislar la lógica de negocio de la base de datos. No requieren PostgreSQL activo.

### Feedback & Moderación

```bash
docker exec -it licium-backend-dev \
  python -m pytest modules/feedback_moderation/tests/ -v
```

Salida esperada:

```
tests/test_moderation_states.py::test_initial_state_is_pending_and_private     PASSED
tests/test_moderation_states.py::test_publish_transition_makes_it_public        PASSED
tests/test_moderation_states.py::test_reject_transition_keeps_it_private        PASSED
tests/test_moderation_states.py::test_merge_fails_if_target_is_same_as_source   PASSED

========================= 4 passed =========================
```

### Community Events

```bash
docker compose -f docker-compose.backend-dev.yml exec \
  -e PYTHONPATH=/opt/licium backend \
  pytest modules/community_events/tests/test_events.py -v
```

Salida esperada:

```
tests/test_events.py::test_publish_event_changes_status_and_visibility   PASSED
tests/test_events.py::test_cancel_event_hides_it_from_public             PASSED
tests/test_events.py::test_checkin_success_for_confirmed_user            PASSED
tests/test_events.py::test_checkin_fails_for_cancelled_user              PASSED

========================= 4 passed =========================
```

---

## Notas para Desarrolladores

### Orden de carga en `__manifest__.yaml`

El orden de los archivos en la clave `data` es crítico. Siempre seguir esta cadena:

```yaml
data:
  - data/groups.yml       # 1. Grupos de seguridad (sin dependencias)
  - data/acl_rules.yml    # 2. ACL (referencia groups por ext_id)
  - data/ui_modules.yml   # 3. Registro en el frontend
  - views/views.yml       # 4. Vistas (referencia modelos ya existentes)
  - views/menu.yml        # 5. Menú (referencia vistas por ext_id)
```

### Foreign Keys: UUID vs Integer

Al hacer referencia a `core_user.id` la FK **debe ser `UUID`**. Para modelos propios del módulo usar `Integer` (SERIAL).

```python
# ❌ DatatypeMismatch con PostgreSQL
reviewed_by_id = field(Integer, ForeignKey("core_user.id"), ...)

# ✅ Correcto
reviewed_by_id = field(UUID, ForeignKey("core_user.id"), ...)
```

### Renombrar la carpeta raíz

Si se renombra el directorio del proyecto, Docker Compose generará un nuevo volumen de PostgreSQL y los datos del anterior quedarán huérfanos. Para resetear limpiamente:

```bash
docker compose -f docker-compose.backend-dev.yml down -v
docker compose -f docker-compose.backend-dev.yml up -d
# Repetir: /api/install + CLI de instalación de módulos
```

---

## Estructura del Repositorio

```
backend/
├── docker-compose.backend-dev.yml
├── filestore/
├── docs/
│   ├── modulos_tarea.md
│   └── tutorial_incremental_modulos_backend.md
└── modules/
    ├── practice_checklist/      # Módulo Nivel 1 — Checklists con bulk actions e i18n
    ├── asset_lending/           # Módulo Nivel 2 — Inventario y préstamos de activos
    ├── feedback_moderation/     # Módulo Nivel 3 — Moderación de sugerencias y comentarios
    └── community_events/        # Módulo Nivel 4 — Eventos con aforo, waitlist y check-in
```

---

## Licencia

Uso interno — Desarrollado durante las prácticas en [Libnamic](https://libnamic.com).

