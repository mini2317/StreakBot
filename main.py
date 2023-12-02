from discord.ext import tasks, commands
from discord.ui import View, Button, Select
from discord import Interaction, ButtonStyle
from emoji import core
import discord, sqlite3, os, asyncio, random, datetime, json

DATABASE_PATH = os.path.join('.','data','project.db')
TIP_PATH = os.path.join('.','data','tips.json')
TOKEN_PATH = os.path.join('.','data','token.txt')
PROJECT_MASTER = 'ProjectMaster'
FHBT_IMAGE = "https://media.discordapp.net/attachments/1175423530054201364/1177105955545153636/face-holding-back-tears.png?ex=65714c59&is=655ed759&hm=ca7484f164beebf32a17f252fd430b5c1df05731899379ecff0fe92bfcb2f738&=&format=webp&width=360&height=360"
whatAreYouDoing = {
    "프로젝트 생성" : set()
}
with open(TOKEN_PATH, 'r', encoding = "UTF-8") as file:
    token = file.read()
bot = commands.Bot(command_prefix='ㅅ', intents=discord.Intents.all())
bot.remove_command('help')

con = sqlite3.connect(DATABASE_PATH)
cur = con.cursor()
tableExist = cur.execute(f"SELECT name FROM sqlite_master WHERE type='table';").fetchall()
if not any(map(lambda x : x[0] == PROJECT_MASTER or PROJECT_MASTER == f"'{x[0]}'", tableExist)):
    cur.execute(f'''CREATE TABLE {PROJECT_MASTER} (projectId TEXT, projectColor int, notionChannel int, roleId INT)''')
con.commit()
con.close()

tipList = None
with open(TIP_PATH, 'r', encoding = "UTF-8") as file:
    tipList = json.loads(file.read())

def randomColor(): return random.randint(0, 255) * 256 * 256 + random.randint(0, 255) * 256 + random.randint(0, 255)

CHANNEL_EMOJI = {
    discord.ChannelType.text : "#️⃣",
    discord.ChannelType.news : "📰",
    discord.ChannelType.news_thread : "🗞️"
}

def fetchServer():
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    search = cur.execute(f'''
        SELECT *
        FROM {PROJECT_MASTER};
    ''').fetchall()
    con.commit()
    con.close()

class RegisterUser(View):
    def __init__(self, ctx, arg):
        super().__init__()
        self.ctx = ctx
        self.arg = arg
        self.disabled = False
    
    @discord.ui.button(label = "확인", style = discord.ButtonStyle.primary, emoji = "✅")
    async def ok(self, interaction, button):
        user = self.ctx.author
        if self.disabled or (not interaction.user.id == user.id):
            return
        projectName = ' '.join(self.arg)
        self.disabled = True
        con = sqlite3.connect(DATABASE_PATH)
        cur = con.cursor()
        search = cur.execute(f'''
            SELECT *
            FROM "{self.ctx.guild.id}_{projectName}"
            WHERE userId = {user.id};
        ''').fetchall()
        if not search:
            cur.execute(f'''INSERT INTO "{self.ctx.guild.id}_{projectName}" (userId) VALUES ({user.id})''')
            embed = discord.Embed(
                title = "✅ 가입 완료 ✅",
                description = '가입 성공 ㅎㅇㅌ',
                color = discord.Color.green()
            )
            role = discord.utils.get(self.ctx.guild.roles, name = projectName)
            if role is not None:
                print(role)
                await user.add_roles(role)
            else:
                embed.description += '\n역할은 누군가가 삭제해서 줄 수가 없음..'
            self.callback = await interaction.response.send_message(embed = embed)
        else:
            embed = discord.Embed(
                title = "⚠️ 가입 실패 ⚠️",
                description='? 이미 가입됨',
                color = 0xed2b2a
            )
            self.callback = await interaction.response.send_message(embed = embed)
        con.commit()
        con.close()

class DeleteUser(View):
    def __init__(self, ctx, arg):
        super().__init__()
        self.ctx = ctx
        self.arg = arg
        self.disabled = False
    
    @discord.ui.button(label = "확인", style = discord.ButtonStyle.primary, emoji = "✅")
    async def ok(self, interaction, button):
        user = self.ctx.message.author
        if self.disabled or (not interaction.user.id == user.id):
            return
        projectName = ' '.join(self.arg)
        self.disabled = True
        con = sqlite3.connect(DATABASE_PATH)
        cur = con.cursor()
        search = cur.execute(f'''
            SELECT *
            FROM "{self.ctx.guild.id}_{projectName}"
            WHERE userId = {user.id};
        ''').fetchall()
        if search:
            embed = discord.Embed(
                title = "✅ 탈퇴 성공",
                description = '탈퇴함..',
                color = discord.Color.green()
            )
            cur.execute(f'''
                DELETE
                FROM "{self.ctx.guild.id}_{projectName}"
                WHERE userId = {user.id}
            ''')
            role = discord.utils.get(self.ctx.guild.roles, name = projectName)
            await user.remove_roles(role)
            self.callback = await interaction.response.send_message(embed = embed)
        else:
            embed = discord.Embed(
                title = "❎ 탈퇴 실패",
                description = '? 등록부터 하셈',
                color = discord.Color.red()
            )
            self.callback = await interaction.response.send_message(embed = embed)
        con.commit()
        con.close()

class DeleteProject(View):
    def __init__(self, ctx, guild, projectName):
        super().__init__()
        self.ctx = ctx
        self.guild = guild
        self.projectName = projectName
        self.disabled = False
    
    @discord.ui.button(label = "확인", style = discord.ButtonStyle.primary, emoji = "✅")
    async def ok(self, interaction, button):
        user = self.ctx.message.author
        if self.disabled or (not interaction.user.id == user.id):
            return
        self.disabled = True
        con = sqlite3.connect(DATABASE_PATH)
        cur = con.cursor()
        search = cur.execute(f'''
            SELECT *
            FROM {PROJECT_MASTER}
            WHERE projectId = "{self.guild.id}_{self.projectName}";
        ''').fetchall()
        if search: 
            role = discord.utils.get(self.guild.roles, name = self.projectName)
            if role is not None: await role.delete()
            cur.execute(f'''DROP TABLE "{self.guild.id}_{self.projectName}"''')
            cur.execute(f'''
                DELETE FROM {PROJECT_MASTER}
                WHERE projectId = "{self.guild.id}_{self.projectName}"
            ''')
            embed = discord.Embed(title = "프로젝트가 제거되었어요..", description = "성공적으로 마무리하셨나요?\n그러셨기를 바랄게요..", color = 0xffbf00)
            embed.set_thumbnail(url = FHBT_IMAGE)
            await interaction.response.send_message(embed = embed)
        else:
            embed = discord.Embed(title = "...??? 그런 프로젝트는 없어요..", description = "철자 다시 확인해보는 게 좋을 것 같아요..", color = discord.Color.red())
            await interaction.response.send_message(embed = embed)
        con.commit()
        con.close()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    if not alertEveryday.is_running():
        alertEveryday.start()
    await bot.change_presence(activity = discord.Game(name = "ㅅ도움"))

@bot.command()
async def 핑(ctx):
    await ctx.send(f'``{bot.latency * 1000}ms``')

@bot.command(name = "도움")
async def 도움(ctx, *arg):
    embed = discord.Embed(title = "도움 <:fhbt:1159345785528385606>", color = 0x18c0e2)
    embed.add_field(name = "가입", value = "가입을 해서 실적을 기록하셈", inline = False)
    embed.add_field(name = "탈퇴", value = "탈퇴해서 실적을 그만 기록하셈", inline = False)
    embed.add_field(name = "프로젝트 생성", value = "프로젝트를 만드셈", inline = False)
    embed.add_field(name = "프로젝트 제거", value = "프로젝트를 끝내셈", inline = False)
    embed.add_field(name = "작성", value = "오늘의 실적을 기록하셈", inline = False)
    embed.add_field(name = "시간 설정", value = "알림시간을 설정합니다", inline = False)
    await ctx.send(embed = embed)

@bot.command(name = "가입")
async def 가입(ctx, *arg):
    if not arg: 
        embed = discord.Embed(title = f"가입 커맨드 사용법", description = "ㅅ가입 <프로젝트 이름>", color = 0xffbf00)
        await ctx.send(embed = embed)
        return
    projectName = ' '.join(arg)
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    search = cur.execute(f'''
        SELECT *
        FROM {PROJECT_MASTER}
        WHERE projectId = "{ctx.guild.id}_{' '.join(arg)}";
    ''').fetchall()
    con.commit()
    con.close()
    if search:
        embed = discord.Embed(title = f"'{projectName}'프로젝트 가입 🔔", description = "가입해서 실적을 기록하세요...", color = 0xffbf00)
        await ctx.send(embed = embed, view = RegisterUser(ctx, arg))
    else:
        embed = discord.Embed(title = f"'{projectName}'프로젝트같은 건 없는 것 같아요..", description = "철자를 다시 확인해보거나 새로 만들어보세요...", color = 0xff0000)
        await ctx.send(embed = embed)

@bot.command(name = "탈퇴")
async def 탈퇴(ctx, *arg):
    if not arg: 
        embed = discord.Embed(title = f"탈퇴 커맨드 사용법", description = "ㅅ탈퇴 <프로젝트 이름>", color = 0xffbf00)
        await ctx.send(embed = embed)
        return
    embed = discord.Embed(title = f"'{' '.join(arg)}' 프로젝트 탈퇴 🔔", description = "탈퇴해서 실적을 그만 기록하셈", color = 0xffbf00)
    await ctx.send(embed = embed, view = DeleteUser(ctx, arg))

@bot.command(name = "팁")
async def 팁(ctx, *arg, nowPage = 1):
    embed = discord.Embed(title = tipList[nowPage - 1]["title"], description = tipList[nowPage - 1]["description"], color = 0xffbf00)
    next = Button(style = ButtonStyle.primary, emoji = "➡️")
    async def next_callback(interaction: Interaction):
        if interaction.user.id != ctx.author.id: return
        nowPage = int(display.label.split('/')[0])
        nowPage += 1
        if nowPage == len(tipList):
            next.style = ButtonStyle.grey
            next.disabled = True
        if nowPage != 1:
            post.disabled = False
            post.style = ButtonStyle.primary
        display.label = f"{nowPage} / {len(tipList)}"
        view = View()
        view.add_item(post)
        view.add_item(display)
        view.add_item(next)
        embed = discord.Embed(title = tipList[nowPage - 1]["title"], description = tipList[nowPage - 1]["description"], color = 0xffbf00)
        await interaction.response.edit_message(embed = embed, view = view)
    display = Button(style = ButtonStyle.grey, label = f"{nowPage} / {len(tipList)}", disabled = True)
    post = Button(style = ButtonStyle.grey, emoji = "⬅️", disabled = True)
    async def post_callback(interaction: Interaction):
        if interaction.user.id != ctx.author.id: return
        nowPage = int(display.label.split('/')[0])
        nowPage -= 1
        if nowPage == 1:
            post.style = ButtonStyle.grey
            post.disabled = True
        if nowPage != len(tipList):
            next.disabled = False
            next.style = ButtonStyle.primary
        display.label = f"{nowPage} / {len(tipList)}"
        view = View()
        view.add_item(post)
        view.add_item(display)
        view.add_item(next)
        embed = discord.Embed(title = tipList[nowPage - 1]["title"], description = tipList[nowPage - 1]["description"], color = 0xffbf00)
        await interaction.response.edit_message(embed = embed, view = view)
    next.callback = next_callback
    post.callback = post_callback
    view = View()
    view.add_item(post)
    view.add_item(display)
    view.add_item(next)
    await ctx.send(embed = embed, view = view)

@bot.command(name = "작성")
async def 작성(ctx, *arg):
    if not arg: 
        embed = discord.Embed(title = f"작성 커맨드 사용법", description = "ㅅ작성 <프로젝트 이름>", color = 0xffbf00)
        await ctx.send(embed = embed)
        return
    projectName = ' '. join(arg)
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    search = cur.execute(f'''
        SELECT *
        FROM {PROJECT_MASTER}
        WHERE projectId = "{ctx.guild.id}_{projectName}";
    ''').fetchall()
    if search:
        search = cur.execute(f'''
            SELECT *
            FROM "{ctx.guild.id}_{projectName}"
            WHERE userId = "{ctx.author.id}";
        ''').fetchall()
        if not search:
            embed = discord.Embed(title = f"? 해당 프로젝트에 가입이 안되어 있는데요?", description = f"``ㅅ가입 {projectName}``으로 프로젝트에 가입하는 게 좋다고 생각해요..", color = discord.Color.red())
            await ctx.send(embed = embed)
            return
        embed = discord.Embed(title = f"'{projectName}'프로젝트에 작성.. 📝", description = "기록을 하신다니 좋은 생각인거 같아요..\n편하게 작성해주세요..\n제한시간이 30초이니 길다면 미리 작성하시고 붙여넣기하시는 걸 권장드려요..", color = 0xffbf00)
        timeOut = discord.Embed(title = "⚠️ 시간 초과", color = discord.Color.red())
        await ctx.send(embed = embed)
        def check(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        try:
            response = await bot.wait_for('message', check = check, timeout = 30.0)
        except:
            await ctx.send(embed = timeOut)
            return
        response = response.content
        today = datetime.date.today().isoformat().replace(*"-_")
        search = cur.execute(f'''
            UPDATE "{ctx.guild.id}_{projectName}"
            SET D{today} = "{response}"
            WHERE userId = "{ctx.author.id}";
        ''').fetchall()
        embed = discord.Embed(title = "저장이 완료되었다..", description = "그렇게 생각하시면 될 것 같아요..", color = discord.Color.green())
        embed.set_thumbnail(url = FHBT_IMAGE)
        await ctx.send(embed = embed)
        con.commit()
        con.close()
    else:
        embed = discord.Embed(title = f"'{projectName}'프로젝트같은 건 없는 것 같아요..", description = "철자를 다시 확인해보거나 새로 만들어보세요...", color = 0xff0000)
        await ctx.send(embed = embed)

@bot.command(name = "조회")
async def 조회(ctx, *arg):
    if not arg: return
    guild = ctx.guild
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    search = cur.execute(f'''
        SELECT *
        FROM {PROJECT_MASTER};
    ''').fetchall()
    con.commit()
    con.close()

@bot.command(name = "프로젝트")
async def 프로젝트(ctx, *arg):
    if not arg: return
    guild = ctx.guild
    if arg[0] == '생성':
        if ctx.author.id in whatAreYouDoing["프로젝트 생성"]:
            embed = discord.Embed(title = "이미 만들고 계시지 않나요?", description = "그것부터 만들어주세요..", color = discord.Color.red())
            embed.set_thumbnail(url = FHBT_IMAGE)
            await ctx.send(embed = embed)
            return
        whatAreYouDoing["프로젝트 생성"].add(ctx.author.id)
        embed = discord.Embed(title = "새로 만들 프로젝트의 이름을 입력해주세요.. 📝", description = "편하게 작성해주세요..", color = 0xffbf00)
        await ctx.send(embed = embed)
        timeOut = discord.Embed(title = "⚠️ 시간 초과", color = discord.Color.red())
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            projectName = await bot.wait_for('message', check = check, timeout = 30.0)
        except:
            await ctx.send(embed = timeOut)
            whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
            return
        if projectName.attachments:
            embed = discord.Embed(title = "⚠️ 그.. 이름에 파일을 넣는 건 좀 아니라고 생각해요..", description = "다시 작성하세요.. 인간..", color = discord.Color.red())
            embed.set_thumbnail(url = FHBT_IMAGE)
            await ctx.send(embed = embed)
            whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
            return
        projectName = projectName.content
        if core.emoji_count(projectName):
            embed = discord.Embed(title = "⚠️ 그.. 이름에 이모지 문자 자체를 넣는 건 좀 아니라고 생각해요..", description = "디스코드 내에서 이모지로 변환되는 문자 (예 : \:cry:)같은 걸로 쓰는 등의 대안이 있어요..\n다시 작성하세요.. 인간..", color = discord.Color.red())
            embed.set_thumbnail(url = FHBT_IMAGE)
            await ctx.send(embed = embed)
            whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
            return
        if '\n' in projectName:
            embed = discord.Embed(title = "⚠️ 그.. 이름에 개행문자를 넣는 건 좀 아니라고 생각해요..", description = "다시 작성하세요.. 인간..", color = discord.Color.red())
            embed.set_thumbnail(url = FHBT_IMAGE)
            await ctx.send(embed = embed)
            whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
            return
        if '@everyone' == projectName:
            embed = discord.Embed(title = "⚠️ 그.. 이름에 에브리원 핑울 넣는 건 좀 아니라고 생각해요..", description = "다시 작성하세요.. 인간..", color = discord.Color.red())
            embed.set_thumbnail(url = FHBT_IMAGE)
            await ctx.send(embed = embed)
            whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
            return
        embed = discord.Embed(title = "프로젝트의 대표색상을 입력해주세요.. 📝", description = "올바른 예) 0xffbf00, 0x00f03b\n올바르지 않은 색상일 경우 무작위로 색상이 지정되어요.. <:fhbt:1159345785528385606>", color = 0xffbf00)
        await ctx.send(embed = embed)
        try:
            color = await bot.wait_for('message', check = check, timeout = 30.0)
        except:
            await ctx.send(embed = timeOut)
            whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
            return
        try:
            color = int(color.content, 16)
            embed = discord.Embed(title = "✨ 예쁜 색깔이네요..", description = "이 글의 색상이 바로 그것이에요..", color = discord.Colour(color))
            await ctx.send(embed = embed)
        except:
            color = randomColor()
            embed = discord.Embed(title = "⚠️ 무작위로 색상이 지정되었어요..", description = "이 경고문의 색상이 바로 그것이에요..", color = discord.Colour(color))
            await ctx.send(embed = embed)
        select = Select(options = [])
        if len(ctx.guild.channels) > 25:
            next = Button(style = ButtonStyle.primary, emoji = "➡️")
            async def next_callback(interaction: Interaction):
                if interaction.user.id != ctx.author.id: return
                nowPage = int(display.label.split('/')[0])
                nowPage += 1
                if nowPage == len(tipList):
                    next.style = ButtonStyle.grey
                    next.disabled = True
                if nowPage != 1:
                    post.disabled = False
                    post.style = ButtonStyle.primary
                display.label = f"{nowPage} / {len(tipList)}"
                select.options.clear()
                for channel in ctx.guild.channels[25 * nowPage : 25 * (nowPage + 1)]:
                    if channel.type in CHANNEL_EMOJI : select.append_option(discord.SelectOption(label = channel.name, value = channel.id, emoji = CHANNEL_EMOJI[channel.type]))
                view = View()
                view.add_item(select)
                view.add_item(post)
                view.add_item(display)
                view.add_item(next)
                await interaction.response.edit_message(embed = embed, view = view)
            display = Button(style = ButtonStyle.grey, label = f"1 / {len(tipList)}", disabled = True)
            post = Button(style = ButtonStyle.grey, emoji = "⬅️", disabled = True)
            async def post_callback(interaction: Interaction):
                if interaction.user.id != ctx.author.id: return
                nowPage = int(display.label.split('/')[0])
                nowPage -= 1
                if nowPage == 1:
                    post.style = ButtonStyle.grey
                    post.disabled = True
                if nowPage != len(tipList):
                    next.disabled = False
                    next.style = ButtonStyle.primary
                display.label = f"{nowPage} / {len(tipList)}"
                select.options.clear()
                for channel in ctx.guild.channels[25 * nowPage : 25 * (nowPage + 1)]:
                    if channel.type in CHANNEL_EMOJI : select.append_option(discord.SelectOption(label = channel.name, value = channel.id, emoji = CHANNEL_EMOJI[channel.type]))
                view = View()
                view.add_item(select)
                view.add_item(post)
                view.add_item(display)
                view.add_item(next)
                await interaction.response.edit_message(embed = embed, view = view)
            next.callback = next_callback
            post.callback = post_callback
        else:
            for channel in ctx.guild.channels:
                if channel.type in CHANNEL_EMOJI : select.append_option(discord.SelectOption(label = channel.name, value = channel.id, emoji = CHANNEL_EMOJI[channel.type]))
        async def selectCallback(interaction: Interaction):
            if interaction.user.id != ctx.author.id: return
            con = sqlite3.connect(DATABASE_PATH)
            cur = con.cursor()
            search = cur.execute(f'''
                SELECT *
                FROM {PROJECT_MASTER}
                WHERE projectId = "{guild.id}_{projectName}";
            ''').fetchall()
            if search:
                embed = discord.Embed(title = "그.. 그 이름을 가진 프로젝트가 이미 있어요..", description = "다른 이름을 사용해주셔야 한다고 생각해요..", color = discord.Color.red())
                embed.set_thumbnail(url = FHBT_IMAGE)
                whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
                return
            try:
                role = await guild.create_role(name = projectName, colour = discord.Colour(color))
                cur.execute(f'''CREATE TABLE "{guild.id}_{projectName}" (userId int, D{datetime.date.today().isoformat().replace(*"-_")} TEXT)''')
                cur.execute(f'''INSERT INTO {PROJECT_MASTER} (projectId, projectColor, notionChannel, roleId) VALUES ("{guild.id}_{projectName}", {color}, "{select.values[0]}", {role.id})''')
                con.commit()
                con.close()
                embed = discord.Embed(title = "야호!", description = "프로젝트가 만들어졌다고 생각해요..", color = discord.Color.green())
                embed.set_thumbnail(url = FHBT_IMAGE)
                whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
                await interaction.response.send_message(embed = embed)
            except PermissionError:
                embed = discord.Embed(title = "그.. 아무래도 역할을 만들 권한이 없는 거 같아요..", description = "그냥 역할은 만들지 말고 프로젝트를 생성할까요?", color = discord.Color.red())
                embed.set_thumbnail(url = FHBT_IMAGE)
                ok = Button(style = ButtonStyle.primary, emoji = "✅")
                async def ok_callback(interaction: Interaction):
                    if interaction.user.id == ctx.author.id:
                        embed = discord.Embed(title = "계속할게요..", description = "사실 그리 막 중요하진 않다고 생각해요..", color = discord.Color.red())     
                        cur.execute(f'''CREATE TABLE "{guild.id}_{projectName}" (userId int, D{datetime.date.today().isoformat().replace(*"-_")} TEXT)''')
                        cur.execute(f'''INSERT INTO {PROJECT_MASTER} (projectId, projectColor, notionChannel, roleId) VALUES ("{guild.id}_{projectName}", {color}, "{select.values[0]}", -1)''')
                        con.commit()
                        con.close()
                        embed = discord.Embed(title = "야호!", description = "프로젝트가 만들어졌다고 생각해요..", color = discord.Color.green())
                        embed.set_thumbnail(url = FHBT_IMAGE)
                        whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
                        await interaction.response.send_message(embed = embed)
                no = Button(style=ButtonStyle.primary, emoji = "✖️")
                async def no_callback(interaction: Interaction):
                    if interaction.user.id == ctx.author.id:
                        embed = discord.Embed(title = "취소했어요..", description = "권한을 주시고 다시 시도하는 걸 추천드려요..", color = discord.Color.red())
                        embed.set_thumbnail(url = FHBT_IMAGE)
                        await interaction.response.send_message(embed = embed)
                        whatAreYouDoing["프로젝트 생성"].remove(ctx.author.id)
                ok.callback = ok_callback
                no.callback = no_callback
                view = View()
                view.add_item(ok)
                view.add_item(no)
                await ctx.send(embed = embed, view = view)
        select.callback = selectCallback
        view = View()
        view.add_item(select)
        if len(ctx.guild.channels) > 25:
            view.add_item(post)
            view.add_item(display)
            view.add_item(next)
        embed = discord.Embed(title = "알림을 보낼 채널을 선택해주세요..", color = 0xffbf00)
        await ctx.send(embed = embed, view = view)
    elif arg[0] == '제거':
        embed = discord.Embed(title = "제거할 프로젝트의 이름을 입력해주세요.. 📝", description = "편하게 작성해주세요..", color = 0xffbf00)
        await ctx.send(embed = embed)
        timeOut = discord.Embed(title = "⚠️ 시간 초과", color = discord.Color.red())
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            projectName = await bot.wait_for('message', check = check, timeout = 30.0)
        except:
            await ctx.send(embed = timeOut)
            return
        projectName = projectName.content
        embed = discord.Embed(title = "⚠️ 진심으로 제거하실건가요..? ⚠️", description = "돌이킬 수 없는 선택이긴 해요..", color = discord.Color.red())
        await ctx.send(embed = embed, view = DeleteProject(ctx, guild, projectName))
        
@tasks.loop(seconds = 1)
async def alertEveryday():
    if datetime.datetime.now().second  == -1:
        if role := discord.utils.get(bot.get_guild(1148512256246693888).roles, name = "프로젝트 참여자"):
            testChannel = bot.get_guild(1148512256246693888).get_channel(1175423530054201364)
            con = sqlite3.connect(DATABASE_PATH)
            cur = con.cursor()
            #search = cur.execute(f'''
            #    SELECT userId
            #    FROM 1148512256246693888_{' '.join(arg)};
            #''').fetchall()
            #ping = '\n'.join(map(lambda x : f'- <@{x[0]}>', search))
            embed = discord.Embed(title = "짤리고 싶지 않으시다면", description = f"실적을 이쯤에서 보고하는 게 좋을 것 같아요...\n{'ping'}")
            embed.set_thumbnail(url = FHBT_IMAGE)
            await testChannel.send(content = f"||{role.mention}||",embed = embed)
            con.commit()
            con.close()
bot.run(token)