import discord
from discord import app_commands
from data.Apro.Aprogergely import imageeditor
from data.commands import *
from data.data_grabber import *
from data.packopening import *
from data.shortcuts import *
from data.exp_essentials import *
from data.trivia import *
import discord
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Variables:
version = "8.6.3"
versiondescription = "More bugs fixed"
gem_win_trivia = 5
winstreak_max = 10
gem_loss_trivia = -5
exp = 10

# Environment variables:
M_user_ids = os.getenv("M_USER_IDS").split(", ")
dbfile = os.getenv("DATABASE")
admindbfile = os.getenv("ADMIN_DB")
environment = os.getenv("ENVIRONMENT")
adminguildids = os.getenv("ADMIN_GUILDS").split(",")

adminguilds = []
for guild in adminguildids:
    adminguilds.append(discord.Object(id=int(guild)))

if environment == "testing":
    guilds=[discord.Object(id=945414516391424040), discord.Object(id=1021360015061291008)]
elif environment == "production":
    guilds=[]
else:
    print("Running in unknown environment")
print(f"Running in {environment} environment")

# Discord bot business:
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(
    name="wiki",
    description="Look up a card on the LAR wiki",
    guilds=guilds
)
async def show_command(interaction, cardname: str, is_onyx: bool = False):
    await interaction.response.defer()
    try:
        embed = await show_command_embed(cardname, is_onyx)

        if embed:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"Card `{cardname}` not found")
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while searching for `{cardname}`", interaction)


@tree.command(
    name="combo",
    description="Look up a card on the LAR wiki",
    guilds=guilds
)
async def combo_command(interaction, card1: str, card2: str):
    await interaction.response.defer()
    print("[Combo] " + card1 + " + " + card2)
    try:
        embed = show_combo_embed(card1=card1, card2=card2)
        if type(embed) == discord.Embed:
            await interaction.followup.send(embed=embed)
        elif type(embed) == str:
            await interaction.followup.send(f"Card `{embed}` not found")
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while searching for the combo: {e}", interaction)

@tree.command(
    name="help",
    description="Help with the commands",
    guilds=guilds,
)
async def help_command(interaction):
    print("[Help] " + interaction.user.name)
    try:
        embed = help_embed(version=version, description=versiondescription)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while using help cmd: {e}", interaction)

groupArena = app_commands.Group(name="arena", description="Arena related commands")

@groupArena.command(
    name="powers",
    description="Look up current arena powers & upcoming ones",
)
async def show_arena(interaction, amount: int = 2):
    """
    Shows the current and upcoming arena powers rotation
    Args:
        amount (int, optional): The amount of upcoming arena powers to show. Defaults to 2 (current and next)
    """
    await interaction.response.defer()
    print("[ArenaPowers] " + str(amount))
    try:
        embed = show_arena_embed(amount=amount, dbfile=dbfile, userid=interaction.user.id)
        if type(embed) == discord.Embed:
            await interaction.followup.send(embed=embed)
        elif type(embed) == int:
            await interaction.followup.send(f"Invalid amount of next arena powers, choose a number between 1 and {embed}", ephemeral=True)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while searching for the arena powers: {e}", interaction)


@groupArena.command(
    name="reset",
    description="At what time does arena resets?",
)
async def show_reset(interaction):
    """
    Shows when the arena reset is going to happen

    """
    await interaction.response.defer()
    print("[ArenaReset]")
    try:
        embed = show_arena_reset_embed()
        if type(embed) == discord.Embed:
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while searching for the arena powers: {e}", interaction)

# add the group to the tree
tree.add_command(groupArena)


@tree.command(
    name="trivia",
    description="Start a trivia question",
    guilds=guilds,
)
async def trivia_command(interaction):
    # Define the question and answers
    try:
        r = await interaction.response.send_message("** **")
        message = await interaction.channel.send("Loading trivia question...")
        embed, view = await trivia_embed(interaction=interaction, winstreak_max=winstreak_max, gem_win_trivia=gem_win_trivia, gem_loss_trivia=gem_loss_trivia, dbfile=dbfile, message=message)
        await message.edit(embed=embed, view=view, content="")
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while getting trivia: {e}", interaction)

@tree.command(
    name="leaderboard",
    description="Leaderboard for the server",
    guilds=guilds,
)
@app_commands.describe(option="Choose what type of leaderboard you want")
@app_commands.choices(option=[
        app_commands.Choice(name="🎉Level", value="Exp"),
        app_commands.Choice(name="💎Gems", value="Gems")
    ])
async def leaderboard_command(interaction, option: app_commands.Choice[str]):
    await interaction.response.defer()
    print("[Leaderboard] " + option.value)
    try:
        embed = await leaderboard_embed(option=option, dbfile=dbfile, interaction=interaction)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while getting the leaderboard: {e}", interaction)

@tree.command(
    name="packopening",
    description="Open a pack",
    guilds=guilds,
)
async def packopening_command(interaction, packname: str):
    await interaction.response.defer()
    print("[PackOpening] " + packname)
    try:
        imgcards, embed = await packopening_embed(interaction=interaction, packname=packname)
        if embed == False:
            await interaction.followup.send(
                f"{imgcards}",
            )
            return
        else:
            await interaction.followup.send(
                f"{interaction.user.mention} opened `{packname}` Pack",
                file=imgcards,
                embed=embed if embed == 4 else None,
            )
        
        os.remove(f"./images/{imgcards.filename}")
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while opening pack `{packname}`: {e}", interaction)


@client.event
async def on_message(message):
    on_message_handler(message=message, dbfile=dbfile, exp=exp)

@tree.command(
    name="profile",
    description="Your Discord Profile",
    guilds=guilds,
)
async def profile_command(interaction):
    # Define the question and answers
    await interaction.response.defer()
    print("[Profile] " + interaction.user.name)
    try:
        res = await profile_embed(interaction=interaction, dbfile=dbfile)
        pic = res["pic"]
        discord_name = res["discord_name"]
        await interaction.followup.send(
            file=pic,
        )
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while getting your profile: {e}", interaction)
    # remove the image
    os.remove(f"./important_images/{discord_name}.png")

    

@tree.command(
    name="setprofile",
    description="Edit your Discord Profile",
    guilds=guilds,
)
@app_commands.describe(option="Choose what type of profile element you want to set")
@app_commands.choices(option=[
        app_commands.Choice(name="🖼️ Avatar", value="avatar"),
        app_commands.Choice(name="🌄 Background", value="background"),
        app_commands.Choice(name="🖌️ Border", value="border")
    ])
async def setprofile_command(interaction, option: app_commands.Choice[str], page: int = 1):
    await interaction.response.defer()
    print("[SetProfile] " + option.value)
    try:
        view = await setprofile_embed(interaction=interaction, dbfile=dbfile, option=option, page=page)
        if type(view) == str:
            await interaction.followup.send(content=view, ephemeral=True)
            return
        await interaction.followup.send(
            "Choose your profile picture",
            view=view, ephemeral=True)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while setting your profile: {e}", interaction)

@tree.command(
    name="claim",
    description="Claim your daily login!",
    guilds=guilds,
)
async def claim_command(interaction):
    print("[Claim] " + interaction.user.name)
    try:
        return_value, text = claim_daily(interaction.user.id, dbfile)
        if return_value == "User not found":
            embed = discord.Embed(
                title="Daily Login",
                description="You need at least 1 message in this server before claiming your Daily Login!",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif return_value == False:
            embed = discord.Embed(
                title="Daily Login",
                description="Next Daily Login " + str(text) + " :clock5:",
                color=discord.Color.orange(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            embed = discord.Embed(
                title="Daily Login",
                description="You have claimed your daily login! \n\n" + str(text),
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while claiming daily login: {e}", interaction)

@tree.command(
    name="addstuff",
    description="Just a command for M",
    guilds=adminguilds,
)
@app_commands.describe(option="Choose what type of stuff")
@app_commands.choices(option=[
        app_commands.Choice(name="📞Exp", value="Exp"),
        app_commands.Choice(name="💎Gems", value="Gems")
    ])
async def addstuff_command(interaction, option: app_commands.Choice[str], amount: int, user_id: str):
    print("[AddStuff] " + str(option) + " " + str(amount) + " " + user_id)
    try:
        returnmsg = add_stuff(option=option, amount=amount, userid=user_id, dbfile=dbfile, M_user_ids=M_user_ids, command_user=interaction.user.id)
        await interaction.response.send_message(f"{returnmsg}")
    except Exception as e:
        handle_error(client, admindbfile, e, f"An error occured while adding: {e}", interaction)

@tree.command(
    name="store",
    description="Open the store",
    guilds=guilds,
)
async def store_command(interaction):
    await interaction.response.defer()
    print("[Store] " + interaction.user.name)
    try:
        embed, view = await store_embed(interaction=interaction, dbfile=dbfile)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while getting the store: {e}", interaction)

@tree.command(
    name="inventory",
    description="Open your inventory",
    guilds=guilds,
)
async def inventory_command(interaction):
    await interaction.response.defer()
    print("[Inventory] " + interaction.user.name)
    try:
        embed = await inventory_embed(interaction=interaction, dbfile=dbfile)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while opening your inventory: {e}", interaction)

    
# worker example:

# last_run = datetime.now().date()  # Set the last run date to the first day of the month

# @tasks.loop(seconds=30)  # Loop every 60 seconds
# async def send_message_at():
#     global last_run
#     now = datetime.now()
#     target_time = time(12, 0, 0)  # Target time is 12:00:00
#     print("trying")
#     if now.time() >= target_time and (last_run is None or last_run < now.date()):
#         print("done")
#         last_run = now.date()  # Update the last run date

@tree.command(
    name="generate",
    description="Generate a card - huge thanks to Aprogergely",
    guilds=guilds,
)
@app_commands.describe(option="Choose rarity")
@app_commands.choices(option=[
        app_commands.Choice(name="Bronze", value="Bronze"),
        app_commands.Choice(name="Silver", value="Silver"),
        app_commands.Choice(name="Gold", value="Gold"),
        app_commands.Choice(name="Diamond", value="Diamond"),
        app_commands.Choice(name="Onyx", value="Onyx")
    ])
async def generate_command(interaction, option:app_commands.Choice[str], name:str, atk: str, dfc:str, img_url: str, is_final_form:bool):
    await interaction.response.defer()
    print("[Generate] " + name)
    try:
        filepath = "./data/Apro/"
        imageCards = imageeditor(image_location=filepath, cardname=name, rarity=option.value, attack=atk, defense=dfc, isFinalForm=is_final_form, level="1", imgurl=img_url, offset_x=0, offset_y=0, resize_factor_override=100)

        await interaction.followup.send(
            f"{interaction.user.mention} generated `{name}`",
            file=imageCards,
        )
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while generating the card: {e}", interaction)
    
    os.remove(f"{imageCards.filename}")


@tree.command(
    name="generatemultiple",
    description="Generate cards",
    guilds=adminguilds,
)
async def generate_command(interaction, options:str, names:str, atks: str, dfcs:str, img_urls: str, is_final_forms:str):
    await interaction.response.defer()
    filename_locations = []
    imageCardsList = []
    for option, name, atk, dfc, img_url, is_final_form in zip(options.split(", "), names.split(", "), atks.split(", "), dfcs.split(", "), img_urls.split(", "), is_final_forms.split(",")):
        print("[Generate] " + name)
        try:
            filepath = "./data/Apro/"
            imageCards = imageeditor(image_location=filepath, cardname=name, rarity=option, attack=atk, defense=dfc, isFinalForm=is_final_form, level="1", imgurl=img_url, offset_x=0, offset_y=0, resize_factor_override=100)
            imageCardsList.append(imageCards)
            filename_locations.append(imageCards.filename)
        except Exception as e:
            await handle_error(client, admindbfile, e, f"An error occured while generating the card: {e}", interaction)

    await interaction.followup.send(
            f"{interaction.user.mention} generated `{names}`:",
            files=imageCardsList,
        )
    for filename in filename_locations:
        os.remove(f"{filename}")


@tree.command(
    name="packview",
    description="What in the pack? Only one way to find out.",
    guilds=guilds,
)
async def generate_command(interaction, packname:str):
    print("[PackView] " + packname)
    try:
        embed = packview_embed(packname)
        if type(embed) == str:
            await interaction.response.send_message(content=embed)
            return
        await interaction.response.send_message(embed=embed)
        print("[PackView] " + packname)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while looking up the pack `{packname}`: {e}", interaction)

@tree.command(
    name="goblin",
    description="When does my goblin spawn?",
    guilds=guilds,
)
@app_commands.describe(goblin="Choose Goblin")
@app_commands.choices(goblin=[
        app_commands.Choice(name="Gold", value="gobgold"),
        app_commands.Choice(name="Diamond", value="gobdia"),
        app_commands.Choice(name="Goblin king", value="gobking")
    ])
async def goblin_command(interaction, goblin:app_commands.Choice[str], goblintime: str = None):
    """
    You can check out here when the goblin spawns and what rewards you can get from it.

    Args:
        goblintime (str, optional): MM-DD-YYYY The date you want to check the goblin for. Standard is today.
    """
    await interaction.response.defer()
    print("[Goblin] " + goblin.value)
    try:
        embed = goblin_embed(goblin=goblin.value, goblintime=goblintime)
        if type(embed) == str:
            await interaction.followup.send(content=embed)
            return
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while checking the goblin: {e}", interaction)
 

@tree.command(
    name="support",
    description="How to contact support",
    guilds=guilds,
)

async def support_command(interaction):
    print("[Support] " + interaction.user.name)
    try:
        embed = support_embed()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while getting support cmd: {e}", interaction)


@tree.command(
    name="sync",
    description="Sync the commands",
    guilds=adminguilds,
)
async def sync_command(interaction):
    await interaction.response.defer()
    print("[Sync] " + interaction.user.name)
    try:
        val = await sync_command_handler(userid=str(interaction.user.id), M_user_ids=M_user_ids, adminguilds=adminguilds, tree=tree)
        await interaction.followup.send(val)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while trying to sync: {e}", interaction)

@tree.command(
    name="setlogging",
    description="Add/Remove current channel as logging channel",
    guilds=adminguilds,
)
async def setlogging_command(interaction):
    await interaction.response.defer()
    print("[SetLogging] " + interaction.user.name)
    try:
        val = await setlogging_command_handler(interaction=interaction, admindbfile=admindbfile)
        await interaction.followup.send(val)
    except Exception as e:
        await handle_error(client, admindbfile, e, f"An error occured while trying to set logging: {e}", interaction)


@client.event
async def on_ready():
    await on_startup_handler(adminguilds=adminguilds, tree=tree, client=client, dbfile=dbfile, admindbfile=admindbfile)

client.run(os.getenv("TOKEN"))
