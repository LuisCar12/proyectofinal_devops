# Comandos AWS CLI - Proyecto DevOps Learner Lab

> Ejecutar TODOS los comandos en la terminal de **AWS Cloud9** (sección 3 del proyecto), con la sesión del Learner Lab activa.
> Región: `us-east-1` (mantenerlo consistente para que todo se vea en la misma vista de la consola).

---

## Sección 8 — Verificar acceso y listar recursos

```bash
# Verifica que las credenciales del Lab están activas
aws sts get-caller-identity
# Debe aparecer voclabs como rol activo

# Listar instancias EC2
aws ec2 describe-instances \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name]' \
  --output table

# Listar buckets S3
aws s3 ls

# Listar stacks de CloudFormation
aws cloudformation list-stacks \
  --query 'StackSummaries[?StackStatus!=`DELETE_COMPLETE`].[StackName,StackStatus]' \
  --output table
```

---

## Sección 5 — Desplegar la plantilla CloudFormation

```bash
# Desde la raíz del repo, donde está template.yaml
aws cloudformation deploy \
  --stack-name devops-stack \
  --template-file template.yaml \
  --region us-east-1 \
  --capabilities CAPABILITY_NAMED_IAM

# Verificar outputs
aws cloudformation describe-stacks \
  --stack-name devops-stack \
  --query 'Stacks[0].Outputs' \
  --output table
```

---

## Sección 9 — S3 ciclo de vida y verificar cifrado

```bash
# Reemplaza BUCKET por el nombre real (devops-bucket-<ACCOUNT_ID>)
BUCKET=$(aws cloudformation describe-stacks --stack-name devops-stack \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)
echo "Bucket: $BUCKET"

# Verifica cifrado AES256 ya activo por defecto
aws s3api get-bucket-encryption --bucket "$BUCKET"

# Aplicar política de ciclo de vida (eliminar objetos a los 30 días)
cat > /tmp/lifecycle.json <<EOF
{
  "Rules": [{
    "ID": "EliminarObjetos30Dias",
    "Status": "Enabled",
    "Filter": { "Prefix": "" },
    "Expiration": { "Days": 30 }
  }]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET" \
  --lifecycle-configuration file:///tmp/lifecycle.json
```

---

## Sección 10 — Infraestructura de red (VPC, subredes, IGW, RT, SG)

```bash
# 1) Crear VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' --output text)
aws ec2 create-tags --resources "$VPC_ID" --tags Key=Name,Value=devops-vpc
echo "VPC: $VPC_ID"

# 2) Subredes
SUBNET_PUB=$(aws ec2 create-subnet --vpc-id "$VPC_ID" \
  --cidr-block 10.0.1.0/24 --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources "$SUBNET_PUB" --tags Key=Name,Value=devops-subnet-publica

SUBNET_PRIV=$(aws ec2 create-subnet --vpc-id "$VPC_ID" \
  --cidr-block 10.0.2.0/24 --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources "$SUBNET_PRIV" --tags Key=Name,Value=devops-subnet-privada

# 3) Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 create-tags --resources "$IGW_ID" --tags Key=Name,Value=devops-igw
aws ec2 attach-internet-gateway --vpc-id "$VPC_ID" --internet-gateway-id "$IGW_ID"

# 4) Tabla de rutas pública
RT_ID=$(aws ec2 create-route-table --vpc-id "$VPC_ID" \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-tags --resources "$RT_ID" --tags Key=Name,Value=devops-rt-publica
aws ec2 create-route --route-table-id "$RT_ID" \
  --destination-cidr-block 0.0.0.0/0 --gateway-id "$IGW_ID"
aws ec2 associate-route-table --subnet-id "$SUBNET_PUB" --route-table-id "$RT_ID"

# 5) Habilitar IP pública automática en la subred pública (necesario para SSM)
aws ec2 modify-subnet-attribute --subnet-id "$SUBNET_PUB" --map-public-ip-on-launch

# 6) Security Group
SG_ID=$(aws ec2 create-security-group --group-name devops-sg \
  --description "SG DevOps" --vpc-id "$VPC_ID" \
  --query 'GroupId' --output text)
aws ec2 create-tags --resources "$SG_ID" --tags Key=Name,Value=devops-sg

aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
  --protocol tcp --port 443 --cidr 0.0.0.0/0
# SSH SOLO desde la red interna (sección 12 - seguridad)
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
  --protocol tcp --port 22 --cidr 10.0.0.0/16

# 7) Lanzar instancia EC2 con LabInstanceProfile
AMI=$(aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query 'Parameter.Value' --output text)

INSTANCE=$(aws ec2 run-instances \
  --image-id "$AMI" --instance-type t2.micro \
  --subnet-id "$SUBNET_PUB" --security-group-ids "$SG_ID" \
  --iam-instance-profile Name=LabInstanceProfile \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=devops-ec2-vpc}]" \
  --query 'Instances[0].InstanceId' --output text)
echo "Instancia: $INSTANCE"

# Conexión: AWS Console → Systems Manager → Session Manager → seleccionar instancia → Iniciar sesión.
```

> Guarda los IDs (`VPC_ID`, `SUBNET_PUB`, `INSTANCE`, etc.) — se necesitan para capturas y para el diagrama.

---

## Sección 11 — Monitoreo CloudWatch

```bash
# Asume que ya tienes la INSTANCE_ID de la sección 5 (CloudFormation)
INSTANCE_ID=$(aws cloudformation describe-stacks --stack-name devops-stack \
  --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" --output text)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Alarma de CPU > 80%
aws cloudwatch put-metric-alarm \
  --alarm-name devops-cpu-alta \
  --alarm-description "Alarma cuando CPU > 80% por 2 periodos de 5 min" \
  --metric-name CPUUtilization --namespace AWS/EC2 \
  --statistic Average --period 300 --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID \
  --treat-missing-data notBreaching

# Dashboard con 2 widgets (CPU EC2 + Objetos S3)
BUCKET=$(aws cloudformation describe-stacks --stack-name devops-stack \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)

cat > /tmp/dashboard.json <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0, "y": 0, "width": 12, "height": 6,
      "properties": {
        "metrics": [["AWS/EC2","CPUUtilization","InstanceId","$INSTANCE_ID"]],
        "period": 300, "stat": "Average", "region": "us-east-1",
        "title": "CPU EC2 - $INSTANCE_ID"
      }
    },
    {
      "type": "metric",
      "x": 12, "y": 0, "width": 12, "height": 6,
      "properties": {
        "metrics": [["AWS/S3","NumberOfObjects","BucketName","$BUCKET","StorageType","AllStorageTypes"]],
        "period": 86400, "stat": "Average", "region": "us-east-1",
        "title": "Objetos en S3 - $BUCKET"
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
  --dashboard-name devops-dashboard \
  --dashboard-body file:///tmp/dashboard.json

# Bucket de logs de Config
aws s3 mb s3://devops-config-logs-$ACCOUNT_ID --region us-east-1

# Configuration recorder (sin delivery channel - LabRole no lo permite)
aws configservice put-configuration-recorder \
  --configuration-recorder name=default,roleARN=arn:aws:iam::$ACCOUNT_ID:role/LabRole,recordingGroup="{allSupported=true,includeGlobalResourceTypes=false}"

# Log group en CloudWatch Logs
aws logs create-log-group --log-group-name /devops/ec2-logs

# Instalar agente CloudWatch en EC2 via SSM
CMD_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --comment "Instalar agente CloudWatch" \
  --parameters 'commands=["sudo dnf install -y amazon-cloudwatch-agent","sudo systemctl enable amazon-cloudwatch-agent","sudo systemctl start amazon-cloudwatch-agent"]' \
  --query 'Command.CommandId' --output text)

# Verificar resultado (espera 30s antes)
sleep 30
aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID"
```

---

## Sección 12 — Seguridad

```bash
# Verificar límite Lambda
aws lambda get-account-settings

# Las reglas restrictivas de SG ya quedaron aplicadas en la sección 10:
# - HTTP 80 / HTTPS 443 → 0.0.0.0/0
# - SSH 22 → 10.0.0.0/16 (solo red interna)
```

---

## Sección 13 — Lambda + API Gateway (microservicio)

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1) Empaquetar la Lambda
cd lambda
zip lambda_function.zip lambda_function.py
cd ..

# 2) Crear la función
aws lambda create-function \
  --function-name microservicio-devops \
  --runtime python3.9 \
  --role arn:aws:iam::$ACCOUNT_ID:role/LabRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda/lambda_function.zip \
  --region us-east-1

# 3) Limitar concurrencia a 10
aws lambda put-function-concurrency \
  --function-name microservicio-devops \
  --reserved-concurrent-executions 10

# 4) Probar Lambda
aws lambda invoke \
  --function-name microservicio-devops \
  --region us-east-1 \
  output.json && cat output.json

# 5) Crear API REST
API_ID=$(aws apigateway create-rest-api --name devops-api \
  --query 'id' --output text)
ROOT_ID=$(aws apigateway get-resources --rest-api-id "$API_ID" \
  --query 'items[0].id' --output text)

# 6) Recurso /microservicio
RES_ID=$(aws apigateway create-resource \
  --rest-api-id "$API_ID" --parent-id "$ROOT_ID" \
  --path-part microservicio \
  --query 'id' --output text)

# 7) Método GET
aws apigateway put-method \
  --rest-api-id "$API_ID" --resource-id "$RES_ID" \
  --http-method GET --authorization-type NONE

# 8) Integración con Lambda
aws apigateway put-integration \
  --rest-api-id "$API_ID" --resource-id "$RES_ID" \
  --http-method GET --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:microservicio-devops/invocations

# 9) Permiso a API Gateway para invocar Lambda
aws lambda add-permission \
  --function-name microservicio-devops \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$ACCOUNT_ID:$API_ID/*/GET/microservicio"

# 10) Desplegar la API
aws apigateway create-deployment \
  --rest-api-id "$API_ID" --stage-name prod

# 11) Probar el microservicio
curl "https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/microservicio"
```

---

## Limpieza al terminar la sesión

```bash
# Borrar stack CloudFormation (esto limpia EC2 y S3 del template)
aws cloudformation delete-stack --stack-name devops-stack

# Borrar Lambda
aws lambda delete-function --function-name microservicio-devops

# Borrar API Gateway
aws apigateway delete-rest-api --rest-api-id "$API_ID"

# Borrar tabla DynamoDB
aws dynamodb delete-table --table-name devops-tabla

# Borrar VPC y todos sus componentes (cuidado: hay que detach IGW antes)
# Más fácil: hacerlo desde la consola en orden inverso (instancias → SG → subredes → IGW → VPC).
```
