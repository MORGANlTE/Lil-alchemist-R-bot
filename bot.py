import discord
from discord import app_commands
from data.data_grabber import *
import discord
import requests
from bs4 import BeautifulSoup

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="quickshow", description="Look up a card in the local database")
async def show_command(interaction, cardname: str, is_onyx: bool = False):
    card = get_card(cardname, is_onyx)
    if card == "Card not found":
        await interaction.response.send_message(f"Card `{cardname}` not found")
    else:
        embed = discord.Embed(
            color=discord.Color.brand_red(),
        )
        embed.set_author(
            icon_url=get_fusion_url(card.fusion),
            name=f"{card.fusion}",
        )
        embed.add_field(name="Full Name", value=card.full_name, inline=True)
        embed.add_field(name="Rarity", value=card.rarity, inline=True)
        embed.add_field(name="Description", value=card.description, inline=False)
        embed.set_thumbnail(url=card.image_url.replace("/\.png\/.*$/", ".png"))
        levels_left = ""
        levels_right = ""
        for i in range(0, 5):
            level = card.level_stats[i]
            level_text = f"{level.level}  -  {level.attack}/{level.defense}\n"
            if i >= 3:
                levels_right += level_text
            else:
                levels_left += level_text

        embed.add_field(name="Levels", value=levels_left, inline=True)
        embed.add_field(name="** **", value=levels_right, inline=True)
        embed.add_field(
            name="Where to acquire",
            value=card.where_to_acquire.replace('"', "")
            .replace("]", "")
            .replace("[", ""),
            inline=False,
        )
        if card.fusion == "Orb":
            if card.rarity == "Onyx":
                onyx_combos = sum(
                    "(Onyx)" in combo.card1 or "(Onyx)" in combo.card2
                    for combo in card.combos
                )
                embed.add_field(
                    name="Combos",
                    value=f"Amount of Onyx Combos: {onyx_combos}",
                    inline=False,
                )
            else:
                other_combos = sum(
                    "(Onyx)" not in combo.card1 and "(Onyx)" not in combo.card2
                    for combo in card.combos
                )
                embed.add_field(
                    name="Combos",
                    value=f"Amount of Combos: {other_combos}",
                    inline=False,
                )
        else:
            combos_left = []
            combos_right = []
            counter = 0
            if card.rarity == "Onyx":
                # filter out all non onyx combos
                card.combos = [
                    combo
                    for combo in card.combos
                    if "(Onyx)" in combo.card1 and "(Onyx)" in combo.card2
                ]
            else:
                # filter out all onyx combos
                card.combos = [
                    combo
                    for combo in card.combos
                    if not "(Onyx)" in combo.card1 and not "(Onyx)" in combo.card2
                ]

            for combo in card.combos:
                if counter % 2 == 0:
                    combos_left.append(f"{counter+1}.{combo.card2} + {combo.card1}")
                else:
                    combos_right.append(f"{counter+1}.{combo.card2} + {combo.card1}")
                counter += 1

            # if empty combos, add a "/"
            if len(card.combos) == 0:
                embed.add_field(name="Combos", value="/", inline=True)
                embed.add_field(name="** **", value="", inline=True)
            else:
                embed.add_field(
                    name="Combos", value="\n".join(combos_left), inline=True
                )
                embed.add_field(
                    name="** **", value="\n".join(combos_right), inline=True
                )

        # add underneath the author the rarity and form
        embed.set_footer(
            text=f"{card.full_name} - {card.rarity} ~ ChinBot",
            icon_url=get_fusion_url(card.fusion),
        )

        await interaction.response.send_message(embed=embed)


@tree.command(name="wiki", description="Look up a card on the LAR wiki")
async def show_command(interaction, cardname: str, is_onyx: bool = False):
    # test if this url gives us a boss card or a normal card
    if is_onyx:
        cardname += "_(Onyx)"
    url = f"https://lil-alchemist.fandom.com/wiki/{cardname.title().replace(' ', '_')}"
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
            await interaction.response.send_message(
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
            if counter % 2 == 0:
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

    await interaction.response.send_message(embed=embed)


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
        name=":mag_right: wiki",
        value="Searches the latest info on the wiki (recommended)",
        inline=True,
    )
    embed.add_field(
        name=":question: help",
        value="Displays this help section",
        inline=True,
    )
    embed.add_field(
        name=":game_die: quickshow",
        value="Look up a card in the local database (outdated)",
        inline=True,
    )
    embed.set_footer(
        text="Made with love by _morganite",
        icon_url="https://cdn.discordapp.com/avatars/405067444764540928/15dd3615a77eb37c700845983f2c88df.webp?size=128",
    )

    await interaction.response.send_message(embed=embed)


import asyncio


# asyncio.run(tree.sync())


@client.event
async def on_ready():
    print(f"[V] Logged in as {client.user} (ID: {client.user.id})")
    # await tree.sync()


client.run("MTE5MDQzMDAyNTczNzA2MDQ0Mg.GAe0_5.vrSgDFLx6Nvb01hDgR9axLg5UDUinJAcBSi0hE")
