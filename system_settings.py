# responses for the FAQ. will be automatically determined which one to send (if any) based on input.
responses = [
    "Matt, AKA MattVidPro AI, is a popular Youtuber that makes content about AI. He loves lemons!",
    "Capybaras are very cute animals, and are often the subject of artistic drawings!",
    "AI music can be generated in a variety of ways, the most common are not open source however.",
    "Trentbot is the best clanker in the world. Amazing bot, 10/10 would recommend."
]

# which model to use to determine the response. BAAI/bge-reranker-v2-m3 is good for most usecases.
# you can use BAAI/bge-reranker-base for limited resource deployments, but it only supports chinese and english.
reranker_model = 'BAAI/bge-reranker-v2-m3'

# status to show on discord with the bot
status_text = "Answering FAQs"