<!-- vi: tw=119
-->

# Python Discord's Code Jam 2024, Contemplative Constellations Team Project

This repository houses the source code of the team project created for **Python Discord's Code Jam 2024**, developed by
**Contemplative Constellations** team.

## Running the bot

To run the bot, you'll first want to install all of the project's dependencies. This is done using the
[`poetry`](https://python-poetry.org/docs/) package manager. You may need to download poetry if you don't already have
it.

To install the dependencies, you can run the `poetry install` command. If you only want to run the bot and you're not
interested in also developing / contributing, you can also run `poetry install --only-root`, which will skip the
development dependencies (tools for linting and testing).

Once done, you will want to activate the virtual environment that poetry has just created for the project. To do so,
simply run `poetry shell`.

You'll now need to configure the bot. See the [configuring section](#configuring-the-bot)

Finally, you can start the bot with `python -m src`.

## Configuring the bot

The bot is configured using environment variables. You can either create a `.env` file and define these variables
there, or you can set / export them manually. Using the `.env` file is generally a better idea and will likely be more
convenient.

| Variable name | Type   | Description                                                                                         |
| ------------- | ------ | --------------------------------------------------------------------------------------------------- |
| `BOT_TOKEN`   | string | Bot token of the discord application (see: [this guide][bot-token-guide] if you don't have one yet) |

[bot-token-guide]: https://guide.pycord.dev/getting-started/creating-your-first-bot#creating-the-bot-application
