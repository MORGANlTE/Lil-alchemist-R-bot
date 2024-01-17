import discord
from discord import app_commands
from data.data_grabber import *
from data.packopening import *
import discord
import requests
from bs4 import BeautifulSoup
from data.trivia import *

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(
    name="wiki",
    description="Look up a card on the LAR wiki",
)
async def show_command(interaction, cardname: str, is_onyx: bool = False):
    await interaction.response.defer()
    # test if this url gives us a boss card or a normal card
    print("[Searching] " + cardname)
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
)
async def help_command(interaction):
    avatar_url = client.user.avatar.url

    embed = discord.Embed(
        title="Bot Commands",
        description="Here are the available commands:",
        color=discord.Color.teal(),
    )
    embed.add_field(
        name=":game_die: wiki",
        value="Searches the latest info on the wiki",
        inline=True,
    )
    embed.add_field(
        name=":question: help",
        value="Displays this help section",
        inline=True,
    )
    embed.add_field(
        name=":question: trivia (WIP)",
        value="Starts a trivia question",
        inline=False,
    )

    embed.add_field(
        name=":space_invader: v2.1.1",
        value="Made wiki command faster",
        inline=False,
    )

    embed.set_footer(
        text="Made with love by _morganite",
        icon_url="https://cdn.discordapp.com/avatars/405067444764540928/15dd3615a77eb37c700845983f2c88df.webp?size=128",
    )

    await interaction.response.send_message(embed=embed)


@tree.command(
    name="trivia",
    description="Start a trivia question",
)
async def trivia_command(interaction):
    # Define the question and answers
    await interaction.response.defer()
    trivia = get_trivia_questions()
    embed = discord.Embed(
        title=trivia.question,
        description=f"1️⃣ {trivia.answers[0]}\n\n2️⃣ {trivia.answers[1]}\n\n3️⃣ {trivia.answers[2]}",
        color=discord.Color.teal(),
    )
    if trivia.image_url_question:
        embed.set_thumbnail(url=trivia.image_url_question)

    await interaction.followup.send(embed=embed)

    message = await interaction.original_response()
    await message.add_reaction("1️⃣")
    await message.add_reaction("2️⃣")
    await message.add_reaction("3️⃣")

    def check(reaction, user):
        return (
            reaction.message.id == message.id
            and user.id != client.user.id
            and str(reaction.emoji) in ["1️⃣", "2️⃣", "3️⃣"]
        )

    # Wait for a reaction to be added
    reaction, user = await client.wait_for("reaction_add", check=check)

    # Check if the reaction is correct
    if str(reaction.emoji) == ["1️⃣", "2️⃣", "3️⃣"][trivia.correct_answer_index]:
        winner_message = f"Correct! {user.mention} answered correctly. The answer was `{trivia.answers[trivia.correct_answer_index]}`."
    else:
        winner_message = f"Wrong! {user.mention} answered incorrectly. The correct answer was `{trivia.answers[trivia.correct_answer_index]}`."

    await interaction.followup.send(winner_message)


@tree.command(
    name="packopening",
    description="Open a pack",
)
async def packopening_command(interaction, packname: str):
    await interaction.response.defer()
    # Simulate opening a pack and get the image URL of the card
    imageCards = await simulate_pack_opening(packname)

    if imageCards == "Not found":
        await interaction.followup.send(f"Pack `{packname}` not found", ephemeral=True)
        return
    if imageCards == "Error occured":
        await interaction.followup.send(
            f"An error occured while opening pack `{packname}`", ephemeral=True
        )
        return
    # random number between 1 and 4, if 4 send the embed
    randomNumber = random.randint(1, 4)

    if randomNumber == 4:
        # create the embed
        embed = discord.Embed(
            description=f"You found 10 <:fragment:1196793443612098560>",
            color=discord.Color.teal(),
        )
        await interaction.followup.send(
            f"{interaction.user.mention} opened `{packname}` Pack",
            embed=embed,
            file=imageCards,
        )
    else:
        await interaction.followup.send(
            f"{interaction.user.mention} opened `{packname}` Pack", file=imageCards
        )


@client.event
async def on_ready():
    # await tree.sync(guild=discord.Object(id=945414516391424040))
    print("[V] Finished setting up commands")
    print(f"[V] Logged in as {client.user} (ID: {client.user.id})")
    # remove everything from the images folder
    delete_saved_images()
    print("[V] Cleared images folder")


client.run("")
