# IMPORTS AND VARIABLES ---------------------------------------------------------------------------------------------------

import discord
from discord.ext import tasks, commands
import os #Import token (on .env file)
from os import system
system('pip install Pillow')
# Custom functions:
from birthday_tracker import birthday
from tracking import track, price_decrease, status_change, mtg_art, ygo_art, cardprices, gameprices, manga_anime, show_items, stop_tracking
# For ygo card art
from PIL import Image
from io import BytesIO
from IPython import display
# Keep the bot running
from keep_running import keep_running

# Create connection to Discord
pheme = discord.Client()

# Variable definition
tcgs = ['ygo','pkmn','mtg']
games = ['physical','digital']
animanga = ['anime','manga']
categories = tcgs + games + animanga

# AUTOMATIC ACTIONS THAT REPEAT EVERY X HOURS ------------------------------------------------------------------------------
@pheme.event
async def on_ready():
    '''
    Whenever Pheme is switched on, print a message saying that she is online. Also, get channel names from the channel ids. 
    Then, run a birthday function every 20 hours, and run a status/price tracking function every 10 hours.
    
    '''
    # Print log message
    print('Pheme is online.')

    # Get channel names from ids
    series_channel = pheme.get_channel(806121692266889226)
    tcg_channel = pheme.get_channel(858715632965779526)
    main_channel = pheme.get_channel(234416220705783808)
    
    #Birthday tracker
    @tasks.loop(hours=20)
    async def birthday_loop():
        '''
        Every 20 hours, execute the birthday function to check if today is a user's birthday. Then, if it's someone's birthday, Pheme will
        print out a birthday message for the user in the main channel of the server.

        '''
        reply_list = birthday()
        if len(reply_list) != 0:
            for m in reply_list:
                await main_channel.send(m)
    birthday_loop.start()

    @tasks.loop(hours=10)
    async def trackers_and_checkers():
        '''
        Every 10 hours, execute the price_decrease and status_change functions to check if the price/status of an item changed. If changes are found,
        print a message for every change/article to inform the users. If no changes are found, don't print anything. The message(s) will be printed
        to different server channels depending on the type of item (ex: a changes in card prices will be printed to the tcg channel).
        '''
        for cat in games:
            m_list = price_decrease(cat)
            if len(m_list)==0:
              continue
            else:
                for m in m_list:
                    await main_channel.send(m)
        for cat in tcgs:
            m_list = price_decrease(cat)
            if len(m_list)==0:
              continue
            else:
                for m in m_list:
                    await tcg_channel.send(m)
        for cat in animanga:
            m_list = status_change(cat)
            if len(m_list)==0:
              continue
            else:
                for m in m_list:
                    await series_channel.send(m)
    trackers_and_checkers.start()

# ACTIONS UPON RECEIVING A USER COMMAND ---------------------------------------------------------------------------------
# Observation: all commands were made to be case insensitive.
@pheme.event
async def on_message(message):
    '''
        This function tells Pheme what to do whenever certain messages/commands appear in the Discord server. 
                
                Parameters:
                        message (str): Written content that is posted to the Discord server by users and bots.
    '''
    # Variables to shorten the code
    reply = message.channel
    msg = message.content
    member = message.author

    # If message is from Pheme (self), ignore.
    if member == pheme.user: 
        return

    # If message is from Athena or Minerva (other bots in the same server), ignore.
    bot_ids = {
                "Athena": 716649964230541343,
                "Minerva": 803248289146470442
            }
    if member.id == bot_ids["Athena"]:
        return
    if member.id == bot_ids["Minerva"]:
        return
    
    # COMMAND: 'info pheme' prints information about Pheme.
    if msg.lower().startswith('info pheme'):
        await reply.send('Hello. I am Pheme, the Goddess of rumour, report and gossip! ヽ(>∀<☆)ノ I was reincarnated as a Discord bot on the 30th May 2022 to help you search and track all the juiciest news  (¬‿¬ )')
    
    # COMMAND: 'track (category) (search)' takes the string after 'track', expecting the first word to be a category, and the remaining words to be 
    # the name of an item that the user wants to start tracking. Then, Pheme searches the web for the item's current price/status information, adds
    # it to a tracking file and also prints a log message for the user.
    if msg.lower().startswith('track'):
        category = msg.lower().split(" ")[1]
        if category not in categories:
            m = 'Please choose a valid category between "ygo" (cards), "pkmn" (cards), "mtg" (cards), "physical" (games), "digital" (games), "anime" or "manga"'
        else:
            search = " ".join(msg.split(" ")[2:])
            m = track(category,search,1)[0]
        await reply.send(m)
    
    # COMMAND: 'stop (category) (search)' takes the string after 'stop', expecting the first word to be a category, and the remaining words to be 
    # the name of an item that is currently being tracked by Pheme. Then, Pheme tries to remove the item from the tracking file and prints a log 
    # message.
    if msg.lower().startswith('stop'):
        category = msg.lower().split(" ")[1]
        if category not in categories:
            m = 'Please choose a valid category between "ygo" (cards), "pkmn" (cards), "mtg" (cards), "physical" (games), "digital" (games), "anime" or "manga"'
            await reply.send(m)
        else:
            search = " ".join(msg.split(" ")[2:])
            m = stop_tracking(category,search)
            await reply.send(m)
    
    # COMMAND: 'list (category)' takes the word after 'list', expecting it to be a category. Then, it prints all the items being tracked by Pheme
    # that belong to that category.
    if msg.lower().startswith('list'):
        category = msg.lower().split(" ")[1]
        if category not in categories:
            m = 'Please choose a valid category between "ygo" (cards), "pkmn" (cards), "mtg" (cards), "physical" (games), "digital" (games), "anime" or "manga"'
            await reply.send(m)
        else:
            m_list = show_items(category)
            if len(m_list) == 0:
                m = 'No results found for this search.'
                await reply.send(m)
            else:
                for m in m_list:
                    await reply.send(m)
    
    # COMMAND: 'search (category) (search)' takes the string after 'search', expecting the first word to be a category, and the remaining words
    # to be the name of the item. Then, if it found any results, it prints the name of the top most relevant products found and their prices/statuses.
    if msg.lower().startswith('search'):
        category = msg.lower().split(" ")[1]
        if category not in categories:
            m = 'Please choose a valid category between "ygo" (cards), "pkmn" (cards), "mtg" (cards), "physical" (games), "digital" (games), "anime" or "manga"'
            await reply.send(m)
        else:
            search = " ".join(msg.split(" ")[2:])
            if category in games:
                m_list = gameprices(category,search,1)
            elif category in tcgs:
                m_list = cardprices(category,search)
            else:
                m_list = manga_anime(category,search)
            if len(m_list) == 0:
                m = 'No results found for this search.'
                await reply.send(m)
            else:
                for m in m_list:
                    await reply.send(m)
    
    # COMMAND: 'show mtg (search)' takes the string after 'show mtg' and searches for an image of a Magic the Gathering card of the same name.
    # Then, Pheme displays the image in the channel where the user requested it.
    if msg.lower().startswith('show mtg'):
        search = msg[9:]
        img = mtg_art(search)
        await reply.send(img)

    # COMMAND: 'show ygo (search)' takes the string after 'show ygo' and searches for an image of a Yu-Gi-Oh! card of the same name. 
    # Then, Pheme displays the image in the channel where the user requested it.
    if msg.lower().startswith('show ygo'):
        search = msg[9:]
        img = ygo_art(search)
        bytes = BytesIO()
        img.save(bytes,format='PNG')
        bytes.seek(0)
        dfile = discord.File(bytes,filename='img.png')
        await reply.send(file=dfile)
        
    # COMMAND: 'terminate pheme' shuts the bot down (turns it off). This command was only used in development, and is commented in production.
    # if msg.lower().startswith('terminate pheme'):
    #     await reply.send('Going to sleep...')
    #     await pheme.logout()
      
# Keep server running so the bot never times off.
keep_running()

# Start Pheme
pheme.run(os.getenv('TOKEN'))