# Smart FAQ Discord Bot

This is a Discord.py bot that I made to help out server staff with FAQs.

It uses an Embeddings Reranker model (by default, `BAAI/bge-reranker-v2-m3`, but can be changed in `system_settings.py`) to intelligently determine what response to give and when to user messages.

This is NOT an LLM or "ChatGPT", so it doesn't generate the responses out of nowhere, it selects them from a predefined list of responses.

Feel free to use it in any NON COMMERCIAL projects, and suggestions are always welcome 🤗

All customization will happen in `system_settings.py` **VERY IMPORTANT** to change the list of pre-defined responses to suit your needs. put as many as you would like!

## Setup and installation

```bash
git clone https://github.com/theminji/Smart-FAQ-Discord-Bot.git
```

Then edit `.env.example` to have your Discord bot token, and rename to `.env`

After that, make a venv and install the requirements

```bash
python -m venv .venv
source .venv/bin/activate # or .venv\Scripts\activate for Windows
pip install -r requirements.txt
```

Next, edit `system_settings.py` to have YOUR responses instead of the default placeholders

**Best practice** for writing responses: restate the question in the answer ("Go to #tickets" -> "To make a support ticket, go to #tickets")

Then run the bot

```bash
python bot.py
```

---

I plan to continue updating this, so the current version will probably not be the last!
