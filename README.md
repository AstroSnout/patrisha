# Patrisha - the Discord Bot

**Patrisha** is a [Discord](https://discordapp.com/) Bot that does all sorts of stuff. It is still an ongoing project, so it's not fully featured yet (you could say she's in alpha development right now) however, there is a plethora of commands at your disposal (listed below).

*If you have any feedback and/or suggestions, [DM me at Trishma#6911 over on Discord](https://discordapp.com/channels/@me/217294231125884929).*

# List of available commands

These are structured in the following format:  
!{subgroup (if available)} \[alias1, alias2...] <argument 1> <argument 2> <optional_argument=default value> 
 
*Some commands that were added on Aug 31st are not listed in the docs.* 
 
## Economy Cog:
*!eco \[b, bal, balance]* - shows your current currency balance  
*!eco \[r, reg, register]* - registers the author to the bank  
*!eco \[w, work]* - earns you currency (command has a set cooldown)  

## Gambling Cog:
*!slot <bet-amount>* - rolls a virtual slot machine (use !help slot to see the pay table)  

## World of Warcraft Cog:
*!guild ss <import-string>* - creates a spreadsheet from a given string (from EventExport add-on)  
*!guild sub <realm-name> <guild-name>* - Patrisha will DM you any members that join/leave the guild  
*!guild unsub <realm-name> <guild-name>* - unsubscribes you from the service mentioned above  
*!m \[a, aff, affix, affixes] <region=eu>* - shows this week's mythic plus affixes  
*!m \[f, first, b, best] <realm-name> <dungeon-name=all>* - shows the top run of a dungeon on realm (defaults to showing all runs)  
*!m \[l, last, w, worst] <realm-name> <dungeon-name=all>* - shows the last run of a dungeon on realm (useful for r.io score)  
*!m \[p, profile, rio] <character-name> <realm-name> <region=eu>* - shows useful mythic plus related info on a character  
*!token <region=eu>* - shows the current token price (valid regions are EU, US, KR and TW)  

## Games:
*!droll <dice>* - roll a die in {number of dies}d{sides on the die} (3d6 for example would roll a 6-sided die 3 times)  
*!roll <range_down=1> <range_up=100>* - roll between 1 and 100, 1 and number1 or number1 and number2  

## Music:
*!\[p, play, stream] <url or song name>* - play a song from a given URL or takes the first result of a search of a given name  
*!\[que, queue]* - shows all queued songs  
*!\[stop, dc, disconnect]* - stops playing music and disconnects from the channel  
*!skip* - stops playing the current song and plays the next one in que  

## Stats:
*!stats post <amount=400>* - shows the most popular post (judging by total reacts) going back a specified amount of messages  
*!stats poster <amount=400>* - ranks members by total reacts on posts looking at the last specified amount of messages  

## Misc:
*!help <command-name=None>* - lists all commands or shows detailed information on a command  
*!feedback <your-feedback>* - use this to send me suggestions and bugs  
*!invitelink* - gives you a link you can use to invite Patrisha to your server
