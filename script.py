import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

VACCINE_TRACKER_BASE_URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin"
TELEGRAM_BOT_BASE_URL = "https://api.telegram.org/bot"

USER_DATA_FILENAME = "./user_data.json"

def save_user_data(user_id_pincode_dict):
	with open(USER_DATA_FILENAME, 'w') as outfile:
		json.dump(user_id_pincode_dict, outfile, indent=2)

def read_user_data():
	user_id_pincode_dict = {}
	if os.path.exists(USER_DATA_FILENAME):
		with open(USER_DATA_FILENAME, 'r') as infile:  
			user_id_pincode_dict = json.load(infile)
	return user_id_pincode_dict

def get_new_user_data():
	user_id_pincode_dict = {}
	bot_update_url = "https://api.telegram.org/bot{}/getUpdates".format(API_TOKEN)

	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
	}
	response = requests.get(bot_update_url, headers=headers)

	json_data = response.json()

	if len(json_data['result']) == 0:
		print("NO USERS UNTIL NOW.")
		return False

	result_list = json_data['result']

	for data in result_list:
		if 'message' in data and 'text' in data['message'] and 'pincode' in data['message']['text']:
			chat_id = data['message']['chat']['id']
			pincode = data['message']['text'].split(" ").pop()
			if pincode in user_id_pincode_dict:
				user_id_pincode_dict[pincode].append(chat_id)
			else:
				user_id_pincode_dict[pincode] = [chat_id]

	save_user_data(user_id_pincode_dict)
	
	return 

def fetch_data(pincode):
	try:
		headers = {
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
		}

		API_URL = VACCINE_TRACKER_BASE_URL + '?pincode={}&date=11-05-2021'.format(pincode)
		response = requests.get(API_URL, headers=headers)

		if response.status_code != 200:
			return False

		json_data = response.json()
		centre_list = []

		if 'centers' in json_data:
			centre_list = json_data['centers']
		
		return centre_list

	except Exception as e:
		print("ERROR:{}".format(e))


def identify_available_slots(centre_list):
	free_slots = []

	data_by_group = [
		{
			"group": 18,
			"data_count": 0,
			"has_data": False,
			"msg": "Age group: 18-44, available at \n",
		},
		{
			"group": 45,
			"data_count": 0,
			"has_data": False,
			"msg": "Age group: 45+, available at \n"
		}
	]

	for centre in centre_list:
		free_centre = {}
		if len(centre['sessions']) == 0:
			continue

		for session in centre['sessions']:

			if session['available_capacity'] > 0:
				free_centre = {
					"name": centre['name'],
					"address": centre['address'], 
					"district": centre['district_name'], 
					"block": centre['block_name'],
					"pincode": centre['pincode'],
					"vaccine": session['vaccine'],
					"type": centre['fee_type'],
					"group": session['min_age_limit'],
					"quantity": session['available_capacity']
				}
				
				group_idx = 0

				if session['min_age_limit'] == 45:
					group_idx = 1
				
				data_by_group[group_idx]['data_count'] += 1
				data_by_group[group_idx]['has_data'] = True
				data_by_group[group_idx]['msg'] +="\n\n {}. {}".format(data_by_group[group_idx]['data_count'],prepare_msg(free_centre))
				
				free_slots.append(free_centre)

	return data_by_group

def prepare_msg(data_dict):
	msg = "{}, \nAddress: {}, {}, Pincode: {}, \nVaccine Name: {}, \nType: {} \nAvailable Quantity: {}".format(
		data_dict['name'], 
		data_dict['address'], 
		data_dict['district'], 
		str(data_dict['pincode']), 
		data_dict['vaccine'], 
		data_dict['type'], 
		str(data_dict['quantity'])
	)
	return msg

def send_notification(msg_dict, recipient_ids):

	for msg_group in msg_dict:
		if msg_group['has_data']:
			print(msg_group)
			for recipient_id in recipient_ids:

				time.sleep(1)

				try:
					print(recipient_id)
					headers = {
						'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
					}

					response = requests.get("https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(API_TOKEN, recipient_id, msg_group['msg']), headers=headers)

					print(response.status_code)
					print("success")
				except Exception as e:
					print("CANNOT SEND MSG:{}".format(e))

def main():
	get_new_user_data()

	user_data = read_user_data()

	for pincode in user_data:	
		response_data = fetch_data(pincode)
		msg_dict = identify_available_slots(response_data)

		print(msg_dict)
		send_notification(msg_dict, user_data[pincode])



if __name__ == "__main__":
	main()