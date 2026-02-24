import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import json
import asyncio
import os
import random

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Carregar perguntas do JSON
with open("temas.json", "r", encoding="utf-8") as f:
    perguntas = json.load(f)

# Dicionário para controlar quizzes por usuário
quizzes = {}
timers = {}
# Função para enviar pergunta com botões
async def enviar_pergunta(user, canal, pergunta):
    # Criar embed
    embed = discord.Embed(
        title=f"Pergunta para {user.name}",
        description=pergunta["pergunta"],
        color=discord.Color.blue()
    )

    if pergunta["imagem"]:
        embed.set_image(url=pergunta["imagem"])

    # Criar view com botões de alternativas
    view = View(timeout=20)
    alternativas = pergunta["alternativas"]
    random.shuffle(alternativas)  # embaralhar

    # Callback de clique
    async def botao_callback(interaction):
        if interaction.user != user:
            await interaction.response.send_message("Essa pergunta não é sua!", ephemeral=True)
            return

        if hasattr(view, "respondido") and view.respondido:
            await interaction.response.send_message("Você já respondeu!", ephemeral=True)
            return

        view.respondido = True
        if interaction.data["custom_id"] in alternativas and alternativas[int(interaction.data["custom_id"])] in pergunta["resposta"]:
            await interaction.response.send_message(f"✅ Você acertou, {user.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Você errou, {user.mention}! A resposta era: {', '.join(pergunta['resposta'])}", ephemeral=True)

    # Criar botões
    for idx, alt in enumerate(alternativas):
        button = Button(label=f"{chr(65+idx)}. {alt}", style=discord.ButtonStyle.primary, custom_id=str(idx))
        button.callback = botao_callback
        view.add_item(button)

    await canal.send(embed=embed, view=view)

# Comando /iniciar
@bot.slash_command(name="iniciar", description="Inicia um quiz com tema selecionado")
async def iniciar(ctx):
    user = ctx.author
    canal = ctx.channel

    # Sortear pergunta aleatória
    pergunta = random.choice(perguntas)
    quizzes[user.id] = pergunta
    await enviar_pergunta(user, canal, pergunta)

# Comando /next
@bot.slash_command(name="next", description="Próxima pergunta do quiz")
async def next_pergunta(ctx):
    user = ctx.author
    canal = ctx.channel
    pergunta = random.choice(perguntas)
    quizzes[user.id] = pergunta
    await enviar_pergunta(user, canal, pergunta)

# Comando /auto
@bot.slash_command(name="auto", description="Inicia o quiz automático com timer de 20s")
async def auto(ctx):
    user = ctx.author
    canal = ctx.channel

    async def loop_quiz():
        while True:
            pergunta = random.choice(perguntas)
            quizzes[user.id] = pergunta
            await enviar_pergunta(user, canal, pergunta)
            await asyncio.sleep(20)  # Timer 20 segundos

    if user.id in timers:
        await ctx.respond("Quiz automático já está rodando!", ephemeral=True)
    else:
        task = bot.loop.create_task(loop_quiz())
        timers[user.id] = task
        await ctx.respond("Quiz automático iniciado! Use /stop para parar.", ephemeral=True)

# Comando /stop
@bot.slash_command(name="stop", description="Para o quiz automático")
async def stop(ctx):
    user = ctx.author
    if user.id in timers:
        timers[user.id].cancel()
        del timers[user.id]
        await ctx.respond("Quiz automático parado!", ephemeral=True)
    else:
        await ctx.respond("Você não tinha um quiz automático rodando.", ephemeral=True)
        # -------------------- MODERAÇÃO AVANÇADA --------------------
log_owner_id = 1327679436128129159  # Seu ID para receber logs

async def enviar_log_dm(mensagem):
    owner = await bot.fetch_user(log_owner_id)
    await owner.send(mensagem)

@bot.event
async def on_member_ban(guild, user):
    canal = discord.utils.get(guild.channels, name="logs")  # opcional
    msg = f"🚫 {user} foi banido no servidor {guild.name}"
    if canal:
        await canal.send(msg)
    await enviar_log_dm(msg)

@bot.event
async def on_member_unban(guild, user):
    msg = f"✅ {user} foi desbanido no servidor {guild.name}"
    await enviar_log_dm(msg)

@bot.event
async def on_member_update(before, after):
    # Exemplo de mute/unmute por roles
    mute_role = discord.utils.get(after.guild.roles, name="Muted")
    if mute_role:
        if mute_role not in before.roles and mute_role in after.roles:
            await enviar_log_dm(f"🔇 {after} foi mutado em {after.guild.name}")
        elif mute_role in before.roles and mute_role not in after.roles:
            await enviar_log_dm(f"🔊 {after} foi desmutado em {after.guild.name}")

# -------------------- MINIGAMES AVANÇADOS --------------------
# Pedra, Papel, Tesoura
@bot.slash_command(name="ppt", description="Jogue Pedra, Papel ou Tesoura com o bot")
async def ppt(ctx, escolha: str):
    opcoes = ["pedra", "papel", "tesoura"]
    escolha_bot = random.choice(opcoes)
    escolha = escolha.lower()
    resultado = ""
    if escolha == escolha_bot:
        resultado = "Empate!"
    elif (escolha == "pedra" and escolha_bot == "tesoura") or \
         (escolha == "papel" and escolha_bot == "pedra") or \
         (escolha == "tesoura" and escolha_bot == "papel"):
        resultado = "Você ganhou!"
    else:
        resultado = "Você perdeu!"
    await ctx.respond(f"Você escolheu: {escolha}\nBot escolheu: {escolha_bot}\n{resultado}")

# Dado (1-6)
@bot.slash_command(name="dado", description="Rola um dado de 1 a 6")
async def dado(ctx):
    n = random.randint(1, 6)
    await ctx.respond(f"🎲 Você tirou: {n}")

# Adivinhação de número
@bot.slash_command(name="adivinhar", description="Tente adivinhar um número de 1 a 10")
async def adivinhar(ctx, numero: int):
    n = random.randint(1, 10)
    if numero == n:
        await ctx.respond(f"🎉 Correto! O número era {n}")
    else:
        await ctx.respond(f"❌ Errado! O número era {n}")

# Cara ou Coroa
@bot.slash_command(name="caraoucoroa", description="Jogue Cara ou Coroa")
async def caraoucoroa(ctx, escolha: str):
    escolha = escolha.lower()
    resultado = random.choice(["cara", "coroa"])
    if escolha == resultado:
        await ctx.respond(f"🎉 Você escolheu {escolha} e saiu {resultado}. Você ganhou!")
    else:
        await ctx.respond(f"❌ Você escolheu {escolha} e saiu {resultado}. Você perdeu!")
        # -------------------- EVENTOS GERAIS --------------------
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    print("✅ Vynn.py rodando!")

# -------------------- COMANDOS AUXILIARES --------------------
@bot.slash_command(name="perfil", description="Mostra seu perfil no bot")
async def perfil(ctx):
    user = ctx.author
    await ctx.respond(f"Perfil de {user.name}\nID: {user.id}\nParticipando do quiz: {'Sim' if user.id in quizzes else 'Não'}")

@bot.slash_command(name="temas", description="Mostra os temas disponíveis")
async def temas(ctx):
    await ctx.respond("🎮 Tema disponível: **Animes**")

# -------------------- RODA O BOT --------------------
bot.run(os.environ["DISCORD_TOKEN"])
