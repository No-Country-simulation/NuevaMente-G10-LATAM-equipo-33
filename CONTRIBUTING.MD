# Pautas de Desarrollo y Contribución — NuevaMente

## Flujo de ramas

```
main → rama de módulo → rama de tarea puntual
```

- **`main`** está protegida. Nadie commitea ni mergea directo ahí — solo vía Pull Request aprobado.
- Cada **módulo** tiene su propia rama (`ingesta-rag`, `orquestacion-agentes`, `backend`, `interfaz`, `oci-storage`, `evaluacion`). Tampoco se commitea directo ahí.
- Cada **tarea puntual** se trabaja en una rama propia, creada desde la rama de su módulo:
  ```bash
  git checkout <rama-del-modulo>
  git checkout -b <rama-del-modulo>-<tarea>
  ```
- Al terminar: push → Pull Request contra la rama del módulo → revisión → merge → **la rama de tarea se elimina**.

## Reglas de convivencia

- **No mergear a `main` bajo ningún motivo antes del release final**.
- **No tocar código de un módulo que no te fue asignado** sin avisar antes a quien lo lleva. Si necesitás algo de otro módulo, coordinen el contrato de datos entre ambos antes de tocar nada.
- Commits en inglés (opcional), formato [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, `docs:`).
- Todo cambio pasa por PR con al menos 1 aprobación antes de mergear.

## Estructura por módulo

Cada carpeta de módulo debe incluir:

```
<modulo>/
├── README.md          # qué hace el módulo + guía de instalación local
├── .gitignore          # archivos sensibles del módulo (.env, venv/, __pycache__/, etc.)
├── requirements.txt    # dependencias del módulo
└── ...                 # código
```

- **README.md del módulo**: cómo instalar, cómo correrlo local, ejemplo de uso mínimo.
- **`.gitignore` propio**: además del `.gitignore` general del repo, cada módulo protege sus credenciales y archivos generados (modelos, cachés, entornos virtuales).
- **`requirements.txt` propio**: cada módulo declara solo sus dependencias — evita instalar de más en módulos que no las necesitan.

## Checklist antes de abrir un PR

- [ ] El código corre local sin errores
- [ ] No se subieron archivos sensibles (`.env`, credenciales, claves de OCI)
- [ ] `requirements.txt` actualizado si se agregaron dependencias
- [ ] Se sugiere el uso de conventional commits