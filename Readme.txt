Telegram bot for kadastr.
Realised feature for taking info about cadastral objects (ZU, OKS)
using rosreestr API by cadastral number.
Bot using getUpdate (not Weebhook) for this moment.
If you don't using proxy then take look at begining of test_bot.py and 
comment rows for proxy users.
Right now bot can be used without django or another web-framework, 
so you can safely remove django from prerequsites.

Working example of bot u can see in telegram @kad61assist_bot
