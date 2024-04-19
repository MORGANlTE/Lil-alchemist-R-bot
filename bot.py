import discord
from discord import app_commands, ButtonStyle, SelectOption
from discord.ui import Button, View, Select
from data.data_grabber import *
from data.packopening import *
from data.shortcuts import *
from data.exp_essentials import *
import discord
import requests
from bs4 import BeautifulSoup
from data.trivia import *
import os
from dotenv import load_dotenv


# Load the .env file
load_dotenv()

# Variables:
version = "5.5.0"
versiondescription = "Trivia rework"
gem_win_trivia = 5
winstreak_max = 10
gem_loss_trivia = -5
exp = 10
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
        name=":game_die: /wiki",
        value="Searches the specified card on the wiki",
        inline=True,
    )
    embed.add_field(
        name=":question: /help",
        value="Displays the help page",
        inline=True,
    )
    embed.add_field(
        name=":bar_chart: /profile",
        value="Shows your profile",
        inline=True,
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
        value="Starts a trivia question",
        inline=True,
    )
    embed.add_field(
        name=":coin: /leaderboard",
        value="Shows your score on the global leaderboard",
        inline=True,
    )
    
    embed.add_field(
        name="** **",
        value=f"v{version} - {versiondescription}\n*All copyrighted material belongs to Monumental*",
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
                print(streak)

                # check if the user was wrong or right
                if self.trivia.answers.index(label) != self.trivia.correct_answer_index:
                    return_message = f"⛔ {interaction.user.mention} did not answer `{self.trivia.answers[self.trivia.correct_answer_index]}` {gem_loss_trivia} :gem:"
                    update_winstreak(user_id, dbfile, 0)
                else:
                    print(gem_win_trivia)
                    print(streak)
                    print(f"streak: {gem_win_trivia + streak}")
                    return_message = f"✅ {interaction.user.mention} answered `{self.trivia.answers[self.trivia.correct_answer_index]}`\n+{gem_win_trivia + streak} :gem: 🔥 {streak}"
                    update_winstreak(user_id, dbfile, streak)
                newgems = add_gems_to_user(user_id, (gem_win_trivia + streak), dbfile)
                print(newgems)

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
    print(trivia.answers)
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
        app_commands.Choice(name="Level leaderboard 🫰", value="Lvl"),
        app_commands.Choice(name="Trivia leaderboard 💎", value="Gems")
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
    description = f"Level: {calculate_level(int(gemsAndPerc[2]))} | {int(gemsAndPerc[2])} Exp | "
    description += f":gem: {str(gemsAndPerc[0])} | 🔥{int(gemsAndPerc[1])}\n\n"
    description += f"**Global {':gem: ' if category else ':crown: '}leaderboard:**\n"

    for i, user in enumerate(top_users):
        if category:
            description += f"\n{get_medal_emoji(i+1)} <@{user[1]}> - :gem: {user[2]} | 🔥 {user[3]}\n"
        else:
            description += f"\n{get_medal_emoji(i+1)} <@{user[1]}> - 👑 Lvl {calculate_level(user[4])} | {user[4]} Exp\n"

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
        await interaction.followup.send(f"Pack `{packname}` not found", ephemeral=True)
        return
    if imageCards == "Error occured":
        await interaction.followup.send(
            f"An error occured while opening pack `{packname}`", ephemeral=True)
        return
    # random number between 1 and 4, if 4 send the embed
    randomNumber = random.randint(1, 4)

    embed = discord.Embed(
        description=f"You found 10 <:fragment:1196793443612098560>",
        color=discord.Color.teal(),
    )

    await waiting.delete()

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

    gemsAndPerc = get_users_gems_and_top_percentage(interaction.user.id, dbfile)
    gems = gemsAndPerc[0] if gemsAndPerc[0] is not None else 0
    winstreak = int(gemsAndPerc[1]) if gemsAndPerc[1] is not None else 0
    exp = get_experience(interaction.user.id, dbfile) if interaction.user.id is not None else 0
    discord_name = interaction.user.display_name
    discord_avatar = interaction.user.avatar.url if interaction.user.avatar is not None else "https://i.ibb.co/nbdqnSL/2.png"
    pic = await make_profile_picture(discord_name, discord_avatar, exp, gems, winstreak)

    await interaction.followup.send(
        file=pic,
    )
    # remove the image
    os.remove(f"./important_images/{discord_name}.png")


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
