<!-- Banner -->
<figure style="margin: auto; max-height: 200px; padding: 10px 5px 20px 5px;">
   <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/assets/Logo/banner_1_no_background_dark_mode.png">
      <img src="docs/assets/Logo/banner_1_no_background.png" align="center">
   </picture>
</figure>

<br>

[Wiki-Wabbit](https://wikiwabbit.com/) is a discord bot that brings the fun of bingeing Wikipedia articles to your dicord server!

# Directory

+ [Features](#Features)
+ [Technical Points](#Technical-Points)
+ [Install Guide](#Install-Guide)
  + [Discord Token](#Discord-Token)
  + [Firebase Service Account](#Firebase-Service-Account)
  + [Gemini API Key](#Gemini-API-Key)
  + [API Ninjas API Key](#API-Ninjas-Key)
  + [Env Settings](#Env-Settings)
  + [Docker](#Docker)

+ [Shout Outs](#Shout-Outs)

# Features

| Command         | Description                                                                |
|-----------------|----------------------------------------------------------------------------|
| `/wiki-guesser` | Starts a game of wiki-guesser! Try and find what wikipedia article you're in. |
| `/wiki-random`  | Get a random wikipedia article.                                            |
| `/wiki-animal`  | Starts a game of wiki-animal! Try and guess the animal's mass!             |
| `/rabbit-hole`  | Dive into wikipedia with AI-guided random exploration!                     |
| `/wiki-search`  | Get a Wikipedia article that you searched for.                             |
| `/leaderboard`  | Returns your guild's leaderboard.                                          |
| `/user-info`    | Returns your stats.                                                        |
| `/reset-scores` | Reset scores of all users in this guild for this guild.                    |
| `/never`        | Never use this command! :surprised:                                        |
| `/sync`         | Sync the command tree.                                                     |
| `/help`         | Display a message with much of the same info as this table has.            |


# Technical Points

<!-- Any interesting technical points you'd like to include go below here. -->

`Wiki-Wabbit` uses `pywikibot` and the Wikipedia REST API. Alongside that, it also makes use of:

+ Firebase
+ Google's Gemini API
+ Ninja API

# Install Guide

[github_install_link]: https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository

First, [clone this repository locally][github_install_link].

We require a few resources to get our bot up and running. For starters, we need
to collect some API tokens used by the bot. You should save these in a safe
place; once they're all collected, we'll be putting them into our
[`config.env`](config.env) file.

The first thing we need is a Discord API token.

### Discord Token
<!-- Install guide. -->
Goto the [Discord Application Page](https://discord.com/developers/applications) you should see this screen.
<figure style="margin: auto; max-height: 200px; padding: 10px 5px 20px 5px;">
   <picture>
      <img src="docs/assets/discord_application_page.png" align="center">
   </picture>
</figure>

After that go and create a discord application by clicking the `New Application` button

Now go down to "Bot" on the left menu and click `Reset Token` that will be your
discord token, put it somewhere safe for later.

While here be sure to turn on the 3 switches below `Privileged Gateway Intents`
 + Presence Intent
 + Server Members Intent
 + Message Content Intent

You should also goto `Installation` in the sidebar menu and goto the Install Link, add your bot to your discord server with this.

### Firebase Service Account

Go to the [Firebase Console](https://console.firebase.google.com/) and click the get started with a Firebase project.
Its name can be anything, so don't worry about that.
After it's made, click on the build tab on the left hand of the screen and scroll down to `Realtime Database`, this will be our database for the bot.
<figure style="margin: auto; max-height: 200px; padding: 10px 5px 20px 5px;">
   <picture>
      <img src="docs/assets/realtime_create.png" align="center">
   </picture>
</figure>

After this, we still need to tell the bot what firebase account we are using.
Head to project settings, it should pop up if you click on the gear near
`Project Overview`.  From there navigate to `Service Accounts` and click
`Generate a New Private Key`. This should download a `json` file that serves as
your key for Firebase. Put that file in a safe place that you can get to easily
(e.g., `secrets/firebase_api_key.json`, which is ignored in our `.gitignore`
file).

And that's all for Firebase.

### Gemini API Key
One of our Commands makes use of AI, and since we don't want to force the end user to run a complex AI model, we are using the Google Gemini free plan.

Goto the [Google AI Studio](https://aistudio.google.com/app/apikey) and just click `Create API key`.
Once you have your key, you can store that somewhere safe for later.
Well that was easy.

#### Warning

The API key may need to be associated with a Google Cloud Project. You can use
the Firebase project created in the previous step, which should be available
from the "Search Google Cloud project" search bar with the same name you gave
it.

### API Ninjas Key
Goto [API Ninjas](https://api-ninjas.com/) and create an account and log in. After you make it, [goto your profile](https://api-ninjas.com/profile).
From here scroll down a bit and click `Show API Key`, copy it, and save it somewhere safe for later.

Now that we have all of our keys and service accounts, it's time to configure the bot!

### Env Settings.
We have included a [config.env](config.env) to allow you to easily set up environment variables for the bot.
+ `TOKEN` is your [Discord API token](#discord-token)
+ `CERT_PATH` is your [Firebase Service Account file path](#firebase-service-account).
+ `GEMINI_API_KEY` is your [Google Gemini API key](#gemini-api-key).
+ `NINJA_API_KEY` is your [API Ninjas API key](#api-ninjas-key).


### Rename `config.env` to `.env`

After you set these, be sure rename `config.env` to just `.env` so the docker knows what to use. _You will get a `KeyError` if you do not do this step_!

### Docker
After you set up your env you can run
```
docker build --tag wikiwabbit .
```
and then after that finishes with no errors run
```
docker run wikiwabbit
```
and everything should be up and running. Return to discord, and check out your bot - however, you might want to kick and reinvite it to auto sync the command tree.

# Shout Outs

Thank you Python Discord for putting this on, I dont think anyone in our team has ever done something like this. And I will do this continuing forward. Really happy with the result.

Enjoy the bot, a lot of work went into this. It was a passion for all of us apart of this team, we had a great time, we poured our all into our features, thank you to the team, theheretic_, WONG-TONG48, teald, spenpal, lotus.css, Xanthian.

# Connection to the theme (Information Overload!)

Wikipedia and wiki sites are notorious for offering users a simple means of digging more deeply into topics---especially topics relatively removed from their original intent. This can lead to a straightforward search becoming a meandering path through various topics, leading to an _overload_ of _information_. The colloquialism for this is "going down a [wiki rabbit hole](https://en.wikipedia.org/wiki/Wiki_rabbit_hole)".

Wiki-wabbit is a tool for expanding on this experience through Discord. Alongside the eponymous `/rabbit-hole` command, other commands allow for engaging with Wikipedia's wealth of information in other ways, such as playing games and pulling up random articles.

# Breakdown of Team Contributions

## `theheretic_`

+ `wikiutils` Implementation
+ Web hosting
+ Docker
+ Initial Idea
+ Team Engagement
+ `Database` Implementation + refactoring (with lotus.css)
+ Install Guide

## `WONG_TONG48`

+ [ TODO ]

## `teald`

+ `ArticleGenerator` Implementation (+ minimal testing)
+ `GiveUpButton` Implementation
+ `wikiutils` refactoring
+ Documentation work (docstrings + some README work)
+ Manual testing for functions/installs and instructions
+ Wiki-Wabbit logo, banners, and icons
+ Initial [Connection to the Theme](#connection-to-the-theme-information-overload)

## `spenpal`

+ `RabbitHole` Implementation
+ Conventional Commits Idea

## `lotus.css`

+ `Database` Implementation (with theheretic_)
+ `User` Implementation

## `Xanthian`

+ [ TODO ]
