# Smart FAQ Discord Bot

This is a Discord.py bot that I made to help out server staff with FAQs.

It uses an Embeddings model (by default, `sentence-transformers/all-MiniLM-L6-v23`, but can be changed in `bot.py`) to intelligently determine what response to give and when to user messages.

This is NOT an LLM or "ChatGPT", so it doesn't generate the responses out of nowhere, it selects them from a predefined list of responses.

Feel free to use it in any of your servers, and suggestions are always welcome in the issues tab 🤗

The actual FAQ responses are in `faq.json`. **VERY IMPORTANT** to change the list of pre-defined responses to suit your needs. put as many as you would like! They can be edited later with slash commands inside Discord whenever you want.

## Setup and installation

```bash
git clone https://github.com/theminji/Smart-FAQ-Discord-Bot.git
```

Then edit `.env.example` to have your Discord bot token, and rename to `.env`

> Make sure your bot has messages intent enabled in Discord developer portal, and it should have read messages and send messages permissions.

After that, make a venv and install the requirements

```bash
uv venv # or python -m venv .venv
source .venv/bin/activate # or .venv\Scripts\activate for Windows
uv pip install -r requirements.txt # or omit uv if using regular python venv
```

Next, edit `faq.json` to have YOUR responses and example questions to trigger the response instead of the default placeholders. You can follow the examples to get good results.

Then run the bot

```bash
python bot.py
```

You can use slash commands to edit and list the FAQ responses without having to ssh into the server and manually edit the file every time. The commands are `/faq_list`, `/faq_add`, and `/faq_remove`.

There is also a `/adminmessage` command in case you want to use it, but it can be removed without impacting any functionality of the bot.

---

I plan to continue updating this, so the current version will probably not be the last!
