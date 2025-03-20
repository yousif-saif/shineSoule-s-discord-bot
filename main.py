import discord
import discord.context_managers
from discord.ext import commands
from dotenv import load_dotenv
import os
from better_profanity import profanity
import json
import time
from datetime import timedelta


load_dotenv()

bot_token = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

# Creating a bot instance
bot = commands.Bot(command_prefix="&", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


async def have_correct_role(ctx: commands.Context):
    role_id = 1351266858841538560
    role = ctx.author.get_role(role_id)
    return role



def have_okay_word(split_message, okay_words):
    for i in split_message:
        if i in okay_words:
            return True

def is_bad_sentence(message):
    with open("./words.json", "r") as words:
        words_json = json.load(words)
        okay_words = words_json["okay_words"]
        more_bad_words = words_json["more_bad_words"]

        profanity.load_censor_words()

    contains_bad_word = lambda message: profanity.contains_profanity(message)

    split_message = message.split()

    
    for i in split_message:
        if i in more_bad_words:
            return True

    if contains_bad_word(message) and not have_okay_word(split_message, okay_words):
        return True

    return False

# TODO: make a role that allows users_spam who hold it to change the okay word list or add a bad word

SPAM_LIMIT = 3

users_spam = []

def count_memebers_in_spam(author):
    bad_words_said = 0
    for i in users_spam:
        # print("THIS IS IIIIII: ", i)
        if time.time() - i["time_stamp"] >= 20:
            del users_spam[users_spam.index(i)]
            continue

        if i["author"] == author:
            bad_words_said += 1
    
    return bad_words_said


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    
    # if the user is adding the okay word, the bot is gonna think it is a bad word,
    # so exlude this message of it has the command "&aow" (add okay word)
    lower_message = message.content.lower()
    if is_bad_sentence(lower_message) and lower_message.split()[0] != "&aow":
        user_spam = { "author": message.author, "time_stamp": time.time() }
        
        if count_memebers_in_spam(message.author) >= SPAM_LIMIT:
            duration = timedelta(minutes=10)
            try:
                await message.author.timeout(duration, reason="saying bad words")
                await message.channel.send(f"Timed out {message.author.mention} because they said too many bad/swear words")


            except:
                await message.channel.send(f"Cant timeout {message.author.mention} because they have higher role")


        users_spam.append(user_spam)
    
        
        if lower_message.split()[0] not in ["&row", "&rbw"]:
            await message.delete()
            await message.channel.send(f"{message.author.mention} hey you cant say that!", delete_after=5)

    await bot.process_commands(message)



def change_words(mode, word):
    """
        mods:
            1. aow (add okay word)
            2. abw (add bad word)
            3. row (remove okay word)
            4. rbw (remove bad word)
    """

    with open("./words.json", "r+") as words:
        json_words = json.load(words)
        more_bad_words = json_words["more_bad_words"]
        okay_words = json_words["okay_words"]

        word = word.lower()

        if mode == "aow":
            if word in okay_words: return "This word is already in there"
            if word in more_bad_words: return "You can't have the same word in both okay and bad words!"

            okay_words.append(word)

        elif mode == "abw":
            if word in more_bad_words: return "This word is already in there"
            if word in okay_words: return "You can't have the same word in both okay and bad words!"

            more_bad_words.append(word)


        elif mode == "row":
            if word not in okay_words: return "This word isn't in okay words"
            okay_words.remove(word)

        elif mode == "rbw":
            if word not in more_bad_words: return "This word isn't in bad words"
            more_bad_words.remove(word)


        words.seek(0)
        words.truncate()  

        json.dump(json_words, words, indent=4)


@bot.command(help="Add okay word")
async def aow(ctx: commands.Context, word=""):
    if not await have_correct_role(ctx):
        return await ctx.send("You dont have the permission to use this command")
    

    if not word: 
        await ctx.send("You need to include a word to add/remove it")
        return

    res = change_words("aow", word)

    if res:
        return await ctx.send(res)

    await ctx.send("The word had been added to okay words")
    

@bot.command(help="Add bad word")
async def abw(ctx, word=""):
    if not word: 
        await ctx.send("You need to include a word to add/remove it")
        return

    res = change_words("abw", word)

    if not await have_correct_role(ctx):
        return await ctx.send("You dont have the permission to use this command")
    

    if res:
        await ctx.send(res)
        return

    await ctx.send("The word had been added to bad words")
    

@bot.command(help="Remove okay word")
async def row(ctx, word=""):
    if not word:
        await ctx.send("You need to include a word to add/remove it")
        return
    
    if not await have_correct_role(ctx):
        return await ctx.send("You dont have the permission to use this command")

    res = change_words("row", word)

    if res:
        await ctx.send(res)
        return

    await ctx.send("The word had been removed from okay words")
    

@bot.command(help="Remove bad word")
async def rbw(ctx, word=""):
    if not await have_correct_role(ctx):
        return await ctx.send("You dont have the permission to use this command")
    
    if not word: 
        await ctx.send("You need to include a word to add/remove it")
        return

    res = change_words("rbw", word)


    if res:
        await ctx.send(res)
        return

    await ctx.send("The word had been removed from bad words")


@bot.command(help="See all okay words")
async def ow(ctx):
    if not await have_correct_role(ctx):
        return await ctx.send("You dont have the permission to use this command")
    
    with open("./words.json", "r") as words:
        json_words = json.load(words)

        okay_words = ", ".join(json_words["okay_words"])
        if not okay_words:
            await ctx.send("No okay words have been set")

        else:
            await ctx.author.send(okay_words)
            await ctx.send("Sent okay words in DMs")

    
@bot.command(help="DM all bad words")
async def bw(ctx):
    if not await have_correct_role(ctx):
        return await ctx.send("You dont have the permission to use this command")
    
    with open("./words.json", "r") as words:
        json_words = json.load(words)

        bad_wrods = ", ".join(json_words["more_bad_words"])
        if not bad_wrods:
            await ctx.send("No bad words have been set")

        else:
            await ctx.author.send("bad/swear words WARNING: ||" + bad_wrods + "||\n(this was triggerd by the user)")
            await ctx.send("Sent bad words in DMs")


bot.run(bot_token)