import discord

class SelectMenu(discord.ui.Select):
    def __init__(self, faqs, original_message: discord.Message):
        self.faqs = faqs
        self.original_message = original_message
        options=[
            discord.SelectOption(label=f"{n + 1}",description=faqs[n]["answer"]) for n in range(len(faqs))
            ]
        super().__init__(placeholder="Select what to trigger",max_values=1,min_values=1,options=options)
        
        
    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0]) - 1 # -1 because its n + 1 for pretty viewing in the actual menu
        faq = self.faqs[index]

        await self.original_message.reply(faq['answer']) # reply to the original message that triggered we did the right click on
        await interaction.response.defer() # close out the interaction response so it doesnt hang