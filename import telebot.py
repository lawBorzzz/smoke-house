import telebot

bot = telebot.TeleBot("7692845826:AAEWYoo1bFU22LNa79-APy_iZyio2dwc9zA")

bot.remove_webhook()
bot.set_webhook("https://d5djr0snme46r5bb2lag.apigw.yandexcloud.net")