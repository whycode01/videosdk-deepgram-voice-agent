# AI Copilot with VideoSDK & Deepgram

This project is an AI Voice Agent that uses VideoSDK for video conferencing, Deepgram for speech-to-text (STT), and OpenAI for language model (LLM) capabilities. The AI Copilot can join meetings, transcribe speech, and respond intelligently.

![videoSDK + Deepgram Integration](https://assets.videosdk.live/images/videosdk-dg-integration.png)

### Start with the project

```sh
git clone https://github.com/videosdk-community/videosdk-deepgram-voice-agent
```

### Client Setup

1. Navigate to `client` dir:
   ```sh
   cp client
   ```
2. Make a copy of the environment configuration file:
   ```sh
   cp .env.example .env
   ```
3. Set the `VITE_APP_AUTH_TOKEN` in the `.env` file with your VideoSDK auth token from [app.videosdk.live](https://app.videosdk.live).

### Python Setup

1. Configure the following environment variables in the `.env` file:

   ```sh
   ROOM_ID=...
   AUTH_TOKEN=...  # (app.videosdk.live)
   LANGUAGE=...

   DEEPGRAM_API_KEY=...  # (console.deepgram.com)
   LLM_API_KEY=...  # (platform.openai.com/api-keys)
   ```

2. Create a virtual environment:
   ```sh
   python -m venv venv
   ```
3. Activate the virtual environment:
   - On Unix or MacOS:
     ```sh
     source venv/bin/activate
     ```
   - On Windows:
     ```sh
     .\venv\Scripts\activate
     ```

### Generate a Room ID

Generate a room ID on the client side and add it to the Python configuration. This can be done by running the client application and using the generated room ID in the `.env` file for the Python setup.

For more information, check out [docs.videosdk.live](https://docs.videosdk.live).
