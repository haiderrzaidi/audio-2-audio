# Voice Chatbot with LiveKit

This project is a voice-enabled chatbot using LiveKit, Python, and a Next.js frontend.

## Prerequisites

- [LiveKit Server](https://docs.livekit.io/)
- Python 3.12
- Node.js & [pnpm](https://pnpm.io/)

## Setup

### 1. Start LiveKit Server

```sh
livekit-server --dev --bind 0.0.0.0
```

### 2. Prepare Python Backend

Download required files:

```sh
python test.py download-files
```

Start the backend server:

```sh
python test.py dev
```

### 3. Setup Frontend

Install dependencies:

```sh
cd voice-assistant-frontend
pnpm install
```

Start the frontend:

```sh
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

Create a `.env` file in your project root with the following (replace with your own keys):

```env
DEEPGRAM_API_KEY="your_deepgram_api_key"
OPENAI_API_KEY="your_openai_api_key"
LIVEKIT_API_KEY="your_livekit_api_key"
LIVEKIT_API_SECRET="your_livekit_api_secret"
LIVEKIT_URL="ws://localhost:7880"
```

**Never commit your `.env` file or API keys to version control.**

## Notes

- Make sure all services are running before accessing the frontend.
- For more details, see the [voice-assistant-frontend/README.md](voice-assistant-frontend/README.md).
