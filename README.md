# Proyecto DevOps — Soluciones Tecnológicas del Futuro

Implementación de un flujo DevOps completo en **AWS Learner Lab** que cubre infraestructura como código, contenedores, CI/CD, monitoreo, seguridad y microservicios.

## Estructura del repositorio

```
.
├── .github/workflows/deploy.yml   # Pipeline CI/CD (test + deploy)
├── docker/
│   ├── app.py                     # App Flask en puerto 5000
│   ├── Dockerfile                 # Multi-stage build
│   ├── docker-compose.yml         # Servicios web + nginx
│   ├── nginx.conf
│   └── requirements.txt
├── lambda/
│   └── lambda_function.py         # Microservicio
├── docs/
│   └── comandos-aws.md            # Cheatsheet completo de comandos CLI
├── automatizacion.py              # boto3: EC2, CloudWatch, S3, ASG
├── s3_automatizacion.py           # boto3: subir y listar objetos
├── dynamodb_operaciones.py        # boto3: CRUD en DynamoDB
├── template.yaml                  # CloudFormation: EC2 + S3
├── setup.sh                       # Instala dependencias del entorno
├── usuarios.sh                    # Gestión de usuarios y permisos
├── limpieza_logs.sh               # Limpieza de logs (cron diario)
└── .gitignore
```

## Mapeo a las secciones del proyecto

| Sección | Contenido | Archivos clave |
|--------|-----------|----------------|
| 1 | Presentación principios DevOps | (entrega aparte) |
| 2 | Repositorio GitHub + ramas + protección | `.gitignore` |
| 3 | Entorno Cloud9 + scripts Bash | `setup.sh`, `usuarios.sh`, `limpieza_logs.sh` |
| 4 | Automatización Python con boto3 | `automatizacion.py` |
| 5 | Plantilla CloudFormation | `template.yaml` |
| 6 | Imagen Docker + docker-compose | `docker/` |
| 7 | Pipeline CI/CD GitHub Actions | `.github/workflows/deploy.yml` |
| 8 | Verificación cuenta y recursos AWS | `docs/comandos-aws.md` |
| 9 | Almacenamiento S3 + DynamoDB | `s3_automatizacion.py`, `dynamodb_operaciones.py` |
| 10 | VPC, subredes, IGW, SG | `docs/comandos-aws.md` |
| 11 | Monitoreo CloudWatch | `docs/comandos-aws.md` |
| 12 | Seguridad: LabRole, SG restrictivo | `docs/comandos-aws.md` |
| 13 | Microservicios Lambda + API Gateway | `lambda/`, `docs/comandos-aws.md` |

## Orden de ejecución sugerido

> Los pasos numerados se ejecutan en **AWS Cloud9** salvo que se indique lo contrario.

### Fase 1 — Repositorio (GitHub navegador + terminal del Lab)

1. Crear repo público en GitHub con README, sin .gitignore ni licencia.
2. Generar PAT (Settings → Developer settings → Tokens classic) con scopes `repo` y `workflow`.
3. Clonar desde la terminal del Learner Lab usando HTTPS y el PAT como contraseña.
4. Crear rama `develop` desde `main`.
5. Configurar Ruleset en `main`: *Require a pull request before merging* + *Block force pushes*.

### Fase 2 — Entorno Cloud9

```bash
# Verificar credenciales
aws sts get-caller-identity   # debe mostrar voclabs

# Iniciar Docker
sudo service docker start
sudo docker run hello-world

# Clonar el repo dentro de ~/environment
cd ~/environment
git clone https://github.com/<usuario>/<repo>.git
cd <repo>
git checkout -b develop

# Ejecutar scripts de setup
bash setup.sh
sudo bash usuarios.sh

# Programar la limpieza de logs (medianoche todos los días)
chmod +x limpieza_logs.sh
(crontab -l 2>/dev/null; echo "0 0 * * * $(pwd)/limpieza_logs.sh") | crontab -
```

### Fase 3 — CloudFormation y boto3

```bash
# Desplegar infra base
aws cloudformation deploy \
  --stack-name devops-stack \
  --template-file template.yaml \
  --region us-east-1 \
  --capabilities CAPABILITY_NAMED_IAM

# Verificar outputs
aws cloudformation describe-stacks --stack-name devops-stack \
  --query 'Stacks[0].Outputs' --output table

# Probar scripts boto3
python3 automatizacion.py
python3 s3_automatizacion.py
python3 dynamodb_operaciones.py
```

### Fase 4 — Docker

```bash
# Instalar docker-compose (no viene preinstalado)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version

# Construir y levantar contenedores manualmente (buildx en Cloud9 es antiguo)
cd docker
sudo docker build -t docker-web .
sudo docker network create devops_network
sudo docker run -d --name web -p 5000:5000 --network devops_network docker-web
sudo docker run -d --name nginx -p 80:80 --network devops_network nginx:latest
sudo docker ps
cd ..
```

### Fase 5 — Pipeline CI/CD

1. En GitHub: **Settings → Secrets and variables → Actions**, agregar:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN`

   > Los valores salen del botón **AWS Details** del Learner Lab. Se actualizan **cada nueva sesión**.

2. Push a `develop` y abrir PR a `main`. Al hacer merge se dispara el workflow.

3. Verificar en la pestaña **Actions** que `test` y `deploy` pasaron en verde.

### Fases 6 a 8 — Red, monitoreo, seguridad y microservicios

Ver el archivo [`docs/comandos-aws.md`](docs/comandos-aws.md) con todos los comandos paso a paso.

## Recordatorios del Learner Lab

- Las credenciales **expiran al terminar la sesión**. Renovar los 3 secrets en GitHub al iniciar una nueva sesión.
- Usar siempre el rol `LabRole` y el perfil `LabInstanceProfile`. **No crear roles ni usuarios IAM nuevos.**
- Región fijada en `us-east-1`.
- Tipos de instancia permitidos: `t2.micro`, `t3.micro`.
- AWS CodeCommit ya **no acepta nuevos clientes**, por eso el pipeline corre en GitHub Actions.

## Convención de commits

- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` cambios en documentación
- `chore:` tareas de mantenimiento

Ejemplo: `feat: añadir script de limpieza de logs con cron`
