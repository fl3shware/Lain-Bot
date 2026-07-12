import json
import os
import random
import time

import discord
from discord.ext import commands, tasks

import config
from data import LAYER_UP_LINES

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data_store")
DATA_PATH = os.path.join(DATA_DIR, "xp_data.json")


def xp_for_layer(layer):
    return config.XP_PER_LAYER * layer


def layer_for_xp(xp):
    return min(xp // config.XP_PER_LAYER, config.MAX_LAYER)


def int_to_roman(n):
    vals = [(1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),(100,"C"),(90,"XC"),
            (50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
    out = ""
    for v, sym in vals:
        while n >= v:
            out += sym
            n -= v
    return out


def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_user(data, user_id):
    # setdefault here so old records (saved before prestige/daily existed) don't break
    user = data.setdefault(user_id, {})
    user.setdefault("xp", 0)
    user.setdefault("last_daily", 0)
    user.setdefault("prestige", 0)
    return user


async def announce_layer_up(destination, member, new_layer):
    if new_layer >= config.MAX_LAYER:
        text = (
            f"{member.mention} has reached Layer {config.MAX_LAYER} - the deepest layer of the Wired.\n"
            f"there is nowhere left to descend... unless you let go and start again.\n"
            f"use =prestige to loop back with a permanent mark."
        )
    else:
        line = random.choice(LAYER_UP_LINES)
        text = f"{member.mention} has descended to Layer {new_layer} of the Wired.\n*{line}*"

    try:
        await destination.send(text)
    except discord.HTTPException:
        pass


class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_cooldowns = {}
        self.reaction_cooldowns = {}
        self.voice_xp_loop.start()

    def cog_unload(self):
        self.voice_xp_loop.cancel()

    # ---- messages ----

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        now = time.time()
        last = self.message_cooldowns.get(message.author.id, 0)
        if now - last < config.XP_COOLDOWN_SECONDS:
            return
        self.message_cooldowns[message.author.id] = now

        data = load_data()
        user = get_user(data, str(message.author.id))
        old_layer = layer_for_xp(user["xp"])
        user["xp"] += random.randint(config.XP_MIN, config.XP_MAX)
        new_layer = layer_for_xp(user["xp"])
        save_data(data)

        if new_layer > old_layer:
            await announce_layer_up(message.channel, message.author, new_layer)

    # ---- reactions ----

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None:
            return

        member = payload.member
        if member is None or member.bot:
            return

        now = time.time()
        last = self.reaction_cooldowns.get(member.id, 0)
        if now - last < config.REACTION_XP_COOLDOWN_SECONDS:
            return
        self.reaction_cooldowns[member.id] = now

        data = load_data()
        user = get_user(data, str(member.id))
        old_layer = layer_for_xp(user["xp"])
        user["xp"] += random.randint(config.REACTION_XP_MIN, config.REACTION_XP_MAX)
        new_layer = layer_for_xp(user["xp"])
        save_data(data)

        if new_layer > old_layer:
            channel = self.bot.get_channel(payload.channel_id)
            if channel is not None:
                await announce_layer_up(channel, member, new_layer)

    # ---- voice ----

    @tasks.loop(seconds=config.VOICE_XP_INTERVAL_SECONDS)
    async def voice_xp_loop(self):
        data = load_data()
        changed = False
        announcements = []

        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                # need 2+ real people in the channel or people could just sit alone and farm it
                eligible = [m for m in vc.members
                            if not m.bot and m.voice is not None and not m.voice.self_deaf and not m.voice.deaf]
                if len(eligible) < 2:
                    continue

                for member in eligible:
                    user = get_user(data, str(member.id))
                    old_layer = layer_for_xp(user["xp"])
                    user["xp"] += random.randint(config.VOICE_XP_MIN, config.VOICE_XP_MAX)
                    new_layer = layer_for_xp(user["xp"])
                    changed = True
                    if new_layer > old_layer:
                        announcements.append((vc, member, new_layer))

        if changed:
            save_data(data)

        for vc, member, new_layer in announcements:
            await announce_layer_up(vc, member, new_layer)

    @voice_xp_loop.before_loop
    async def before_voice_xp_loop(self):
        await self.bot.wait_until_ready()

    # ---- commands ----

    @commands.command(name="xphelp", aliases=["howxp", "xpinfo"])
    async def xphelp(self, ctx):
        embed = discord.Embed(
            title="how to connect deeper into the wired",
            description=f"{config.MAX_LAYER} layers total, {config.XP_PER_LAYER} xp each. "
                        f"hit layer {config.MAX_LAYER} and use =prestige to loop back with a permanent rank.",
            color=0xFFFFFF,
        )
        embed.add_field(
            name="[ chat ]",
            value=f"{config.XP_MIN}-{config.XP_MAX} xp per message, once every {config.XP_COOLDOWN_SECONDS}s",
            inline=False,
        )
        embed.add_field(
            name="[ voice ]",
            value=f"{config.VOICE_XP_MIN}-{config.VOICE_XP_MAX} xp every {config.VOICE_XP_INTERVAL_SECONDS}s "
                  f"while in a voice channel with someone else",
            inline=False,
        )
        embed.add_field(
            name="[ reactions ]",
            value=f"{config.REACTION_XP_MIN}-{config.REACTION_XP_MAX} xp per reaction, "
                  f"once every {config.REACTION_XP_COOLDOWN_SECONDS}s",
            inline=False,
        )
        embed.add_field(
            name="[ =daily ]",
            value=f"{config.DAILY_XP_MIN}-{config.DAILY_XP_MAX} xp bonus, once every 24h",
            inline=False,
        )
        embed.add_field(
            name="other commands",
            value="=rank -> your progress\n=layers -> server leaderboard\n=prestige -> reset at max layer for a permanent rank",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily(self, ctx):
        data = load_data()
        user = get_user(data, str(ctx.author.id))

        now = time.time()
        elapsed = now - user["last_daily"]
        if elapsed < config.DAILY_COOLDOWN_SECONDS:
            remaining = config.DAILY_COOLDOWN_SECONDS - elapsed
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            await ctx.send(f"already connected today, try again in {hours}h {minutes}m")
            return

        old_layer = layer_for_xp(user["xp"])
        gained = random.randint(config.DAILY_XP_MIN, config.DAILY_XP_MAX)
        user["xp"] += gained
        user["last_daily"] = now
        new_layer = layer_for_xp(user["xp"])
        save_data(data)

        await ctx.send(f"{ctx.author.mention} connected to the Wired and gained {gained} xp")

        if new_layer > old_layer:
            await announce_layer_up(ctx.channel, ctx.author, new_layer)

    @commands.command(name="prestige")
    async def prestige(self, ctx):
        data = load_data()
        user = get_user(data, str(ctx.author.id))

        current_layer = layer_for_xp(user["xp"])
        if current_layer < config.MAX_LAYER:
            await ctx.send(f"not there yet, you're at Layer {current_layer}, need Layer {config.MAX_LAYER}")
            return

        user["xp"] = 0
        user["prestige"] += 1
        save_data(data)

        title = int_to_roman(user["prestige"])
        await ctx.send(
            f"{ctx.author.mention} let go of everything and fell back into the Wired.\n"
            f"they now carry the mark Prestige {title}, and begin again at Layer 0."
        )

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = load_data()
        user = get_user(data, str(member.id))
        save_data(data)

        xp = user["xp"]
        layer = layer_for_xp(xp)
        prestige = user["prestige"]

        embed = discord.Embed(title=f"{member.display_name}'s connection to the Wired", color=0xFFFFFF)

        if prestige > 0:
            embed.add_field(name="prestige", value=int_to_roman(prestige), inline=True)

        embed.add_field(name="layer", value=f"{layer}/{config.MAX_LAYER}", inline=True)
        embed.add_field(name="total xp", value=str(xp), inline=True)

        if layer >= config.MAX_LAYER:
            embed.add_field(name="status", value="deepest layer reached, use =prestige to loop back", inline=False)
        else:
            current_floor = xp_for_layer(layer)
            next_ceiling = xp_for_layer(layer + 1)
            progress = xp - current_floor
            needed = next_ceiling - current_floor
            embed.add_field(name="progress to next layer", value=f"{progress} / {needed} xp", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="layers")
    async def layers(self, ctx):
        data = load_data()
        if not data:
            await ctx.send("no one has connected to the Wired yet.")
            return

        ranked = sorted(data.items(), key=lambda item: (item[1].get("prestige", 0), item[1]["xp"]), reverse=True)[:10]

        lines = []
        for i, (user_id, user) in enumerate(ranked, start=1):
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"user {user_id}"
            layer = layer_for_xp(user["xp"])
            prestige = user.get("prestige", 0)
            tag = f"Prestige {int_to_roman(prestige)} - " if prestige > 0 else ""
            lines.append(f"{i}. {name} - {tag}Layer {layer} ({user['xp']} xp)")

        embed = discord.Embed(title="deepest into the wired", description="\n".join(lines), color=0xFFFFFF)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(XP(bot))
