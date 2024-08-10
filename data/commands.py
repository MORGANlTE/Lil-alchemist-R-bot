import discord
from data.commands import *
from data.data_grabber import *
from data.packopening import *
from data.shortcuts import *
from data.exp_essentials import *
from data.trivia import *
from discord import SelectOption

async def show_command_embed(cardname, is_onyx):
  print("[Searching] " + cardname)
  t = check_if_custom_name(cardname)
  if t is not None and t is not False:
      return t

  urls = construct_urls(cardname, is_onyx)

  test = ()
  url = ""
  
  test = get_correct_url(urls, cardname)
  if test is None:
      imgurls = construct_image_urls(cardname, is_onyx)
      return get_just_image(imgurls, cardname)
  
  url = test["url"]

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
  ) = test["info"]

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
            value=f"{next_arena_power['description']}\n{formatted}\n\n" + ("" if i == amount - 1 else f":clock1: <t:{next_next_arena_power_timestamp}:R> - <t:{next_next_arena_power_timestamp}>:"),
            inline=False,
        )

    embed.add_field(
        name="** **",
        value=f"<:newMBot0:1251265938142007486> ~ Arena Powers - :heart: <@271483861895086081> for the data",
    )

    return embed

def show_arena_reset_embed():
    # Set start time 
    starttime = datetime(2024, 7, 9, 4, 0, 0, 0)
    # each arena week is 6 days 23 hours and 30 minutes which is equal to 10 050 minutes
    # each season is 27 days 22 hours is equal to 40 200 minutes

    currenttime = datetime.now()

    # get the difference between the current time and the start time
    difference = currenttime - starttime

    # get the minutes that have passed since the start time
    minutes_passed = difference.total_seconds() / 60

    # get the next arena reset time
    next_arena_reset = abs(minutes_passed // 10050)

    # next season reset
    next_season_reset = abs(minutes_passed // 40200)

    next_arena_reset_timestamp = int((starttime + timedelta(minutes=((next_arena_reset + 1) * 10050))).timestamp())
    next_season_reset_timestamp = int((starttime + timedelta(minutes=((next_season_reset + 1) * 40200))).timestamp())

    embed = discord.Embed(
        title="Next Arena Reset",
        description=f"\n\n",
        color=discord.Color.pink(),
    )
    embed.add_field(
        name=f"Arena Reset",
        value=f":clock1: <t:{next_arena_reset_timestamp}:R> - <t:{next_arena_reset_timestamp}>",
        inline=False,)    
    embed.add_field(
        name=f"Season Reset",
        value=f":clock1: <t:{next_season_reset_timestamp}:R> - <t:{next_season_reset_timestamp}>",
        inline=False,)

    embed.add_field(
        name="** **",
        value=f"<:newMBot0:1251265938142007486> Made with :anger: by <@436146993530667009> & :heart: by <@405067444764540928>",
    )

    return embed

def show_event_embed(amount, dbfile, userid):

    starttime = datetime(2024, 8, 6, 3, 0, 0, 0)
    starttime = starttime - timedelta(days=70)
    # add 7 hours
    starttime = starttime + timedelta(hours=8)
    
    # endtime = datetime(2024, 8, 16, 3, 0, 0, 0)
    # each event has cooldown period between next event for 4 days
    events = get_events()
    max_events_allowed = len(events)
    if amount < 1 or amount > max_events_allowed:
        return max_events_allowed
        


    
    starter_event = events[5]

    currenttime = datetime.now()

    # get the difference between the current time and the start time
    difference = currenttime - starttime

    # get the days and hours
    days = difference.days

    # hours
    hours = difference.seconds // 3600

    # get the next event
    amount_of_days_between_events = 4
    # check how many events have passed
    event_index = days // (len(events) + amount_of_days_between_events)
    next_event = events[event_index]
    endtime = starttime + timedelta(days=(days // (len(events) + amount_of_days_between_events) + 1) * (len(events) + amount_of_days_between_events)) - timedelta(days=4)
    endtime_timestamp = int(endtime.timestamp())
    embed = discord.Embed(
        title="Events",
        description=f"`Current event`\nEnds <t:{endtime_timestamp}:R> at <t:{endtime_timestamp}>",
        color=discord.Color.teal(),
    )
    for i in range(0, amount):
        next_event = events[(days // (len(events) + amount_of_days_between_events) + i) % len(events)]
        next_next_event_timestamp = int((starttime + timedelta(days=(days // (len(events) + amount_of_days_between_events) + i + 1) * (len(events) + amount_of_days_between_events))).timestamp())
        embed.add_field(
            name=f"{next_event['eventname']} Event",
            value=f"{next_event['bossemoji']} {next_event['bossname']} - <:gcc:1258877882571427880> {next_event['eventgcc']} {next_event['eventemoji']}\n\n" + ("" if i == amount - 1 else f"Starts <t:{next_next_event_timestamp}:R> - <t:{next_next_event_timestamp}>"),
            inline=False,
        )

    embed.add_field(
        name="** **",
        value=f"<:newMBot0:1251265938142007486> ~ Event Cycle :heart: <@405067444764540928>",
    )
    

    return embed

def show_combo_embed(card1, card2):
    
    urls = construct_urls(card1)
    url = ""

    
    test = get_correct_url(urls, cardname=card1)
    if test is None:
        return card1

    url = test["url"]

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
    ) = test["info"]
    
    def find_value(key, data):
        result = [value for k, value in data if k == key]
        return result[0] if result else None
    
    result = find_value(card2, combos)
    if result is None:
        return card2
        
    urls = construct_urls(result)
    url = ""

    test = get_correct_url(urls, cardname=result)

    if test is None:
        return result
    
    url = test["url"]

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
    ) = test["info"]

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
        (":flower_playing_cards: /pack", "Commands for the Packs", True),
        (":question: /help", "Displays the help page", True),
        ("<:gobking:1258839599938142269> /goblin", "Shows the next goblin spawn", True),
        ("<:Anna:1270751642576490507> /event", "More information about the current events", True),
        (":crossed_swords: /arena", "Shows the current and upcoming arena powers/reset time", True),
        ("** **", "** **", False),
        ("Server related", "** **", False),
        (":coin: /leaderboard", "Shows the global leaderboard", True),
        ("👑 /profile", "Profile commands", True),
        (":sos: /support", "How to contact support for Monumental", True),
        ("** **", "** **", False),
        ("Fun", "** **", False),
        (":moneybag: /claim", "Claim your daily login", True),
        (":gem: /trivia", "Some fun trivia to try out", True),
        (":shopping_cart: /store", "Open the store", True),
        (":coral: /generate", "Make a custom card LAR style - :heart: <@429653599296028683>!", True),
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
    if str(message.channel.type) == "private_thread" or str(message.channel.type) == "public_thread":
        return
    # Give the user some experience; but only if the user has not been given experience in the last minute
    return_value = add_experience_to_user(message.author.id, exp, dbfile)
    # print the user and their id
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
    

async def profile_embed(interaction, dbfile):
    gemsAndPerc = get_users_gems_and_top_percentage(interaction.user.id, dbfile)
    gems = gemsAndPerc[0] if gemsAndPerc[0] is not None else 0
    winstreak = int(gemsAndPerc[1]) if gemsAndPerc[1] is not None else 0
    exp = get_experience(interaction.user.id, dbfile) if interaction.user.id is not None else 0
    discord_name = interaction.user.display_name
    discord_avatar = interaction.user.avatar.url if interaction.user.avatar is not None else "https://i.ibb.co/nbdqnSL/2.png"
    custom_pfp = get_custom_pfp(interaction.user.id, dbfile) + ".png"
    leaderboard_rank = gemsAndPerc[3]
    pic = await make_profile_picture(discord_name, discord_avatar, exp, gems, winstreak, leaderboard_rank, custom_pfp)

    return {"pic":pic, "discord_name":discord_name}

async def setprofile_embed(interaction, dbfile, page, option):
    start_idx = (page - 1) * 5
    end_idx = start_idx + 5
    
    if option.value == "avatar":
        pfps = get_pfps(interaction.user.id, dbfile)
    #elif option.value == "background":
        #pfps = get_backgrounds(interaction.user.id, dbfile)
    #elif option.value == "border":
    #    pfps = get_borders(interaction.user.id, dbfile)
    else:
        return "Invalid element type. Choose from 'avatar', 'background', or 'border'."
    
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
        return f"You have no profile pictures at page {page}"
    select = PfpSelect(options, pfps, dbfile)

    view = discord.ui.View(timeout=None)
    view.add_item(select)

    return view

def add_stuff(option, amount, userid, dbfile, M_user_ids, command_user):
    add_pfp(command_user, str(int(math.sqrt(484))) , dbfile)
    if str(command_user) not in M_user_ids:
        return "You are not allowed to use this command\nhttps://tenor.com/view/cat-screaming-sleeping-no-nein-gif-18647031"
    else:
        if option.value == "Gems":
            newamount = add_gems_to_user(userid, amount, dbfile)
        else:
            t = add_experience_to_user(userid, amount, dbfile)
            if t == False:
                return "Too fast"
                return
            newamount = t["exptotal"]

        print(f"Added {amount} {option.value} to {userid} - New total: {newamount}")
        return f"Added {amount} {option.value} to {userid} / <@{userid}>\nNew total: {newamount} {option.value}"

async def store_embed(interaction, dbfile):
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

    return embed, view

async def inventory_embed(interaction, dbfile):
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
            name=f"**Page {i+1}**",
            value="\n".join(chunk),
            inline=True,
        )

    embed.set_footer(
        text="Made with love by _morganite",
        icon_url="https://iili.io/JlxAR7R.png",
    )

    return embed

def packview_embed(packname):
    if len(packname) < 2:
        return f"There are no pack names this short man, what r u doing 😅"
    
    packcontent = get_pack_contents(packname)

    if packcontent == "Not found":
        packcontent = get_pack_contents(packname.capitalize())

    
    
    embed = discord.Embed(
        title=f"{packname} Pack",
        color=discord.Color.dark_magenta(),
    )

    if packcontent == "Not found":
        closestpack = find_closest_pack(packname, get_packs())
        
        packcontent = get_pack_contents(closestpack)

        embed.add_field(
            name=f"Pack `{packname}` not found",
            value=f"Showing results for `{closestpack}`",
            inline=False,
        )
        packname = closestpack
    
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

    return embed

def packlist_embed():
    embed = discord.Embed(
        title="Packs",
        description="",
        color=discord.Color.dark_magenta(),
    )
    packs = get_packs()

    # replace all _ with spaces
    packs = [pack.replace("_", " ").replace("%27", "\'") for pack in packs]

    # remove all packs that are duplicates
    packs = list(set(packs))
    packs = sorted(packs)
    
    # remove pack called "Specials"
    packs.remove("Specials")

    chunked_packs = list(chunk_list(packs, 5))

    for i, chunk in enumerate(chunked_packs):
        embed.add_field(
            name=f"** **",
            value="\n".join(chunk),
            inline=True,
        )

    embed.set_thumbnail(url="https://i.ibb.co/dcmVQDc/MBot.png")

    embed.set_footer(
        text="Made with love by _morganite",
        icon_url="https://iili.io/JlxAR7R.png",
    )

    return embed

def goblin_embed(goblintime, goblin):
    try:
        if goblintime is None:
            gtime = datetime.now()
        else:
            gtime = datetime.strptime(goblintime, "%m-%d-%Y")
    except:
        return "Please provide a valid date in the format MM-DD-YYYY"

    embed = discord.Embed(
        title=f"Goblins overview",
        color=discord.Color.brand_red(),
    )
    
    goblins = get_goblins()

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

    return embed

def support_embed():
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

    return embed

async def sync_commands(adminguilds, tree):
    await tree.sync()
    for guild in adminguilds:
      await tree.sync(guild=guild)

async def on_startup_handler(adminguilds, tree, client, dbfile, admindbfile):
    print(f"[V] Logged in as {client.user} (ID: {client.user.id})")
    delete_saved_images()
    print("[V] Cleared images folder")
    setup_packs()
    print("[V] Setup the packs")
    setup_databases(dbfile, admindbfile)
    print("[V] Db created/checked")
    # print in what guilds the bot is
    print(f"[V] Connected to servers:")
    for guild in client.guilds:
        print(f"  - {guild.name} ({guild.member_count} members)")

    membercount = get_member_count(client)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{membercount} members"))


async def sync_command_handler(userid, M_user_ids, adminguilds, tree):
    if userid not in M_user_ids:
        return "You are not allowed to use this command"
    await sync_commands(adminguilds=adminguilds, tree=tree)
    print("[V] Synced Guilds")
    setup_packs()
    print("[V] Synced Packs")
    return "✅ Synced Guilds Globally 🌍\n✅ Synced admin guilds 🐦‍⬛\n✅ Synced Packs ⛱️"

async def setlogging_command_handler(interaction, admindbfile):
    guild_id = interaction.guild.id
    channel_id = interaction.channel.id
    set_logs = set_logging_channel(guild_id, channel_id, admindbfile)
    if set_logs == False:
        return f"⛔ Logging channel removed in server `{interaction.guild.name}`"
    return f"✅ Added logging channel <#{channel_id}> in server `{interaction.guild.name}`"

async def status_command_handler(status, client, statustext):
    # can be status listening playing or watching
    if status == "Listening":
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=statustext))
    elif status == "Playing":
        await client.change_presence(activity=discord.Game(name=statustext))
    elif status == "Watching":
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=statustext))
    elif status == "Streaming":
        await client.change_presence(activity=discord.Streaming(name=statustext, url="https://www.twitch.tv/monumental_llc"))
    elif status == "Servers":
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(client.guilds)} servers"))
    elif status == "Members":
        membercount = get_member_count(client)
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{membercount} members"))
    else:
        await client.change_presence(activity=None)

    return f"✅ Status set to `{status} {statustext}`"

async def clear_command_handler(client):
    await client.change_presence(activity=None)
    return "🚫 Status cleared"