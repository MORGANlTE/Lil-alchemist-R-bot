import discord
from discord import app_commands
from discord.ui import Button, View, Select
from data.Apro.Aprogergely import imageeditor
from data.commands import *
from data.data_grabber import *
from data.packopening import *
from data.shortcuts import *
from data.exp_essentials import *
from data.trivia import *
import datetime
import discord
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import re
import json

# Load the .env file
load_dotenv()

# Variables:
version = "8.4.0"
versiondescription = "Updated arena cmd w/ amount & formatting updated"
gem_win_trivia = 5
winstreak_max = 10
gem_loss_trivia = -5
exp = 10

# Environment variables:
M_user_ids = os.getenv("M_USER_IDS").split(", ")
dbfile = os.getenv("DATABASE")
environment = os.getenv("ENVIRONMENT")
adminguildids = os.getenv("ADMIN_GUILDS").split(",")
print(f"Admin guilds: {adminguildids}")

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
        print(e)
        # print full error
        await interaction.followup.send(f"An error occured while searching for `{cardname}`: {e}")

@tree.command(
    name="arena",
    description="Look up current arena powers & upcoming ones",
    guilds=guilds
)
async def show_arena(interaction, amount: int = 2):
    """
    Shows the current and upcoming arena powers rotation
    Args:
        amount (int, optional): The amount of upcoming arena powers to show. Defaults to 2 (current and next)
    """
    await interaction.response.defer()
    try:
        embed = show_arena_embed(amount=amount, dbfile=dbfile, userid=interaction.user.id)
        if type(embed) == discord.Embed:
            await interaction.followup.send(embed=embed)
        elif type(embed) == int:
            await interaction.followup.send(f"Invalid amount of next arena powers, choose a number between 1 and {embed}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occured while searching for the arena powers: {e}")

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
        await interaction.followup.send(f"An error occured while searching for the combo: {e}")


@tree.command(
    name="help",
    description="Help with the commands",
    guilds=guilds,
)
async def help_command(interaction):
    try:
        embed = help_embed(version=version, description=versiondescription)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"An error occured while fetching the help: {e}")


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
        await interaction.response.send_message(f"An error occured while fetching the trivia question: {e}")

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
    try:
        embed = await leaderboard_embed(option=option, dbfile=dbfile, interaction=interaction)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"An error occured while fetching the leaderboard: {e}")



@tree.command(
    name="packopening",
    description="Open a pack",
    guilds=guilds,
)
async def packopening_command(interaction, packname: str):
    await interaction.response.defer()
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
        await interaction.followup.send(f"An error occured while opening the pack: {e}")

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
    try:
        res = await profile_embed(interaction=interaction, dbfile=dbfile)
        pic = res["pic"]
        discord_name = res["discord_name"]
    except Exception as e:
        await interaction.response.send_message(f"An error occured while fetching the profile: {e}")

    await interaction.followup.send(
        file=pic,
    )
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
    try:
        view = await setprofile_embed(interaction=interaction, dbfile=dbfile, option=option, page=page)
        await interaction.response.send_message(
            "Choose your profile picture",
            view=view, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occured while setting the profile: {e}")

@tree.command(
    name="claim",
    description="Claim your daily login!",
    guilds=guilds,
)
async def claim_command(interaction):
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
        await interaction.response.send_message(f"An error occured while claiming the daily login: {e}")

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
    try:
        returnmsg = add_stuff(option=option, amount=amount, userid=user_id, dbfile=dbfile, M_user_ids=M_user_ids, command_user=interaction.user.id)
        await interaction.response.send_message(f"{returnmsg}")
    except Exception as e:
        await interaction.response.send_message(f"An error occured while adding stuff: {e}")

@tree.command(
    name="store",
    description="Open the store",
    guilds=guilds,
)
async def store_command(interaction):

    pages = ["Avatars", "🚧 - Backgrounds - 🚧", "🚧 - Borders - 🚧"]
    class PfpSelect(discord.ui.Select):
        def __init__(self, options):
            super().__init__(placeholder='Buy your new pfp...', options=options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            pfpid = self.values[0]
            user_id = interaction.user.id
            # buy the pfp
            returnmsg = buy_pfp(pfpid, user_id, dbfile)
            if returnmsg[0] == True:
                print(f"[Store] User {user_id} bought pfp {pfpid}")
            # give feedback to user
            await interaction.followup.send(
                f"{returnmsg[0] == True and '✅' or '⛔'} {returnmsg[1]}",
                ephemeral=True
            )

    class StoreSelect(discord.ui.Select):
        def __init__(self, options):
            super().__init__(placeholder='Choose your answer...', options=options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            label = self.values[0]
            user_id = interaction.user.id
            if label == "Avatars":
                nb_pfps = get_store_pfps_not_bought(user_id, dbfile)
                if len(nb_pfps) == 0:
                    await interaction.followup.send(
                        f"🛒 You have bought all the profile pictures!",
                        ephemeral=True
                    )
                    return
                # we got the pfps, now we need to make a select with all the pfps
                options = [discord.SelectOption(label=answer, value=str(i)) for i, answer in nb_pfps.items()]
                select = PfpSelect(options)
                view = discord.ui.View(timeout=None)
                view.add_item(select)
                await interaction.followup.send(
                    "Buy a pfp",
                    view=view, ephemeral=True)
    
    # Define the question and answers
    options = [discord.SelectOption(label=answer) for i,answer in enumerate(pages)]
    select = StoreSelect(options)
    view = discord.ui.View(timeout=None)
    view.add_item(select)

    await interaction.response.defer()
    embed = discord.Embed(
        title="Store",
        description="Here are the available items in the store:",
        color=discord.Color.teal(),
    )
    embed.add_field(
        name="Avatars",
        value="",
        inline=True,
    )
    embed.add_field(
        name="🚧 - Backgrounds",
        value="",
        inline=True,
    )
    embed.add_field(
        name="Borders - 🚧",
        value="",
        inline=True,
    )

    embed.set_footer(
        text="Made with love by _morganite",
        icon_url="https://iili.io/JlxAR7R.png",
    )

    await interaction.followup.send(embed=embed, view=view)

@tree.command(
    name="inventory",
    description="Open your inventory",
    guilds=guilds,
)
async def inventory_command(interaction):
    await interaction.response.defer()
    embed = discord.Embed(
        title="Inventory",
        description="Here are the items in your inventory:",
        color=discord.Color.teal(),
    )
    
    pfps = get_pfps(interaction.user.id, dbfile)
    pfps = json.loads(pfps)
    pfps = [get_description_pfp(pfps[i]) for i in range(len(pfps))]
    
    chunked_pfps = list(chunk_list(pfps, 5))

    embed.add_field(
        name="Profile Pictures",
        value="\n",
        inline=False,
    )

    for i, chunk in enumerate(chunked_pfps):
        embed.add_field(
            name=f"** **",
            value="\n".join(chunk),
            inline=True,
        )

    embed.set_footer(
        text="Made with love by _morganite",
        icon_url="https://iili.io/JlxAR7R.png",
    )

    await interaction.followup.send(embed=embed)


    
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
    try:
        filepath = "./data/Apro/"
        imageCards = imageeditor(image_location=filepath, cardname=name, rarity=option.value, attack=atk, defense=dfc, isFinalForm=is_final_form, level="1", imgurl=img_url, offset_x=0, offset_y=0, resize_factor_override=100)

        await interaction.followup.send(
            f"{interaction.user.mention} generated `{name}`",
            file=imageCards,
        )
        print("Generated card " + name)
    except Exception as e:
        await interaction.followup.send(
            f"An error occured while generating the card `{name}`, please check your image url"
        )
    
    os.remove(f"{imageCards.filename}")


@tree.command(
    name="packview",
    description="What in the pack? Only one way to find out.",
    guilds=guilds,
)
async def generate_command(interaction, packname:str):
    if len(packname) < 2:
        await interaction.response.send_message(f"There are no pack names this short man, what r u doing 😅", ephemeral=True)
        return
    packcontent = get_pack_contents(packname)

    if packcontent == "Not found":
        closestpack = find_closest_pack(packname, get_packs())
        await interaction.response.send_message(f"Pack `{packname}` not found\nDid you mean `{closestpack}`?", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"{packname} Pack",
        color=discord.Color.dark_magenta(),
    )
    # link to the wiki
    embed.add_field(
        name="Wiki Page",
        value=f"[Click here to visit the wiki page](https://lil-alchemist.fandom.com/wiki/Special_Packs/{packname.replace(' ', '_')})",
        inline=False,
    )

    for row in packcontent["cards"]:
        embed.add_field(name=row[0].replace("_", " ").replace("%27s", "'").replace("%26", "&"), value=row[2] + " " + row[1], inline=True)
    
    # check if valid url

    if re.match(r"(http|https)://.*\.(?:png|jpg|jpeg|gif|png)", packcontent["img"]):
        embed.set_thumbnail(url=packcontent["img"])

    print("[PackLookup] " + packname)
    await interaction.response.send_message(embed=embed)

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
    try:
        if goblintime is None:
            gtime = datetime.now()
        else:
            gtime = datetime.strptime(goblintime, "%m-%d-%Y")
    except:
        await interaction.response.send_message("Please provide a valid date in the format MM-DD-YYYY", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Goblins overview",
        color=discord.Color.brand_red(),
    )
    
    goblins = get_goblins()

    goblin = goblin.value 
    
    spawntimeC = (gtime + timedelta(days=goblins[goblin]["spawn_daysC"])).strftime("%m-%d-%Y")
    spawntime = (gtime + timedelta(days=goblins[goblin]["spawn_days"])).strftime("%m-%d-%Y")
    # convert spawntime to unix timestamp
    spawn_timestamp = int(datetime.strptime(spawntime, "%m-%d-%Y").timestamp())
    spawnC_timestamp = int(datetime.strptime(spawntimeC, "%m-%d-%Y").timestamp())

    rewardstext = "\n".join(goblins[goblin]["rewards"])
    embed.add_field(
        name=str(goblins[goblin]["name"]) + " " + str(goblins[goblin]['emoji']),
        value=f"<t:{spawn_timestamp}:D>\n{goblins[goblin]['health']} HP\n{str(goblins[goblin]['spawnC'])}% chance starting day <t:{spawnC_timestamp}:D>\n",
        inline=False
    )
    embed.add_field(
        name="Rewards",
        value=rewardstext,
        inline=False
    )

    embed.add_field(
        name="** **",
        value="<:newMBot0:1251265938142007486> Goblin info - :heart: <@511322291972341800> for the data",
        inline=False,
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(
    name="support",
    description="How to contact support",
    guilds=guilds,
)

async def support_command(interaction):
    embed = discord.Embed(
        title="Support",
        color=discord.Color.teal(),
    )
    embed.add_field(
        name="** **",
        value="""
        Hey there, magical adventurer! 🧙‍♂️ Need a hand in the mystical world of Little Alchemist Remastered?
        \n🌟 Just shoot an email over to `support@littlealchemist.io` with your Player ID, Player Name, and spill the beans about the puzzling enigma you've stumbled upon. 
        \n🕵️‍♂️ We're all ears (and wands)! Don't forget to spice it up with images or videos—let's make this adventure one for the scrolls! 📜✨
        \n👑 When it comes to questions about gameplay, remember, our Discord community is your enchanted haven! 
        \n🔮 Join the fun, share your wisdom, and get answers from fellow adventurers. 
        \n🗡️🛡️ Let's keep the magic alive, and may your gaming journey be filled with epic adventures and laughter! 🌟🤗✨""",
        inline=False,
    )
    embed.add_field(
        name="** **",
        value="*<:newMBot0:1251265938142007486> ChinBot is not in any way affiliated with [Monumental](https://monumental.io/)*",
    )
    await interaction.response.send_message(embed=embed)


@tree.command(
    name="sync",
    description="Sync the commands",
    guilds=adminguilds,
)
async def sync_command(interaction):
    await interaction.response.defer()
    await tree.sync()
    for guild in adminguilds:
      await tree.sync(guild=guild)
    await interaction.followup.send("Synced")
    print("[V] Synced Guilds")


@client.event
async def on_ready():
    for guild in adminguilds:
      await tree.sync(guild=guild)
    print("[V] Finished setting up commands")
    print(f"[V] Logged in as {client.user} (ID: {client.user.id})")
    delete_saved_images()
    print("[V] Cleared images folder")
    setup_packs()
    print("[V] Setup the packs")
    setup_database(dbfile)
    print("[V] Db created/checked")


client.run(os.getenv("TOKEN"))
