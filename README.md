# Website Monitor tool 🔍
Script to check whether a website has changed by comparing 
the previous sha256 hash with the current one.

## Configuration
1. Install Python 3.7.7 and every library in `requirements.txt` with
   `pip install -r requirements.txt`.

2. Websites to be monitored are listed in  `websites.csv`. 
   Write the website you want to monitor here.

3. Please, insert two commas `,,` after the website name as the script
   put the most current hash after the first comma.
   
4. Put the `id` or the `class` of the element of the webpage
   you want to monitor (this is necessary as some webpages change
   some elements each time they are refreshed, an image for example).
   To do so, open the webpage and press `CTRL+shift+C` and click with
   the mouse over the desired element. Then check that 
   the `class` or the `id` is unique by searching them in the webpage 
   html code (press `CTRL+U`).
   
5. Insert another comma `,`. Here the script will insert the last date
   it has checked the webpage. This is for you, little human!

6. If you want the output to be sent to Telegram, ask the `@BotFather` bot to create a new bot for you.
   Get your token from the chat with `@BotFather`, add your bot 
   to a group and access `https://api.telegram.org/bot<token>/getUpdates` 
   to get your chat id.

## Use
Open a terminal window (or powershell in Windows) in the repository folder
(maybe you have to `cd` to your directory) and type:
```shell script
python main.py
```

If you want to receive the results to Telegram, 
run 
```shell script
python main.py --token <your_telegram_token> --chat-id <your_chat_id>
```
and replace `<your_telegram_token>` and `<your_chat_id>` with the ones from point 6.

## Caveat
Some websites use JavaScript to create the webpage using your browser.
Now, the website monitor script doesn't deal with browsers but it only
gets the raw html without running any JavaScript.
Therefore, select carefully which website you can monitor!

By the way, I'm working on this feature with [Selenium](https://www.selenium.dev/).

Also, this kind of scraping is based on the immutability of the website
which is being scraped; if the website changes for any reason, it is 
highly possible that you should check your scraping parameters (point 4).
An alternative, which in the real world is never issued by any website host,
is to use the API which a website exposes and ensures a far more stable
experience in getting down data. 
Maybe big recruiting companies have this kind of API!

## License 

All the material in this repo is available through the
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-nc-sa/4.0/>).
