import discord
import requests
from bs4 import BeautifulSoup
from data.Apro.Aprogergely import imageeditor
from data.commands import *
from data.data_grabber import *
from data.packopening import *
from data.shortcuts import *
from data.exp_essentials import *
from data.trivia import *

async def show_command_embed(cardname, is_onyx):
  print("[Searching] " + cardname)
  t = check_if_custom_name(cardname)
  if t is not None and t is not False:
      return t

  urls = [construct_url(cardname, is_onyx), construct_url(cardname, is_onyx, is_boss=True)]

  test = ()
  url = ""
  
  test = get_correct_url(urls, cardname)
  if test is None:
      return test

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
  return embed

def show_arena_embed(amount, dbfile, userid):
    add_pfp(userid, str((math.factorial(5) // math.factorial(3)) + 6) , dbfile)
    # Set start time 
    starttime = datetime(2024, 7, 9, 9, 0, 0, 0)
    arenapowers = get_arena_powers()
    max_powers_allowed = (len(arenapowers) + 1)
    if amount < 1 or amount > max_powers_allowed:
        return max_powers_allowed
    
    currenttime = datetime.now()

    # get the difference between the current time and the start time
    difference = currenttime - starttime

    # get the days and hours
    days = difference.days

    # get the next arena power
    next_arena_power = arenapowers[(days // 7 + 1) % len(arenapowers)]


    def format_tiers(tiers):
        return "\n".join(
            [
                f"{tier.get('power', '')} {tier.get('emoji', '')} - {tier.get('orb', '')} <:orb:1262862680021270731>"
                for tier in tiers
            ]
        )
    embed = discord.Embed(
        title="Arena Powers",
        description=":clock1: `Current`:\n\n",
        color=discord.Color.teal(),
    )

    for i in range(0, amount):
        next_arena_power = arenapowers[(days // 7 + i) % len(arenapowers)]
        next_next_arena_power_timestamp = int((starttime + timedelta(days=(days // 7 + i + 1) * 7)).timestamp())
        formatted = format_tiers(next_arena_power['tiers']).strip()
        if formatted.startswith("-"):
            formatted = formatted.strip()[1:]
        
        embed.add_field(
            name=f"{next_arena_power['emoji']} {next_arena_power['name']}",
            value=f"{next_arena_power['description']}\n{formatted}\n\n" + ("" if i == amount - 1 else f":clock1: <t:{next_next_arena_power_timestamp}:R>:"),
            inline=False,
        )

    embed.add_field(
        name="** **",
        value=f"<:newMBot0:1251265938142007486> ~ Arena Powers - :heart: <@271483861895086081> for the data",
    )

    return embed

def show_combo_embed(card1, card2):
    
    urls = [construct_url(card1), construct_url(card1)]
    url = ""

    
    test = get_correct_url(urls, cardname=card1)
    if test is None:
        return card1


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
    
    def find_value(key, data):
        result = [value for k, value in data if k == key]
        return result[0] if result else None
    
    result = find_value(card2, combos)
    if result is None:
        return card2
        
    urls = [construct_url(result), construct_url(result)]
    url = ""

    test = get_correct_url(urls, cardname=result)

    if test is None:
        return result
    
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

    embed = discord.Embed(
        color=get_embedcolor(rarity),
    )
    embed.set_author(
        icon_url=get_fusion_url(fusion),
        name=f"{fusion}",
    )
    embed.add_field(
        name="Wiki Page",
        value=f"[Click here to visit the wiki page]({url})",
        inline=False,
    )
    embed.add_field(name="Full Name", value=result.title(), inline=True)
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
        text=f"{result.title()} - {rarity} ~ ChinBot & LAR Wiki",
        icon_url=get_fusion_url(fusion),
    )

    return embed

def help_embed(version, description):
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are the available commands:",
        color=discord.Color.teal(),
    )

    fields = [
        ("Informational", "** **", False),
        (":game_die: /wiki", "Searches the specified card on the wiki", True),
        ("🔍 /combo", "Searches the specified combo on the wiki", True),
        (":flower_playing_cards: /packview", "Shows the contents of a pack", True),
        (":question: /help", "Displays the help page", True),
        ("<:gobking:1258839599938142269> /goblin", "Shows the next goblin spawn", True),
        (":crossed_swords: /arena", "Shows the current and upcoming arena powers", True),
        ("** **", "** **", False),
        ("Server related", "** **", False),
        (":coin: /leaderboard", "Shows the global leaderboard", True),
        (":bar_chart: /profile", "Shows your profile", True),
        ("👑 /setprofile", "Edit your profile", True),
        (":sos: /support", "How to contact support for Monumental", True),
        ("** **", "** **", False),
        ("Fun", "** **", False),
        (":moneybag: /claim", "Claim your daily login", True),
        (":package: /packopening", "Opens a pack", True),
        (":gem: /trivia", "Some fun trivia to try out", True),
        (":shopping_cart: /store", "Open the store", True),
        ("🚁 /inventory", "Shows your inventory", True),
        (":coral: /generate", "Make a custom card classical LA style! - :heart: Aprogergely!", True),
    ]

    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)


    embed.add_field(
        name="** **",
        value=f"<:newMBot0:1251265938142007486> v{version} - {description}\n*All copyrighted material belongs to [Monumental](https://monumental.io/)*",
        inline=False,
    )

    embed.set_footer(
        text="Made with love by _morganite",
        icon_url="https://iili.io/JlxAR7R.png",
    )
    return embed

async def trivia_embed(interaction, winstreak_max, gem_win_trivia, gem_loss_trivia, dbfile, message):
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

    embed, trivia = await generate_embed_trivia(interaction)
    emojis = ["1️⃣", "2️⃣", "3️⃣"]
    options = [discord.SelectOption(label=answer, emoji=emojis[i]) for i,answer in enumerate(trivia.answers)]
    select = TriviaSelect(options, trivia, dbfile, embed=embed, message=message)
    view = discord.ui.View(timeout=None)
    view.add_item(select)

    return embed, view

async def leaderboard_embed(option, interaction, dbfile):
    category = True if option.value == "Gems" else False
    # Define the question and answers
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

    return embed

async def packopening_embed(interaction, packname):
    packname = packname.strip()

    if len(packname) < 2:
        return "There are no pack names this short man, what r u doing 😅", False
    
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
        return f"Pack `{packname}` not found\nDid you mean `{closestpack.replace('_', ' ')}`?", False
    
    if imageCards == "Error occured":
        return f"An error occured while opening pack `{packname}`, please check console", False
    
    # random number between 1 and 4, if 4 send the embed
    randomNumber = random.randint(1, 4)
    if randomNumber == 4:
        embed = discord.Embed(
        description=f"You found 10 <:fragment:1196793443612098560>",
        color=discord.Color.teal(),
        )
    else:
        embed = None

    return imageCards, embed

def on_message_handler(message, exp, dbfile):
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

    if return_value["levelup"] == True:
        return