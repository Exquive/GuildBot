import discord
from discord.ext import commands
import asyncio

# ================= НАСТРОЙКИ =================

import os
TOKEN = os.getenv("DISCORD_TOKEN")

FORM_CHANNEL_NAME = "ankety"
LOG_CHANNEL_NAME = "bot-logs"

OFFICER_ROLE_NAMES = ["Officer Crew", "GM"]
ROLE_AFTER_FORM = "Member"

TIMEOUT_SECONDS = 3000

QUESTIONS = [
    "1️⃣ **Питання:**\nДосвід та класи: Ваш досвід гри на патчі 3.3.5a. Класи та спеціалізації, якими володієте на високому рівні. Вкажіть ключові досягнення (LoD, Bane, RS 25HC), якщо є.",

    "2️⃣ **Питання:**\nПріоритети: Ваша мета в гільдії — жорсткий прогрес (спідрани, мін-максинг) чи стабільне закриття контенту в адекватні терміни?",

    "3️⃣ **Питання:**\nРейд-тайм: Чи підходить вам наш графік (Середа/Четверг/Неділя - 19:00)? Чи гарантуєте стабільний онлайн без запізнень?",

    "4️⃣ **Питання:**\nІнтерфейс: Надішліть скриншот вашого UI в рейді або бойовому режимі. Офіцери мають бачити бі́нди та актуальні аддони.",

    "5️⃣ **Питання:**\nОптимізація (Min-Max): Які професії прокачані на персонажі? Чи готові ви змінити їх для мін-максу за потреби рейду?",

    "6️⃣ **Питання:**\nКоординація: Наявність мікрофона та можливість активного спілкування в Discord. Чи готові ви оперативно доповідати про механіки (Defile, мітки тощо)?",

    "7️⃣ **Питання:**\nАльти: Чи є у вас підготовлені альти для заміни в рейдах? Якщо так — вкажіть ніки.",

    "8️⃣ **Питання:**\nІсторія: Попередня гільдія та конкретна причина переходу до нас.",

    "9️⃣ **Питання:**\nПідготовка: Наявність запасу хімії (фласки, поти) та їжі на весь рейд-тайм. Чи є для вас проблемою повний pre-pot на кожному пулі?"
]

QUESTION_TITLES = [
    "Досвід та класи",
    "Пріоритети",
    "Рейд-тайм",
    "Інтерфейс",
    "Оптимізація (Min-Max)",
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

# ================= VIEW З КНОПКАМИ =================

class ReviewView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member

    def disable_buttons(self):
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if any(role.name in OFFICER_ROLE_NAMES for role in interaction.user.roles):
            return True

        await interaction.response.send_message(
            "❌ Тільки Officer Crew або GM можуть приймати рішення.",
            ephemeral=True
        )
        return False

    @discord.ui.button(label="🟢 Прийняти", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=ROLE_AFTER_FORM)
        if role:
            await self.member.add_roles(role)

        try:
            await self.member.send(
                "🟢 **Вашу анкету схвалено!**\n"
                "Ласкаво просимо до складу гільдії 🎉\n"
                "Звʼяжіться з офіцером у грі."
            )
        except:
            pass

        await send_log(
            interaction.guild,
            f"🟢 Анкета прийнята: {self.member.mention} — {interaction.user.mention}"
        )

        self.disable_buttons()
        await interaction.message.edit(view=self)
        await interaction.response.send_message("✅ Анкету прийнято", ephemeral=True)

    @discord.ui.button(label="🔴 Відхилити", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.send(
                "🔴 **Вашу анкету відхилено.**\n"
                "Дякуємо за інтерес до гільдії."
            )
        except:
            pass

        await send_log(
            interaction.guild,
            f"🔴 Анкета відхилена: {self.member.mention} — {interaction.user.mention}"
        )

        self.disable_buttons()
        await interaction.message.edit(view=self)
        await interaction.response.send_message("❌ Анкету відхилено", ephemeral=True)

# ================= EVENTS =================

@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")

@bot.event
async def on_member_join(member):
    if len(member.roles) > 1:
        return

    await send_log(member.guild, f"👤 Новий учасник: {member}")

    try:
        dm = await member.create_dm()
        answers = []

        await dm.send(
            f"👋 Вітаємо, **{member.name}**!\n\n"
            "Для доступу до гільдії необхідно пройти анкету.\n"
            f"⏰ У вас є {TIMEOUT_SECONDS // 60} хвилин."
        )

        await asyncio.sleep(3)

        for question in QUESTIONS:
            await dm.send(question)

            def check(m):
                return m.author == member and isinstance(m.channel, discord.DMChannel)

            msg = await bot.wait_for("message", check=check, timeout=TIMEOUT_SECONDS)

            answers.append({
                "question": question,
                "text": msg.content if msg.content else "📎 Файл прикріплено",
                "file": msg.attachments[0].url if msg.attachments else None
            })

        # ======= ПОВІДОМЛЕННЯ КОРИСТУВАЧУ =======
        await dm.send(
            "✅ **Дякуємо за відповіді!**\n"
            "Ваша заявка передана офіцерам та знаходиться на розгляді ⏳"
        )

        # ======= АНКЕТА ДЛЯ ОФІЦЕРІВ =======
        form_text = f"📋 **Нова анкета**\n👤 {member.mention}\n\n"

        for i, ans in enumerate(answers):
            form_text += (
                f"**{i+1}️⃣ {QUESTION_TITLES[i]}:**\n"
                f"{ans['text']}\n\n"
            )

        form_channel = discord.utils.get(member.guild.text_channels, name=FORM_CHANNEL_NAME)

        mentions = []
        for role_name in OFFICER_ROLE_NAMES:
            role = discord.utils.get(member.guild.roles, name=role_name)
            if role:
                mentions.append(role.mention)

        await form_channel.send(
            f"{' '.join(mentions)}\n\n{form_text}",
            view=ReviewView(member)
        )

        for ans in answers:
            if ans["file"]:
                await form_channel.send(
                    f"🖼 **Скріншот від {member.mention}:**\n{ans['file']}"
                )

        await send_log(member.guild, f"📋 Нова анкета від {member.mention}")

    except asyncio.TimeoutError:
        await send_log(member.guild, f"⏰ Таймаут анкети: {member.mention}")

    except Exception as e:
        await send_log(member.guild, f"💥 Помилка: `{e}`")
        print("❌ Помилка:", e)

bot.run(TOKEN)
