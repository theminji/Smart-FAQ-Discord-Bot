import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio
import json
from sentence_transformers import SentenceTransformer
import numpy as np
load_dotenv()

# setup the bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2") # change this if you want to any embedding model
print("Model loaded")

# load faq.json and grab all the data
with open("faq.json", "r", encoding="utf-8") as file:
    responses = json.load(file)

faq_threshold = responses["settings"]["faq_threshold"]

# async lock
embedding_lock = asyncio.Lock()

# helper function to update the faq entries when a new one is added or removed
def update_faq_entries():
    global entries, question_embeddings

    entries = [
        (question, faq)
        for faq in responses["faqs"]
        for question in faq["questions"]
    ]

    question_embeddings = (
        model.encode(
            [question for question, faq in entries],
            normalize_embeddings=True
        )
        if entries else None
    )

update_faq_entries()

# async handle the user message so it doesnt get backloged
async def handle_message(message: discord.Message):
    q = message.content.strip()
    if not q:
        return

    # Capture matching FAQ entries and embeddings together
    current_entries = entries
    current_embeddings = question_embeddings

    if not current_entries:
        return

    async with embedding_lock:
        query_embedding = await asyncio.to_thread(
            model.encode,
            q,
            normalize_embeddings=True
        )

    # Find the closest question using cosine similarity
    scores = current_embeddings @ query_embedding

    best_index = int(np.argmax(scores))
    best_score = float(scores[best_index])

    if best_score >= faq_threshold:
        best_question, best_faq = current_entries[best_index]
        await message.reply(best_faq["answer"])

# login the bot
@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in: {client.user}')
    await client.change_presence(activity=discord.CustomActivity(name="Answering FAQs")) # this line is optional, just makes the bot look more professional.

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
async def faq_add(interaction: discord.Interaction, answer: str, question_1: str, question_2: str = None, question_3: str = None):
    if interaction.user.guild_permissions.kick_members:
        questions = [q for q in [question_1, question_2, question_3] if q and q.strip()]

        # generate a unique ID for the new FAQ
        new_id = max((faq["id"] for faq in responses["faqs"]), default=0) + 1

        faq_response = {
            "id": new_id,
            "questions": questions,
            "answer": answer
        }

        responses["faqs"].append(faq_response)  # add the new FAQ response to the list

        with open("faq.json", "w", encoding="utf-8") as file:
            json.dump(responses, file, indent=4, ensure_ascii=False) # update faq.json file
        update_faq_entries()
        
        embed = discord.Embed(
            color=discord.Color.green(),
            description=f"**ID:** {new_id}\n**Questions:**\n" + "\n".join(f"- {q}" for q in questions) + f"\n\n**Answer:**\n{answer}"
        )
        await interaction.response.send_message("New FAQ response added successfully!", embed=embed) # let the user know that the new FAQ response was added
    else:
        await interaction.response.send_message("Hey you can't do that!", ephemeral=True) # let the non-admin/mod users know that they cant run this command


@tree.command(name="faq_remove", description="Remove an existing FAQ response from the bot (admins only)")
async def faq_remove(interaction: discord.Interaction, faq_id: int):
    if interaction.user.guild_permissions.kick_members:
        faq_response = next((faq for faq in responses["faqs"] if faq["id"] == faq_id), None)

        if faq_response:
            responses["faqs"].remove(faq_response)

            with open("faq.json", "w", encoding="utf-8") as file:
                json.dump(responses, file, indent=4, ensure_ascii=False) # update faq.json file
            update_faq_entries()
            
            embed = discord.Embed(
                color=discord.Color.red(),
                description=f"**ID:** {faq_id}\n**Questions:**\n" + "\n".join(f"- {q}" for q in faq_response["questions"]) + f"\n\n**Answer:**\n{faq_response['answer']}"
            )
            await interaction.response.send_message("FAQ response removed successfully!", embed=embed) # let the user know that the FAQ response was removed
        else:
            await interaction.response.send_message("FAQ response not found! Use /faq_list to see all available responses and their IDs.", ephemeral=True) # let the user know that the FAQ response was not found

    else:
        await interaction.response.send_message("Hey you can't do that!", ephemeral=True) # let the non-admin/mod users know that they cant run this command


@tree.command(name="faq_list", description="List all available FAQ responses")
async def faq_list(interaction: discord.Interaction):
    if interaction.user.guild_permissions.kick_members:
        if not responses["faqs"]:
            await interaction.response.send_message("No FAQ responses available.", ephemeral=True)
        else:
            embed = discord.Embed(
                color=discord.Color.blue(),
                description="\n\n".join(
                    f"**ID: {faq['id']}**\n"
                    f"**Questions:**\n" + "\n".join(f"- {q}" for q in faq["questions"]) +
                    f"\n**Answer:** {faq['answer']}"
                    for faq in responses["faqs"]
                )
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
                responses["settings"]["faq_threshold"] = faq_threshold

                with open("faq.json", "w", encoding="utf-8") as file:
                    json.dump(responses, file, indent=4, ensure_ascii=False)

                await interaction.response.send_message(f"FAQ threshold updated to: {faq_threshold}", ephemeral=True)
            else:
                await interaction.response.send_message("Invalid threshold value. Please provide a value between 0 and 1.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Current FAQ threshold: {faq_threshold}", ephemeral=True)
    else:
        await interaction.response.send_message("Hey you can't do that!", ephemeral=True) # let the non-admin/mod users know that they cant run this command

client.run(os.getenv("BOT_TOKEN"))