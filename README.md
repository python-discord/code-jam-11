# Mordle
Wordle with more fun and more information.
See more in [this slide](https://docs.google.com/presentation/d/1cCAn2Ggavuf-VrAuh-mOnEE_v00eoi68kCEKvENDXug/edit?usp=sharing) to acknowledge all of its functionalities.

## Installation
Mordle requires only several dependencies to run, be sure to clone it first:
```
git clone git@github.com:cin-lawrence/code-jam-2024
```
Ensure you have a Bot account and a server to run the Bot.

To create a Bot account, see more [here](https://discordpy.readthedocs.io/en/stable/discord.html#creating-a-bot-account).

Upon creating a Bot account and a Discord server, retrieve the Bot token and the server ID (see `Server Settings > Widget > Server ID`, then copy it).

**The application can be installed using either of 2 ways below.**

### In the host machine
Change your working directory to the project's root folder.
```
cd code-jam-2024
```
Install the dependencies. _It could be nicer if you have a virtual environment._
```
pip install -r requirements-dev.txt
```
Exports your environment variables, including the Bot token and the server ID retrieved.
```
export DISCORD_TOKEN=<your discord token>
export GUILD_ID=<your server ID>
```
Run the application from the current working directory.
```
python -m app.main
```

### Using Docker
Docker encapsulates all requirements needed for the application.

Though more advanced, this is the recommended way to run the app.

Follow the [official documentation](https://docs.docker.com/get-docker/) to install Docker.

Rename the `.env` in `./config` folder,
```
mv ./config/app/.env.example ./config/app/.env
```
and add your environment variables.
```
DISCORD_TOKEN=<your discord token>
GUILD_ID=<your server ID>
```
The latest version of Docker already has docker-compose included. To minimize the steps needed, it is recommended to use docker-compose.
```
docker compose build
docker compose up -d
```
The steps above are sufficient to spin up the application. To shut down the application:
```
docker compose down
```
If you want to use the pre-built image:
```
docker run --env-file ./config/app/.env mikosurge/mordle:v0.0.1
```

## The Ornate Orbits team
- **@Atonement**: repository setup, first bot implementation, code refactoring, trivia crawling, commits, and PRs managing.
- **@Xerif**: main game logic, most of the commands, slideshow creator.
- **@kvothe**: some nltk, crawling, math, and trivia logic.
- **@Bh**: tests writing, bug fixing.
