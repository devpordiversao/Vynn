import discord
from discord.ext import commands, tasks
from discord import app_commands, Interaction, ui
import json
import random
import asyncio
import os
import difflib

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ----------- CARREGAR TEMAS -----------
temas_files = {
    "naruto": "temas.json",
    "escola": "temas2.json",
    "futebol": "temas3.json",
    "curiosidades": "temas4.json"
}

temas_data = {}
for key, file in temas_files.items():
    with open(file, "r", encoding="utf-8") as f:
        temas_data[key] = json.load(f)

# ----------- PARTIDAS ATIVAS -----------
partidas_ativas = {}  # guild_id: {tema, perguntas, index, auto, pontos, multipla, ja_clicou}

# ----------- FUNÇÃO COMPARAR RESPOSTA -----------
def comparar_resposta(correta, resposta_usuario):
    correta = correta.lower().strip()
    resposta_usuario = resposta_usuario.lower().strip()
    ratio = difflib.SequenceMatcher(None, correta, resposta_usuario).ratio()
    return ratio >= 0.8  # 80% de similaridade aceita

# ----------- VIEW MÚLTIPLA ESCOLHA -----------
class MultipleChoiceView(ui.View):
    def __init__(self, pergunta, guild_id):
        super().__init__(timeout=20)
        self.pergunta = pergunta
        self.guild_id = guild_id
        self.add_buttons()
    
    def add_buttons(self):
        for letra, resposta in self.pergunta.get("opcoes", {}).items():
            self.add_item(MCButton(letra, resposta, self.pergunta["resposta"], self.guild_id))
            
class MCButton(ui.Button):
    def __init__(self, letra, resposta, correta, guild_id):
        super().__init__(label=f"{letra}. {resposta}", style=discord.ButtonStyle.primary)
        self.letra = letra
        self.resposta = resposta
        self.correta = correta
        self.guild_id = guild_id

    async def callback(self, interaction: Interaction):
        partida = partidas_ativas[self.guild_id]
        if interaction.user.id in partida.get("ja_clicou", []):
            await interaction.response.send_message("❌ Você já respondeu!", ephemeral=True)
            return
        partida.setdefault("ja_clicou", []).append(interaction.user.id)
        if comparar_resposta(self.correta, self.resposta):
            pontos = partida.setdefault("pontos", {})
            pontos[interaction.user.id] = pontos.get(interaction.user.id,0)+1
            await interaction.response.send_message(f"✅ {interaction.user.name} acertou! Total de pontos: {pontos[interaction.user.id]}")
        else:
            await interaction.response.send_message(f"❌ {interaction.user.name} errou!", ephemeral=True)

# ----------- ENVIAR PERGUNTA COM TIMER VISUAL -----------
async def enviar_pergunta(interaction: Interaction, guild_id):
    partida = partidas_ativas[guild_id]
    idx = partida["index"]
    if idx >= len(partida["perguntas"]):
        await finalizar_partida(interaction, guild_id)
        return
    pergunta = partida["perguntas"][idx]

    embed = discord.Embed(title=f"Pergunta {idx+1}", description=pergunta["pergunta"], color=discord.Color.gold())
    if "imagem" in pergunta and pergunta["imagem"]:
        embed.set_image(url=pergunta["imagem"])
    
    partida["ja_clicou"] = []

    if partida.get("multipla", True) and "opcoes" in pergunta:
        view = MultipleChoiceView(pergunta, guild_id)
        await interaction.channel.send(embed=embed, view=view)
    else:
        msg = await interaction.channel.send(embed=embed)
        for t in range(20,0,-5):
            await interaction.channel.send(f"⏱ {t}s restantes")
            await asyncio.sleep(5)
        await interaction.channel.send("⏰ Tempo esgotado! Ninguém acertou ou acertou tarde demais.")

# ----------- FINALIZAR PARTIDA COM TOP 3 -----------
async def finalizar_partida(interaction: Interaction, guild_id):
    partida = partidas_ativas[guild_id]
    pontos = partida.get("pontos", {})
    if not pontos:
        await interaction.channel.send("🔹 Partida encerrada! Ninguém marcou pontos.")
    else:
        ranking = sorted(pontos.items(), key=lambda x: x[1], reverse=True)[:3]
        desc = ""
        emojis = ["🥇","🥈","🥉"]
        for i, (user_id, pts) in enumerate(ranking):
            user = interaction.guild.get_member(user_id)
            desc += f"{emojis[i]} {user.name if user else 'Desconhecido'} — {pts} pontos\n"
        embed = discord.Embed(title="🏆 Top 3 da partida", description=desc, color=discord.Color.purple())
        await interaction.channel.send(embed=embed)
    del partidas_ativas[guild_id]

# ----------- COMANDOS -----------
@bot.tree.command(name="temas", description="Mostra todos os temas disponíveis")
async def temas(interaction: Interaction):
    texto = ""
    for tema in temas_data.keys():
        texto += f"- {tema}\n"
    embed = discord.Embed(title="Temas Disponíveis", description=texto, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="perfil", description="Mostra seu perfil e pontos")
async def perfil(interaction: Interaction):
    pontos_totais = {}
    for partida in partidas_ativas.values():
        for user_id, pts in partida.get("pontos", {}).items():
            pontos_totais[user_id] = pontos_totais.get(user_id,0)+pts
    user_pts = pontos_totais.get(interaction.user.id, 0)
    embed = discord.Embed(title=f"Perfil de {interaction.user.name}", description=f"Pontos acumulados: {user_pts}", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

# ----------- INICIAR COM DOIS DROPDOWNS -----------
class ModoSelect(ui.Select):
    def __init__(self, guild_id):
        options = [
            discord.SelectOption(label="Normal", description="Responda digitando a resposta"),
            discord.SelectOption(label="Múltipla Escolha", description="Responda clicando nos botões A/B/C/D")
        ]
        self.guild_id = guild_id
        super().__init__(placeholder="Escolha o modo de jogo...", options=options, min_values=1, max_values=1)
    
    async def callback(self, interaction: Interaction):
        modo = self.values[0]
        partidas_ativas[self.guild_id]["multipla"] = True if modo == "Múltipla Escolha" else False
        await interaction.response.send_message(f"✅ Modo **{modo}** selecionado! Use /next para começar a jogar.")

@bot.tree.command(name="iniciar", description="Inicia uma partida em determinado tema")
async def iniciar(interaction: Interaction):
    class TemaSelect(ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=k, description=f"Jogar tema {k}") for k in temas_data.keys()]
            super().__init__(placeholder="Escolha um tema...", options=options, min_values=1, max_values=1)
        
        async def callback(self, interaction: Interaction):
            tema = self.values[0]
            guild_id = interaction.guild.id
            perguntas = temas_data[tema][list(temas_data[tema].keys())[0]]
            perguntas_copia = perguntas.copy()
            random.shuffle(perguntas_copia)
            partidas_ativas[guild_id] = {"tema": tema, "perguntas": perguntas_copia, "index":0, "auto":False, "pontos":{}, "multipla":True, "ja_clicou":[]}

            view_modo = ui.View()
            view_modo.add_item(ModoSelect(guild_id))
            await interaction.response.send_message(f"🎮 Tema **{tema}** selecionado! Agora escolha o modo:", view=view_modo)

    view = ui.View()
    view.add_item(TemaSelect())
    await interaction.response.send_message("Selecione o tema que deseja jogar:", view=view)

# ----------- NEXT -----------
@bot.tree.command(name="next", description="Avança para a próxima pergunta")
async def next(interaction: Interaction):
    guild_id = interaction.guild.id
    if guild_id not in partidas_ativas:
        await interaction.response.send_message("❌ Nenhuma partida ativa neste servidor.")
        return
    partida = partidas_ativas[guild_id]
    await enviar_pergunta(interaction, guild_id)
    partida["index"] +=1

# ----------- AUTO -----------
@bot.tree.command(name="auto", description="Inicia a partida automática")
async def auto(interaction: Interaction):
    guild_id = interaction.guild.id
    if guild_id not in partidas_ativas:
        await interaction.response.send_message("❌ Nenhuma partida ativa. Use /iniciar")
        return
    partidas_ativas[guild_id]["auto"] = True
    await interaction.response.send_message("🤖 Modo automático iniciado! Perguntas automáticas a cada 25s. Use /stop para parar.")
    
    async def auto_loop():
        while partidas_ativas.get(guild_id, {}).get("auto", False):
            await enviar_pergunta(interaction, guild_id)
            partidas_ativas[guild_id]["index"] +=1
            if partidas_ativas[guild_id]["index"] >= len(partidas_ativas[guild_id]["perguntas"]):
                await finalizar_partida(interaction, guild_id)
                break
            await asyncio.sleep(25)

    bot.loop.create_task(auto_loop())

# ----------- STOP -----------
@bot.tree.command(name="stop", description="Para a partida automática")
async def stop(interaction: Interaction):
    guild_id = interaction.guild.id
    if guild_id in partidas_ativas:
        partidas_ativas[guild_id]["auto"] = False
        await interaction.response.send_message("🛑 Partida pausada!")
    else:
        await interaction.response.send_message("❌ Nenhuma partida ativa.")

# ----------- RESPOSTAS TEXTUAIS (modo normal) -----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    guild_id = message.guild.id
    if guild_id in partidas_ativas:
        partida = partidas_ativas[guild_id]
        if not partida.get("multipla", True):
            idx = partida["index"]-1
            if idx<0: return
            pergunta = partida["perguntas"][idx]
            if comparar_resposta(pergunta["resposta"], message.content):
                pontos = partida.setdefault("pontos", {})
                pontos[message.author.id] = pontos.get(message.author.id,0)+1
                await message.channel.send(f"✅ {message.author.name} acertou! Total de pontos: {pontos[message.author.id]}")

# ----------- RUN BOT -----------
TOKEN = os.environ.get("DISCORD_TOKEN")
bot.run(TOKEN)
