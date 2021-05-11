# vaccine-tracker-bot
Telegram bot to notify users for available vaccine slots for selected pincode


To use this code, 
- create a bot on telegram's botFather
- use the token received from the above step in your .env file
- send a message to the bot in the following format: /pincode <your_pincode_for_tracking>. e.g: /pincode 110030
- next schedule the script in a cron, or once using python script.py. It will send a notification to all the users of the bot with valid pincodes every time the script runs.