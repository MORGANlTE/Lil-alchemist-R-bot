import discord
from discord import app_commands, ButtonStyle, SelectOption
from discord.ui import Button, View, Select
from data.data_grabber import *
from data.packopening import *
from data.shortcuts import *
import datetime
from data.exp_essentials import *
import discord
import requests
from bs4 import BeautifulSoup
from data.trivia import *
import os
from dotenv import load_dotenv
from data.Apro.Aprogergely import imageeditor
import re
import json


# Load the .env file
load_dotenv()

# Variables:
version = "8.1.0"
versiondescription = "Leaderboard avatars added permanently"

gem_win_trivia = 5
winstreak_max = 10
gem_loss_trivia = -5
exp = 10
# get userids from .env file
M_user_ids = os.getenv("M_USER_IDS").split(", ")
print(M_user_ids)
dbfile = os.getenv("DATABASE")

# Check the value of the ENVIRONMENT variable
environment = os.getenv("ENVIRONMENT")
reset_commands = os.getenv("RESET_COMMANDS") if os.getenv("RESET_COMMANDS") is not None else True

if environment == "testing":
    guilds=[discord.Object(id=945414516391424040), discord.Object(id=1021360015061291008)]
elif environment == "production":
    guilds=[]
else:
    # Code for other environments or default behavior
    print("Running in unknown environment")
print(f"Running in {environment} environment")

# Functions:
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
    # test if this url gives us a boss card or a normal card
    print("[Searching] " + cardname)
    t = check_if_custom_name(cardname)
    if t is not None and t is not False:
        await interaction.followup.send(embed=t)
        return

    if is_onyx:
        cardname += "_(Onyx)"
    url = f"https://lil-alchemist.fandom.com/wiki/{cardname.title().replace(' ', '_').replace('_And_', '_and_')}"
    test = ()
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")
        test = parseinfo(soup, cardname)
    except Exception as e:
        # print(f"Error: {str(e)}")
        try:
            print("card not found, checking boss card")
            url = f"https://lil-alchemist.fandom.com/wiki/{cardname.title().replace(' ', '_')}_(Card)"
            resp = requests.get(url)
            soup = BeautifulSoup(resp.content, "html.parser")
            test = parseinfo(soup, cardname)
        except Exception as e:
            # print the exact error happening
            # print(f"Error: {str(e)}")
            try:
                print("card not found, checking capitalized card")
                url = f"https://lil-alchemist.fandom.com/wiki/{cardname.replace(' ', '_')}"
                resp = requests.get(url)
                soup = BeautifulSoup(resp.content, "html.parser")
                test = parseinfo(soup, cardname)
            except Exception as e:
                # print the exact error happening
                # print(f"Error: {str(e)}")
                await interaction.followup.send(
                    f"Card `{cardname}` not found", ephemeral=True
                )
                return

    # if we get here, the card is found

    (
        imgurl,
        description,
        base_attack,
        base_defense,
        base_power,
        rarity,
        form,
        fusion,
        where_to_acquire,
        recipes,
        combos,
        level_stats,
    ) = test
    # transform the name cardname eg chinchilla into Chinchilla and dr. robo into Dr. Robo

    embed = discord.Embed(
        color=get_embedcolor(rarity),
    )
    embed.set_author(
        icon_url=get_fusion_url(fusion),
        name=f"{fusion}",
    )
    # add url link to wiki
    embed.add_field(
        name="Wiki Page",
        value=f"[Click here to visit the wiki page]({url})",
        inline=False,
    )
    embed.add_field(name="Full Name", value=cardname.title(), inline=True)
    embed.add_field(name="Rarity", value=rarity, inline=True)
    embed.add_field(name="Description", value=description, inline=False)
    embed.set_thumbnail(url=imgurl)
    levels_left = ""
    levels_right = ""
    for level in level_stats.items():
        level_text = f"{level[0]}  -  {level[1]['Attack']}/{level[1]['Defense']}\n"
        if int(level[0]) >= 4:
            levels_right += level_text
        else:
            levels_left += level_text

    embed.add_field(name="Levels", value=levels_left, inline=True)
    embed.add_field(name="** **", value=levels_right, inline=True)

    embed.add_field(
        name="Where to acquire", value=", ".join(where_to_acquire), inline=False
    )

    if fusion == "Orb":
        embed.add_field(
            name="Combos",
            value=f"Amount of Combos: {len(combos)}",
            inline=False,
        )

    else:
        combos_left = []
        combos_right = []
        counter = 0
        if rarity == "Onyx":
            # filter out all non onyx combos
            combos = [
                combo
                for combo in combos
                if "(Onyx)" in combo[0] and "(Onyx)" in combo[1]
            ]
        else:
            # filter out all onyx combos
            combos = [
                combo
                for combo in combos
                if not "(Onyx)" in combo[0] and not "(Onyx)" in combo[1]
            ]

        for combo in recipes:
            if counter < (len(recipes) / 2):
                combos_left.append(f"{counter+1}.{combo[1]} + {combo[0]}")
            else:
                combos_right.append(f"{counter+1}.{combo[1]} + {combo[0]}")
            counter += 1

        # if empty combos, add a "/"
        if len(recipes) == 0:
            embed.add_field(name="Combos", value="/", inline=True)
            embed.add_field(name="** **", value="", inline=True)
        else:
            embed.add_field(name="Combos", value="\n".join(combos_left), inline=True)
            embed.add_field(name="** **", value="\n".join(combos_right), inline=True)

    # add underneath the author the rarity and form
    embed.set_footer(
        text=f"{cardname.title()} - {rarity} ~ ChinBot & LAR Wiki",
        icon_url=get_fusion_url(fusion),
    )

    await interaction.followup.send(embed=embed)


@tree.command(
    name="help",
    description="Help with the commands",
    guilds=guilds,
)
async def help_command(interaction):
    avatar_url = client.user.avatar.url

    embed = discord.Embed(
        title="Bot Commands",
        description="Here are the available commands:",
        color=discord.Color.teal(),
    )

    embed.add_field(
        name="Informational",
        value="** **",
        inline="False",
    )
    

    embed.add_field(
        name=":game_die: /wiki",
        value="Searches the specified card on the wiki",
        inline=True,
    )
    embed.add_field(
        name=":flower_playing_cards: /packview",
        value="Shows the contents of a pack",
        inline=True,
    )
    embed.add_field(
        name=":question: /help",
        value="Displays the help page",
        inline=True,
    )
    embed.add_field(
        name="<:gobking:1258839599938142269> /goblin",
        value="Shows the next goblin spawn",
        inline=True,
    )

    # empty row here:
    embed.add_field(
        name="** **",
        value="** **",
        inline=False,
    )
    embed.add_field(
        name="\nServer related",
        value="** **",
        inline="False",
    )
    
    embed.add_field(
        name=":coin: /leaderboard",
        value="Shows the global leaderboard",
        inline=True,
    )
    embed.add_field(
        name=":bar_chart: /profile",
        value="Shows your profile",
        inline=True,
    )
    embed.add_field(
        name="👑 /setprofile",
        value="Edit your profile",
        inline=True,
    )
    
    embed.add_field(
        name=":sos: /support",
        value="How to contact support for Monumental",
        inline=True,
    )
    
    # empty row here:
    embed.add_field(
        name="** **",
        value="** **",
        inline=False,
    )
    embed.add_field(
        name="\nFun",
        value="** **",
        inline="False",
    )

    embed.add_field(
        name=":moneybag: /claim",
        value="Claim your daily login",
        inline=True,
    )
    embed.add_field(
        name=":package: /packopening",
        value="Opens a pack",
        inline=True,
    )
    embed.add_field(
        name=":gem: /trivia",
        value="Some fun trivia to try out",
        inline=True,
    )
    embed.add_field(
        name=":shopping_cart: /store",
        value="Open the store",
        inline=True,
    )
    embed.add_field(
        name="🚁 /inventory",
        value="Shows your inventory",
        inline=True,
    )
    embed.add_field(
        name=":coral: /generate",
        value="Make a custom card classical LA style! - Thx Aprogergely!",
        inline=True,
    )
    embed.add_field(
        name="** **",
        value=f"<:newMBot0:1251265938142007486> v{version} - {versiondescription}\n*All copyrighted material belongs to [Monumental](https://monumental.io/)*",
        inline=False,
    )

    embed.set_footer(
        text="Made with love by _morganite",
        icon_url="https://iili.io/JlxAR7R.png",
    )

    await interaction.response.send_message(embed=embed)


@tree.command(
    name="trivia",
    description="Start a trivia question",
    guilds=guilds,
)
async def trivia_command(interaction):
    # Define the question and answers

    class TriviaSelect(discord.ui.Select):
            def __init__(self, options, trivia, dbfile, embed, message):
                super().__init__(placeholder='Choose your answer...', options=options)
                self.trivia = trivia
                self.dbfile = dbfile
                self.embed = embed
                self.message = message

            async def callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                label = self.values[0]
                user_id = interaction.user.id
                streak = get_winstreak(user_id, self.dbfile)
                if streak == None:
                    streak = 1
                elif streak >= winstreak_max:
                    streak = winstreak_max
                else:
                    streak += 1

                # check if the user was wrong or right
                if self.trivia.answers.index(label) != self.trivia.correct_answer_index:
                    return_message = f"⛔ {interaction.user.mention} did not answer `{self.trivia.answers[self.trivia.correct_answer_index]}` {gem_loss_trivia} :gem:"
                    update_winstreak(user_id, dbfile, 0)
                else:
                    return_message = f"✅ {interaction.user.mention} answered `{self.trivia.answers[self.trivia.correct_answer_index]}`\n+{gem_win_trivia + streak} :gem: 🔥 {streak}"
                    update_winstreak(user_id, dbfile, streak)
                newgems = add_gems_to_user(user_id, (gem_win_trivia + streak), dbfile)

                # add the message to the embed
                self.embed.add_field(name="Answer", value=return_message, inline=False)

                # we edit the embed again, with a new question
                embed, trivia = await generate_embed_trivia(interaction)
                self.options = [discord.SelectOption(label=answer) for answer in trivia.answers]
                self.trivia = trivia
                embed.add_field(name="Last question", value=return_message, inline=False)
                self.embed = embed
                # put the new embed
                await self.message.edit(embed=embed, view=self.view)
                    
    r = await interaction.response.send_message("** **")
    message = await interaction.channel.send("Loading trivia question...")
    embed, trivia = await generate_embed_trivia(interaction)
    emojis = ["1️⃣", "2️⃣", "3️⃣"]
    options = [discord.SelectOption(label=answer, emoji=emojis[i]) for i,answer in enumerate(trivia.answers)]
    select = TriviaSelect(options, trivia, dbfile, embed=embed, message=message)
    view = discord.ui.View(timeout=None)
    view.add_item(select)

    await message.edit(embed=embed, view=view, content="")

    # edit_only = False
    # last_message = await interaction.channel.history(limit=1).flatten()
    # if last_message[0].id != interaction.message.id:
    #     edit_only = True

    # we let the user select an answer, now we check if the answer is correct
    # get the answer:
    # message = await interaction.followup.send(embed=embed, view=view)

    

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
    category = True if option.value == "Gems" else False
    # Define the question and answers
    await interaction.response.defer()
    top_users = get_top_users(dbfile, category)
    gemsAndPerc = get_users_gems_and_top_percentage(interaction.user.id, dbfile)
    # if any value in the list is None, set it to 0
    if gemsAndPerc is None:
        gemsAndPerc = [0, 0]

    # for each gem and percentage, if it is None, set it to 0
    newlist = []
    for i in range(len(gemsAndPerc)):
        if gemsAndPerc[i] is None:
            newlist.append(0)
        else:
            newlist.append(gemsAndPerc[i])

    gemsAndPerc = newlist

    # Format the top users into a mentionable format
    description = "**Your score**\n"
    if not category:
        description += f"#{str(gemsAndPerc[3])}"
        description += f" - {int(gemsAndPerc[2])} Exp"
    else:
        description += f":gem: {str(gemsAndPerc[0])} - 🔥{int(gemsAndPerc[1])}"
        
    description += f"\n\n**Global {':gem: ' if category else ':crown: '}leaderboard:**\n"

    for i, user in enumerate(top_users):
        if category:
            description += f"\n{get_medal_emoji(i+1)} <@{user[1]}> - :gem: {user[2]} | 🔥 {user[3]}\n"
        else:
            description += f"\n{get_medal_emoji(i+1)} <@{user[1]}> - 👑 Lvl {calculate_level(user[4])} | {user[4]} Exp\n"
    set_leaderboard_rank_pfps(gemsAndPerc[3], interaction.user.id, dbfile)
    embed = discord.Embed(
        description=f"{description}",
        color=discord.Color.brand_green(),
    )
    iconurl = interaction.user.avatar.url if interaction.user.avatar else "https://iili.io/JlxRIZ7.png"
    embed.set_author(
        name=f"{interaction.user.name}'s score",
        icon_url=iconurl
    )
    if category:
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2850/2850979.png")
    else:
        embed.set_thumbnail(url="https://iili.io/Jc4oxEl.png")
    await interaction.followup.send(embed=embed)

def get_medal_emoji(rank):
    if rank == 1:
        return "🥇"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    elif rank == 4:
        return "🔥"
    else:
        return "👾"
  


@tree.command(
    name="packopening",
    description="Open a pack",
    guilds=guilds,
)
async def packopening_command(interaction, packname: str):
    await interaction.response.defer()
    packname = packname.strip()

    if len(packname) < 2:
        await interaction.response.send_message(f"There are no pack names this short man, what r u doing 😅", ephemeral=True)
        return
    
    gif = discord.File(
            f"./opening.gif",
            filename=f"opening.gif",
        )

    waiting = await interaction.followup.send(
        f"{interaction.user.mention} waiting for `{packname}` Pack...",
        file=gif,
    )

    # Simulate opening a pack and get the image URL of the card
    imageCards = await simulate_pack_opening(packname)


    if imageCards == "Not found":
        imageCards = await simulate_pack_opening(packname.capitalize())

    await waiting.delete()

    if imageCards == "Not found":
        closestpack = find_closest_pack(packname.replace(" ", "_"), get_packs())
        await interaction.followup.send(f"Pack `{packname}` not found\nDid you mean `{closestpack.replace('_', ' ')}`?", ephemeral=True)
        return
    if imageCards == "Error occured":
        await interaction.followup.send(
            f"An error occured while opening pack `{packname}`, please check console")
        return
    # random number between 1 and 4, if 4 send the embed
    randomNumber = random.randint(1, 4)

    embed = discord.Embed(
        description=f"You found 10 <:fragment:1196793443612098560>",
        color=discord.Color.teal(),
    )


    await interaction.followup.send(
        f"{interaction.user.mention} opened `{packname}` Pack",
        file=imageCards,
        embed=embed if randomNumber == 4 else None,
    )
    
    # remove the image

    os.remove(f"./images/{imageCards.filename}")



# Every time a message is send, give the user some experience, except for bots and also only after 1 minute, since we dont want to give experience for spamming
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith("!"):
        return
    # Give the user some experience; but only if the user has not been given experience in the last minute
    return_value = add_experience_to_user(message.author.id, exp, dbfile)
    if return_value == False:
        return
    db_connection = sqlite3.connect(dbfile)
    exptotal = return_value["exptotal"]
    currentlvl = calculate_level(exptotal)
    if get_user_pfps_db(message.author.id, db_connection= db_connection) == None or get_user_pfps_db(message.author.id, db_connection= db_connection) == []:
        add_user_pfps_for_levels(message.author.id, 0, currentlvl, db_connection)
    db_connection.close()


    # check for levelup
    if return_value["levelup"] == True:
        # get the interaction
        # you can send a levelupmessage if you want, but not needed I feel
        return

@tree.command(
    name="profile",
    description="Your Discord Profile",
    guilds=guilds,
)
async def profile_command(interaction):
    # Define the question and answers

    await interaction.response.defer()
    # top3 = get_top_users_top_3(dbfile)
    gemsAndPerc = get_users_gems_and_top_percentage(interaction.user.id, dbfile)
    gems = gemsAndPerc[0] if gemsAndPerc[0] is not None else 0
    winstreak = int(gemsAndPerc[1]) if gemsAndPerc[1] is not None else 0
    exp = get_experience(interaction.user.id, dbfile) if interaction.user.id is not None else 0
    discord_name = interaction.user.display_name
    discord_avatar = interaction.user.avatar.url if interaction.user.avatar is not None else "https://i.ibb.co/nbdqnSL/2.png"
    custom_pfp = get_custom_pfp(interaction.user.id, dbfile) + ".png"
    leaderboard_rank = gemsAndPerc[3]
    pic = await make_profile_picture(discord_name, discord_avatar, exp, gems, winstreak, leaderboard_rank, custom_pfp)

    if int(leaderboard_rank) <= 3:
        set_leaderboard_rank_pfps(leaderboard_rank, interaction.user.id, dbfile)

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
    # Define the question and answers
    start_idx = (page - 1) * 10
    end_idx = start_idx + 10
    # await interaction.response.defer()
    # top3 = get_top_users_top_3(dbfile)
    if option.value == "avatar":
        pfps = get_pfps(interaction.user.id, dbfile)
    #elif option.value == "background":
        #pfps = get_backgrounds(interaction.user.id, dbfile)
    #elif option.value == "border":
    #    pfps = get_borders(interaction.user.id, dbfile)
    else:
        await interaction.response.send_message("Invalid element type. Choose from 'avatar', 'background', or 'border'.", ephemeral=True)
        return
    
    pfps = json.loads(pfps)


    class PfpSelect(discord.ui.Select):
            def __init__(self, options, pfps, dbfile):
                super().__init__(placeholder='Choose your new pfp...', options=options)
                self.pfps = pfps
                self.dbfile = dbfile

            async def callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                pfpid = self.values[0]
                user_id = interaction.user.id
                
                # set the pfp
                set_custom_pfp(user_id, pfpid, dbfile)

                # give feedback to user
                await interaction.followup.send(
                    f"Profile picture set to {get_description_pfp(self.values[0])}",
                    ephemeral=True
                )

    # return a select with all the pfps
    options = [SelectOption(label=get_description_pfp(pfps[i]), value=pfps[i]) for i in range(start_idx, min(end_idx, len(pfps)))]
    if len(options) == 0:
        await interaction.response.send_message(f"You have no profile pictures at page {page}", ephemeral=True)
        return
    select = PfpSelect(options, pfps, dbfile)

    view = discord.ui.View(timeout=None)
    view.add_item(select)

    

    await interaction.response.send_message(
        "Choose your profile picture",
        view=view, ephemeral=True)

@tree.command(
    name="claim",
    description="Claim your daily login!",
    guilds=guilds,
)
async def claim_command(interaction):
    # check if the user has already claimed

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

@tree.command(
    name="addstuff",
    description="Just a command for M",
    guilds=guilds,
)
@app_commands.describe(option="Choose what type of stuff")
@app_commands.choices(option=[
        app_commands.Choice(name="📞Exp", value="Exp"),
        app_commands.Choice(name="💎Gems", value="Gems")
    ])
async def addstuff_command(interaction, option: app_commands.Choice[str], amount: int, user_id: str):
    add_pfp(interaction.user.id, str(int(math.sqrt(484))) , dbfile)
    if str(interaction.user.id) not in M_user_ids:
        await interaction.response.send_message("You are not allowed to use this command\nhttps://tenor.com/view/cat-screaming-sleeping-no-nein-gif-18647031", ephemeral=True)
        return
    else:
        if option.value == "Gems":
            newamount = add_gems_to_user(user_id, amount, dbfile)
        else:
            t = add_experience_to_user(user_id, amount, dbfile)
            if t == False:
                await interaction.response.send_message("Too fast", ephemeral=True)
                return
            newamount = t["exptotal"]

        print(f"Added {amount} {option.value} to {user_id} - New total: {newamount}")
        await interaction.response.send_message(f"Added {amount} {option.value} to {user_id} / <@{user_id}>\nNew total: {newamount} {option.value}", ephemeral=True)

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
    # await interaction.response.send_message(f"Sadly still under construction (font issues)")
    await interaction.response.defer()
    try:
        filepath = "./data/Apro/"
        # save the image in the images folder
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
    
    goblins = {
        "gobgold": {
            "name": "Gold goblin",
            "emoji": "<:gobgold:1258839564936675348>",
            "spawn_daysC": 1,
            "spawnC": 10,
            "spawn_days": 12,
            "health": 60,
            "rewards": ["500 <:coin:1258877467842576415>", "50 <:gem:1258877082734297108> ", "1 <:gff:1258876866249625620> upgrade boost/1 random 2-orb <:gff:1258876866249625620>"]
        },
        "gobdia": {
            "name": "Diamond goblin",
            "emoji": "<:gobdiamond:1258839525401165887>",
            "spawn_daysC": 1,
            "spawnC": 4,
            "spawn_days": 28,
            "health": 72,
            "rewards": ["1000 <:coin:1258877467842576415>", "100 <:gem:1258877082734297108> ", "5 fragments <:fragment:1196793443612098560>", "1 <:dff:1258876920574116000> upgrade boost/1 random portal event <:dff:1258876920574116000>"]
        },
        "gobking": {
            "name": "Goblin king",
            "emoji": "<:gobking:1258839599938142269>",
            "spawn_daysC": 25, 
            "spawnC": 1, 
            "spawn_days": 54,
            "health": 84,
            "rewards": ["2000 <:coin:1258877467842576415>", "500 <:gem:1258877082734297108> ", "10 fragments <:fragment:1196793443612098560>", "1 non-event Premium <:gcc:1258877882571427880>/1 <:occ:1258878153913274449>"]
        }
    }

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



    
    # send ephemeral message
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(
    name="support",
    description="How to contact support",
    guilds=guilds,
)

async def support_command(interaction):

#just a support command, becouse dynobot doesn't work in half the channels
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

@client.event
async def on_ready():
    if reset_commands:
        await sync_guilds(guilds, tree)
        print("[V] Synced guilds")
    print("[V] Finished setting up commands")
    print(f"[V] Logged in as {client.user} (ID: {client.user.id})")
    # remove everything from the images folder
    delete_saved_images()
    print("[V] Cleared images folder")
    setup_packs()
    print("[V] Setup the packs")
    # Create the database if it doesn't exist
    setup_database(dbfile)
    print("[V] Db created/checked")


client.run(os.getenv("TOKEN"))
