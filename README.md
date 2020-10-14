# Website Monitor tool 🔍
Script to check whether a website has changed by comparing 
the previous sha256 hash with the current one.

## ⚙️Configuration
1. Websites to be monitored are listed in a personalised `.csv` file.
   An example of the initial configuration can be found in the file
   `example_websites.csv`. Here is the specification of the file:
   
   * The first row must be the following:
     ```
     ,hash,filter,last_change_date
     ```
   
   * In each row insert the URL of the website to be monitored;
   
   * Insert two commas `,,` after the website name as the script
     put the most current hash after the first comma;
   
   * If you want to monitor the whole page, skip this point.
     To monitor a single portion, 
     put the `id` or the `class` of the element of the webpage
     you want to monitor (this is necessary as some webpages change
     some elements each time they are refreshed, an image for example).
     To do so, open the webpage and press `CTRL+shift+C` 
     (or `CMD+shift+U` on MacOS) 
     and click with the mouse over the desired element. 
     Then check that the `class` or the `id` is unique by searching them
     in the webpage html code (press `CTRL+U` or `CMD + U` on MacOS);
     
   * Insert another comma `,`. Here the script will insert the last date
     it has checked the webpage. This is for you, little human!

2. If you want the output to be sent to Telegram, 
   ask the `@BotFather` bot to create a new bot for you.
   Get your `<telegram-token>` from the chat with `@BotFather`, 
   add your bot to a group and access 
   `https://api.telegram.org/bot<telegram-token>/getUpdates` 
   to get your `<chat-id>`.

3. If you want to temporary prevent a website from being checked, add
   a single ``#`` at the very beginning of its line, just before the
   website url. 

## 🔮 Use

### 🐳 Docker
A [docker](https://www.docker.com/) image is available for Linux.
Assuming you have a standard docker installation, you can run the image
with these commands:
```shell script
# get the image from the GitHub Registry
# check the most recent image!
sudo docker pull ghcr.io/robin-castellani/website-monitor/website-monitor:0.2

# run it without telegram and printing the output to the terminal (-t)
sudo docker run -t \
  ghcr.io/robin-castellani/website-monitor/website-monitor:0.2 \
  <website-file.csv>

# to run it with telegram and without printing the output to the terminal
#  and without binding the terminal to the container (--detach)
sudo docker run --detach \
  ghcr.io/robin-castellani/website-monitor/website-monitor:0.2 \
  --token <telegram-token> --chat-id <chat-id> \
  <website-file.csv>

# I suggest to add a --name <container-name> when running the container
# in this way you can inspect its logs with
# sudo docker container logs <container-name>

# also, the --rm option remove the container once it has run
```

### 🐍 Direct use
1. Install Python 3.7.7 (or Python 3.8.5) and every library 
   in `requirements.txt` with `pip install -r requirements.txt`.
   
2. Open a terminal window (or powershell in Windows) in the repository folder
   (maybe you have to `cd` to your directory) and type:
   ```shell script
   python main.py <website-file.csv>
   ```
   Of course, replace `<website-file.csv>` with the path of the file
   with the list of websites to monitor.

If you want to receive the results to Telegram, 
run 
```shell script
python main.py \
  --token <telegram-token> --chat-id <chat-id> \
  <website-file.csv>
```
and replace `<telegram-token>` and `<chat-id>` 
with the ones from point 2.


## ⚠️Caveat
Some websites use JavaScript to create the webpage using your browser.
Now, the website monitor script doesn't deal with browsers but it only
gets the raw html without running any JavaScript.
Therefore, select carefully which website you can monitor!

By the way, I'm working on this feature with [Selenium](https://www.selenium.dev/).

Also, this kind of scraping is based on the immutability of the website
which is being scraped; if the website changes for any reason, it is 
highly possible that you should check your scraping parameters (see configuration).
An alternative, which in the real world is never issued by any website host,
is to use the API which a website exposes and ensures a far more stable
experience in getting down data. 
Maybe big recruiting companies have this kind of API!

## ❓ Run the test suite
For advanced users, it is possible to run the test suite, which
is located in the `Test` folder. 
Anyway, it runs at every push at the repository through
a GitHub Action.

## 📜 License 

All the material in this repo is available through the
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-nc-sa/4.0/>).
