# KanMind Backend API

Backend API for a Kanban-style task management application built with Django and Django REST Framework.

## Features

- User registration and login with token authentication
- Board management
- Task management
- Comment system
- Permission-based access control
- RESTful API structure

---

## Tech Stack

- Python
- Django
- Django REST Framework
- DRF Token Authentication

---

## Project Structure

```bash
core/
│
├── auth_app/
│   ├── api/
│   ├── models.py
│   └── ...
│
├── kanban_app/
│   ├── api/
│   ├── models.py
│   └── ...
│
├── core/
│   ├── settings.py
│   ├── urls.py
│   └── ...
```

---

## Installation

### Clone repository

```bash
git clone https://github.com/Dusty404/KanMind.git
cd <repository-name>
```

### Create virtual environment

```bash
python -m venv env
```

### Activate virtual environment

#### Windows

```bash
env\Scripts\activate
```

#### Linux / Mac

```bash
source env/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run migrations

```bash
python manage.py migrate
```

---


## Start development server

```bash
python manage.py runserver
```

Server runs on:

```bash
http://127.0.0.1:8000/
```

---

## Authentication

This project uses DRF Token Authentication.

Example header:

```http
Authorization: Token your_token_here
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/registration/` | Register user |
| POST | `/api/login/` | Login user |
| POST | `/api/logout/` | Logout user |

---

### Boards

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/boards/` | Get boards |
| POST | `/api/boards/` | Create board |
| GET | `/api/boards/<id>/` | Get board details |
| PATCH | `/api/boards/<id>/` | Update board |
| DELETE | `/api/boards/<id>/` | Delete board |

---

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks/` | Get tasks |
| POST | `/api/tasks/` | Create task |
| GET | `/api/tasks/<id>/` | Get task details |
| PATCH | `/api/tasks/<id>/` | Update task |
| DELETE | `/api/tasks/<id>/` | Delete task |

---

### Comments

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks/<task_id>/comments/` | Get comments |
| POST | `/api/tasks/<task_id>/comments/` | Create comment |
| DELETE | `/api/tasks/<task_id>/comments/<id>/` | Delete comment |

---

## HTTP Status Codes

| Status Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 403 | Forbidden |
| 404 | Not Found |

---

## Notes

- Code follows Django REST Framework conventions

---