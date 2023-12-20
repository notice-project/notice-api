<div align="center">

# Not!ce API

![Not!ce logo](docs/logo-light.png#gh-light-mode-only)

API server for the Not!ce application.

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python&logoColor=%23cccccc)](https://www.python.org/downloads/release/python-31013/)
[![PDM Managed](https://img.shields.io/badge/PDM-managed-blueviolet?style=for-the-badge&logo=pdm)](https://pdm-project.org/)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.105-009688?logo=fastapi&style=for-the-badge)](https://fastapi.tiangolo.com/)
[![Deepgram](https://img.shields.io/badge/deepgram-nova--2-000000?style=for-the-badge)](https://deepgram.com)
[![OpenAI](https://img.shields.io/badge/openai-GPT--3.5-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)

[Usage](#usage) • [Getting Started](#getting-started) • [Contributing](#contributing)

</div>

## Usage

### Requirements

- [Python 3.10](https://www.python.org/downloads/release/python-31013/)
- [PDM](https://pdm-project.org/)

### Running

#### Environment Variables

Before running the server, you need to set the following environment variables:

> You can set them in a `.env` file in the root directory of the project, there is a `.env.example` file for reference.

- Common

  | Variable               | Description                             | Default |
  | ---------------------- | --------------------------------------- | ------- |
  | `BACKEND_CORS_ORIGINS` | Allowed origins for CORS in JSON format | `["*"]` |
  | `LOG_JSON_FORMAT`      | Whether to log in JSON format           | `false` |
  | `LOG_LEVEL`            | Logging level                           | `info`  |
  | `SESSION_SECRET_KEY`   | Secret key for session                  |         |

- OAuth

  | Variable                     | Description                | Default |
  | ---------------------------- | -------------------------- | ------- |
  | `NYCU_OAUTH_CLIENT_ID`       | NYCU OAuth client ID       |         |
  | `NYCU_OAUTH_CLIENT_SECRET`   | NYCU OAuth client secret   |         |
  | `GOOGLE_OAUTH_CLIENT_ID`     | Google OAuth client ID     |         |
  | `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth client secret |         |

- Data Storage

  | Variable              | Description                                 | Default |
  | --------------------- | ------------------------------------------- | ------- |
  | `MYSQL_ROOT_PASSWORD` | MySQL root password (Please don't use root) |         |
  | `MYSQL_USER`          | MySQL user                                  |         |
  | `MYSQL_PASSWORD`      | MySQL password                              |         |
  | `MYSQL_DATABASE`      | MySQL host                                  |         |
  | `MINIO_ROOT_USER`     | MinIO root user                             |         |
  | `MINIO_ROOT_PASSWORD` | MinIO root password (>= 8 characters)       |         |

#### Docker

If you need a MySQL database and a MinIO server running locally, you can use the following command:

```bash
docker compose up -d
```

#### Running the server

1. Clone the repository

   ```bash
   git clone https://github.com/notice-project/notice-api.git
   # or
   git clone git@github.com:notice-project/notice-api.git
   ```

2. Install dependencies

   ```bash
   pdm install
   ```

3. Run the development server

   ```bash
   pdm run dev
   ```

   The server will be running at [http://localhost:8000](http://localhost:8000).

## Getting Started

### Overview

The API server consists of the following components:

- Gateway: The entry point of the API server, which handles the communication between the client and the server.
- OAuth: The third-party OAuth clients, which handles the authentication of the user.
- Transcript: The transcript module, which handles the transcript of streaming audio from the client.
- Note Helper: The note helper module, which handles the logic of the `notice me` feature behind the scenes.

### API Documentation

The API documentation is available at [GitHub Pages](https://notice-project.github.io/notice-api/).

## Contributing

### Code Style

We use [ruff](https://astral.sh/ruff) for both code formatting and linting. You can run the following commands to:

- Format the code

  ```bash
  pdm run format
  ```

- Lint the code

  ```bash
  pdm run lint
  ```

### Type Checking

We use [Pyright](https://github.com/microsoft/pyright) for type checking. You can run the following command to check the types:

```bash
pdm run typecheck
```

### Commit Messages

For writing commit and pull request messages, please follow the [Gitmoji](https://gitmoji.dev/) style guide.
