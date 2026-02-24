import discord
from discord.ext import commands
import os, json, random, asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

scores = {}

def load_questions():
    questions = {}
    for file in ["temas.json","temas2.json","temas3.json","temas4.json"]:
        try:
            with open(file, "r", encoding="utf-8") as f:
                questions.update(json.load(f))
        except:
            pass
    return questions

QUESTIONS = load_questions()
active_game = {}

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

@bot.command()
async def iniciar(ctx, tema):
    tema = tema.lower()
    if tema not in QUESTIONS:
        await ctx.send("Tema não encontrado.")
        return

    q = random.choice(QUESTIONS[tema])
    active_game[ctx.channel.id] = {"resposta": q["resposta"].lower(), "tema": tema}

    msg = await ctx.send(f"📚 **Pergunta ({tema})**\n{q['pergunta']}\n⏳ 20s")

    for i in range(20,0,-1):
        await asyncio.sleep(1)

    if ctx.channel.id in active_game:
        await ctx.send("⏰ Ninguém acertou!")
        active_game.pop(ctx.channel.id)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in active_game:
        data = active_game[message.channel.id]
        if message.content.lower() == data["resposta"]:
            user = str(message.author)
            scores[user] = scores.get(user,0)+1
            await message.channel.send(f"🎉 {message.author.mention} acertou! (+1 ponto)")
            active_game.pop(message.channel.id)

    await bot.process_commands(message)

@bot.command()
async def rank(ctx):
    if not scores:
        await ctx.send("Sem pontuação ainda.")
        return
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    msg = "🏆 Ranking:\n"
    for i,(u,p) in enumerate(top,1):
        msg += f"{i}. {u} - {p} pts\n"
    await ctx.send(msg)

bot.run(os.getenv("DISCORD_TOKEN"))
