import discord, os, re
from discord.ext import tasks
from datetime import datetime

DEBUG = True
def log(s):
    if DEBUG:
        print(s)

token = os.getenv("DISCORD_BOT_TOKEN")

class TimeoutTim(discord.Client):
    TOchannel_name = "verification-room"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timedout = dict()
        self.member_roles = dict()

    def sec2str(self, time):
        h = int(time/3600)
        m = int((time - 3600*h) / 60)
        s = time - 3600*h - 60*m

        time_str = "{} second(s)".format(s)
        if m:
            time_str = "{} minute(s) and {}".format(m, time_str)
        if h:
            time_str = "{} hour(s), {}".format(h, time_str)

        return time_str

    def time_left(self, member):
        log("Time_Left")
        time = self.timedout[member.id][1] - (datetime.now() - self.timedout[member.id][0]).seconds
        return self.sec2str(time)
        
    def check_timeout(self, member):
        return (self.timedout[member.id][1] - (datetime.now() - self.timedout[member.id][0]).seconds) < 0

    async def timeout(self, member, minutes, channel):
        TOchannel = discord.utils.get(member.guild.channels, name=self.TOchannel_name)
        if member.id in self.timedout:
            await channel.send("{} is already in timeout with {} remaining.".format(member.name, self.time_left(member)))
            return
        else:
            if member.roles:
                self.member_roles[member.id] = []
                for role in member.roles:
                    if role.name != "@everyone":
                        self.member_roles[member.id].append(role)
                await member.remove_roles(*self.member_roles[member.id], reason="{} has been bad and was put in timeout as punishment".format(member.name))
            await member.add_roles(discord.utils.get(member.guild.roles, name="Timeout"), reason="{} has been bad and was put in timeout as punishment".format(member.name))
            
            self.timedout[member.id] = [datetime.now(), minutes*60, member]
            await channel.send("{} has been sent to the shadow realm for {}.".format(member.name, self.sec2str(minutes*60)))
            await TOchannel.send("Hello, {}.\n\nYou have been sent here for {} minutes because you have been naughty. I hope you use this time as a chance to reflect on your actions and come up with a formal apology for what you have done.\n\nFeel free to use `~timeleft` to see how much longer you have in timeout.".format(member.mention, minutes))
            

    async def remove_timeout(self, member):
        if member.id in self.timedout:
            await member.remove_roles(discord.utils.get(member.guild.roles, name="Timeout"), reason="{} is done with timeout".format(member.name))
            if self.member_roles[member.id]:
                await member.add_roles(*self.member_roles[member.id], reason="{} is done with timeout".format(member.name))

            self.timedout.pop(member.id)
            self.member_roles.pop(member.id)
            TOchannel = discord.utils.get(member.guild.channels, name=self.TOchannel_name)
            await TOchannel.send("{}'s timeout is over.".format(message.mentions[0].name))
        else:
            return

    def add_time(self, member, minutes):
        self.timedout[member.id][1] = self.timedout[member.id][1] + 60*minutes

        

    async def on_ready(self):
        print(f'{client.user} has connected to Discord!')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="your behavior"))

    async def on_message(self, message):
        content = message.content
        user = message.author
        channel = message.channel
        guild = message.guild
        TOchannel = discord.utils.get(message.guild.channels, name=self.TOchannel_name)

        if user == self.user:
            return

        if message.content.startswith("~help"):
            e = discord.Embed(
                    title = "TimeoutTim Commands",
                    description = "Need to punish the naughty kids out there? He does it!",
                    color = 0x7dcac0
                )
            e.set_thumbnail(url="https://i.imgur.com/vazfrxN.png")
            e.add_field(name="~timeout @user [minutes in timeout]", value="Places @user in timeout for given amount of time.", inline=False)
            e.add_field(name="~free @user", value="Frees @user from timeout.", inline=False)
            e.add_field(name="~add @user [minutes to add to timeout]", value="Adds given amount of time to @user's timeout.", inline=False)
            e.add_field(name="~timeleft", value="Gives time left in your timeout.", inline=False)
            e.add_field(name="~timeleft @user", value="Gives time left in @user's timeout.", inline=False)
            e.add_field(name="~help", value="What do you think this does?", inline=False)

            
            await channel.send(embed=e)
        elif message.content.startswith("~timeout "):
            if user.roles[-1].position < guild.get_member(self.user.id).roles[-1].position and not user.guild_permissions.administrator:
                return
            
            words = [x.strip() for x in message.content.split(' ')]
            if (len(words) == 2) and (len(message.mentions) == 1):
                minutes = 10

                if message.mentions[0].roles[-1].position > guild.get_member(self.user.id).roles[-1].position:
                    return
                
                await self.timeout(message.mentions[0], minutes, channel)
            elif (len(words) == 3) and (len(message.mentions) == 1) and (re.match('^[0-9]*$', words[2])):
                if message.mentions[0].roles[-1].position > guild.get_member(self.user.id).roles[-1].position:
                    return
                
                minutes = int(words[2])
                await self.timeout(message.mentions[0], minutes, channel)
            else:
                await channel.send("Invalid command. Please use `~timeout @user [minutes in timeout]`")
                return

        elif message.content.startswith("~free "):
            if user.roles[-1].position < guild.get_member(self.user.id).roles[-1].position and not user.guild_permissions.administrator:
                return
            
            words = [x.strip() for x in message.content.split(' ')]
            if (len(words) != 2) or (len(message.mentions) != 1):
                await channel.send("Invalid command. Please use `~free @user`")
                return
            if message.mentions[0].id in self.timedout:
                await self.remove_timeout(message.mentions[0])
                await channel.send("{} has been set free.".format(message.mentions[0].name))
            else:
                await channel.send("{} is not currently on timeout.".format(message.mentions[0].name))
            
        elif message.content.startswith("~timeleft"):
            if channel.name != "timeout":
                return
            
            words = [x.strip() for x in message.content.split(' ')]
            if len(words) == 1:
                if message.author.id in self.timedout:
                    await channel.send("You have {} remaining in timeout.".format(self.time_left(message.author)))
                    return
                else:
                    await channel.send("You are not currently on timeout.")
                    return
            elif len(words) == 2 and (len(message.mentions) == 1):
                if message.mentions[0].id in self.timedout:
                    await channel.send("{} has {} remaining in timeout.".format(message.mentions[0].name, self.time_left(message.mentions[0])))
                    return
                else:
                    await channel.send("{} is not currently on timeout.".format(message.mentions[0].name))
                    return
            else:
                await channel.send("Invalid command. Please use `~timeleft @user`")
                return

        elif message.content.startswith("~add "):
            if user.roles[-1].position < guild.get_member(self.user.id).roles[-1].position and not user.guild_permissions.administrator:
                return
            
            words = [x.strip() for x in message.content.split(' ')]
            if (len(words) == 3) and (len(message.mentions) == 1) and (re.match('^[0-9]*$', words[2])):
                if message.mentions[0].id in self.timedout:
                    minutes = int(words[2])
                    self.add_time(message.mentions[0], minutes)
                    await channel.send("Added {} minutes to {}'s timeout.".format(minutes, message.mentions[0]))
                else:
                    await channel.send("{} is not currently on timeout.".format(message.mentions[0].name))
            else:
                await channel.send("Invalid command. Please use `~add @user [minutes to add to timeout]`")
                return
        elif message.content.startswith("-SR"):
            await channel.send("https://splatoon2.ink/")

        

    @tasks.loop(seconds = 1)
    async def track_loop(self):
        await self.wait_until_ready()

        for m in self.timedout:
            member = self.timedout[m][2]
            
            if self.check_timeout(member):
                await self.remove_timeout(member)
                return
            

    

if __name__ == "__main__":
    client = TimeoutTim()
    client.track_loop.start()
    client.run(token)
