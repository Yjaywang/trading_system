# 🚀 Trading System

Crawls futures & options data, analyzes it, generates trading signals, and executes trades.

---

## 🧱 Tech Stack

- **Backend**: Django + Celery  
- **Queue/Cache**: Redis  
- **Web Server**: Nginx  
- **Containerized**: Docker, Docker Compose  
- **Dev Environment**: VS Code + Dev Containers

---

## 🧰 Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Visual Studio Code](https://code.visualstudio.com/)
- [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Git

---

## ⚙️ Quick Start (Dev)

### 1. Clone Project

```bash
git clone <your-repo-url>
cd <your-folder>
```

### 2. Add `.env` file

Copy or paste your environment variables into the project root.

### 3. Open in VS Code

Launch VS Code and click **"Reopen in Container"** when prompted.  
（or `Cmd+Shift+P` → `Dev Containers: Reopen in Container`）

### 4. Start Django Server

```bash
python trading_system/manage.py runserver 0.0.0.0:8000
```

### 5. Leave dev container

`Cmd+Shift+P` → `Dev Containers: Reopen Folder Locally`

### URLs

- App: http://localhost:8000  
- Celery Flower: http://localhost:5555

---

## 💻 Common Commands

| Task             | Command                                            |
|------------------|----------------------------------------------------|
| DB Migrate       | `python trading_system/manage.py migrate`                         |
| Make Migration   | `python trading_system/manage.py makemigrations`                  |
| Create Superuser | `python trading_system/manage.py createsuperuser`                |
| Run Tests        | `python trading_system/manage.py test`                            |

---

## 🚀 Deploy to Production

> Simple Docker Compose deployment with Nginx + SSL

### Requirements

- Ubuntu 22.04+ Server
- Docker & Docker Compose installed

### Deployment Steps

```bash
sudo apt update && sudo apt install git -y
git clone <your-repo-url>
cd <your-folder>

sh aws_initialization.sh
sh deployment.sh
```

---

## 📁 Project Structure

```bash
    ├── .devcontainer/
    │   └── devcontainer.json       # Defines the VS Code Dev Container environment
    ├── trading_system/             # Main application source code directory (Django project)
    │   ├── core/                   # A Django app for core functionalities
    │   ├── trading_system/         # Django project's main settings directory
    │   │   ├── settings.py         # Main project settings (database, auth, etc.)
    │   │   ├── urls.py             # Root URL configuration
    │   │   └── celery.py           # Celery application definition
    │   └── manage.py               # Django's command-line utility for management tasks
    ├── .dockerignore               # Specifies files to exclude from the Docker image build context
    ├── .gitignore                  # Specifies files to be ignored by Git
    ├── deployment.sh               # Custom script for deployment procedures
    ├── docker-compose.yml          # Defines the entire multi-container application stack (base)
    ├── docker-compose.override.yml # Overrides for local development (e.g., port mapping, volumes)
    ├── Dockerfile                  # Instructions to build the main application's Docker image
    ├── nginx.conf                  # Nginx web server configuration
    ├── requirements.txt            # A list of Python package dependencies
    ├── supervisord.conf            # Supervisor process manager configuration (manages Django/Celery)
    └── README.md                   # This file
```
