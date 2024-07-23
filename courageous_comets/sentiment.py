import logging

from discord import Message
from nltk.sentiment import SentimentIntensityAnalyzer
from redis.asyncio import Redis

from courageous_comets.models import SentimentResult
from courageous_comets.redis.keys import key_schema

MAX_MESSAGE_LENGTH = 256

logger = logging.getLogger(__name__)


def calculate_sentiment(content: str, key: str) -> SentimentResult:
    """
    Calculate the sentiment of a message.

    Uses the NLTK sentiment intensity analyzer to calculate the sentiment of a message.

    Messages can be up to 256 characters long. If a message is longer than 256 characters,
    it will be truncated.

    Parameters
    ----------
    content : str
        The message content to analyze.
    key : str
        The Redis key for the message. Used for logging.

    Returns
    -------
    courageous_comets.models.SentimentResult
        The sentiment of the message.
    """
    truncated = content[:MAX_MESSAGE_LENGTH]

    if truncated != content:
        logger.warning("Truncated message %s to %s characters", key, MAX_MESSAGE_LENGTH)

    sia = SentimentIntensityAnalyzer()
    result = sia.polarity_scores(truncated)

    return SentimentResult.model_validate(result)


async def store_sentiment(message: Message, redis: Redis) -> None:
    """
    Calculate the sentiment of a message and store the result in Redis.

    A message must have a guild, channel, author and message ID. If any of these are missing,
    the message will be ignored.

    Empty messages will also be ignored.

    Parameters
    ----------
    message : discord.Message
        The message to process.
    redis : redis.asyncio.Redis
        The Redis connection instance.
    """
    # Ignore empty messages
    if not message.content:
        logger.warning("Ignoring empty message %s", message.id)
        return

    # Extract the IDs from the message
    guild_id = message.guild.id if message.guild else 0
    channel_id = message.channel.id if message.channel else 0
    user_id = message.author.id if message.author else 0
    message_id = message.id if message.id else 0

    # Ignore messages without all required IDs
    if not all((guild_id, channel_id, user_id, message_id)):
        logger.warning("Ignoring message %s with missing IDs", message.id)
        return

    # Construct the Redis key
    key = key_schema.sentiment_tokens(
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        message_id=message_id,
    )

    # Calculate the sentiment
    sentiment = calculate_sentiment(message.content, key)

    # Store the sentiment in Redis
    await redis.hset(
        key,
        mapping=sentiment.model_dump(mode="json"),
    )  # pyright: ignore[reportGeneralTypeIssues]

    logger.info("Stored sentiment for message %s", key)


async def get_sentiment(key: str, redis: Redis) -> SentimentResult:
    """
    Retrieve the sentiment of a message from Redis.

    Parameters
    ----------
    key : str
        The Redis key to retrieve the sentiment from.
    redis : redis.asyncio.Redis
        The Redis connection instance.

    Returns
    -------
    courageous_comets.models.SentimentResult
        The sentiment of the message.
    """
    neg, neu, pos, compound = await redis.hmget(key, "neg", "neu", "pos", "compound")  # type: ignore

    return SentimentResult(
        neg=float(neg or 0),
        neu=float(neu or 0),
        pos=float(pos or 0),
        compound=float(compound or 0),
    )
