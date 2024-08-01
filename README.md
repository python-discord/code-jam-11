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

### Using docker

The project also supports [docker](https://www.docker.com/) installation, which should allow running the project
anywhere, without installing all of the dependencies manually. This is a lot more convenient way to run the bot, if you
just want to run it and you don't wish to do any actual development.

To use docker, you can check out the images that are automatically built after each update to the `main` branch at
[ghcr](https://github.com/itsdrike/code-jam-2024/pkgs/container/code-jam-2024). You can also use [`docker
compose`](https://docs.docker.com/compose/) with the [`docker-compose.yaml`](./docker-compose.yaml) file, which will
pull this image from ghcr. To run the container using this file, you can use the following command:

```bash
docker compose up
```

> [!TIP]
> To run the container in the background, add the `-d` flag to the command.

If you want to build the image locally (to include some other changes that aren't yet in the main branch, maybe during
development or to customize something when deploying), you can also use
[`docker-compose.local.yaml`](./docker-compose.local.yaml), which defines an image building step from our
[`Dockerfile`](./Dockerfile). To run this local version of docker-compose, you can use the following command:

```bash
docker compose -f ./docker-compose.local.yaml up
```

> [!IMPORTANT]
> Note that you will still need to create a `.env` file with all of the configuration variables (see [the configuring
> section](#configuring-the-bot)

## Configuring the bot

The bot is configured using environment variables. You can either create a `.env` file and define these variables
there, or you can set / export them manually. Using the `.env` file is generally a better idea and will likely be more
convenient.

| Variable name              | Type   | Default       | Description                                                                                                         |
| -------------------------- | ------ | ------------- | ------------------------------------------------------------------------------------------------------------------- |
| `BOT_TOKEN`                | string | N/A           | Bot token of the discord application (see: [this guide][bot-token-guide] if you don't have one yet)                 |
| `TVDB_API_KEY`             | string | N/A           | API key for TVDB (see [this page][tvdb-api-page] if you don't have one yet)                                         |
| `TVDB_RATE_LIMIT_REQUESTS` | int    | 5             | Amount of requests that the bot is allowed to make to the TVDB API within `TVDB_RATE_LIMIT_PERIOD`                  |
| `TVDB_RATE_LIMIT_PERIOD`   | float  | 100           | Period of time in seconds, within which the bot can make up to `TVDB_RATE_LIMIT_REQUESTS` requests to the TVDB API. |
| `SQLITE_DATABASE_FILE`     | path   | ./database.db | Path to sqlite database file, can be relative to project root (if the file doesn't yet exists, it will be created)  |

[bot-token-guide]: https://guide.pycord.dev/getting-started/creating-your-first-bot#creating-the-bot-application
[tvdb-api-page]: https://www.thetvdb.com/api-information

### Debug configuration variables

| Variable name        | Type   | Default | Description                                                                                                         |
| -------------------- | ------ | ------- | ------------------------------------------------------------------------------------------------------------------- |
| `ECHO_SQL`           | bool   | 0       | If `1`, print out every SQL command that SQLAlchemy library runs internally (can be useful when debugging)          |
| `DB_ALWAYS_MIGRATE`  | bool   | 0       | If `1`, database migrations will always be performed, even on a new database (instead of just creating the tables). |
| `DEBUG`              | bool   | 0       | If `1`, debug logs will be enabled, if `0` only info logs and above will be shown                                   |
| `LOG_FILE`           | path   | N/A     | If set, also write the logs into given file, otherwise, only print them                                             |
| `TRACE_LEVEL_FILTER` | custom | N/A     | Configuration for trace level logging, see: [trace logs config section](#trace-logs-config)                         |

### Trace logs config

We have a custom `trace` log level for the bot, which can be used for debugging purposes. This level is below `debug`
and can only be enabled if `DEBUG=1`. This log level is controlled through the `TRACE_LEVEL_FILTER` environment
variable. It works in the following way:

- If `DEBUG=0`, the `TRACE_LEVEL_FILTER` variable is ignored, regardless of it's value.
- If `TRACE_LEVEL_FILTER` is not set, no trace logs will appear (debug logs only).
- If `TRACE_LEVEL_FILTER` is set to `*`, the root logger will be set to `TRACE` level. All trace logs will appear.
- When `TRACE_LEVEL_FILTER` is set to a list of logger names, delimited by a comma, each of the specified loggers will
  be set to `TRACE` level, leaving the rest at `DEBUG` level. For example: `TRACE_LEVEL_FILTER="src.exts.foo.foo,src.exts.bar.bar"`
- When `TRACE_LEVEL_FILTER` starts with a `!` symbol, followed by a list of loggers, the root logger will be set to
  `TRACE` level, with the specified loggers being set to `DEBUG` level.
