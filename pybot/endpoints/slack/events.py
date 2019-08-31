import asyncio
import logging

from sirbot import SirBot
from slack.events import Event

from pybot.endpoints.slack.utils.event_utils import (
    build_messages,
    get_backend_auth_headers,
    link_backend_user,
    send_community_notification,
    send_user_greetings,
    get_profile_suggestions,
    build_suggestion_messages,
)

logger = logging.getLogger(__name__)


def create_endpoints(plugin):
    plugin.on_event("team_join", team_join, wait=False)


async def team_join(event: Event, app: SirBot) -> None:
    """
    Handler for when the Slack workspace has a new member join.

    After 30 seconds sends the new user a greeting, some resource links, and
    notifies the community channel of the new member.
    """
    slack_api = app.plugins["slack"].api
    user_id = event["user"]["id"]

    *user_messages, community_message = build_messages(user_id)
    futures = [
        send_user_greetings(user_messages, slack_api),
        send_community_notification(community_message, slack_api),
    ]

    logger.info(f"New team join event: {event}")
    await asyncio.sleep(30)
    await asyncio.wait(futures)

    headers = await get_backend_auth_headers(app.http_session)
    if headers:
        await link_backend_user(user_id, headers, slack_api, app.http_session)

        suggested_channels = get_profile_suggestions(slack_api)
        if suggested_channels:
            suggestion_messages = build_suggestion_messages(user_id, suggested_channels)
            await asyncio.wait([send_user_greetings(suggestion_messages, slack_api)])
