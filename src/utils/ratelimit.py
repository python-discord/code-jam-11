import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Concatenate, cast

from aiocache import BaseCache
from discord import ApplicationContext, Cog

from src.bot import Bot
from src.utils.log import get_logger

log = get_logger(__name__)


class RateLimitExceededError(Exception):
    """Exception raised when a rate limit was exceeded."""

    def __init__(  # noqa: PLR0913
        self,
        msg: str | None,
        *,
        key: str,
        limit: int,
        period: float,
        closest_expiration: float,
        updates_when_exceeded: bool,
    ) -> None:
        """Initialize the rate limit exceeded error.

        :param msg:
            Custom error message to include in the exception.

            This exception should also be shown to the user if the exception makes its way
            to the error handler. If this is not provided, a generic message will be used.
        :param key: Cache key that was rate-limit.
        :param period: The period of time in seconds, in which the limit is enforced.
        :param closest_expiration: The unix time-stamp of the closest expiration of the rate limit.
        :param updates_when_exceeded: Does the rate limit get updated even if it was exceeded.
        """
        self.msg = msg
        self.key = key
        self.limit = limit
        self.period = period
        self.closest_expiration = closest_expiration
        self.updates_when_exceeded = updates_when_exceeded

        err_msg = f"Rate limit exceeded for key '{key}' ({limit}/{period}s)"
        if msg:
            err_msg += f": {msg}"
        super().__init__(err_msg)


async def rate_limit(
    cache: BaseCache,
    key: str,
    *,
    limit: int,
    period: float,
    update_when_exceeded: bool = False,
    err_msg: str | None = None,
) -> None:
    """Log a new request for given key, enforcing the rate limit.

    The cache keys are name-spaced under 'rate-limit' to avoid conflicts with other cache keys.

    The rate-limiting uses a sliding window approach, where each request has its own expiration time
    (i.e. a request is allowed if it is within the last `period` seconds). The requests are stored
    as time-stamps under given key in the cache.

    :param cache: The cache instance used to keep track of the rate limits.
    :param key: The key to use for this rate-limit.
    :param limit: The number of requests allowed in the period.
    :param period: The period of time in seconds, in which the limit is enforced.
    :param update_when_exceeded:
        Log a new rate-limit request time even if the limit was exceeded.

        This can be useful to disincentivize users from spamming requests, as they would
        otherwise still receive the response eventually. With this behavior, they will
        actually need to wait and not spam requests.

        By default, this behavior is disabled, mainly for global / internal rate limits.
    :param err_msg:
        Custom error message to include in the `RateLimitExceededError` exception.

        This message will be caught by the error handler and sent to the user, instead
        of using a more generic message.
    :raises RateLimitExceededError: If the rate limit was exceeded.
    """
    current_timestamp = time.time()

    # No existing requests
    if not await cache.exists(key, namespace="rate-limit"):
        log.trace(f"No existing rate-limit requests for key {key!r}, adding the first one")
        await cache.set(key, (current_timestamp,), ttl=period, namespace="rate-limit")
        return

    # Get the existing requests
    cache_time_stamps = cast(tuple[float, ...], await cache.get(key, namespace="rate-limit"))
    log.trace(f"Fetched {len(cache_time_stamps)} existing requests for key {key!r}")

    # Expire requests older than the period
    remaining_time_stamps = list(cache_time_stamps)
    for time_stamp in cache_time_stamps:
        if (current_timestamp - time_stamp) > period:
            remaining_time_stamps.remove(time_stamp)

    # Also remove the oldest requests, keeping only up to limit
    # This is just to avoid the list growing for no reason.
    # As an advantage, it also makes it easier to find the closest expiration time.
    remaining_time_stamps = remaining_time_stamps[-limit:]

    log.trace(f"Found {len(remaining_time_stamps)} non-expired existing requests for key {key!r}")

    # Add the new request, along with the existing non-expired ones, resetting the key
    # Only do this if the rate limit wasn't exceeded, or if updating on exceeded requests is enabled
    if len(remaining_time_stamps) < limit or update_when_exceeded:
        log.trace("Updating rate limit with the new request")
        new_timestamps: tuple[float, ...] = (*remaining_time_stamps, current_timestamp)
        await cache.set(key, new_timestamps, ttl=period, namespace="rate-limit")

    # Check if the limit was exceeded
    if len(remaining_time_stamps) >= limit:
        # If update on exceeded requests are enabled, add the current timestamp to the list
        # and trim to limit requests, allowing us to obtain the proper closest timestamp
        if update_when_exceeded:
            remaining_time_stamps.append(current_timestamp)
            remaining_time_stamps = remaining_time_stamps[-limit:]

        closest_expiration = min(remaining_time_stamps) + period

        log.debug(f"Rate limit exceeded on key: {key!r}")
        log.trace(f"Exceeded rate limit details: {limit}/{period}s, {remaining_time_stamps=!r}, {closest_expiration=}")
        raise RateLimitExceededError(
            err_msg,
            key=key,
            limit=limit,
            period=period,
            closest_expiration=closest_expiration,
            updates_when_exceeded=update_when_exceeded,
        )


type CogCommandFunction[T: Cog, **P] = Callable[Concatenate[T, ApplicationContext, P], Awaitable[None]]
type TransformFunction[T, R] = Callable[[T, ApplicationContext], R]


def rate_limited[T: Cog, **P](
    key: str | Callable[[T, ApplicationContext], str],
    *,
    limit: int | TransformFunction[T, int],
    period: float | TransformFunction[T, float],
    update_when_exceeded: bool | TransformFunction[T, bool] = False,
    err_msg: str | None | TransformFunction[T, str | None] = None,
) -> Callable[[CogCommandFunction[T, P]], CogCommandFunction[T, P]]:
    """Apply rate limits to given cog command function.

    The decorated function must be a slash command function that belongs to a cog class
    (as an instance method). Make sure to apply this decorator before the ``slash_command``
    decorator.

    This uses the :func:`rate_limit` function internally to enforce the rate limits.
    See its description for more info.

    All of the parameters can be set directly, or they can be callables, which will get called
    with self (the cog instance) and ctx, using the return value as the value of that parameter.
    These parameters will then all be forwarded to the ``rate_limit`` function.

    .. note::
        Py-cord does provide a built-in way to rate-limit commands through "cooldown" structures.
        These work similarly to our custom implementation, but bucketing isn't as flexible and
        doesn't work globally across the whole application.

        Using this decorator is therefore preferred, even for simple rate limits, for consistency.
    """

    def inner(func: CogCommandFunction[T, P]) -> CogCommandFunction[T, P]:
        @wraps(func)
        async def wrapper(self: T, ctx: ApplicationContext, *args: P.args, **kwargs: P.kwargs) -> None:
            bot = ctx.bot
            if not isinstance(bot, Bot):
                raise TypeError(
                    "The bot instance must be of our custom Bot type (src.bot.Bot), "
                    f"found: {bot.__class__.__qualname__}"
                )

            cache = bot.cache

            # Call transformer functions, if used
            key_ = key(self, ctx) if isinstance(key, Callable) else key
            limit_ = limit(self, ctx) if isinstance(limit, Callable) else limit
            period_ = period(self, ctx) if isinstance(period, Callable) else period
            update_when_exceeded_ = (
                update_when_exceeded(self, ctx) if isinstance(update_when_exceeded, Callable) else update_when_exceeded
            )
            err_msg_ = err_msg(self, ctx) if isinstance(err_msg, Callable) else err_msg

            await rate_limit(
                cache,
                key_,
                limit=limit_,
                period=period_,
                update_when_exceeded=update_when_exceeded_,
                err_msg=err_msg_,
            )
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return inner
