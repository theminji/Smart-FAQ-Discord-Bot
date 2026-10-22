# which model to use to determine the response. BAAI/bge-reranker-v2-m3 is good for most usecases.
# you can use BAAI/bge-reranker-base for limited resource deployments, but it only supports chinese and english.
reranker_model = 'BAAI/bge-reranker-v2-m3'

# status to show on discord with the bot
status_text = "Answering FAQs"