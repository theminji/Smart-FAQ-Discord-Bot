import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio
import datetime
import json
from FlagEmbedding import FlagReranker
import system_settings

load_dotenv()

# setup the bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


reranker = FlagReranker(system_settings.reranker_model, use_fp16=True)
print("Model loaded")

# load the list of possible responses that the bot can give (in system_settings.py)
responses = system_settings.responses

# async handle the user message so it doesnt get backloged
async def handle_message(message: discord.Message):
    # prep the lists for similarity scoring
    lists = []
    # grab user input
    q = message.content
    for response in responses:
        lists.append([q, response])

    # actual calculation for which (if any) response to send
    scores = reranker.compute_score(lists, normalize=True)

    # send FAQ response if one is high enough (take the max)
    best_score = max(scores)
    if best_score > 0.25:
        best_index = scores.index(best_score)
        await message.reply(responses[best_index])

# login the bot
@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in: {client.user}')
    await client.change_presence(activity=discord.CustomActivity(name=system_settings.status_text)) # this line is optional, just makes the bot look more professional. change the text in system_settings.py

@client.event
async def on_message(message):
    if message.author == client.user: # skip the messages from this bot
        return
    # async handle message so that the bot doesnt get backlogged
    asyncio.create_task(handle_message(message))

# this command/function is optional, it just allows for smoohter moderation with users without revealing who sent it
@tree.command(name="adminmessage", description="Send an anonymous message in the current channel (admins only)")
async def admin_message(interaction: discord.Interaction, message: str):
    if interaction.user.guild_permissions.kick_members: # make sure the user is a mod/admin before running the command
        await interaction.response.send_message("Sending anonymous message", ephemeral=True)
        channel = interaction.channel
        embed = discord.Embed(
            color=discord.Color.gold(), # you can replace this with any color you want, I just like the gold color https://discordpy.readthedocs.io/en/latest/api.html?highlight=color#discord.Colour.gold
            title="Message from admins",
            description=message
        )
        await channel.send(embed=embed)
    else:
        await interaction.response.send_message("Hey you can't do that!", ephemeral=True) # let the non-admin/mod users know that they cant run this command

client.run(os.getenv("BOT_TOKEN"))