import discord
from discord.ext import commands
import asyncio
import os

# ================= НАСТРОЙКИ =================

TOKEN = os.getenv("DISCORD_TOKEN")

FORM_CHANNEL_NAME = "ankety"
LOG_CHANNEL_NAME = "bot-logs"

OFFICER_ROLE_NAMES = ["Officer Crew", "GM"]
ROLE_AFTER_FORM = "Trial"

TIMEOUT_SECONDS = 3000

QUESTIONS = [
    "1️⃣ **Питання:**\nДосвід та класи: Ваш досвід гри на патчі 3.3.5a. Класи та спеціалізації, якими володієте на високому рівні. Вкажіть ключові досягнення (LoD, Bane, RS 25HC), якщо є.",
    "2️⃣ **Питання:**\nПріоритети: Ваша мета в гільдії — жорсткий прогрес (спідрани, мін-максинг) чи стабільне закриття контенту в адекватні терміни?",
    "3️⃣ **Питання:**\nРейд-тайм: Чи підходить вам наш графік (Середа/Четверг/Неділя(Опціонально) - 19:00)? Чи гарантуєте стабільний онлайн без запізнень?",
    "4️⃣ **Питання:**\nІнтерфейс: Надішліть скриншот вашого UI в рейді або бойовому режимі. Офіцери мають бачити бі́нди та актуальні аддони.",
    "5️⃣ **Питання:**\nОптимізація (Min-Max): Які професії прокачані на персонажі? Чи готові ви змінити їх для мін-максу за потреби рейду?",
    "6️⃣ **Питання:**\nКоординація: Наявність мікрофона та можливість активного спілкування в Discord. Чи готові ви оперативно доповідати про механіки?",
    "7️⃣ **Питання:**\nАльти: Чи є у вас підготовлені альти для заміни в рейдах?",
    "8️⃣ **Питання:**\nІсторія: Попередня гільдія та причина переходу.",
    "9️⃣ **Питання:**\nПідготовка: Хімія, їжа, pre-pot на кожному пулі."
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

async def send_log(guild, text):
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel:
        await channel.send(text)

# ================= VIEW =================

class ReviewView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member

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
            await self.member.send("🟢 Анкету схвалено! Ласкаво просимо 🎉")
        except:
            pass

        await send_log(interaction.guild, f"🟢 Прийнято: {self.member} ({interaction.user})")
        self.disable_buttons()
        await interaction.message.edit(view=self)
        await interaction.response.send_message("✅ Прийнято", ephemeral=True)

    @discord.ui.button(label="🔴 Відхилити", style=discord.ButtonStyle.danger)
    async def reject(self, interaction, button):
        try:
            await self.member.send("🔴 Анкету відхилено.")
        except:
            pass

        await send_log(interaction.guild, f"🔴 Відхилено: {self.member} ({interaction.user})")
        self.disable_buttons()
        await interaction.message.edit(view=self)
        await interaction.response.send_message("❌ Відхилено", ephemeral=True)

# ================= АНКЕТА =================

async def start_form(member):
    await send_log(member.guild, f"📝 Запуск анкети: {member}")
    dm = await member.create_dm()
    answers = []

    await dm.send(f"👋 Вітаємо, **{member.name}**!\nАнкета запущена офіцером.")

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

    await dm.send("✅ Дякуємо! Анкета на розгляді ⏳")

    form = f"📋 **Нова анкета**\n👤 {member.mention}\n\n"
    for i, a in enumerate(answers):
        form += f"**{QUESTION_TITLES[i]}:**\n{a['text']}\n\n"

    channel = discord.utils.get(member.guild.text_channels, name=FORM_CHANNEL_NAME)

    mentions = []
    for r in OFFICER_ROLE_NAMES:
        role = discord.utils.get(member.guild.roles, name=r)
        if role:
            mentions.append(role.mention)

    await channel.send(f"{' '.join(mentions)}\n\n{form}", view=ReviewView(member))

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
