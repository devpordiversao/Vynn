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

# =========================
# UTIL
# =========================
def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def parecido(a, b):
    return a in b or b in a

# =========================
# CARREGAR TEMAS
# =========================
def carregar_temas():
    temas = {}
    arquivos = ["temas.json", "temas2.json", "temas3.json", "temas4.json"]

    for arq in arquivos:
        if os.path.exists(arq):
            with open(arq, "r", encoding="utf-8") as f:
                temas.update(json.load(f))
    return temas

TEMAS = carregar_temas()

# =========================
# VARIÁVEIS
# =========================
jogo_ativo = False
modo_auto = False
tema_atual = None
resposta_atual = None
pontuacao = {}
streak = {}
respondido = False

# =========================
# MULTIPLE CHOICE
# =========================
class QuizView(discord.ui.View):
    def __init__(self, opcoes, correta):
        super().__init__(timeout=20)
        self.correta = normalizar(correta)
        self.respondido = False

        letras = ["A", "B", "C", "D"]

        for i, opc in enumerate(opcoes):
            self.add_item(QuizButton(letras[i], opc, self))

class QuizButton(discord.ui.Button):
    def __init__(self, letra, texto, view):
        super().__init__(label=f"{letra}. {texto}", style=discord.ButtonStyle.primary)
        self.texto = texto
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.respondido:
            return

        resposta = normalizar(self.texto)

        if resposta == self.view_ref.correta:
            self.view_ref.respondido = True

            user = str(interaction.user)
            pontuacao[user] = pontuacao.get(user, 0) + 1
            streak[user] = streak.get(user, 0) + 1

            msg = f"🎉 {interaction.user.mention} acertou! (+1)"

            if streak[user] >= 3:
                msg += f"\n🔥 {interaction.user.name} está em streak de {streak[user]}!"

            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("❌ Errou 😈", ephemeral=True)

# =========================
# PERGUNTA
# =========================
async def nova_pergunta(canal, modo="normal"):
    global resposta_atual, respondido

    if not jogo_ativo:
        return

    pergunta = random.choice(TEMAS[tema_atual])
    resposta_atual = normalizar(pergunta["resposta"])
    respondido = False

    embed = discord.Embed(
        title="🧠 Pergunta",
        description=pergunta["pergunta"],
        color=0x3498db
    )

    if "imagem" in pergunta:
        embed.set_image(url=pergunta["imagem"])

    if modo == "multiple":
        opcoes = [pergunta["resposta"]]
        while len(opcoes) < 4:
            fake = random.choice(TEMAS[tema_atual])["resposta"]
            if fake not in opcoes:
                opcoes.append(fake)

        random.shuffle(opcoes)

        desc = pergunta["pergunta"] + "\n\n"
        letras = ["A", "B", "C", "D"]

        for i, opc in enumerate(opcoes):
            desc += f"{letras[i]}. {opc}\n"

        embed.description = desc

        view = QuizView(opcoes, pergunta["resposta"])
        await canal.send(embed=embed, view=view)
    else:
        await canal.send(embed=embed)

    timer_msg = await canal.send("⏳ Tempo: 20s")

    for i in range(20, 0, -1):
        if respondido:
            return
        await timer_msg.edit(content=f"⏳ Tempo: {i}s")
        await asyncio.sleep(1)

    if not respondido:
        await canal.send(f"❌ Tempo acabou! Resposta: **{resposta_atual}**")

# =========================
# COMANDOS
# =========================

@bot.tree.command(
    name="iniciar",
    description="Inicia um quiz no modo manual (use /next)"
)
@app_commands.describe(tema="Tema", modo="normal ou multiple", tipo="manual")
async def iniciar(interaction: discord.Interaction, tema: str, modo: str, tipo: str):
    global jogo_ativo, tema_atual, modo_auto

    if tema not in TEMAS:
        await interaction.response.send_message("❌ Tema inválido", ephemeral=True)
        return

    jogo_ativo = True
    tema_atual = tema
    modo_auto = False

    await interaction.response.send_message(f"🚀 Quiz iniciado: {tema}")
    await nova_pergunta(interaction.channel, modo)


@bot.tree.command(
    name="auto",
    description="Inicia o quiz automático (até /stop)"
)
@app_commands.describe(tema="Tema", modo="normal ou multiple")
async def auto(interaction: discord.Interaction, tema: str, modo: str):
    global jogo_ativo, tema_atual, modo_auto

    if tema not in TEMAS:
        await interaction.response.send_message("❌ Tema inválido", ephemeral=True)
        return

    jogo_ativo = True
    tema_atual = tema
    modo_auto = True

    await interaction.response.send_message(f"🔥 AUTO iniciado: {tema}")

    while jogo_ativo:
        await nova_pergunta(interaction.channel, modo)
        await asyncio.sleep(2)


@bot.tree.command(
    name="next",
    description="Pular para a próxima pergunta"
)
async def next_q(interaction: discord.Interaction):
    if not jogo_ativo:
        await interaction.response.send_message("❌ Nenhum jogo ativo", ephemeral=True)
        return

    await interaction.response.send_message("➡️ Próxima...")
    await nova_pergunta(interaction.channel)


@bot.tree.command(
    name="stop",
    description="Finaliza o quiz e mostra o ranking"
)
async def stop(interaction: discord.Interaction):
    global jogo_ativo

    jogo_ativo = False

    ranking = sorted(pontuacao.items(), key=lambda x: x[1], reverse=True)[:3]

    desc = ""
    for i, (user, pts) in enumerate(ranking, 1):
        desc += f"{i}. {user} — {pts} pts\n"

    embed = discord.Embed(
        title="🏆 Resultado Final",
        description=desc if desc else "Ninguém pontuou 😢",
        color=0xf1c40f
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="perfil",
    description="Veja suas estatísticas no quiz"
)
async def perfil(interaction: discord.Interaction):
    user = str(interaction.user)

    pontos = pontuacao.get(user, 0)
    streak_user = streak.get(user, 0)

    embed = discord.Embed(
        title=f"📊 Perfil de {interaction.user.name}",
        color=0x2ecc71
    )

    embed.add_field(name="🏆 Pontos", value=str(pontos), inline=True)
    embed.add_field(name="🔥 Streak", value=str(streak_user), inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="temas",
    description="Lista todos os temas disponíveis"
)
async def temas(interaction: discord.Interaction):
    lista = list(TEMAS.keys())
    texto = "\n".join([f"• {tema}" for tema in lista])

    embed = discord.Embed(
        title="📚 Temas disponíveis",
        description=texto[:4000],
        color=0x3498db
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================
# RESPOSTAS
# =========================
@bot.event
async def on_message(message):
    global respondido

    if message.author.bot:
        return

    if jogo_ativo and not respondido:
        user_resp = normalizar(message.content)

        if len(user_resp) < 2:
            return

        if parecido(user_resp, resposta_atual):
            respondido = True

            user = str(message.author)
            pontuacao[user] = pontuacao.get(user, 0) + 1
            streak[user] = streak.get(user, 0) + 1

            msg = f"🎉 {message.author.mention} acertou! (+1)"

            if streak[user] >= 3:
                msg += f"\n🔥 Streak de {streak[user]}!"

            await message.channel.send(msg)

        elif user_resp in resposta_atual:
            await message.channel.send("🤏 Quase acertou...")

    await bot.process_commands(message)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔥 Vynn online como {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
