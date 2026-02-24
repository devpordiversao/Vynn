import discord
from discord.ext import commands, tasks
from discord import app_commands, Interaction, ui
import json
import random
import asyncio
import os

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

# ----------- HELPERS -----------
def comparar_resposta(correta, resposta_usuario):
    return correta.lower() in resposta_usuario.lower()

# ----------- VIEW MÚLTIPLA ESCOLHA -----------
class MultipleChoiceView(ui.View):
    def __init__(self, pergunta, guild_id):
        super().__init__(timeout=20)
        self.pergunta = pergunta
        self.guild_id = guild_id
        self.vencedores = []
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

# ----------- FUNÇÃO ENVIAR PERGUNTA -----------
async def enviar_pergunta(interaction: Interaction, guild_id):
    partida = partidas_ativas[guild_id]
    idx = partida["index"]
    pergunta = partida["perguntas"][idx]

    embed = discord.Embed(title=f"Pergunta {idx+1}", description=pergunta["pergunta"], color=discord.Color.gold())
    if "imagem" in pergunta and pergunta["imagem"]:
        embed.set_image(url=pergunta["imagem"])
    
    if partida.get("multipla", True) and "opcoes" in pergunta:
        view = MultipleChoiceView(pergunta, guild_id)
        await interaction.channel.send(embed=embed, view=view)
    else:
        await interaction.channel.send(embed=embed)
        # timer 20s
        for i in range(20,0,-1):
            await asyncio.sleep(1)
        await interaction.channel.send("⏰ Ninguém acertou!")

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
        await interaction.response.send_message(f"🎮 Partida iniciada no tema **{tema}**! Digite /next para próxima pergunta ou /auto para automática.")

@bot.tree.command(name="iniciar", description="Inicia uma partida em determinado tema")
async def iniciar(interaction: Interaction):
    view = ui.View()
    view.add_item(TemaSelect())
    await interaction.response.send_message("Selecione o tema que deseja jogar:", view=view)

@bot.tree.command(name="next", description="Avança para a próxima pergunta")
async def next(interaction: Interaction):
    guild_id = interaction.guild.id
    if guild_id not in partidas_ativas:
        await interaction.response.send_message("❌ Nenhuma partida ativa neste servidor.")
        return
    partida = partidas_ativas[guild_id]
    idx = partida["index"]
    if idx >= len(partida["perguntas"]):
        await interaction.response.send_message("✅ Todas as perguntas acabaram!")
        del partidas_ativas[guild_id]
        return
    await enviar_pergunta(interaction, guild_id)
    partida["index"] +=1
    partida["ja_clicou"] = []

@bot.tree.command(name="auto", description="Inicia a partida automática")
async def auto(interaction: Interaction):
    guild_id = interaction.guild.id
    if guild_id not in partidas_ativas:
        await interaction.response.send_message("❌ Nenhuma partida ativa. Use /iniciar")
        return
    partidas_ativas[guild_id]["auto"] = True
    await interaction.response.send_message("🤖 Modo automático iniciado! Use /stop para parar.")

@bot.tree.command(name="stop", description="Para a partida automática")
async def stop(interaction: Interaction):
    guild_id = interaction.guild.id
    if guild_id in partidas_ativas:
        partidas_ativas[guild_id]["auto"] = False
        await interaction.response.send_message("🛑 Partida pausada!")
    else:
        await interaction.response.send_message("❌ Nenhuma partida ativa.")

# ----------- CAPTURAR RESPOSTAS TEXTUAIS (normal) -----------
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
