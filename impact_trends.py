#!pip install python-telegram-bot gigachain sentence_transformers faiss-cpu nest_asyncio
#!pip install -U langchain-community
#!pip install arxiv

import logging
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pathlib import Path
from langchain.chat_models.gigachat import GigaChat
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

API_TOKEN = 'YOUR_API_TOKEN'

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)

sber = 'YOUR_SBER_TOKEN'
llm = GigaChat(credentials=sber, verify_ssl_certs=False)

conversation = ConversationChain(llm=llm, verbose=True, memory=ConversationBufferMemory())

embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

search = arxiv.Search(
    query="management",
    max_results=10,
    sort_by=arxiv.SortCriterion.SubmittedDate
)
documents = []

for result in search.results():
    documents.append(result.summary)

document_embeddings = embedder.encode(documents)
index = faiss.IndexFlatL2(document_embeddings.shape[1])
index.add(document_embeddings)

def search(query, k=1):
    query_embedding = embedder.encode([query])
    distances, indices = index.search(query_embedding, k)
    results = [documents[idx] for idx in indices[0]]
    return results

def generate_response(input_text):
    response = conversation.predict(input=input_text)
    return response

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Пожалуйста, задайте свой вопрос.")

def answer_from_llm(query):
    retrieved_docs = search(query, k=3)
    context = "\n".join(retrieved_docs)
    prompt = f"Контекст: {context}\n\nВопрос: {query}"
    result = generate_response(prompt)
    return result

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    processing_message = await update.message.reply_text("Ваш запрос обрабатывается, пожалуйста, подождите...")

    response = answer_from_llm(user_text)

    await processing_message.delete()
    await update.message.reply_text(response)
    await update.message.reply_text("Вы можете задать еще вопрос или уточнить детали.")

async def main():
    application = ApplicationBuilder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

import asyncio
asyncio.run(main())
