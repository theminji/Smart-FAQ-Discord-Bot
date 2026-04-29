# Smart FAQ Discord Bot

This is a Discord.py bot that I made to help out server staff with FAQs.

It uses an Embeddings Reranker model (by default, `BAAI/bge-reranker-v2-m3`, but can be changed in `system_settings.py`) to intelligently determine what response to give and when to user messages.

This is NOT an LLM or "ChatGPT", so it doesn't generate the responses out of nowhere, it selects them from a predefined list of responses.

Feel free to use it in any NON COMMERCIAL projects, and suggestions are always welcome 🤗

All customization will happen in `system_settings.py` **VERY IMPORTANT** to change the list of pre-defined responses to suit your needs. put as many as you would like!

I plan to continue updating this, so the current version will probably not be the last!
