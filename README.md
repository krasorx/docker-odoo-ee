# docker-odoo-ee

Plantilla reutilizable para levantar Odoo 19 Enterprise con Docker, Traefik y módulos OCA/custom.

## Requisitos

- Docker + Docker Compose v2
- Traefik corriendo con la red externa `traefik_net` y el entry point `websecure`
- Acceso SSH a los repositorios de módulos (GitHub/GitLab)

## Estructura

```
.
├── addons/                  # Módulos comunitarios (git-ignorado, gestionado por setup.sh)
├── ee-addons/
│   └── enterprise/          # Módulos Enterprise de Odoo (git-ignorado, clonar manualmente)
├── modules.conf             # Lista de módulos a clonar
├── setup.sh                 # Script que clona / actualiza módulos desde modules.conf
├── docker-compose.yml
├── Dockerfile
├── odoo.conf.template       # Plantilla de configuración (addons_path se genera en runtime)
├── entrypoint.sh            # Genera odoo.conf y arranca Odoo
├── requirements.txt         # Dependencias Python adicionales
└── .env.example             # Variables de entorno de ejemplo
```

## Inicio rápido

### 1. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con PROJECT_NAME, MAIN_HOST, contraseñas, etc.
```

### 2. Clonar módulos Enterprise

```bash
git clone git@github.com:odoo/enterprise.git -b 19.0 ee-addons/enterprise
```

### 3. Declarar módulos adicionales en `modules.conf`

```
git@github.com:OCA/purchase-workflow.git -b 19.0 OCA/purchase-workflow
git@github.com:OCA/web.git               -b 19.0 OCA/web
git@github.com:miempresa/mis-addons.git  -b main  miempresa/mis-addons
```

### 4. Clonar los módulos

```bash
chmod +x setup.sh
./setup.sh
```

### 5. Levantar

```bash
docker compose up -d --build
```

## addons_path

El `entrypoint.sh` construye el `addons_path` automáticamente en cada arranque escaneando la estructura `addons/ORG/repo`. Los módulos Enterprise (`ee-addons/enterprise`) se añaden siempre al final.

Ejemplo: si `modules.conf` tiene `OCA/purchase-workflow` y `miempresa/mis-addons`, el path generado será:

```
/mnt/extra-addons/OCA/purchase-workflow,/mnt/extra-addons/miempresa/mis-addons,/mnt/extra-addons/enterprise
```

## Traefik

El `docker-compose.yml` usa `${PROJECT_NAME}` (definido en `.env`) para nombrar routers y servicios de Traefik, lo que permite correr varias instancias en el mismo host sin colisiones:

| Variable       | Descripción                                  |
|----------------|----------------------------------------------|
| `PROJECT_NAME` | Nombre único del proyecto (ej. `miodoo`)     |
| `MAIN_HOST`    | Dominio principal (ej. `odoo.midominio.com`) |

La red `traefik_net` debe existir como red externa en Docker:

```bash
docker network create traefik_net
```

## Actualizar módulos

```bash
./setup.sh          # hace git pull en cada módulo ya clonado
docker compose restart odoo
```
