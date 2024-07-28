from collections.abc import Sequence

import discord

from src.bot import Bot
from src.db_adapters.lists import refresh_list_items
from src.db_adapters.user import user_get_list_safe, user_get_safe
from src.db_tables.user_list import UserList
from src.tvdb.client import Movie, Series

from .movie_series_view import MovieView, SeriesView


def _search_view(
    bot: Bot,
    user_id: int,
    invoker_user_id: int,
    watched_list: UserList,
    favorite_list: UserList,
    results: Sequence[Movie | Series],
    cur_index: int = 0,
) -> MovieView | SeriesView:
    result = results[cur_index]

    if isinstance(result, Movie):
        view = MovieView(
            bot=bot,
            user_id=user_id,
            invoker_user_id=invoker_user_id,
            watched_list=watched_list,
            favorite_list=favorite_list,
            media_data=result,
        )
    else:
        view = SeriesView(
            bot=bot,
            user_id=user_id,
            invoker_user_id=invoker_user_id,
            watched_list=watched_list,
            favorite_list=favorite_list,
            media_data=result,
        )

    if len(results) == 1:
        return view

    # Add support for switching between search results dynamically
    search_result_dropdown = discord.ui.Select(
        placeholder="Not what you're looking for? Select a different result.",
        options=[
            discord.SelectOption(
                label=(result.bilingual_name or "")[:100],
                value=str(i),
                description=result.overview[:100] if result.overview else None,
            )
            for i, result in enumerate(results)
        ],
        row=2,
    )

    async def _search_dropdown_callback(interaction: discord.Interaction) -> None:
        if not await view._ensure_correct_invoker(interaction):  # pyright: ignore[reportPrivateUsage]
            return

        if not search_result_dropdown.values or not isinstance(search_result_dropdown.values[0], str):
            raise ValueError("Dropdown values are empty or not a string but callback was triggered.")

        index = int(search_result_dropdown.values[0])
        new_view = _search_view(bot, user_id, invoker_user_id, watched_list, favorite_list, results, index)
        await new_view.send(interaction)

    search_result_dropdown.callback = _search_dropdown_callback

    view.add_item(search_result_dropdown)
    return view


async def search_view(
    bot: Bot,
    user_id: int,
    invoker_user_id: int,
    results: Sequence[Movie | Series],
) -> MovieView | SeriesView:
    """Construct a view showing the search results.

    This uses specific views to render a single result. This view is then modified to
    add support for switching between the search results.
    """
    user = await user_get_safe(bot.db_session, user_id)
    watched_list = await user_get_list_safe(bot.db_session, user, "watched")
    favorite_list = await user_get_list_safe(bot.db_session, user, "favorite")
    await refresh_list_items(bot.db_session, watched_list)
    await refresh_list_items(bot.db_session, favorite_list)

    return _search_view(bot, user_id, invoker_user_id, watched_list, favorite_list, results, 0)
