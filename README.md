# Slack Socket Image Demo

## How to run

This demo uses poetry to manage python dependencies.

### 1. Install python dependencies

```sh
poetry install
```

### 2. Set envvar required for Slack API

> if you are planning to run it with vscode debugger, the launch setting is set up to load from a .env file as well

```sh
export SLACK_APP_TOKEN='xapp-***'
export SLACK_BOT_TOKEN='xoxb-***'
```

### 3. Add the required scopes and slash commands in Slack api dashboard

OAuth & Permissions > Scopes > Bot Token Scopes

- app_mentions:read
- chat:write
- commands
- files:write

Slash commands:

- /hello-socket-mode
- /echo
- /plot
- /inline-plot

**Remember to reinstall app in workspace after setting up the new scopes**

### 4. Start services (both of them)

> The launch configurations are all set up in vscode as well

FastAPI server

```sh
uvicorn api:app
```

Slack Socket Bot

```sh
poetry run python slack.py
```

### 5. Test out the commands in slack

Add the bot to the channel by calling `@botname` in `#channel`.

The bot should respond `Hi there, @your_username`

Try the `/plot` command test out the image generation flow.

---

## Caveats

As mentioned in the [code](slack.py#L51-L73), there are a couple of caveats when sharing images as a bot.
