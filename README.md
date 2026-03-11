# GitHub Notifier Bot

<p align="center">
  <img src="assets/image.png" width="200" alt="GitHub Notifier Bot">
  <br><br>
  <img src="https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white" alt="Python 3.13">
  <img src="https://img.shields.io/badge/aiogram-3.15-26A5E4?logo=telegram&logoColor=white" alt="aiogram 3">
  <img src="https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white" alt="Telegram Bot">
</p>

Telegram bot that forwards GitHub webhook events to Telegram channels.

## Setup

```bash
uv sync
cp .env.example .env  # fill in BOT_TOKEN, GITHUB_WEBHOOK_SECRET
uv run python -m bot
```

## Webhook

Payload URL: `https://<your-domain>/webhook/github`, content type `application/json`, secret = `GITHUB_WEBHOOK_SECRET`.

## Config

Single channel via env vars (see `.env.example`) or multi-channel via `config.yaml` (see `config.yaml.example`).
