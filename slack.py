"""
Token envvars required:
- SLACK_APP_TOKEN
- SLACK_BOT_TOKEN

Bot Token Scopes required:
- app_mentions:read
- chat:write
- commands
- files:write

Slash commands:
- /hello-socket-mode
- /echo
- /plot
- /inline-plot
- /advanced-search
"""

import asyncio
import json
import random
import string
from typing import Any, Dict, List

import aiohttp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

app = AsyncApp()


def encode_data(data: Dict[str, Any]) -> str:
    """adapter for dict->str usage in block action values"""
    return json.dumps(data)


def decode_data(data_str: str) -> Dict[str, Any]:
    """adapter for str->dict usage in block action values"""
    return json.loads(data_str)


async def get_data(search_term: str, count: int = 5) -> Dict[str, str]:
    """mock api call"""
    results = {search_term: "127.0.0.1"}
    for _ in range(count - 1):
        random_username = search_term + random.choice(string.ascii_lowercase)
        random_ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
        results[random_username] = random_ip
    await asyncio.sleep(0.3)
    return results


@app.action("clear_cache")  # type: ignore
async def handle_clear_cache_action(ack: AsyncAck, say: AsyncSay, body: Dict[str, Any]):
    await ack()
    data = decode_data(body["actions"][0]["value"])
    await say(
        f"Clearing cache for *{data['username']}*: Client IP: `{data['ip_addr']}`"
    )


@app.action("advanced_search")  # type: ignore
async def handle_advanced_search_action(
    ack: AsyncAck, say: AsyncSay, body: Dict[str, Any]
):
    search_term = body["actions"][0]["value"]
    await ack(f"Got it. Looking up {search_term}")
    results = await get_data(search_term)
    blocks: List[Dict[str, Any]] = [
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "emoji": True,
                "text": f"Here are the results for {search_term}",
            },
        },
        {"type": "divider"},
    ]
    for username, ip_addr in results.items():
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{username}*\nClient IP: `{ip_addr}`",
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Clear Cache",
                    },
                    "action_id": f"clear_cache",
                    "value": encode_data({"username": username, "ip_addr": ip_addr}),
                },
            }
        )

    await say(blocks=blocks, text="results")


@app.command("/advanced-search")  # type: ignore
async def handle_advanced_search_command(ack: AsyncAck):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": "Find users by keyword",
                "emoji": True,
            },
        },
        {
            "dispatch_action": True,
            "type": "input",
            "element": {
                "type": "plain_text_input",
                "action_id": "advanced_search",
            },
            "label": {"type": "plain_text", "text": "Advanced Search 🔍", "emoji": True},
        },
    ]
    await ack(blocks=blocks, text="search input")


@app.command("/inline-plot")  # type: ignore
async def send_plot_link(ack: AsyncAck, say: AsyncSay):
    """Standard way of sharing image in slack. Does not work if slack cannot access image"""
    await ack()
    blocks = [
        {
            "type": "image",
            "image_url": "http://localhost:8000/df/any.png",
            "alt_text": "inspiration",
        }
    ]
    await say(blocks=blocks, text="plot image")


@app.command("/plot")  # type: ignore
async def call_plot_api(
    ack: AsyncAck, say: AsyncSay, client: AsyncWebClient, body: Dict[str, str]
):
    """Shares plot image by downloading image from fastapi server and uploading to slack
    This slackoverflow answer has the steps required
    ref: https://stackoverflow.com/a/58189401

    A few caveats.
    1. To send image in blocks (structured fancy messages), it has to be a public url (slack needs to be able to fetch it)
    2. Uploaded files are not considered public accessible until files.sharedPublicURL is called
    3. Bots can not call files.sharedPublicURL API

    Potential workaround (never tried, not reccomended)
    4. Start up a user client
    5. Bot client pass file id to user client
    6. User client makes file url public
    7. Bot sends block message with public url

    files.sharedPublicURL docs: https://api.slack.com/methods/files.sharedPublicURL

    This means that there is not many ways that bots can share "non-public" images on slack.
    Current flow:
    1. Download file from "non-public" source
    2. Upload to slack as file
    3. Send file permalink to channel (rely on link auto-preview to show image, kinda sucks 😕)
    """
    await ack()

    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8000/df/any.png"
        async with session.get(url) as resp:
            if resp.status != 200:
                await say("error connecting to api server")
                return

            try:
                await say(f"downloading file from {url}")
                img_bytes = await resp.read()
            except Exception as e:
                await say(f"error downloading file: {e}")
                return

    try:
        await say(f"uploading file to slack")
        results = await client.files_upload(file=img_bytes)
    except SlackApiError as e:
        await say(f"error uploading file: {e}")
        return

    if not results["ok"]:
        await say("something went terribly wrong")
        await say(f"```{results}```")
    else:
        await say(results["file"]["permalink"])


@app.command("/hello-socket-mode")  # type: ignore
async def hello_command(ack: AsyncAck, body: Dict[str, str]) -> None:
    user_id = body["user_id"]
    await ack(f"Hi <@{user_id}>!")


@app.command("/echo")  # type: ignore
async def repeat_text(ack: AsyncAck, say: AsyncSay, body: Dict[str, str]) -> None:
    await ack()
    await say(f"{body['text']}")


@app.event("app_mention")  # type: ignore
async def event_test(event: Dict[str, Any], say: AsyncSay) -> None:
    await say(f"Hi there, <@{event['user']}>!")


async def main():
    handler = AsyncSocketModeHandler(app)
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
