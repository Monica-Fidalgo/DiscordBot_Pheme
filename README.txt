Pheme is a discord bot that uses web scraping to search and track information about a products' status or price. The product can be a game (physical or digital format), a trading card 
(from any of the following franchises: magic the gathering, yu-gi-oh! or pokemon), an anime series or a manga series. The bot can also call different APIs to display a card's image (but
only for magic the gathering and yu-gi-oh! cards).

The project is made of the following files:

1) Project_Presentation.pdf: PDF file with presentation slides that explain how to develop and host a discord bot online for free. This document provides very detailed (tutorial-like)
explanations of all the commands and functions developed for the bot. Some of the functions might have suffered some changes since the creation of this PDF file, since the bot has
received some patches and updates.

2) keep_running.py: This file contains the code for Pheme's web server (for online hosting purposes).

3) main.py: This file contains the main code for Pheme with all her tasks and commands. Inside this file you will find imports of functions present in files 2), 4) and 5).

4) birthday_tracker.py: File wiht a birthday tracking function.

5) tracking.py: File with all the product searching, tracking and showing functions.

List of Pheme commands:

a) Every 20h, Pheme checks if today is a user's birthday and if yes, print a birthday message for the user.

b) Every 10h, Pheme checks if the status/price of any item that she is currently tracked has suffered any positive changes (ex: a new manga chapter came out OR an item's price decreased).
If yes, she informs the server by printing a message in the appropriate channels (ex: a message about cards is printed to the tcg channel). 

c) 'info pheme' prints information about Pheme.

d) 'search (category) (search)' takes the string after 'search', expecting the first word to be a category, and the remaining words to be the name of an item. Then, she prints the name and 
prices/statuses of the top most relevant results found (if any).

e) 'track (category) (search)' takes the string after 'track', expecting the first word to be a category, and the remaining words to be the name of an item that the user wants to start 
tracking. Then, Pheme searches the web for the item's current price/status information, adds it to a tracking file and prints a log message for the user.

f) 'list (category)' takes the word after 'list', expecting it to be a category. Then, it prints all the items being tracked by Pheme belonging to that category.

g) 'stop (category) (search)' takes the string after 'stop', expecting the first word to be a category, and the remaining words to be the name of an item that is currently being tracked 
by Pheme. Then, Pheme tries to remove the item from the tracking file and prints a log message. The name on the command must match the name on the file exactly.

h) 'show mtg (search)' takes the string after 'show mtg' and searches for an image of a Magic the Gathering card of the same name. Then, Pheme displays the image in the channel where 
the user requested it. Fuzzy search is possible.

i) 'show ygo (search)' takes the string after 'show ygo' and searches for an image of a Yu-Gi-Oh! card of the same name. Then, Pheme displays the image in the channel where the user 
requested it. The requested name must match the name on the card exactly (no fuzzy search allowed). 