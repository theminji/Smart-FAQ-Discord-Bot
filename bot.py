import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from pagination import Pagination
from select_menu import SelectMenu

load_dotenv()

# setup the bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2") # change this if you want to any embedding model
print("Model loaded")

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

# helper function to reload the faq.json file and update the entries and embeddings
def reload_faqs():
    global responses, faq_threshold

    with open("faq.json", "r", encoding="utf-8") as file:
        responses = json.load(file)

    faq_threshold = responses["settings"]["faq_threshold"]

    update_faq_entries()
    

# load faq.json and grab all the data
reload_faqs()

# async handle the user message so it doesnt get backloged
async def handle_message(message: discord.Message):
    q = message.content.strip()
    if not q:
        return

    # capture matching FAQ entries and embeddings together
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

    # find the closest question using cosine similarity
    scores = current_embeddings @ query_embedding

    best_index = int(np.argmax(scores))
    best_score = float(scores[best_index])

    if best_score >= faq_threshold:
        best_question, best_faq = current_entries[best_index]
        best_faq["times_triggered"] += 1
        # update the faq.json file with the new times_triggered value
        with open("faq.json", "w", encoding="utf-8") as file:
            json.dump(responses, file, indent=4, ensure_ascii=False)
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

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "You do not have permission to run this command.", 
            ephemeral=True
        )
    else:
        # fallback for other unexpected errors so they still print to console
        print(f"Unhandled error: {error}")
        
        
### SLASH COMMANDS ARE BELOW


# this command/function is optional, it just allows for smoohter moderation with users without revealing who sent it
@app_commands.default_permissions(kick_members=True)
@tree.command(name="adminmessage", description="Send an anonymous message in the current channel (admins only)")
async def admin_message(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("Sending anonymous message", ephemeral=True)
    channel = interaction.channel
    embed = discord.Embed(
        color=discord.Color.gold(), # you can replace this with any color you want, I just like the gold color https://discordpy.readthedocs.io/en/latest/api.html?highlight=color#discord.Colour.gold
        title="Message from admins",
        description=message
    )
    await channel.send(embed=embed)

@app_commands.default_permissions(kick_members=True)
@tree.command(name="faq_add", description="Add a new FAQ response to the bot (admins only)")
async def faq_add(interaction: discord.Interaction, answer: str, question_1: str, question_2: str = None, question_3: str = None):
    questions = [q for q in [question_1, question_2, question_3] if q and q.strip()]

    # generate a unique ID for the new FAQ
    new_id = max((faq["id"] for faq in responses["faqs"]), default=0) + 1

    faq_response = {
        "id": new_id,
        "questions": questions,
        "answer": answer,
        "times_triggered": 0
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

@app_commands.default_permissions(kick_members=True)
@tree.command(name="faq_remove", description="Remove an existing FAQ response from the bot (admins only)")
async def faq_remove(interaction: discord.Interaction, faq_id: int):
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

@app_commands.default_permissions(kick_members=True)
@tree.command(name="faq_list", description="List all available FAQ responses")
async def faq_list(interaction: discord.Interaction):
    reload_faqs()
    if not responses["faqs"]:
        await interaction.response.send_message(
            "No FAQ responses available.",
            ephemeral=True
        )
        return

    results_per_page = 5

    async def get_page(page: int):
        total_pages = Pagination.compute_total_pages(
            len(responses["faqs"]), results_per_page
        )

        offset = (page - 1) * results_per_page
        page_faqs = responses["faqs"][offset:offset + results_per_page]

        embed = discord.Embed(
            title="Available FAQ Responses",
            color=discord.Color.blue(),
            description="\n\n".join(
                f"**ID: {faq['id']}**\n"
                f"**Questions:**\n"
                + "\n".join(f"- {q}" for q in faq["questions"])
                + f"\n**Answer:** {faq['answer']}"
                for faq in page_faqs
            )
        )

        embed.set_footer(text=f"Page {page} of {total_pages}")

        return embed, total_pages

    await Pagination(interaction, get_page).navigate()

@app_commands.default_permissions(kick_members=True)
@tree.command(name="faq_set_threshold", description="Edit or show the FAQ activation threshold")
async def faq_set_threshold(interaction: discord.Interaction, new_threshold: float = None):
    global faq_threshold
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
        
@app_commands.default_permissions(kick_members=True)
@tree.command(name="faq_test", description="Test the FAQ response for a question without sending it publicly")
async def faq_test(interaction: discord.Interaction, question: str):
    global faq_threshold

    best_faq = None
    best_score = -1.0

    async with embedding_lock:
        query_embedding = await asyncio.to_thread(
            model.encode,
            question,
            normalize_embeddings=True
        )

    embedding_index = 0

    for faq in responses["faqs"]:
        for q in faq["questions"]:
            score = float(question_embeddings[embedding_index] @ query_embedding)

            if score > best_score:
                best_score = score
                best_faq = faq

            embedding_index += 1

    if best_faq and best_score >= faq_threshold:
        await interaction.response.send_message(f"Test result for '{question}': {best_faq['answer']}\nScore {best_score:.2f}", ephemeral=True)
    else:
        await interaction.response.send_message(f"No suitable FAQ found for '{question}'.\nClosest was '{best_faq['questions'][0]}' with a score of {best_score:.2f}", ephemeral=True)

@app_commands.default_permissions(kick_members=True)
@tree.command(name="faq_stats", description="See the stats about your FAQ bot")
async def faq_stats(interaction: discord.Interaction):

    total_faqs_triggered = sum(faq["times_triggered"] for faq in responses["faqs"])

    most_triggered_faq = max(
        responses["faqs"],
        key=lambda faq: faq["times_triggered"],
        default=None
    )

    if most_triggered_faq and most_triggered_faq["times_triggered"] > 0:
        most_triggered_text = (
            f"{most_triggered_faq['questions'][0]} "
            f"({most_triggered_faq['times_triggered']} times)"
        )
    else:
        most_triggered_text = "No FAQs have been triggered yet."

    embed = discord.Embed(
        title="FAQ Bot Stats",
        color=discord.Color.blue(),
        description=(
            f"Your server has {len(responses['faqs'])} FAQs configured.\n"
            f"Total FAQs triggered: {total_faqs_triggered}\n"
            f"Most triggered FAQ: {most_triggered_text}\n\n"
        ),
    )
    embed.add_field(name="Request more features", value="[on my Github](https://github.com/theminji/Smart-FAQ-Discord-Bot/issues)", inline=False)
    await interaction.response.send_message(embed=embed)

# just learned about context menus so adding that for a manual FAQ trigger
@app_commands.default_permissions(kick_members=True)
@tree.context_menu(name="Manual FAQ")
async def manual_faq(interaction: discord.Interaction, message: discord.Message):
    
    # create the "view " (dropdown menu)
    faq_dropdown = SelectMenu(responses["faqs"], original_message=message)
    view = discord.ui.View()
    view.add_item(faq_dropdown)
    await interaction.response.send_message(view=view, ephemeral=True)
    # the callback in select_menu.py will automatically trigger the response to the original message, so dont worry about that here

client.run(os.getenv("BOT_TOKEN"))

## btw the reason im using
# if not interaction.user.guild_permissions.kick_members:
# for all the commands that require admin permissions is because some servers dont give hteir mods full admin perms, 
# so i check for kick_members permission instead of full admin permissions to include all those mods