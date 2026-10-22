import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio
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

# load faq.json and grab all the data
with open("faq.json", "r") as f:
    data = json.load(f)

responses = data["faqs"]
faq_threshold = data["settings"]["faq_threshold"]

# async lock
reranker_lock = asyncio.Lock()

# async handle the user message so it doesnt get backloged
async def handle_message(message: discord.Message):
    if not responses: # if the list of responses is empty, just return and do nothing
        return

    # prep the lists for similarity scoring
    lists = []
    # grab user input
    q = message.content.strip()
    if not q:
        return
    
    pairs = [[q, response] for response in responses]
    
    # actual calculation for which (if any) response to send
    async with reranker_lock:
        scores = await asyncio.to_thread(
            reranker.compute_score,
            pairs,
            normalize=True
        )


    # send FAQ response if one is high enough (take the max)
    best_score = max(scores)
    if best_score > faq_threshold: # change this with a slash command or in faq.json
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
    # message filtering so we can be sure it is only from a user and not other bots or dms or anything
    if message.author == client.user:
        return
    if message.author.bot:
        return
    if not message.guild:
        return
    if not message.content.strip():
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


@tree.command(name="faq_add", description="Add a new FAQ response to the bot (admins only)")
async def faq_add(interaction: discord.Interaction, faq_response: str):
    if interaction.user.guild_permissions.kick_members: 
        responses.append(faq_response)  # add the new FAQ response to the list

        with open("faq.json", "w", encoding="utf-8") as file:
            json.dump(responses, file, indent=4) # update faq.json file
        
            embed = discord.Embed(
                color=discord.Color.green(),
                description=faq_response
            )
            await interaction.response.send_message("New FAQ response added successfully!", embed=embed) # let the user know that the new FAQ response was added
    else:
        await interaction.response.send_message("Hey you can't do that!", ephemeral=True) # let the non-admin/mod users know that they cant run this command

@tree.command(name="faq_remove", description="Remove an existing FAQ response from the bot (admins only)")
async def faq_remove(interaction: discord.Interaction, faq_response: str):
    if interaction.user.guild_permissions.kick_members: 
        if faq_response in responses:
            responses.remove(faq_response)

            with open("faq.json", "w", encoding="utf-8") as file:
                json.dump(responses, file, indent=4) # update faq.json file
                
                embed = discord.Embed(
                    color=discord.Color.red(),
                    description=faq_response
                )
                await interaction.response.send_message("FAQ response removed successfully!", embed=embed) # let the user know that the FAQ response was removed
        else:
            await interaction.response.send_message("FAQ response not found! Use /faq_list to see all available responses and then copy paste from there.", ephemeral=True) # let the user know that the FAQ response was not found

    else:
        await interaction.response.send_message("Hey you can't do that!", ephemeral=True) # let the non-admin/mod users know that they cant run this command

@tree.command(name="faq_list", description="List all available FAQ responses")
async def faq_list(interaction: discord.Interaction):
    if interaction.user.guild_permissions.kick_members:
        if not responses:
            await interaction.response.send_message("No FAQ responses available.", ephemeral=True)
        else:
            embed = discord.Embed(
                color=discord.Color.blue(),
                description="\n".join(responses)
            )
            await interaction.response.send_message("Available FAQ responses:", embed=embed, ephemeral=True) # send the list of FAQ responses to the user
    else:
        await interaction.response.send_message("Hey you can't do that!", ephemeral=True) # let the non-admin/mod users know that they cant run this command

@tree.command(name="faq_set_threshold", description="Edit or show the FAQ activation threshold")
async def faq_set_threshold(interaction: discord.Interaction, new_threshold: float = None):
    global faq_threshold

    if interaction.user.guild_permissions.kick_members:
        if new_threshold is not None:
            if 0 <= new_threshold <= 1:
                faq_threshold = new_threshold
                with open("faq.json", "r+") as file:
                    data = json.load(file)
                    data["settings"]["faq_threshold"] = faq_threshold
                    file.seek(0)
                    json.dump(data, file, indent=4)
                    file.truncate()
                await interaction.response.send_message(f"FAQ threshold updated to: {faq_threshold}", ephemeral=True)
            else:
                await interaction.response.send_message("Invalid threshold value. Please provide a value between 0 and 1.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Current FAQ threshold: {faq_threshold}", ephemeral=True)
    else:
        await interaction.response.send_message("Hey you can't do that!", ephemeral=True) # let the non-admin/mod users know that they cant run this command
client.run(os.getenv("BOT_TOKEN"))