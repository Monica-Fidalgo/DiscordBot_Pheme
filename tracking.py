# IMPORTS -------------------------------------------------------------------------------------------------------------------

from bs4 import BeautifulSoup
import requests
from os.path import exists
import pandas as pd
from datetime import datetime
import json
from PIL import Image
from io import BytesIO
from IPython import display

# SEARCH FUNCTIONS ----------------------------------------------------------------------------------------------------------

def gameprices(type,search,t):
    '''
    This function takes in a game's name or url and returns information about the game's price.
            
            Parameters:
                    type (str): game format ('physical' or 'digital'), will determine which webpage we get the prices from (nedgame.nl or steam, 
                                respectively).
                    search (str): Name of the game if t=1; url of the game's webpage if t=2.
                    t (int): t =1 if the game is being searched/tracked for the first time; and 2 if the game has already been registered in the 
                            price tracking file before. This acts a security mechanism: sometimes a new game comes out with a name similar to another
                            game we were already tracking. If we search by game name in the webshop, the first result will be always be the newest game.
                            Because of this, if we want to track an older game, using only the name can get us in trouble. In the worst case scenario
                            we will get a bug: "price decreased from 99999 euros to XX euros" and a new game we didn't search for gets added to the 
                            tracking file. To combat this, if the game is already in the tracking file, we dont use the game name to search for the 
                            updated price - we use the webpage of the game's URL instead. 
                            

            Returns:
                    result (list): List of tuples with game title(s), game price(s), game url(s) and discount price(s) (if the game(s) is(are) on 
                                    discount in the steam website). If we are searching the game for the first time, results is a list with 5 items
                                    (top 5 results). If we are searching for a game that we are already tracking, then the result list will have 
                                    1 item only. Discounted prices are only collected for 'digital' games (steam discounts).
    '''
    if t==1:
        if type == 'physical':
            # NEDGAME: Search for the top 5 most relevant results, return a list of tuples with name, price and url information.
            search_url = 'https://www.nedgame.nl/zoek/zoek:' + search.replace(" ","_") + '/&sorteer=relevantie'
            html_search = requests.get(search_url).text
            soup = BeautifulSoup(html_search,'html.parser')
            products = soup.find_all("div", attrs={"class": "productShopHeader"})
            results = []  
            for p in products:  
                title = p.find('div', attrs={'class':'title'}).text.split("\n\n")[1]
                url = p.find('div', attrs={'class':'titlewrapper'}).find('a', attrs={'class':'productTitleLink'},href=True)['href']
                all_prices = p.find('div', attrs={'class':'buy'})
                (states,prices) = (all_prices.find_all('div', attrs={'class':'staat'}), all_prices.find_all("div", attrs={"class":"currentprice"}))
                price_info = []
                for s,pr in zip(states,prices):
                    state = (s.text.replace("Nieuw","New").replace("Gebruikt","Used")+': '+pr.text)
                    price_info.append(state)
                results.append((title, price_info, url, ''))

            return results[:5]

        elif type == 'digital':
            # STEAM: Search for the top 5 most relevant results, return a list of tuples with name, price and url information.
            search_url = 'https://store.steampowered.com/search/?term=' + search.replace(" ","+") 
            html_search = requests.get(search_url).text
            soup = BeautifulSoup(html_search,'html.parser')
            products = soup.find_all("div", attrs={"class": "responsive_search_name_combined"})
            results = []  
            for idx,p in enumerate(products):
                title = p.find("span", attrs={"class": "title"}).text
                url = soup.find_all("a",attrs={"class": "search_result_row ds_collapse_flag"},href=True)[idx]['href']
                try:
                    price = p.find("div", attrs={"class": "col search_price responsive_secondrow"}).text.split("\r\n")[1].strip()
                    results.append((title, price, url, ''))
                except: # If the game is on discount, the price on the webpage will be in a different class:
                    try:
                        price = p.find("div", attrs={"class": "col search_price discounted responsive_secondrow"}).text.split("\n")[1].strip().split("€")[0]+'€'
                        discount_price = p.find("div", attrs={"class": "col search_price discounted responsive_secondrow"}).text.split("\n")[1].strip().split("€")[1]+'€'
                        results.append((title, price, url, discount_price))
                    except:
                        pass

            return results[:5]
    elif t==2:
        if type == 'physical': 
            # NEDGAME: Using the URL of a game which we saved in the tracking file previously, search the webpage to get updated price information.
            search_url = search
            html_search = requests.get(search_url).text
            soup = BeautifulSoup(html_search,'html.parser')
            title = soup.find('div', attrs={'class':'productTitle show-for-mobile'}).text.split("\n")[1]
            all_prices = soup.find('div', attrs={'class':'buy'})
            (states, prices) = (all_prices.find_all('div', attrs={'class':'staat'}),all_prices.find_all('div', attrs={'class':'currentprice'}))
            price_info = []
            for s,pr in zip(states,prices):
                state = (s.text.replace("Nieuw","New").replace("Gebruikt","Used")+': '+pr.text)
                price_info.append(state)
            result = [(title, price_info, search_url, '')]
            return result

        elif type == 'digital':
            # STEAM: Using the URL of a game which we saved in the tracking file previously, search the webpage to get updated price information.
            search_url = search
            html_search = requests.get(search_url).text
            soup = BeautifulSoup(html_search,'html.parser')
            title = soup.find('div', attrs={'class':'apphub_AppName'}).text
            price = soup.find("div", attrs={"class": "game_purchase_price price"}).text.split("\r\n")[1].replace('\t','')

            try: # If the game is on discount, the discount price on the webpage will be in a different class:
                discount = soup.find("p", attrs={"class": "game_purchase_discount_countdown"}).text
                discount_price = soup.find("div", attrs={"class": "discount_final_price"}).text
            except: # If discount returns an error (there is no discount class in the webpage), then the game is not on discount and:
                discount_price = ''

            result = [(title, price, search_url, discount_price)]
            return result            

def cardprices(tcg,search):
    '''
    Takes in a card game name and a card name. Returns the lowest average price found for the card, the card version and expansion. 
            
            Parameters:
                    tcg (str): Card game name. Accepted values: 'ygo' (Yu-Gi-Oh!), 'mtg' (Magic the Gathering), 'pkmn' (Pokemon)
                    search (str): Card name.

            Returns: 
                    results (list): List of tuples in the format (name,expansion,price).
    '''
    results = []
    #CARDMARKET top results
    if tcg == 'mtg': 
        search_url = 'https://www.cardmarket.com/en/Magic/Products/Singles?idCategory=1&idExpansion=0&searchString='+search.replace(" ","+")+'&onlyAvailable=on&idRarity=0&sortBy=price_asc&perSite=20'
    elif tcg == 'ygo':
        tcg_search = 'YuGiOh'
        search_url = 'https://www.cardmarket.com/en/YuGiOh/Products/Singles?idCategory=5&idExpansion=0&searchString='+search.replace(" ","+")+'&onlyAvailable=on&idRarity=0&sortBy=price_asc&perSite=20'
    elif tcg == 'pkmn':
        search_url = 'https://www.cardmarket.com/en/Pokemon/Products/Singles?idExpansion=0&searchString='+search.replace(" ","+")+'&onlyAvailable=on&idRarity=0&sortBy=price_asc&perSite=30'

    html_search = requests.get(search_url).text
    soup = BeautifulSoup(html_search,'html.parser')
    (cardnames,expansions,prices) = (soup.find_all("div", attrs={"class": "col-10 col-md-8 px-2 flex-column align-items-start justify-content-center"}),soup.find_all("div", attrs={"class": "col-icon small"}),soup.find_all("div", attrs={"class": "col-price pr-sm-2"}) )

    for n,e,p in zip(cardnames,expansions,prices):
        name = n.text
        price = p.text
        if (name != 'Name') and (price != "From"):
            expansion = str(e).split('title=')[1].split('"')[1]
            results.append((name,expansion,price))

    return results

def manga_anime(type,search):
    '''
    Takes in a series' type and name. Returns the status of the series (number of the latest episode/chapter).
            
            Parameters:
                    type (str): Type of series. Accepted values are 'anime' and 'manga'.
                    search (str): Series name.

            Returns: 
                    results (list): List of tuples in the format (title, chpt) or (title, ep) depending on whether we requested a manga or anime
                                    series, respectively.
    '''
    if type == 'manga':
        search_url = 'https://mangarock.herokuapp.com/search/story/'+search.replace(" ","_")
        html_search = requests.get(search_url).text
        soup = BeautifulSoup(html_search,'html.parser')
        series = soup.find_all("div", attrs={"class": "story_item"})
        results = [] 
        for s in series:
            title = s.find("h3", attrs={"class": "story_name"}).text.split("\n")[1]
            chpt = s.find("em", attrs={"class": "story_chapter"}).text.split('\n')[2].strip()
            results.append((title, chpt))
        return results

    if type == 'anime': #top 4 results
        search_url = 'https://animebee.to/search?keyword='+search.replace(" ","+")
        html_search = requests.get(search_url).text
        soup = BeautifulSoup(html_search,'html.parser')
        series = soup.find_all("div", attrs={"class": "flw-item flw-item-big"})
        results = [] 
        for s in series:
            title = s.find("h3", attrs={"class": "film-name"}).text.split("\n")[1]
            ep = s.find("div", attrs={"class": "tick-item tick-eps"}).text
            results.append((title, ep))
        return results

# SAVE FUNCTIONS ------------------------------------------------------------------------------------------------------------

def save_price(data,category):
    '''
    This function takes in information about an item's price and inserts or updates the data inside a tracking file ("price_tracker.csv") 
    with this new information.
            
            Parameters:
                    data (tuple): Tuple with (name,expansion,price) data if the item is a CARD, and (title, price, search_url, discount_price) if 
                                    the item is a GAME.
                    category (str): Can be any of the following strings: 'ygo'/'pkmn'/'mtg' for CARDS; and 'physical'/'digital' for GAMES.
                                    Depending on the category, the data will be saved to the tracking file differently.                                 

            Returns: 
                    (msg,lowest_price,previous) (tuple): Returns a log message to be shown to the user + the current lowest price of the item 
                                                        + the price of the item at the time it was last recorded in the tracking file. The file
                                                        will always contain the most updated price for the item.
    '''
    tcgs = ['ygo','pkmn','mtg']
    games = ['physical','digital']

    if category in tcgs: 
        name = data[0]
        expansion = data[1]
        url = ''
        # From the price string, we will remove only the price data as float.
        lowest_price = float(data[2].split(' €')[0].replace(',','.'))

    elif category in games:
        name = data[0]
        url = data[2]
        expansion = ''
        if category == 'physical':
            if len(data[1]) ==1:
                # If the price list has 1 item, there is only one type of price ("New"). 
                # From the price string, we will remove only the price data as float.
                data[1][0] = data[1][0].replace('Pre-Order',"New")
                lowest_price = float(data[1][0].split("New: € ")[1].replace(',','.').replace('-','00'))
            elif len(data[1]) ==2: 
                # If the price list has 2 itemw, there is also a "Used" (second hand) price.
                # From the price string, we will remove only the price data as float. 
                lowest_price = float(data[1][1].split("Used: € ")[1].replace(',','.').replace('-','00'))
            else:
                # If for some reason there is no price:
                print("Cannot track this game because it does not have a price.")
                return # exit function
        elif category == 'digital':
            # If the price string only says Free or Free to play, then the price is 0EUR.
            if data[1] == 'Free To Play' or data[1] == 'Free':
                lowest_price = 0.0
            else:
            # Else, the price string, we will remove only the price data as float.
                lowest_price = float(data[1].split('€')[0].replace(',','.'))
    
    # Create file for the first time if it doesnt exist.
    if exists("price_tracker.csv") == False:
        file = open("price_tracker.csv","w") 
        file.write("Name|Category|Lowest_Price|Expansion|DateChecked|URL")
        file.close()

    # Open file as pandas dataframe.
    df_prices = pd.read_csv("price_tracker.csv",delimiter="|")

    # Check if card/game item already exists in file
    if category in games:
        # If its a game, check by URL
        df_check = df_prices[df_prices['URL']==url]
    else:
        # If its a card, check by name
        df_check = df_prices[df_prices['Name']==name]

    if df_check.empty:
        # If the item isnt in the file:
        previous = 999999
        date_time_previous = ''
    else:
        # Else, get this information from the file:
        previous = df_check['Lowest_Price'].iloc[0]
        date_time_previous = df_check['DateChecked'].iloc[0]

    # Get current datetime
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

    # Create new dataframe with update (new row)
    update =  {'Name': name, 'Category': category, 'Lowest_Price': lowest_price, 'Expansion': expansion, 'DateChecked':date_time, 'URL':url}
    df_update = pd.DataFrame(update, index=[0])

    # Update the file with the most recent data
    if previous == 999999: 
        # If its a new item, concatenate df_update with df_prices
        df_prices = pd.concat([df_prices, df_update])
    else: 
        # If the item was already in the file, replace the old row in df_prices with the new row from df_update
        if category in games:
            df_prices.update(df_prices[['URL']].merge(df_update, 'left'))
        else:
            df_prices.update(df_prices[['Name']].merge(df_update, 'left'))

    # Save changes to file
    df_prices.to_csv("price_tracker.csv","|",index=False)

    # Print log messages
    if category in tcgs:
        if previous == 999999:
            msg = "The lowest price for " + name + " is " + str(lowest_price) +'€ and corresponds to the expansion '+expansion+'. You never saved prices for this card before.'
        else:
            msg = "The lowest average price for " + name + " is " + str(lowest_price) +'€ and corresponds to the expansion '+expansion+'. The previous time you tracked, on '+date_time_previous+', the lowest price was ' + str(previous)+'€.'

    elif category in games: 
        if previous == 999999:
            msg = "The lowest price for " + name + " is " + str(lowest_price) +'€. You never saved prices for this game before.'
        else:
            msg = "The lowest average price for " + name + " is " + str(lowest_price) +'€. The previous time you tracked, on '+date_time_previous+', the lowest price was ' + str(previous)+'€.'

    return (msg,lowest_price,previous)

def save_status(data,category):
    '''
    This function takes in information about a series' status and inserts or updates the data inside a tracking file ("status_tracker.csv") 
    with this new information.
            
            Parameters:
                    data (tuple): Tuple with (title, chpt) data if the series is a manga or (title, ep) if it's an anime.
                    category (str): Type of series. Can be 'manga' or 'anime'.                                 

            Returns: 
                    (msg,status,previous) (tuple): Returns a log message to be shown to the user + the current status of the series 
                                                        + the status of the series at the time it was last recorded in the tracking file. 
                                                        The file will always contain the most updated status for the item.
    '''       
    name = data[0]
    status = data[1]

    # Create file for the first time if it doesnt exist
    if exists("status_tracker.csv") == False:
        file = open("status_tracker.csv","w") 
        file.write("Name|Category|Status|DateChecked")
        file.close()

    # Open file as pandas dataframe
    df_status = pd.read_csv("status_tracker.csv",delimiter="|")

    # Check if series name exists in file
    df_check = df_status[df_status['Name']==name]

    if df_check.empty:
        # If the series isnt in the file:
        previous = 'N/A'
        date_time_previous = ''
    else:
        # Else, get this information from the file:
        previous = df_check['Status'].iloc[0]
        date_time_previous = df_check['DateChecked'].iloc[0]

    # Get current datetime
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

    # Create new dataframe with update (new row)
    update =  {'Name': name, 'Category': category, 'Status': status, 'DateChecked':date_time}
    df_update = pd.DataFrame(update, index=[0])

    # Update the file with the most recent data
    if previous == 'N/A':
        # If its a new series, concatenate df_update with df_status
        df_status = pd.concat([df_status, df_update])
    else: 
        # If the series was already in the file, replace the old row in df_status with the new row from df_update
        df_status.update(df_status[['Name']].merge(df_update, 'left'))

    # Save changes to file
    df_status.to_csv("status_tracker.csv","|",index=False)

    # Print log messages
    if previous == 'N/A':
        msg = "The current status for " + name + " is " + status +'. You never saved the status of this series before.'
    else:
        msg = "The current status for " + name + " is " + status +'. The previous time you tracked, on '+date_time_previous+', the status was ' + previous+'.'

    return (msg,status,previous)

# TRACKING FUNCTIONS ---------------------------------------------------------------------------------------------------------

def track(cat,name,t):
    '''
    This function searches an item with name/url 'name' and from category 'cat', collects data about the item's status or price, then saves 
    this data to a tracking file. To this end, this function calls all the functions defined previously: gameprices, cardprices, manga_anime,
    save_price and save_status.
            
            Parameters:
                    cat (str): Category the item belongs to. Accepted values are:  'ygo','pkmn','mtg'; 'physical','digital'; 'anime','manga'
                    name (str): Name of the item we wish to track.
                    t (int): t=1 if we are adding the item to the tracking file for the first time and t=2 if the item is already being tracked.
                            This variable is only relevant if our item is a game (categories 'physical' and 'digital') and is not used in any other
                            circumstance.

            Returns: 
                    (log,current,previous,discount) (tuple): Tuple with a message log + current status/price of the item + previous status/price of
                                                            the item + discount price (if the item is on discount - only for 'digital' category).
    '''
    tcgs = ['ygo','pkmn','mtg']
    games = ['physical','digital']
    animanga = ['anime','manga']

    try:
        if cat in tcgs: 
            results = cardprices(cat,name)
            data = []
            for r in results:
                if r[0] == name:
                    data.append(r)
            discount = ''
            (log,current,previous) = save_price(data[0],cat)

        elif cat in games: #gets first result from search function, saves it to file
            results = gameprices(cat,name,t)
            data = results[0]
            discount = data[3]
            (log,current,previous) = save_price(data,cat)

        elif cat in animanga:
            results = manga_anime(cat,name)
            data = results[0]
            discount = ''
            (log,current,previous) = save_status(data,cat)
            
        return (log,current,previous,discount)

    except:
        return ('Your search is too ambiguous. If you are trying to track a card, you must match the name on the card exactly.',0,0)

def stop_tracking(cat,item):
    '''
    Removes an item from the tracking file.
            
            Parameters:
                    cat (str): Category the item belongs to. Accepted values are:  'ygo','pkmn','mtg'; 'physical','digital'; 'anime','manga'
                    item (str): Name of the item to be removed (exactly as is in the tracking file).

            Returns: 
                    msg (str): Log message.
    '''  
    tcgs = ['ygo','pkmn','mtg']
    games = ['physical','digital']
    animanga = ['anime','manga']
    
    if cat in tcgs+games:
        df = pd.read_csv("price_tracker.csv",delimiter="|")
        if item in list(df[df['Category'] == cat]['Name']):
            df_delete = df[(df['Name'] == item) & (df['Category'] == cat)]
            df.drop(df_delete.index, axis=0,inplace=True)
            df.to_csv("price_tracker.csv","|",index=False)
            msg = 'Item '+item+' was deleted from the price tracking file and is no longer being tracked.' 
        else: 
            msg = 'Item name is ambiguous. It should perfectly match the name on the file.'
    
    elif cat in animanga:
        df = pd.read_csv("status_tracker.csv",delimiter="|")
        if item in list(df[df['Category'] == cat]['Name']):
            df_delete = df[(df['Name'] == item) & (df['Category'] == cat)]
            df.drop(df_delete.index, axis=0,inplace=True)
            df.to_csv("status_tracker.csv","|",index=False)
            msg = 'Item '+item+' was deleted from the status tracking file and is no longer being tracked.' 
        else: 
            msg = 'Item name is ambiguous. It should perfectly match the name on the file.'
    
    return msg

# AUTOMATICALLY CHECK FOR CHANGE FUNCTIONS ------------------------------------------------------------------------------------

def price_decrease(cat):
    '''
    Searches for price changes/discounts in every item listed in the tracking file "price_tracker.csv" that belongs to a certain category.
            
            Parameters:
                    cat (str): Category the item belongs to. Accepted values are:  'ygo','pkmn','mtg'; 'physical','digital'.

            Returns: 
                    msg_list (list): List of log messages.
    '''
    df_prices = pd.read_csv("price_tracker.csv",delimiter="|")
    df_cat = df_prices[df_prices['Category']==cat]
    (names,urls) = (list(df_cat['Name']),list(df_cat['URL']))
    msg_list = []

    if cat in ['physical','digital']:
        for n,u in zip(names,urls):
            try:
                resultn = track(cat,u,2) 
                if resultn[1] < resultn[2]:
                    msg = "The price of "+n+" DECREASED from "+ str(resultn[2]) + "€ to "+str(resultn[1])+'€.'
                    msg_list.append(msg)
                if resultn[3] != '':
                    msg2 = 'The game "'+n+'" is currently on discount! The discount price is '+resultn[3]+'.'
                    msg_list.append(msg2)
            except:
                pass

    else:
        for n in names:
            try:
                resultn = track(cat,n,1)
                if resultn[1] < resultn[2]:
                    msg = "The price of "+n+" DECREASED from "+ str(resultn[2]) + "€ to "+str(resultn[1])+'€.'
                    msg_list.append(msg)
            except:
                pass

    return msg_list

def status_change(cat):
    '''
    Searches for status changes in every item listed in the tracking file "status_tracker.csv" that belongs to a certain category.
            
            Parameters:
                    cat (str): Category the item belongs to. Accepted values are: 'anime', 'manga'.

            Returns: 
                    msg_list (list): List of log messages.
    '''
    type = 'episode' if cat == 'anime' else 'chapter'
    df_prices = pd.read_csv("status_tracker.csv",delimiter="|")
    df_cat = df_prices[df_prices['Category']==cat]
    names = list(df_cat['Name'].unique())
    msg_list = []
    for n in names:
        try:
            resultn = track(cat,n)
            if resultn[1] != resultn[2]:
                msg = "There is a new "+type+" of "+n+"! The status CHANGED from "+ str(resultn[2]) + " to "+str(resultn[1])+'.'
                msg_list.append(msg)
        except:
            pass

    return msg_list

# SHOW FUNCTIONS --------------------------------------------------------------------------------------------------------------

def show_items(cat):
    '''
    Shows all items registered in the tracking files that belong to a certain category.
            
            Parameters:
                    cat (str): Category the item belongs to. Accepted values are:  'ygo','pkmn','mtg'; 'physical','digital'; 'anime','manga'

            Returns: 
                    msg_list (list): List of item names present in the tracking file.
    '''
    tcgs = ['ygo','pkmn','mtg']
    games = ['physical','digital']
    animanga = ['anime','manga']
    if cat in tcgs+games:
        df = pd.read_csv("price_tracker.csv",delimiter="|")
        msg_list = list(df[df['Category'] == cat]['Name'])
    elif cat in animanga:
        df = pd.read_csv("status_tracker.csv",delimiter="|")
        msg_list = list(df[df['Category'] == cat]['Name'])
    
    return msg_list
  
def mtg_art(search):
    '''
    Calls the Scryfall API to get card image data of a Magic the Gathering (MTG) card with name 'search'. Fuzzy search is allowed.
            
            Parameters:
                    search (str): Card name.

            Returns: 
                    img (str): URL to the card's image.
    '''
    call_url = "https://api.scryfall.com/cards/named?fuzzy="+search.replace(" ","+")
    call_card = requests.get(call_url)
    card_dict = json.loads(call_card.text)

    if call_card.status_code == 404:
        img = 'Ambiguous name “'+search+'”. Add more words to refine your search.'
    else:
        img = card_dict['image_uris']['normal']

    return img

def ygo_art(search):
    '''
    Calls the Yugiohprices API to get card image data of a Yu-Gi-Oh! (YGO) card with name 'search' (must match the name of the card exactly).
            
            Parameters:
                    search (str): Card name.

            Returns: 
                    img (JpegImageFile): Image byte data.
    '''
    call_url = "http://yugiohprices.com/api/card_image/"+search
    call_card = requests.get(call_url)

    if call_card.status_code == 404:
        img = 'Ambiguous name “'+search+'”. Add more words to refine your search.'
    else: 
        img = Image.open(BytesIO(call_card.content))

    return img