from random import randint
from typing import NamedTuple

import discord
from discord import ButtonStyle, Enum, app_commands
from discord.utils import MISSING
from pywikibot import Page

from wikiutils import is_article_title, make_embed, rand_wiki, search_wikipedia, update_user

ACCURACY_THRESHOLD = 0.8


class Button(NamedTuple):
    style: ButtonStyle = ButtonStyle.secondary
    label: str | None = None
    disabled: bool = False
    custom_id: str | None = None
    url: str | None = None
    emoji: str | discord.Emoji | discord.PartialEmoji | None = None
    row: int | None = None
    sku_id: int | None = None


class Comp(NamedTuple):
    score: list[int]
    ranked: bool = False
    article: Page = None
    user: int = 0


class _Ranked(Enum):
    YES = 1
    NO = 0


class ExcerptButton(discord.ui.Button):
    """Button for revealing more of the summary."""

    def __init__(self, *, info: Button, summary: str, score: list[int], owners: list[discord.User]) -> None:
        super().__init__(
            style=info.style,
            label=info.label,
            disabled=info.disabled,
            custom_id=info.custom_id,
            url=info.url,
            emoji=info.emoji,
            row=info.row,
            sku_id=info.sku_id,
        )
        self.summary = summary
        self.score = score
        self.ind = 1
        self.owners = owners
    async def callback(self, interaction: discord.Interaction) -> None:
        """Reveal more of the summary."""
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)       
            return 
        self.ind += 1
        self.score[0] -= (len("".join(self.summary[: self.ind])) - len("".join(self.summary[: self.ind - 1]))) // 2

        if self.summary[: self.ind] == self.summary or len(".".join(self.summary[: self.ind + 1])) > 1990:  # noqa:PLR2004
            self.view.remove_item(self)

        await interaction.message.edit(content=f"Excerpt: {". ".join(self.summary[:self.ind])}.", view=self.view)
        await interaction.response.defer()
class GuessButton(discord.ui.Button):
    """Button to open guess modal."""

    def __init__(self, *, info: Button, comp: Comp, owners: list[discord.User]) -> None:
        super().__init__(
            style=info.style,
            label=info.label,
            disabled=info.disabled,
            custom_id=info.custom_id,
            url=info.url,
            emoji=info.emoji,
            row=info.row,
            sku_id=info.sku_id,
        )
        self.ranked = comp.ranked
        self.article = comp.article
        self.score = comp.score
        self.user = comp.user
        self.owners = owners
    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)      
            return  
        guess_modal = GuessInput(
            title="Guess!", comp=Comp(ranked=self.ranked, article=self.article, score=self.score, user=self.user)
        )
        guess_modal.add_item(discord.ui.TextInput(label="Your guess", placeholder="Enter your guess here..."))
        await interaction.response.send_modal(guess_modal)


class GuessInput(discord.ui.Modal):
    """Input feild for guessing."""

    def __init__(
        self, *, title: str = MISSING, timeout: float | None = None, custom_id: str = MISSING, comp: Comp
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.ranked = comp.ranked
        self.score = comp.score
        self.user = comp.user
        self.article = comp.article
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Guess the article."""
        if self.ranked and interaction.user.id != self.user:
            await interaction.response.send_message(
                "You cannot guess because you were not the on who started this ranked game of wiki-guesser.",
                ephemeral=True,
            )
            return

        page = await search_wikipedia(self.children[0].value)
        if page.title() == self.article.title():
            embed = make_embed(self.article)
            # TODO: For Some Reason this doesnt work, it got mad
            msg = f"Congratulations {interaction.user.mention}! You figured it out, your score was {self.score[0]}!"
            await interaction.response.send_message(content=msg, embed=embed)
            print(self.ranked)
            if self.ranked:
                print(self.score[0])
                user = interaction.user
                for i in [interaction.guild_id, 0]:
                    await update_user(i, user, self.score[0])
            await interaction.message.edit(view=None)
            return
        await interaction.response.send_message("That's incorrect, please try again.", ephemeral=True)
        self.score[0] -= 5


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list."""

    def __init__(
        self,
        *,
        info: Button,
        comp: Comp,
        links: list[str],
        message: str,
        owners : list[discord.User]
    ) -> None:
        super().__init__(
            style=info.style,
            label=info.label,
            disabled=info.disabled,
            custom_id=info.custom_id,
            url=info.url,
            emoji=info.emoji,
            row=info.row,
            sku_id=info.sku_id,
        )
        self.score = comp.score
        self.message = message
        self.links = links
        self.owners = owners
    async def callback(self, interaction: discord.Interaction) -> None:
        """Show 10 diffrent links."""
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)
            return
        if interaction.message.content:
            await interaction.message.edit(view=None)
        else:
            await interaction.message.delete()

        selected_links = []
        self.score[0] -= 10
        for _ in range(10):
            selected_links.append(self.links.pop(randint(0, len(self.links) - 1)))  # noqa: S311
            if len(self.links) == 1:
                selected_links.append(self.links.pop(0))
                break
        await interaction.response.send_message(
            content=f"{self.message}\n```{"\n".join(selected_links)}```",
            view=self.view,
            delete_after=180,
        )
        if len(self.links) == 0:
            self.view.remove_item(self)


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    @tree.command(
        name="wiki-guesser",
        description="Starts a game of wiki-guesser! Try and find what wikipedia article your in.",
    )
    async def wiki(interaction: discord.Interaction, ranked: _Ranked = _Ranked.NO) -> None:
        try:
            ranked: bool = bool(ranked.value)
            if ranked == True:
                owners = [interaction.user]
            else:
                owners = [*interaction.guild.members]
                
            score = [1000]
            if ranked:
                await interaction.response.send_message(content=f"Starting a game of **Ranked** Wikiguesser for {owners[0].mention}")
            else:
                await interaction.response.send_message(content=f"Starting a game of Wikiguesser")
            article = await rand_wiki()
            print(article.title())

            links = [link.title() for link in article.linkedPages() if is_article_title(link.title())]

            excerpt = article.extract(chars=1200)

            for i in article.title().split():
                excerpt = excerpt.replace(i, "~~CENSORED~~")
                excerpt = excerpt.replace(i.lower(), "~~CENSORED~~")

            sentances = excerpt.split(". ")

            excerpt_view = discord.ui.View()
            guess_button = GuessButton(
                info=Button(label="Guess!", style=discord.ButtonStyle.success),
                comp=Comp(ranked=ranked, article=article, score=score, user=interaction.user.id),
                owners=owners
            )
            excerpt_button = ExcerptButton(
                info=Button(label="Show more", style=discord.ButtonStyle.primary), summary=sentances, score=score, owners=owners
            )

            excerpt_view.add_item(excerpt_button)
            excerpt_view.add_item(guess_button)

            await interaction.followup.send(
                content=f"Excerpt: {sentances[0]}.",
                view=excerpt_view,
                wait=True,
            )

            view = discord.ui.View()
            link_button = LinkListButton(
                info=Button(
                    label="Show more links in article",
                ),
                comp=Comp(score=score),
                links=links,
                message="Links in article:",
                owners=owners
            )

            view.add_item(link_button)

            await interaction.followup.send(view=view, wait=True)
            await interaction.delete_original_response()
        except discord.app_commands.errors.CommandInvokeError as e:
            print(e)
