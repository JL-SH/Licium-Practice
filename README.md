# LibnamicProyectos - Backend

Sistema modular de backend basado en Licium para la gestión de checklists internos con soporte para múltiples idiomas, configuración dinámica y acciones masivas.

## Descripción

Proyecto que implementa un módulo backend completo llamado `practice_checklist` demostrando las capacidades del framework Licium. Incluye modelos de datos, servicios con acciones personalizadas, interfaz admin automática, seguridad basada en grupos y ACL, bulk actions, settings dinámicos e internacionalización.

## Estructura

```
backend/
├── modules/
│   └── practice_checklist/
│       ├── __init__.py
│       ├── __manifest__.yaml
│       ├── models/
│       │   ├── __init__.py
│       │   └── checklist.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── checklist.py
│       ├── data/
│       │   ├── groups.yml
│       │   ├── acl_rules.yml
│       │   ├── ui_modules.yml
│       │   └── settings.yml
│       ├── views/
│       │   ├── views.yml
│       │   └── menu.yml
│       └── i18n/
│           ├── es.yml
│           └── en.yml
├── docs/
  └── tutorial_incremental_modulos_backend.md
```

## Tutorial y Mejoras Incrementales

El proyecto completa el tutorial en `docs/tutorial_incremental_modulos_backend.md` y implementa las siguientes mejoras incrementales:

1. **Mejora 1 - Bulk Actions**: Acción `set_done_bulk` para marcar múltiples items a la vez desde la interfaz admin.
2. **Mejora 2 - Settings**: Modelo y servicio para gestionar configuración dinámica del módulo (auto_close_enabled, auto_close_days, notification_enabled).
3. **Mejora 3 - Internacionalización**: Traducciones completas al español e inglés para la interfaz admin.

## Referencias

- Tutorial completo: `docs/tutorial_incremental_modulos_backend.md`
- Módulo: `modules/practice_checklist/`

---