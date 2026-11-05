# Deployment Guide

Complete deployment documentation for the Flask React Todo App across multiple platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Platform-Specific Guides](#platform-specific-guides)
  - [AWS ECS Fargate](#aws-ecs-fargate)
  - [GCP Cloud Run](#gcp-cloud-run)
  - [Azure Container Apps](#azure-container-apps)
  - [Heroku](#heroku)
  - [Railway](#railway)
  - [VPS with Docker Compose](#vps-with-docker-compose)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### General Requirements

- Docker Engine 24.0+
- Docker Compose 2.20+
- Git 2.40+
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Cloud Provider CLI Tools

Install the CLI tools for your target platform:

```bash
# AWS
pip install awscli

# GCP
curl https://sdk.cloud.google.com | bash

# Azure
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Heroku
npm install -g heroku

# Railway
npm install -g @railway/cli
```

### Required Secrets

Create the following secrets in your CI/CD platform:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Flask secret key | `your-secret-key-here` |
| `JWT_SECRET_KEY` | JWT signing key | `your-jwt-secret-key` |
| `FLASK_ENV` | Environment mode | `production` |

---

## Environment Variables

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/todoapp

# Flask
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# Security
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=604800

# CORS
CORS_ORIGINS=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_DEFAULT=100/hour
RATE_LIMIT_AUTH=10/minute
```

### Frontend Environment Variables

```bash
# API Configuration
VITE_API_URL=https://api.yourdomain.com/api
VITE_APP_NAME=Todo App
VITE_APP_VERSION=1.0.0

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_SENTRY_DSN=
```

### Docker Compose Environment

```bash
# Create .env file for docker-compose
cat > .env << EOF
# Database
DB_USER=todoapp
DB_PASSWORD=secure-password-here
DB_NAME=todoapp

# Backend
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Deployment
DOMAIN=yourdomain.com
EMAIL=admin@yourdomain.com
EOF
```

---

## Platform-Specific Guides

### AWS ECS Fargate

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      VPC                                │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Application Load Balancer            │  │
│  │                   (Port 80/443)                   │  │
│  └──────────────────────┬──────────────────────────┘  │
│                         │                              │
│  ┌──────────────────────┴──────────────────────────┐  │
│  │              ECS Cluster (Fargate)              │  │
│  │  ┌─────────────┐        ┌─────────────┐         │  │
│  │  │  Backend    │        │  Frontend   │         │  │
│  │  │  Service    │        │  Service    │         │  │
│  │  │  (Port 5000)│        │  (Port 80)  │         │  │
│  │  └─────────────┘        └─────────────┘         │  │
│  └───────────────────────────────────────────────────┘  │
│                         │                              │
│  ┌──────────────────────┴──────────────────────────┐  │
│  │              RDS PostgreSQL                      │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Step 1: Create ECR Repositories

```bash
# Login to AWS
aws configure

# Create ECR repositories
aws ecr create-repository --repository-name flask-react-todo-backend
aws ecr create-repository --repository-name flask-react-todo-frontend

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
```

#### Step 2: Build and Push Images

```bash
# Build backend
docker build -t flask-react-todo-backend ./backend

# Tag and push backend
docker tag flask-react-todo-backend:latest \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/flask-react-todo-backend:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/flask-react-todo-backend:latest

# Build frontend
docker build -t flask-react-todo-frontend ./frontend

# Tag and push frontend
docker tag flask-react-todo-frontend:latest \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/flask-react-todo-frontend:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/flask-react-todo-frontend:latest
```

#### Step 3: Create Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "flask-react-todo",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/flask-react-todo-backend:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "FLASK_ENV", "value": "production"},
        {"name": "DATABASE_URL", "value": "postgresql://..."}
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/flask-react-todo",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    },
    {
      "name": "frontend",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/flask-react-todo-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "dependsOn": [
        {
          "containerName": "backend",
          "condition": "START"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/flask-react-todo",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "frontend"
        }
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

#### Step 4: Create ECS Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name flask-react-todo

# Create service
aws ecs create-service \
  --cluster flask-react-todo \
  --service-name flask-react-todo-service \
  --task-definition flask-react-todo \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=frontend,containerPort=80"
```

#### Step 5: Configure Application Load Balancer

```bash
# Create target group
aws elbv2 create-target-group \
  --name flask-react-todo-tg \
  --protocol HTTP \
  --port 80 \
  --vpc-id vpc-xxx \
  --target-type ip

# Create load balancer
aws elbv2 create-load-balancer \
  --name flask-react-todo-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

---

### GCP Cloud Run

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   GCP Project                           │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Cloud Load Balancing               │   │
│  │              (Global HTTPS LB)                  │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         │                              │
│  ┌──────────────────────┴──────────────────────────┐   │
│  │              Cloud Run Services                 │   │
│  │  ┌─────────────┐        ┌─────────────┐         │   │
│  │  │  Backend    │        │  Frontend   │         │   │
│  │  │  Service    │        │  Service    │         │   │
│  │  │  (Region)   │        │  (Region)   │         │   │
│  │  └─────────────┘        └─────────────┘         │   │
│  └───────────────────────────────────────────────────┘   │
│                         │                              │
│  ┌──────────────────────┴──────────────────────────┐   │
│  │              Cloud SQL (PostgreSQL)           │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### Step 1: Enable APIs and Configure gcloud

```bash
# Login to GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

#### Step 2: Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create todo-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB

# Create database
gcloud sql databases create todoapp --instance=todo-postgres

# Create user
gcloud sql users create todoapp \
  --instance=todo-postgres \
  --password=YOUR_SECURE_PASSWORD

# Get connection name
export DB_CONNECTION_NAME=$(gcloud sql instances describe todo-postgres --format='value(connectionName)')
```

#### Step 3: Store Secrets in Secret Manager

```bash
# Create secrets
echo -n "your-secret-key" | gcloud secrets create flask-secret-key --data-file=-
echo -n "your-jwt-secret" | gcloud secrets create jwt-secret-key --data-file=-
echo -n "postgresql://todoapp:password@/todoapp?host=/cloudsql/$DB_CONNECTION_NAME" | \
  gcloud secrets create database-url --data-file=-
```

#### Step 4: Build and Push Images

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/flask-react-todo-backend:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/flask-react-todo-backend:latest'
      - './backend'

  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/flask-react-todo-frontend:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/flask-react-todo-frontend:latest'
      - './frontend'

  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/flask-react-todo-backend:$COMMIT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/flask-react-todo-frontend:$COMMIT_SHA']

  # Deploy backend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'flask-react-todo-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/flask-react-todo-backend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-secrets'
      - 'SECRET_KEY=flask-secret-key:latest,JWT_SECRET_KEY=jwt-secret-key:latest,DATABASE_URL=database-url:latest'
      - '--add-cloudsql-instances'
      - '$DB_CONNECTION_NAME'

  # Deploy frontend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'flask-react-todo-frontend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/flask-react-todo-frontend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

images:
  - 'gcr.io/$PROJECT_ID/flask-react-todo-backend:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/flask-react-todo-frontend:$COMMIT_SHA'
```

Submit build:

```bash
gcloud builds submit --config cloudbuild.yaml
```

#### Step 5: Configure Cloud Build Trigger

```bash
# Create trigger
gcloud beta builds triggers create github \
  --repo-name=flask-react-todo \
  --repo-owner=your-github-username \
  --branch-pattern='^main$' \
  --build-config='cloudbuild.yaml'
```

#### Step 6: Custom Domain Mapping

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service flask-react-todo-frontend \
  --domain todo.yourdomain.com \
  --region us-central1

# Verify domain ownership and configure DNS as instructed
```

---

### Azure Container Apps

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Azure Subscription                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Container Apps Environment           │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────────┐     │   │
│  │  │              Container Apps             │     │   │
│  │  │  ┌─────────┐      ┌─────────┐         │     │   │
│  │  │  │ Backend │      │ Frontend│         │     │   │
│  │  │  │ (5000)  │      │ (80)    │         │     │   │
│  │  │  └────┬────┘      └────┬────┘         │     │   │
│  │  │       │                │                │     │   │
│  │  │       └────────────────┘                │     │   │
│  │  │              Ingress                      │     │   │
│  │  └─────────────────────────────────────────┘     │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────────┐     │   │
│  │  │         Azure Database for PostgreSQL   │     │   │
│  │  └─────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Azure Container Registry             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### Step 1: Create Resource Group and ACR

```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name flask-react-todo-rg \
  --location eastus

# Create Container Registry
az acr create \
  --resource-group flask-react-todo-rg \
  --name flaskreacttodoacr \
  --sku Basic \
  --admin-enabled true

# Get ACR credentials
az acr credential show --name flaskreacttodoacr --query "passwords[0].value"
```

#### Step 2: Build Images with ACR Tasks

```bash
# Build backend
az acr build \
  --registry flaskreacttodoacr \
  --image flask-react-todo-backend:latest \
  --file backend/Dockerfile \
  ./backend

# Build frontend
az acr build \
  --registry flaskreacttodoacr \
  --image flask-react-todo-frontend:latest \
  --file frontend/Dockerfile \
  ./frontend
```

#### Step 3: Create PostgreSQL Database

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group flask-react-todo-rg \
  --name flask-react-todo-db \
  --location eastus \
  --admin-user todoapp \
  --admin-password YOUR_SECURE_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15

# Create database
az postgres flexible-server db create \
  --resource-group flask-react-todo-rg \
  --server-name flask-react-todo-db \
  --database-name todoapp

# Allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group flask-react-todo-rg \
  --name flask-react-todo-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### Step 4: Create Container Apps Environment

```bash
# Create Container Apps environment
az containerapp env create \
  --name flask-react-todo-env \
  --resource-group flask-react-todo-rg \
  --location eastus

# Get ACR login server
export ACR_LOGIN_SERVER=$(az acr show --name flaskreacttodoacr --query loginServer --output tsv)
```

#### Step 5: Deploy Backend Container App

```bash
# Create backend container app
az containerapp create \
  --name flask-react-todo-backend \
  --resource-group flask-react-todo-rg \
  --environment flask-react-todo-env \
  --image $ACR_LOGIN_SERVER/flask-react-todo-backend:latest \
  --target-port 5000 \
  --ingress external \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $(az acr credential show --name flaskreacttodoacr --query "username" -o tsv) \
  --registry-password $(az acr credential show --name flaskreacttodoacr --query "passwords[0].value" -o tsv) \
  --env-vars "FLASK_ENV=production" \
  --secrets "db-url=postgresql://todoapp:PASSWORD@flask-react-todo-db.postgres.database.azure.com:5432/todoapp" \
             "secret-key=YOUR_SECRET_KEY" \
             "jwt-secret=YOUR_JWT_SECRET" \
  --environment-variables "DATABASE_URL=secretref:db-url" \
                           "SECRET_KEY=secretref:secret-key" \
                           "JWT_SECRET_KEY=secretref:jwt-secret"
```

#### Step 6: Deploy Frontend Container App

```bash
# Get backend URL
export BACKEND_URL=$(az containerapp show \
  --name flask-react-todo-backend \
  --resource-group flask-react-todo-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

# Create frontend container app
az containerapp create \
  --name flask-react-todo-frontend \
  --resource-group flask-react-todo-rg \
  --environment flask-react-todo-env \
  --image $ACR_LOGIN_SERVER/flask-react-todo-frontend:latest \
  --target-port 80 \
  --ingress external \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $(az acr credential show --name flaskreacttodoacr --query "username" -o tsv) \
  --registry-password $(az acr credential show --name flaskreacttodoacr --query "passwords[0].value" -o tsv) \
  --env-vars "VITE_API_URL=https://$BACKEND_URL/api"
```

#### Step 7: Bicep Template (Infrastructure as Code)

Create `main.bicep`:

```bicep
param location string = resourceGroup().location
param environmentName string = 'flask-react-todo-env'
param acrName string = 'flaskreacttodoacr'
param dbServerName string = 'flask-react-todo-db'
param dbName string = 'todoapp'

// Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// PostgreSQL Server
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: dbServerName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    storage: {
      storageSizeGB: 32
    }
    administratorLogin: 'todoapp'
    administratorPassword: 'YOUR_SECURE_PASSWORD'
  }
}

// Container Apps Environment
resource env 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  properties: {}
}

// Backend Container App
resource backend 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'flask-react-todo-backend'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 5000
      }
      secrets: [
        {
          name: 'database-url'
          value: 'postgresql://todoapp:PASSWORD@${dbServerName}.postgres.database.azure.com:5432/${dbName}'
        }
        {
          name: 'secret-key'
          value: 'YOUR_SECRET_KEY'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: '${acr.properties.loginServer}/flask-react-todo-backend:latest'
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'FLASK_ENV'
              value: 'production'
            }
          ]
          resources: {
            cpu: 0.5
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// Frontend Container App
resource frontend 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'flask-react-todo-frontend'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: '${acr.properties.loginServer}/flask-react-todo-frontend:latest'
          env: [
            {
              name: 'VITE_API_URL'
              value: 'https://${backend.properties.configuration.ingress.fqdn}/api'
            }
          ]
          resources: {
            cpu: 0.25
            memory: '512Mi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
      }
    }
  }
}

output backendUrl string = backend.properties.configuration.ingress.fqdn
output frontendUrl string = frontend.properties.configuration.ingress.fqdn
```

Deploy with Bicep:

```bash
az deployment group create \
  --resource-group flask-react-todo-rg \
  --template-file main.bicep
```

---

### Heroku

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Heroku Platform                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Heroku Dynos                       │   │
│  │  ┌─────────────┐        ┌─────────────┐         │   │
│  │  │  Web Dyno   │        │  Web Dyno   │         │   │
│  │  │  (Backend)  │        │  (Frontend) │         │   │
│  │  └─────────────┘        └─────────────┘         │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                              │
│  ┌──────────────────────┴──────────────────────────┐   │
│  │              Heroku Postgres                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Heroku Redis (Optional)            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### Step 1: Install Heroku CLI and Login

```bash
# Install Heroku CLI
npm install -g heroku

# Login
heroku login
```

#### Step 2: Create Heroku Apps

```bash
# Create backend app
heroku create flask-react-todo-api --region us

# Create frontend app
heroku create flask-react-todo-web --region us
```

#### Step 3: Add PostgreSQL Addon

```bash
# Add PostgreSQL to backend
heroku addons:create heroku-postgresql:mini --app flask-react-todo-api

# Get database URL
heroku config:get DATABASE_URL --app flask-react-todo-api
```

#### Step 4: Configure Environment Variables

```bash
# Backend environment variables
heroku config:set FLASK_ENV=production --app flask-react-todo-api
heroku config:set SECRET_KEY=$(openssl rand -hex 32) --app flask-react-todo-api
heroku config:set JWT_SECRET_KEY=$(openssl rand -hex 32) --app flask-react-todo-api

# Frontend environment variables
heroku config:set VITE_API_URL=https://flask-react-todo-api.herokuapp.com/api --app flask-react-todo-web
```

#### Step 5: Create Procfile

Create `backend/Procfile`:

```
web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 wsgi:app
release: flask db upgrade
```

Create `frontend/Procfile`:

```
web: npm run preview -- --port $PORT --host
```

#### Step 6: Create app.json

Create `app.json`:

```json
{
  "name": "Flask React Todo App",
  "description": "A full-stack todo application with Flask backend and React frontend",
  "repository": "https://github.com/yourusername/flask-react-todo",
  "keywords": ["flask", "react", "todo", "postgresql"],
  "addons": [
    {
      "plan": "heroku-postgresql:mini",
      "as": "DATABASE"
    }
  ],
  "env": {
    "FLASK_ENV": {
      "description": "Flask environment mode",
      "value": "production"
    },
    "SECRET_KEY": {
      "description": "Flask secret key for session management",
      "generator": "secret"
    },
    "JWT_SECRET_KEY": {
      "description": "JWT secret key for token signing",
      "generator": "secret"
    }
  },
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ],
  "scripts": {
    "postdeploy": "flask db upgrade"
  }
}
```

#### Step 7: Deploy with Git

```bash
# Deploy backend
cd backend
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a flask-react-todo-api
git push heroku main

# Deploy frontend
cd ../frontend
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a flask-react-todo-web
git push heroku main
```

#### Step 8: GitHub Actions Integration

Create `.github/workflows/heroku-deploy.yml`:

```yaml
name: Deploy to Heroku

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: akhileshns/heroku-deploy@v3.13.15
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: flask-react-todo-api
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
          appdir: backend

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: akhileshns/heroku-deploy@v3.13.15
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: flask-react-todo-web
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
          appdir: frontend
```

---

### Railway

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Railway Platform                      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Railway Services                   │   │
│  │  ┌─────────────┐        ┌─────────────┐         │   │
│  │  │  Backend    │        │  Frontend   │         │   │
│  │  │  Service    │        │  Service    │         │   │
│  │  └────┬────────┘        └────┬────────┘         │   │
│  │       │                      │                  │   │
│  │       └──────────────────────┘                  │   │
│  │              Railway Network                    │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                              │
│  ┌──────────────────────┴──────────────────────────┐   │
│  │              Railway PostgreSQL                 │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

#### Step 2: Create railway.json

Create `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 4 wsgi:app",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

#### Step 3: Initialize Project

```bash
# Create new project
railway init --name flask-react-todo

# Add PostgreSQL plugin
railway add --database postgres

# Link to project
railway link
```

#### Step 4: Configure Environment Variables

```bash
# Set environment variables
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set JWT_SECRET_KEY=$(openssl rand -hex 32)

# Database URL is automatically set by Railway
# DATABASE_URL=postgresql://...
```

Or create `railway.toml`:

```toml
[environments.production]
  [environments.production.deploy]
    healthcheckPath = "/api/health"
    healthcheckTimeout = 30

  [environments.production.variables]
    FLASK_ENV = "production"
    PYTHON_VERSION = "3.11"
```

#### Step 5: Deploy

```bash
# Deploy from current directory
railway up

# Deploy specific service
railway up --service backend

# View logs
railway logs

# Open deployed app
railway open
```

#### Step 6: Custom Domain

```bash
# Add custom domain
railway domain add todo.yourdomain.com

# Configure DNS with the provided CNAME record
```

---

### VPS with Docker Compose

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   VPS (Ubuntu 22.04)                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Docker Compose Stack               │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │              Nginx Proxy                │   │   │
│  │  │           (Port 80/443)                 │   │   │
│  │  └───────────────────┬─────────────────────┘   │   │
│  │                      │                        │   │
│  │  ┌───────────────────┴─────────────────────┐   │   │
│  │  │              Application Services       │   │   │
│  │  │  ┌─────────┐      ┌─────────┐          │   │   │
│  │  │  │ Backend │      │ Frontend│          │   │   │
│  │  │  │ (5000)  │      │ (80)    │          │   │   │
│  │  │  └─────────┘      └─────────┘          │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  │                      │                        │   │
│  │  ┌───────────────────┴─────────────────────┐   │   │
│  │  │              PostgreSQL                 │   │   │
│  │  │           (Port 5432)                   │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Let's Encrypt SSL                  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### Step 1: Provision VPS

Recommended VPS specifications:

- **CPU**: 2 vCPU
- **RAM**: 4 GB
- **Storage**: 50 GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: Public IP, ports 22, 80, 443 open

Providers: DigitalOcean, Linode, Vultr, AWS EC2, Hetzner

#### Step 2: Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Re-login for group changes
newgrp docker
```

#### Step 3: Create Docker Compose Configuration

Create `/opt/flask-react-todo/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-todoapp}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
      POSTGRES_DB: ${DB_NAME:-todoapp}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-todoapp}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - app-network

  backend:
    image: ${REGISTRY:-ghcr.io}/${IMAGE_NAME:-yourusername/flask-react-todo}-backend:${TAG:-latest}
    environment:
      DATABASE_URL: postgresql://${DB_USER:-todoapp}:${DB_PASSWORD:-changeme}@db:5432/${DB_NAME:-todoapp}
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      FLASK_ENV: production
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-network

  frontend:
    image: ${REGISTRY:-ghcr.io}/${IMAGE_NAME:-yourusername/flask-react-todo}-frontend:${TAG:-latest}
    environment:
      VITE_API_URL: /api
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - certbot-data:/etc/letsencrypt
      - certbot-www:/var/www/certbot
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - app-network

  certbot:
    image: certbot/certbot
    volumes:
      - certbot-data:/etc/letsencrypt
      - certbot-www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - app-network

volumes:
  postgres_data:
  certbot-data:
  certbot-www:

networks:
  app-network:
    driver: bridge
```

#### Step 4: Configure Nginx

Create `/opt/flask-react-todo/nginx/nginx.conf`:

```nginx
upstream backend {
    server backend:5000;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    server_name ${DOMAIN};
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};
    
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/${DOMAIN}/chain.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

#### Step 5: SSL Certificate with Let's Encrypt

```bash
# Create directories
sudo mkdir -p /opt/flask-react-todo/nginx/ssl
sudo mkdir -p /opt/flask-react-todo/certbot-data
sudo mkdir -p /opt/flask-react-todo/certbot-www

# Get initial certificate
docker run -it --rm \
  -v /opt/flask-react-todo/certbot-data:/etc/letsencrypt \
  -v /opt/flask-react-todo/certbot-www:/var/www/certbot \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  --preferred-challenges http \
  --agree-tos \
  --email admin@${DOMAIN} \
  -d ${DOMAIN}
```

#### Step 6: Create Environment File

Create `/opt/flask-react-todo/.env`:

```bash
# Database
DB_USER=todoapp
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=todoapp

# Application
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Deployment
DOMAIN=yourdomain.com
REGISTRY=ghcr.io
IMAGE_NAME=yourusername/flask-react-todo
TAG=latest
```

#### Step 7: Create Systemd Service

Create `/etc/systemd/system/flask-react-todo.service`:

```ini
[Unit]
Description=Flask React Todo App
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/flask-react-todo
Environment=COMPOSE_PROJECT_NAME=flask-react-todo

ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
ExecReload=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d --build

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable flask-react-todo
sudo systemctl start flask-react-todo
```

#### Step 8: Deploy Script

Create `/opt/flask-react-todo/scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

# Configuration
APP_DIR="/opt/flask-react-todo"
BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment...${NC}"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo -e "${YELLOW}Creating database backup...${NC}"
docker exec flask-react-todo_db_1 pg_dump -U todoapp todoapp > $BACKUP_DIR/backup_$TIMESTAMP.sql || true

# Pull latest images
echo -e "${YELLOW}Pulling latest images...${NC}"
cd $APP_DIR
docker-compose -f docker-compose.prod.yml pull

# Deploy with zero downtime
echo -e "${YELLOW}Deploying new version...${NC}"
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale backend=2 backend
sleep 10

# Health check
echo -e "${YELLOW}Running health checks...${NC}"
if curl -f http://localhost/api/health; then
    echo -e "${GREEN}Health check passed!${NC}"
    docker-compose -f docker-compose.prod.yml up -d --no-deps --scale backend=1 backend
else
    echo -e "${RED}Health check failed! Rolling back...${NC}"
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d
    exit 1
fi

# Cleanup old images
echo -e "${YELLOW}Cleaning up old images...${NC}"
docker image prune -f

echo -e "${GREEN}Deployment completed successfully!${NC}"
```

Make executable:

```bash
chmod +x /opt/flask-react-todo/scripts/deploy.sh
```

#### Step 9: GitHub Actions for VPS Deployment

Create `.github/workflows/vps-deploy.yml`:

```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USERNAME }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/flask-react-todo
            export TAG=${{ github.ref_name }}
            ./scripts/deploy.sh
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failures

**Symptoms**: Application fails to start with database connection errors

**Solutions**:

```bash
# Check database container logs
docker-compose logs db

# Verify database is healthy
docker-compose exec db pg_isready -U todoapp

# Check connection string format
# Format: postgresql://user:password@host:port/database
```

#### SSL Certificate Issues

**Symptoms**: HTTPS not working, certificate errors

**Solutions**:

```bash
# Test certificate renewal
docker run -it --rm \
  -v /opt/flask-react-todo/certbot-data:/etc/letsencrypt \
  certbot/certbot renew --dry-run

# Check certificate expiry
openssl x509 -in /opt/flask-react-todo/certbot-data/live/yourdomain.com/cert.pem -noout -dates
```

#### Container Health Check Failures

**Symptoms**: Containers restarting continuously

**Solutions**:

```bash
# Check container logs
docker-compose logs --tail 100 backend

# Verify health endpoint
curl http://localhost:5000/api/health

# Check resource limits
docker stats
```

#### Memory Issues

**Symptoms**: OOM (Out of Memory) errors

**Solutions**:

```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Limit container memory
docker-compose -f docker-compose.prod.yml up -d --memory="512m" backend
```

### Platform-Specific Troubleshooting

#### AWS ECS

```bash
# Check service events
aws ecs describe-services \
  --cluster flask-react-todo \
  --services flask-react-todo-service \
  --query 'services[0].events'

# View CloudWatch logs
aws logs tail /ecs/flask-react-todo --follow
```

#### GCP Cloud Run

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Check service status
gcloud run services describe flask-react-todo-backend --region us-central1
```

#### Azure Container Apps

```bash
# View logs
az containerapp logs show \
  --name flask-react-todo-backend \
  --resource-group flask-react-todo-rg \
  --follow

# Check revision status
az containerapp revision list \
  --name flask-react-todo-backend \
  --resource-group flask-react-todo-rg
```

### Performance Optimization

#### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_todos_user_id ON todos(user_id);
CREATE INDEX idx_todos_status ON todos(status);
CREATE INDEX idx_todos_created_at ON todos(created_at DESC);

-- Analyze tables
ANALYZE todos;
ANALYZE users;
```

#### Nginx Optimization

```nginx
# Add to nginx.conf
worker_processes auto;
worker_connections 4096;

# Enable caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=STATIC:10m inactive=24h max_size=1g;

location /static/ {
    proxy_cache STATIC;
    proxy_cache_valid 200 1d;
    expires 1d;
}
```

---

## Security Checklist

- [ ] Change default database passwords
- [ ] Use strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules (only allow ports 22, 80, 443)
- [ ] Set up automated security updates
- [ ] Enable database encryption at rest
- [ ] Configure backup encryption
- [ ] Set up log monitoring and alerting
- [ ] Implement rate limiting
- [ ] Use non-root containers

---

## Support

For additional support:

- GitHub Issues: https://github.com/yourusername/flask-react-todo/issues
- Documentation: https://docs.flask-react-todo.example.com
- Email: support@flask-react-todo.example.com
