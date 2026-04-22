---
title: Digital FTE Backend
emoji: 🤖
colorFrom: cyan
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Digital FTE Agent - Backend (Hugging Face Space)

This is the production backend for the Digital FTE Agent, hosted on Hugging Face Spaces for 24/7 autonomous operation without a credit card.

## 🚀 Deployment Instructions

1. **Create Space:** Go to [hf.co/new-space](https://huggingface.co/new-space), name it, and select **Docker** as the SDK.
2. **Upload Files:** Upload every file inside the `backend` folder to your Space.
3. **Set Secrets:** In your Space **Settings** -> **Variables and Secrets**, add:
   - `DATABASE_URL`: Your Neon Postgres URL.
   - `GROQ_API_KEY`: Your Groq API key.
   - `ENVIRONMENT`: `production`
   - `ALLOW_ORIGINS`: `https://your-vercel-frontend-url.vercel.app`

## 🧠 Autonomous Features
The "Living Agent" starts automatically and runs in the background 24/7 on this Space.
