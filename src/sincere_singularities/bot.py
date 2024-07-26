import asyncio

from disnake import ApplicationCommandInteraction, Intents, TextChannel
from disnake.ext import commands

from sincere_singularities.modules.conditions import ConditionManager
from sincere_singularities.modules.order_queue import OrderQueue
from sincere_singularities.modules.restaurants_view import Restaurants

intents = Intents.default()
bot = commands.InteractionBot(intents=intents)
background_tasks = set()


@bot.slash_command(name="clear_webhooks")
async def clear_webhooks(inter: ApplicationCommandInteraction) -> None:
    """Clears the webhoooks in a channel."""
    # Check user permissions
    permissions = inter.channel.permissions_for(inter.author)
    if not permissions.manage_webhooks:
        await inter.response.send_message("You dont have the permissions to Manage Webhooks!", ephemeral=True)
        return

    # Check if the Message was sent in a Text Channel
    if not isinstance(inter.channel, TextChannel):
        await inter.response.send_message("Im only able to clear webhooks inside of a Text Channel!", ephemeral=True)
        return

    webhooks = await inter.channel.webhooks()
    for webhook in webhooks:
        await webhook.delete()

    await inter.response.send_message("Webhooks cleared!", ephemeral=True)


@bot.slash_command(name="clear_threads")
async def clear_threads(inter: ApplicationCommandInteraction) -> None:
    """Clears the threads in a channel."""
    # Check user permissions
    permissions = inter.channel.permissions_for(inter.author)
    if not permissions.manage_threads:
        await inter.response.send_message("You dont have the permissions to Manage Threads!", ephemeral=True)
        return

    # Check if the Message was sent in a Text Channel
    if not isinstance(inter.channel, TextChannel):
        await inter.response.send_message("Im only able to clear threads inside of a Text Channel!", ephemeral=True)
        return

    for thread in inter.channel.threads:
        await thread.delete()

    await inter.response.send_message("Threads cleared!", ephemeral=True)


@bot.slash_command(name="start_game")
async def start_game(inter: ApplicationCommandInteraction) -> None:
    """Main Command of our Game: /start_game"""
    # Check if the Message was sent in a Text Channel
    if not isinstance(inter.channel, TextChannel):
        await inter.response.send_message(
            "You can only start a Game Session inside of a Text Channel!", ephemeral=True
        )
        return

    # Start Order Queue
    order_queue = OrderQueue(inter)
    # Load Restaurants
    restaurants = Restaurants(inter, order_queue)

    # Sending Start Menu Embed
    await inter.response.send_message(embed=restaurants.embeds[0], view=restaurants.view, ephemeral=True)

    # Spawning Orders
    await order_queue.spawn_orders()

    # Load ConditionManager (Orders need to be initialized)
    condition_manager = ConditionManager(order_queue, restaurants)
    restaurants.condition_manager = condition_manager
    # Spawning Conditions
    task = asyncio.create_task(condition_manager.spawn_conditions())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    # Creating Temporary example order
    from sincere_singularities.modules.order import CustomerInfo, Order

    customer_info = CustomerInfo(
        order_id="Test123",
        name="Customer Name",
        address="Customer Address",
        delivery_time="9 o'clock.",
        extra_information="Dont ring the bell.",
    )
    example_order_text = str(
        "OrderID: Test123 \n"
        "Hello, my name is Customer Name. I would like to have 2 Pizza Starter0 and a "
        "Main Course0 delivered to my house Customer Address at 9 o'clock. "
        "Please dont ring the bell."
    )
    example_order = Order(customer_information=customer_info, restaurant_name="Pizzaria")
    example_order.foods["Starters"].append("Pizza Starter0")
    example_order.foods["Starters"].append("Pizza Starter0")
    example_order.foods["Main Courses"].append("Main Course0")

    await order_queue.create_order("Customer Name", example_order_text, example_order)


@bot.event
async def on_ready() -> None:
    """Bot information logging when starting up."""
    print(
        f"Logged in as {bot.user} (ID: {bot.user.id}).\n"
        f"Running on {len(bot.guilds)} servers with {bot.latency * 1000:,.2f} ms latency.",
    )
