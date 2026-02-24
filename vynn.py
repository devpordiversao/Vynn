import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import random
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------- PERGUNTAS DO QUIZ (30 perguntas) --------------------
perguntas = [
    {"pergunta": "Qual o nome completo de Naruto?", "resposta":["Naruto Uzumaki"], "imagem": None, "alternativas":["Naruto Uzumaki","Sasuke Uchiha","Kakashi Hatake","Sakura Haruno"]},
    {"pergunta": "Qual o Kekkei Genkai do Sasuke?", "resposta":["Sharingan"], "imagem": None, "alternativas":["Sharingan","Byakugan","Rinnegan","Mangekyo"]},
    {"pergunta": "Quem é o pai do Goku?", "resposta":["Bardock"], "imagem": None, "alternativas":["Bardock","Gohan","Vegeta","Piccolo"]},
    {"pergunta": "Qual a transformação mais famosa do Goku?", "resposta":["Super Saiyajin"], "imagem": None, "alternativas":["Super Saiyajin","Kaioken","Ultra Instinct","Oozaru"]},
    {"pergunta": "Qual o nome do Titã de Ataque que Eren se transforma?", "resposta":["Titã de Ataque"], "imagem": None, "alternativas":["Titã de Ataque","Titã Colossal","Titã Fêmea","Titã Bestial"]},
    {"pergunta": "Quem matou os pais do Eren?", "resposta":["Titã Sorridente","Dina Fritz"], "imagem": None, "alternativas":["Titã Sorridente","Titã Colossal","Titã Bestial","Titã Fêmea"]},
    {"pergunta": "Qual o nome da espada do Ichigo em Bleach?", "resposta":["Zangetsu"], "imagem": None, "alternativas":["Zangetsu","Tensa Zangetsu","Souou","Haineko"]},
    {"pergunta": "Qual o poder do Luffy em One Piece?", "resposta":["Gomu Gomu no Mi"], "imagem": None, "alternativas":["Gomu Gomu no Mi","Mera Mera no Mi","Hito Hito no Mi","Goro Goro no Mi"]},
    {"pergunta": "Quem é o rei dos piratas em One Piece?", "resposta":["Gol D. Roger"], "imagem": None, "alternativas":["Gol D. Roger","Monkey D. Luffy","Edward Newgate","Blackbeard"]},
    {"pergunta": "Qual o nome da organização dos Akatsuki em Naruto?", "resposta":["Akatsuki"], "imagem": None, "alternativas":["Akatsuki","Konoha","Anbu","Ordem Secreta"]},
    {"pergunta": "Quem é o Deus da Destruição no universo 7 em Dragon Ball?", "resposta":["Beerus"], "imagem": None, "alternativas":["Beerus","Whis","Vegeta","Goku"]},
    {"pergunta": "Qual o nome do professor de Naruto?", "resposta":["Iruka Umino"], "imagem": None, "alternativas":["Iruka Umino","Kakashi Hatake","Jiraiya","Asuma Sarutobi"]},
    {"pergunta": "Qual o poder do Deku em My Hero Academia?", "resposta":["One For All"], "imagem": None, "alternativas":["One For All","All For One","Half-Cold Half-Hot","Explosion"]},
    {"pergunta": "Quem deu o poder pro Deku?", "resposta":["All Might"], "imagem": None, "alternativas":["All Might","All For One","Endeavor","Midnight"]},
    {"pergunta": "Qual o nome da espada do Zoro em One Piece?", "resposta":["Wado Ichimonji"], "imagem": None, "alternativas":["Wado Ichimonji","Sandai Kitetsu","Shusui","Yubashiri"]},
    {"pergunta": "Qual o número do Hollow do Ichigo?", "resposta":["Hollow Branco"], "imagem": None, "alternativas":["Hollow Branco","Hollow Negro","Hollow Vermelho","Hollow Azul"]},
    {"pergunta": "Qual o nome completo do Light Yagami em Death Note?", "resposta":["Light Yagami"], "imagem": None, "alternativas":["Light Yagami","L Lawliet","Ryuk","Misa Amane"]},
    {"pergunta": "Como se chama o Shinigami parceiro do Light?", "resposta":["Ryuk"], "imagem": None, "alternativas":["Ryuk","Rem","Sidoh","Shidoh"]},
    {"pergunta": "Qual o nome do protagonista de Fullmetal Alchemist?", "resposta":["Edward Elric"], "imagem": None, "alternativas":["Edward Elric","Alphonse Elric","Roy Mustang","Winry Rockbell"]},
    {"pergunta": "O que Edward perdeu na transmutação humana?", "resposta":["Braço direito","Perna esquerda"], "imagem": None, "alternativas":["Braço direito","Perna esquerda","Olho esquerdo","Mão direita"]},
    {"pergunta": "Qual o nome da vila do Naruto?", "resposta":["Vila da Folha","Konohagakure"], "imagem": None, "alternativas":["Vila da Folha","Vila da Areia","Vila da Névoa","Vila da Pedra"]},
    {"pergunta": "Quem é o vilão principal de My Hero Academia?", "resposta":["All For One"], "imagem": None, "alternativas":["All For One","Tomura Shigaraki","Dabi","Himiko Toga"]},
    {"pergunta": "Qual o nome do Titã Colossal em Ataque dos Titãs?", "resposta":["Bertholdt Hoover"], "imagem": None, "alternativas":["Bertholdt Hoover","Reiner Braun","Eren Yeager","Annie Leonhart"]},
    {"pergunta": "Qual o nome da organização de caçadores em Hunter x Hunter?", "resposta":["Associação de Caçadores"], "imagem": None, "alternativas":["Associação de Caçadores","Organização Zoldyck","G.I","Phantom Troupe"]},
    {"pergunta": "Qual o poder do Killua em Hunter x Hunter?", "resposta":["Eletricidade","Godspeed"], "imagem": None, "alternativas":["Eletricidade","Godspeed","Força","Velocidade"]},
    {"pergunta": "Qual o nome do protagonista de Demon Slayer?", "resposta":["Tanjiro Kamado"], "imagem": None, "alternativas":["Tanjiro Kamado","Nezuko Kamado","Zenitsu Agatsuma","Inosuke Hashibira"]},
    {"pergunta": "Quem transformou a irmã do Tanjiro em demônio?", "resposta":["Muzan Kibutsuji"], "imagem": None, "alternativas":["Muzan Kibutsuji","Akaza","Doma","Kokushibo"]},
    {"pergunta": "Qual o nome da respiração do Tanjiro?", "resposta":["Respiração da Água","Respiração do Sol"], "imagem": None, "alternativas":["Respiração da Água","Respiração do Sol","Respiração da Lua","Respiração da Fumaça"]},
    {"pergunta": "Quem é o líder dos Pilares em Demon Slayer?", "resposta":["Kagaya Ubuyashiki"], "imagem": None, "alternativas":["Kagaya Ubuyashiki","Giyu Tomioka","Shinobu Kocho","Kyojuro Rengoku"]},
    {"pergunta": "Qual o nome do protagonista de Tokyo Ghoul?", "resposta":["Ken Kaneki"], "imagem": None, "alternativas":["Ken Kaneki","Touka Kirishima","Renji Yomo","Hideyoshi Nagachika"]}
]
# -------------------- PERGUNTAS RESTANTES (completando 50) --------------------
perguntas += [
    {"pergunta": "Qual a organização que caça Ghouls em Tokyo Ghoul?", "resposta":["CCG","Comissão de Contra Medidas de Ghoul"], "imagem": None, "alternativas":["CCG","Aogiri Tree","Ghoul Association","Tokyo Police"]},
    {"pergunta": "Qual o nome do protagonista de Sword Art Online?", "resposta":["Kirito","Kazuto Kirigaya"], "imagem": None, "alternativas":["Kirito","Asuna","Eugeo","Sinon"]},
    {"pergunta": "Qual o nome da namorada do Kirito em SAO?", "resposta":["Asuna"], "imagem": None, "alternativas":["Asuna","Leafa","Sinon","Alice"]},
    {"pergunta": "Qual o poder especial de Rimuru em That Time I Got Reincarnated as a Slime?", "resposta":["Predador Único"], "imagem": None, "alternativas":["Predador Único","Regeneração","Força","Magia"]},
    {"pergunta": "Qual o nome do protagonista de Re:Zero?", "resposta":["Subaru Natsuki"], "imagem": None, "alternativas":["Subaru Natsuki","Emilia","Rem","Ram"]},
    {"pergunta": "Qual o poder do Subaru em Re:Zero?", "resposta":["Retorno pela Morte"], "imagem": None, "alternativas":["Retorno pela Morte","Magia","Força","Velocidade"]},
    {"pergunta": "Qual o nome do protagonista de Sword Art Online Alicization?", "resposta":["Kirito"], "imagem": None, "alternativas":["Kirito","Eugeo","Alice","Sinon"]},
    {"pergunta": "Quem é o antagonista principal de SAO?", "resposta":["Akihiko Kayaba","Heathcliff"], "imagem": None, "alternativas":["Akihiko Kayaba","Heathcliff","Sugou Nobuyuki","Kuradeel"]},
    {"pergunta": "Qual o nome do protagonista de Overlord?", "resposta":["Ainz Ooal Gown","Momonga"], "imagem": None, "alternativas":["Ainz Ooal Gown","Momonga","Albedo","Shalltear"]},
    {"pergunta": "Qual a classe do Ainz em Overlord?", "resposta":["Mago Supremo","Lich"], "imagem": None, "alternativas":["Mago Supremo","Lich","Guerreiro","Necromante"]},
    {"pergunta": "Qual o nome do protagonista de Black Clover?", "resposta":["Asta"], "imagem": None, "alternativas":["Asta","Yuno","Noelle","Yami"]},
    {"pergunta": "Qual o poder único do Asta em Black Clover?", "resposta":["Anti-Magia"], "imagem": None, "alternativas":["Anti-Magia","Magia de Fogo","Magia de Vento","Magia da Luz"]},
    {"pergunta": "Quem é o rival do Asta em Black Clover?", "resposta":["Yuno"], "imagem": None, "alternativas":["Yuno","Noelle","Luck","Finral"]},
    {"pergunta": "Qual o nome do protagonista de Fairy Tail?", "resposta":["Natsu Dragneel"], "imagem": None, "alternativas":["Natsu Dragneel","Lucy Heartfilia","Gray Fullbuster","Erza Scarlet"]},
    {"pergunta": "Qual a magia do Natsu em Fairy Tail?", "resposta":["Magia do Dragão de Fogo"], "imagem": None, "alternativas":["Magia do Dragão de Fogo","Magia de Terra","Magia de Água","Magia de Gelo"]},
    {"pergunta": "Quem criou o Natsu como filho?", "resposta":["Igneel"], "imagem": None, "alternativas":["Igneel","Makarov","Zeref","Laxus"]},
    {"pergunta": "Qual o nome da guilda principal de Fairy Tail?", "resposta":["Fairy Tail"], "imagem": None, "alternativas":["Fairy Tail","Phantom Lord","Blue Pegasus","Lamia Scale"]},
    {"pergunta": "Qual o nome do protagonista de Tower of God?", "resposta":["Bam","Twenty-Fifth Bam"], "imagem": None, "alternativas":["Bam","Rachel","Khun Aguero","Rak Wraithraiser"]},
    {"pergunta": "Quem é a amiga que o Bam procura em Tower of God?", "resposta":["Rachel"], "imagem": None, "alternativas":["Rachel","Khun","Androssi","Endorsi"]},
    {"pergunta": "Qual o nome do protagonista de No Game No Life?", "resposta":["Sora"], "imagem": None, "alternativas":["Sora","Shiro","Steph","Jibril"]},
    {"pergunta": "Qual o nome da irmã do Sora em No Game No Life?", "resposta":["Shiro"], "imagem": None, "alternativas":["Shiro","Sora","Izuna","Jibril"]},
    {"pergunta": "Qual o poder do Escanor em Seven Deadly Sins?", "resposta":["Sunshine"], "imagem": None, "alternativas":["Sunshine","Darkness","Strength","Flame"]},
    {"pergunta": "Quem é o protagonista de Seven Deadly Sins?", "resposta":["Meliodas"], "imagem": None, "alternativas":["Meliodas","Elizabeth","Ban","Diane"]},
    {"pergunta": "Qual o pecado do Meliodas?", "resposta":["Ira"], "imagem": None, "alternativas":["Ira","Gula","Luxúria","Inveja"]},
    {"pergunta": "Qual o nome do protagonista de Vinland Saga?", "resposta":["Thorfinn"], "imagem": None, "alternativas":["Thorfinn","Askeladd","Canute","Bjorn"]},
    {"pergunta": "Quem matou o pai do Thorfinn?", "resposta":["Askeladd"], "imagem": None, "alternativas":["Askeladd","Canute","Bjorn","Floki"]},
    {"pergunta": "Qual o nome do protagonista de Jujutsu Kaisen?", "resposta":["Yuji Itadori"], "imagem": None, "alternativas":["Yuji Itadori","Megumi Fushiguro","Nobara Kugisaki","Satoru Gojo"]},
    {"pergunta": "Qual o espírito maldito que habita o Yuji?", "resposta":["Ryomen Sukuna"], "imagem": None, "alternativas":["Ryomen Sukuna","Mahito","Jogo","Hanami"]},
    {"pergunta": "Quem é o professor do Yuji em Jujutsu Kaisen?", "resposta":["Satoru Gojo"], "imagem": None, "alternativas":["Satoru Gojo","Kento Nanami","Suguru Geto","Toge Inumaki"]},
    {"pergunta": "Qual o nome do protagonista de Chainsaw Man?", "resposta":["Denji"], "imagem": None, "alternativas":["Denji","Power","Aki Hayakawa","Makima"]}
]

# -------------------- FUNÇÃO PARA ENVIAR PERGUNTA --------------------
async def enviar_pergunta(ctx, pergunta_obj):
    """Envia uma pergunta de quiz com botões de múltipla escolha"""
    view = View(timeout=20)  # 20 segundos para responder

    for alt in pergunta_obj["alternativas"]:
        button = Button(label=alt, style=discord.ButtonStyle.primary)

        async def callback(interaction, alt=alt):
            if interaction.user != ctx.author:
                await interaction.response.send_message("Você não pode responder esta pergunta!", ephemeral=True)
                return
            if alt in pergunta_obj["resposta"]:
                await interaction.response.edit_message(content=f"✅ Correto! A resposta era: {', '.join(pergunta_obj['resposta'])}", view=None)
            else:
                await interaction.response.edit_message(content=f"❌ Você errou! A resposta correta era: {', '.join(pergunta_obj['resposta'])}", view=None)

        button.callback = callback
        view.add_item(button)

    embed = discord.Embed(title="Quiz de Anime", description=pergunta_obj["pergunta"], color=discord.Color.blurple())
    await ctx.send(embed=embed, view=view)
    # -------------------- COMANDOS SLASH --------------------
@bot.command()
async def iniciar(ctx):
    """Inicia o quiz de anime"""
    ctx.quiz_perguntas = perguntas.copy()  # Faz uma cópia das perguntas para cada usuário
    if not ctx.quiz_perguntas:
        await ctx.send("Não há perguntas disponíveis no momento!")
        return
    pergunta_obj = random.choice(ctx.quiz_perguntas)
    ctx.quiz_perguntas.remove(pergunta_obj)
    await enviar_pergunta(ctx, pergunta_obj)


@bot.command()
async def next(ctx):
    """Mostra a próxima pergunta do quiz"""
    if not hasattr(ctx, "quiz_perguntas") or not ctx.quiz_perguntas:
        await ctx.send("Não há mais perguntas! Use /iniciar para começar novamente.")
        return
    pergunta_obj = random.choice(ctx.quiz_perguntas)
    ctx.quiz_perguntas.remove(pergunta_obj)
    await enviar_pergunta(ctx, pergunta_obj)


# -------------------- MINIGAMES SIMPLES --------------------
@bot.command()
async def pedrapapeltesoura(ctx):
    """Inicia Pedra, Papel ou Tesoura"""
    opcoes = ["Pedra","Papel","Tesoura"]
    escolha_bot = random.choice(opcoes)
    await ctx.send(f"O bot escolheu: {escolha_bot}\nFaça sua jogada com /jogar [Pedra/Papel/Tesoura]")

@bot.command()
async def jogar(ctx, escolha):
    """Joga Pedra, Papel ou Tesoura"""
    escolha = escolha.capitalize()
    opcoes = ["Pedra","Papel","Tesoura"]
    if escolha not in opcoes:
        await ctx.send("Escolha inválida! Pedra, Papel ou Tesoura.")
        return
    escolha_bot = random.choice(opcoes)
    resultado = ""
    if escolha == escolha_bot:
        resultado = "Empate!"
    elif (escolha=="Pedra" and escolha_bot=="Tesoura") or (escolha=="Tesoura" and escolha_bot=="Papel") or (escolha=="Papel" and escolha_bot=="Pedra"):
        resultado = "Você ganhou!"
    else:
        resultado = "Você perdeu!"
    await ctx.send(f"Você: {escolha}\nBot: {escolha_bot}\nResultado: {resultado}")


# -------------------- OUTROS MINIGAMES SIMPLES --------------------
@bot.command()
async def dado(ctx):
    """Joga um dado de 6 lados"""
    resultado = random.randint(1,6)
    await ctx.send(f"🎲 O dado caiu em: {resultado}")

@bot.command()
async def moeda(ctx):
    """Joga cara ou coroa"""
    resultado = random.choice(["Cara", "Coroa"])
    await ctx.send(f"🪙 O resultado foi: {resultado}")
    # -------------------- MODERAÇÃO AVANÇADA --------------------
@bot.event
async def on_member_ban(guild, user):
    # Envia log para o servidor (caso haja canal #logs)
    canal_log = discord.utils.get(guild.text_channels, name="logs")
    if canal_log:
        await canal_log.send(f"🚫 {user} foi banido do servidor {guild.name}")
    # Envia log para o dono do bot via DM
    dono = await bot.fetch_user(1327679436128129159)  # Substitua pelo seu ID
    await dono.send(f"🚫 {user} foi banido do servidor {guild.name}")

@bot.event
async def on_member_unban(guild, user):
    dono = await bot.fetch_user(YOUR_USER_ID)
    await dono.send(f"✅ {user} foi desbanido do servidor {guild.name}")

@bot.event
async def on_member_update(before, after):
    dono = await bot.fetch_user(YOUR_USER_ID)
    if before.nick != after.nick:
        await dono.send(f"✏️ {before} mudou o nickname para {after.nick} em {after.guild.name}")

# -------------------- MINIGAMES AVANÇADOS --------------------
@bot.command()
async def adivinhar(ctx):
    """Minigame: Adivinhe o número"""
    numero = random.randint(1,50)
    await ctx.send("🎯 Tente adivinhar o número entre 1 e 50 usando /palpite [número]")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for _ in range(5):  # 5 tentativas
        try:
            msg = await bot.wait_for("message", check=check, timeout=20)
            palpite = int(msg.content)
            if palpite == numero:
                await ctx.send(f"🎉 Correto! O número era {numero}")
                return
            elif palpite < numero:
                await ctx.send("⬆️ Mais alto!")
            else:
                await ctx.send("⬇️ Mais baixo!")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Tempo esgotado! O número era {numero}")
            return
        except ValueError:
            await ctx.send("Digite apenas números!")

# -------------------- START DO BOT --------------------
bot.run(os.environ["DISCORD_TOKEN"])
