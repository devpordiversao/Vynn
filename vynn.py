import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# CARREGAR TEMAS
# =========================
def carregar_temas():
    temas = {}
    arquivos = ["temas.json", "temas2.json", "temas3.json", "temas4.json"]

    for arquivo in arquivos:
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                temas.update(data)

    return temas

TEMAS = carregar_temas()

# =========================
# VARIÁVEIS
# =========================
jogo_ativo = False
tema_atual = None
resposta_atual = None
pontuacao = {}
respondido = False
mensagem_timer = None

# =========================
# READY + SYNC
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online como {bot.user}")

# =========================
# INICIAR
# =========================
@bot.tree.command(name="iniciar", description="Inicia o quiz")
@app_commands.describe(tema="Escolha o tema")
async def iniciar(interaction: discord.Interaction, tema: str):
    global jogo_ativo, tema_atual

    if tema not in TEMAS:
        await interaction.response.send_message(
            f"❌ Tema inválido!\nDisponíveis: {', '.join(TEMAS.keys())}",
            ephemeral=True
        )
        return

    jogo_ativo = True
    tema_atual = tema

    await interaction.response.send_message(f"🔥 Quiz iniciado: **{tema}**")

    await nova_pergunta(interaction.channel)

# =========================
# NOVA PERGUNTA
# =========================
async def nova_pergunta(channel):
    global resposta_atual, respondido, mensagem_timer

    if not jogo_ativo:
        return

    pergunta = random.choice(TEMAS[tema_atual])
    resposta_atual = pergunta["resposta"].lower()
    respondido = False

    embed = discord.Embed(
        title="❓ Pergunta",
        description=pergunta["pergunta"],
        color=discord.Color.blue()
    )

    msg = await channel.send(embed=embed)

    # TIMER EM UMA MENSAGEM
    mensagem_timer = await channel.send("⏳ Tempo: 20s")

    for i in range(20, 0, -1):
        if respondido or not jogo_ativo:
            return

        await mensagem_timer.edit(content=f"⏳ Tempo: {i}s")
        await asyncio.sleep(1)

    if not respondido:
        await channel.send(f"❌ Tempo acabou! Resposta: **{resposta_atual}**")

# =========================
# NEXT
# =========================
@bot.tree.command(name="next", description="Próxima pergunta")
async def next_question(interaction: discord.Interaction):
    if not jogo_ativo:
        await interaction.response.send_message("❌ Nenhum jogo ativo!", ephemeral=True)
        return

    await interaction.response.send_message("➡️ Próxima pergunta...")
    await nova_pergunta(interaction.channel)

# =========================
# STOP
# =========================
@bot.tree.command(name="stop", description="Parar o quiz")
async def stop(interaction: discord.Interaction):
    global jogo_ativo

    if not jogo_ativo:
        await interaction.response.send_message("❌ Nenhum jogo ativo!", ephemeral=True)
        return

    jogo_ativo = False

    if pontuacao:
        ranking = sorted(pontuacao.items(), key=lambda x: x[1], reverse=True)[:3]

        desc = ""
        for i, (user, pontos) in enumerate(ranking, 1):
            desc += f"**{i}.** {user} — {pontos} pts\n"

        embed = discord.Embed(
            title="🏆 Top 3",
            description=desc,
            color=discord.Color.gold()
        )
    else:
        embed = discord.Embed(
            title="😢 Ninguém pontuou",
            color=discord.Color.red()
        )

    await interaction.response.send_message("🛑 Quiz encerrado!", embed=embed)

# =========================
# RESPOSTAS
# =========================
@bot.event
async def on_message(message):
    global respondido

    if message.author.bot:
        return

    if jogo_ativo and not respondido:
        if message.content.lower() == resposta_atual:
            respondido = True

            user = str(message.author)

            if user not in pontuacao:
                pontuacao[user] = 0

            pontuacao[user] += 1

            await message.channel.send(f"✅ {message.author.mention} acertou! (+1)")

    await bot.process_commands(message)

# =========================
# RUN
# =========================
bot.run(os.getenv("DISCORD_TOKEN"))
