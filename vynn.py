import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import asyncio
import os
import unicodedata

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def carregar_temas():
    with open("temas.json", "r", encoding="utf-8") as f:
        return json.load(f)

TEMAS = carregar_temas()

jogo_ativo = False
tema_atual = None
resposta_correta = None
pontuacao = {}

class QuizView(discord.ui.View):
    def __init__(self, pergunta_data):
        super().__init__(timeout=20)
        self.resposta = pergunta_data["resposta"]
        self.opcoes = pergunta_data["opcoes"]
        self.respondido = False

        for letra, texto in self.opcoes.items():
            self.add_item(QuizButton(letra, texto, self))

class QuizButton(discord.ui.Button):
    def __init__(self, letra, texto, view):
        super().__init__(label=f"{letra}. {texto}", style=discord.ButtonStyle.primary)
        self.letra = letra
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.respondido:
            return

        if self.letra == self.view_ref.resposta:
            self.view_ref.respondido = True

            user = str(interaction.user)
            pontuacao[user] = pontuacao.get(user, 0) + 1

            await interaction.response.send_message(f"🎉 {interaction.user.mention} acertou!")
        else:
            await interaction.response.send_message("❌ Errou!", ephemeral=True)

async def nova_pergunta(canal):
    global resposta_correta

    pergunta = random.choice(TEMAS[tema_atual])
    resposta_correta = pergunta

    desc = f"{pergunta['pergunta']}\n\n"
    for letra, texto in pergunta["opcoes"].items():
        desc += f"{letra}. {texto}\n"

    embed = discord.Embed(
        title="🧠 Pergunta",
        description=desc,
        color=0x3498db
    )

    if "imagem" in pergunta:
        embed.set_image(url=pergunta["imagem"])

    view = QuizView(pergunta)

    await canal.send(embed=embed, view=view)

    msg = await canal.send("⏳ 20s")

    for i in range(20, 0, -1):
        if view.respondido:
            return
        await msg.edit(content=f"⏳ {i}s")
        await asyncio.sleep(1)

    if not view.respondido:
        correta = pergunta["opcoes"][pergunta["resposta"]]
        await canal.send(f"❌ Tempo acabou! Resposta: **{correta}**")

@bot.tree.command(name="iniciar", description="Inicia o quiz")
async def iniciar(interaction: discord.Interaction, tema: str):
    global jogo_ativo, tema_atual

    if tema not in TEMAS:
        await interaction.response.send_message("❌ Tema inválido", ephemeral=True)
        return

    jogo_ativo = True
    tema_atual = tema

    await interaction.response.send_message(f"🚀 Quiz iniciado: {tema}")
    await nova_pergunta(interaction.channel)

@bot.tree.command(name="next", description="Próxima pergunta")
async def next_q(interaction: discord.Interaction):
    await interaction.response.send_message("➡️ Próxima")
    await nova_pergunta(interaction.channel)

@bot.tree.command(name="stop", description="Finaliza o quiz")
async def stop(interaction: discord.Interaction):
    ranking = sorted(pontuacao.items(), key=lambda x: x[1], reverse=True)[:3]
    texto = "\n".join([f"{i+1}. {u} - {p}" for i, (u, p) in enumerate(ranking)])

    embed = discord.Embed(
        title="🏆 Ranking",
        description=texto if texto else "Sem pontos",
        color=0xf1c40f
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="temas", description="Ver temas")
async def temas(interaction: discord.Interaction):
    lista = "\n".join(TEMAS.keys())
    await interaction.response.send_message(lista, ephemeral=True)

@bot.tree.command(name="perfil", description="Seu perfil")
async def perfil(interaction: discord.Interaction):
    user = str(interaction.user)
    pontos = pontuacao.get(user, 0)
    await interaction.response.send_message(f"{interaction.user.name}: {pontos} pontos")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if jogo_ativo:
        user_msg = normalizar(message.content)
        correta = resposta_correta["opcoes"][resposta_correta["resposta"]]
        if user_msg in normalizar(correta):
            user = str(message.author)
            pontuacao[user] = pontuacao.get(user, 0) + 1
            await message.channel.send(f"🎉 {message.author.mention} acertou!")

    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Online {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
