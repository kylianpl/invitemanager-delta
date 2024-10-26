# InviteManager Delta
This is a discord bot that knows (guess) who was the inviter for every new join, it also makes ranks (roles that you get when they invited a certain number of people), welcome and leave messages, auto role, as well as some other things.
The source code here is made in python. It's a bit messy and not really using the best practices.

## Contact
For any questions or concerns, contact me in the [support server](https://discord.gg/QH7Kg7bthX).

## How to contribute
First, you can give ideas for the bot in the [support server](#contact).
If you don't know how to code, you can help by translating the bot, just go in the lang directory, download the json file from the language you're most familiar, and edit the text after the `:`. Then send the file in a ticket on the [support server](#contact).
You can also contribute by developing a new feature you would like to see, and send a pull request to this repo.

## How to run
1. Clone this repository (necessary)
```bash
git clone https://github.com/kylianpl/invitemanager-delta.git
cd invitemanager-delta
```
2. Create a python virtual environment and activate it (recommended)
```bash
python -m venv .venv
source .venv/bin/activate
```
3. Install the dependencies
```bash
pip install -r requirements.txt
```
4. Copy the `config-sample.json` to `config.json` and put your bot token as well as the id of an error channel, a join channel, a debug guild (server) and bot admins.
Obtain the bot token from the [discord developer portal](https://discord.com/developers/applications).
Obtain the ids from the discord client (you may need to activate the developer mode in advanced settings).
5. Run the bot
```bash
python base.py
```
