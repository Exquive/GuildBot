import discord
from discord.ext import commands
import asyncio
import os

# ================= НАСТРОЙКИ =================

TOKEN = os.getenv("DISCORD_TOKEN")

FORM_CHANNEL_NAME = "ankety"
LOG_CHANNEL_NAME = "bot-logs"

OFFICER_ROLE_NAMES = ["Officer Crew", "GM", "Officer"]
ROLE_AFTER_FORM = "Trial"

TIMEOUT_SECONDS = 3000

QUESTIONS = [
    "1️⃣ **Питання:**\nДосвід та класи: Ваш досвід гри на патчі 3.3.5a.",
    "2️⃣ **Питання:**\nПріоритети: Мета в гільдії.",
    "3️⃣ **Питання:**\nРейд-тайм: Чи підходить графік?",
    "4️⃣ **Питання:**\nІнтерфейс: Надішліть скриншот UI.",
    "5️⃣ **Питання:**\nОптимізація: Професії та min-max.",
    "6️⃣ **Питання:**\nКоординація: Мікрофон, Discord.",
    "7️⃣ **Питання:**\nАльти.",
    "8️⃣ **Питання:**\nІсторія: Попередня гільдія.",
    "9️⃣ **Питання:**\nПідготовка: Хімія, їжа, pre-pot."
]

QUESTION_TITLES = [
    "Досвід та класи",
    "Пріоритети",
    "Рейд-тайм",
    "Інтерфейс",
    "Оптимізація",
    "Координація",
    "Альти",
    "Історія",
    "Підготовка"
]

# =============================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= ЛОГИ =================

async def send_log(guild, content=None, view=None):
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel:
        await channel.send(content=content, view=view)

# ================= VIEW =================

class LogLinkView(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="🔗 Перейти до анкети",
            url=url,
            style=discord.ButtonStyle.link
        ))

class ReviewView(discord.ui.View):
    def __init__(self, member, anketa_url):
        super().__init__(timeout=None)
        self.member = member
        self.anketa_url = anketa_url

    def disable_buttons(self):
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction):
        if any(r.name in OFFICER_ROLE_NAMES for r in interaction.user.roles):
            return True
        await interaction.response.send_message("❌ Недостатньо прав", ephemeral=True)
        return False

    @discord.ui.button(label="🟢 Прийняти", style=discord.ButtonStyle.success)
    async def accept(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name=ROLE_AFTER_FORM)
        if role:
            await self.member.add_roles(role)

        try:
            await self.member.send(
                "🟢 **Анкету схвалено!**\n"
                "Ласкаво просимо до гільдії 🎉"
            )
        except:
            pass

        await send_log(
            interaction.guild,
            f"🟢 **Прийнято:** {self.member.mention}\n"
            f"👮 Офіцер: {interaction.user.mention}",
            view=LogLinkView(self.anketa_url)
        )

        self.disable_buttons()
        await interaction.message.edit(view=self)
        await interaction.response.send_message("✅ Прийнято", ephemeral=True)

    @discord.ui.button(label="🔴 Відхилити", style=discord.ButtonStyle.danger)
    async def reject(self, interaction, button):
        try:
            await self.member.send("🔴 **Анкету відхилено.**")
        except:
            pass

        await send_log(
            interaction.guild,
            f"🔴 **Відхилено:** {self.member.mention}\n"
            f"👮 Офіцер: {interaction.user.mention}",
            view=LogLinkView(self.anketa_url)
        )

        self.disable_buttons()
        await interaction.message.edit(view=self)
        await interaction.response.send_message("❌ Відхилено", ephemeral=True)

# ================= АНКЕТА =================

async def start_form(member):
    await send_log(member.guild, f"📝 **Запуск анкети:** {member.mention}")

    dm = await member.create_dm()
    answers = []

    await dm.send(f"👋 Вітаємо, **{member.name}**!\nАнкета запущена.")

    await asyncio.sleep(3)

    for q in QUESTIONS:
        await dm.send(q)

        def check(m):
            return m.author == member and isinstance(m.channel, discord.DMChannel)

        msg = await bot.wait_for("message", check=check, timeout=TIMEOUT_SECONDS)

        answers.append({
            "text": msg.content if msg.content else "📎 Файл",
            "file": msg.attachments[0].url if msg.attachments else None
        })

    await dm.send("✅ **Дякуємо!** Анкета передана офіцерам ⏳")

    form_text = f"📋 **Нова анкета**\n👤 {member.mention}\n\n"
    for i, a in enumerate(answers):
        form_text += f"**{QUESTION_TITLES[i]}:**\n{a['text']}\n\n"

    channel = discord.utils.get(member.guild.text_channels, name=FORM_CHANNEL_NAME)

    mentions = []
    for r in OFFICER_ROLE_NAMES:
        role = discord.utils.get(member.guild.roles, name=r)
        if role:
            mentions.append(role.mention)

    anketa_message = await channel.send(f"{' '.join(mentions)}\n\n{form_text}")
    anketa_url = anketa_message.jump_url

    await anketa_message.edit(view=ReviewView(member, anketa_url))

    for a in answers:
        if a["file"]:
            await channel.send(f"🖼 {a['file']}")

# ================= EVENTS =================

@bot.event
async def on_ready():
    print(f"✅ Бот онлайн: {bot.user}")

@bot.event
async def on_member_join(member):
    if len(member.roles) <= 1:
        await start_form(member)

# ================= КОМАНДА =================

@bot.command()
async def startform(ctx, member: discord.Member):
    if not any(r.name in OFFICER_ROLE_NAMES for r in ctx.author.roles):
        await ctx.send("❌ Недостатньо прав")
        return

    await ctx.send(f"📝 Анкета запущена для {member.mention}")
    await start_form(member)

bot.run(TOKEN)