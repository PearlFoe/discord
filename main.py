from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from loguru import logger

from requests.exceptions import SSLError

import threading
import random
import time
import json
import sys
import os

logger.remove()
logger.add(sys.stderr, format="<green>{time.hour}:{time.minute}:{time.second}:{time.microsecond}, {time.year}-{time.month}-{time.day}</green> - <lvl>{level}</lvl> - <c>{thread.name}</c> - <lvl>{message}</lvl>", level="INFO")
logger.add('main_log_file.log', format="<green>{time.hour}:{time.minute}:{time.second}:{time.microsecond}, {time.year}-{time.month}-{time.day}</green> - <lvl>{level}</lvl> - <c>{thread.name}</c> - <lvl>{message}</lvl>", level="DEBUG")

def get_blacklist(file_name):
	data = None
	with open(file_name, encoding='utf-8') as f:
		data = f.read()

	try:
		return data.split('\n')
	except Exception:
		return []

def dump_blacklist(file_name, data):
	with open(file_name, 'w') as f:
		f.write(data)

def get_config(file_name):
	data = None
	with open(file_name) as f:
		data = json.loads(f.read())

	return data

def get_proxy(file_name):
	data = None
	with open(file_name) as f:
		data = f.read()

	for proxy in data.split('\n'):
		yield proxy

def get_proxy_count(file_name):
	data = None
	with open(file_name) as f:
		data = f.read()

	return len(data.split('\n'))

def get_accounts(file_name):
	data = None
	with open(file_name) as f:
		data = f.read()

	accounts = []
	for i in data.split('\n'):
		account = i.split(':')
		accounts.append({
			'email':account[0],
			'password':account[1],
			'token':account[2]
		})

	for account in accounts:
		yield account

def get_users_to_mail(file_name):
	data = None
	with open(file_name) as f:
		data = f.read()

	for user in data.split('\n'):
		yield user

def locate_url(part_url, driver):
	start_time = time.time()
	while True:
		if part_url in driver.current_url:
			return True
		else:
			if time.time() - start_time > 15:
				return False

def get_message_text(file_name):
	data = None
	with open(file_name, encoding='utf-8') as f:
		data = f.read()

	return data

def send_message(driver, user):
	actions = ActionChains(driver)

	message = get_message_text('message.txt')
	if not message:
		logger.info('Empty message.')
		return False

	try:
		user_chat = driver.find_element_by_xpath(f'//a[@aria-label="{user} (личное сообщение)"]')
	except Exception:
		logger.info(f'Chat with user {user} was not found.')
	else:
		actions.click(user_chat).perform()
		del actions

	input_field = None
	try:
		_ = WebDriverWait(driver, 15).until(EC.presence_of_element_located(
												(By.XPATH, f'//div[@aria-label="Написать @{user}"]')))
		input_field = driver.find_element_by_xpath(f'//div[@aria-label="Написать @{user}"]')
	except Exception:
		pass

	for _ in range(3):
		try:
			actions = ActionChains(driver)
			actions.click(input_field)
			actions.pause(0.25)
			actions.perform()

			input_field.send_keys(message)
			input_field.send_keys(Keys.ENTER)
		except Exception:
			pass
		else:
			logger.debug(f'Message was sent successfully to user {user}.')
			return True

	logger.info('Message was not sent.')
	return False

def make_request(proxies, account, users_to_mail, invite):
	tread_name = threading.current_thread().name
	
	options = Options()
	options.add_experimental_option('excludeSwitches', ['enable-logging']) #disables webdriver loggs

	proxy = next(proxies)
	seleniumwire_options = {
		'proxy': {
			'http': f'http://{proxy}', 
			'https': f'https://{proxy}',
		}
	}

	if config['HEADLESS_MODE']:
		options.add_argument("--headless")

	#driver initialisation
	driver = None
	try:
		#driver = webdriver.Chrome(seleniumwire_options=seleniumwire_options, options=options)
		driver = webdriver.Chrome(options=options) #without proxy
	except SSLError:
		logger.error('An error occured during driver creation.')
		return
	else:
		logger.debug('Web driver was created successfully.')
		#driver.set_page_load_timeout(15)

	try:
		driver.get('https://discord.com/login')
	except Exception:
		logger.error('An error occured during page loading.')
		return
	else:
		logger.debug('Page loaded successfully.')
		time.sleep(2)

	#log in by token
	try:
		token = account['token']

		#js script to log in by token
		script = f'''function login(token) {{
						setInterval(() => {{
							document.body.appendChild(document.createElement `iframe`).contentWindow.localStorage.token = `"${{token}}"`
						}}, 50);
						setTimeout(() => {{
							location.reload();
						}}, 2500);
					}}
						login('{token}');
				'''
		driver.execute_script(script)
		
		#waiting pop up message that indicates successful log in
		_ = WebDriverWait(driver, 15).until(EC.presence_of_element_located(
													(By.XPATH, '//div[@id="popout_3"]')))
	except Exception:
		logger.error('An error occured trying to log in.')
		return
	else:
		email = account['email']
		logger.info(f'Successfully logged in account {email}.')

	try:
		driver.get(invite)
		_ = WebDriverWait(driver, 15).until(EC.presence_of_element_located(
													(By.XPATH, '//button[@type="button"]')))
		actions = ActionChains(driver)
		button = driver.find_element_by_xpath('//button[@type="button"]')
		actions.click(button).perform()
		del actions
	except Exception:
		logger.error('An error occured trying to use invite.')
		return

	try:
		_ = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
											(By.XPATH, '//div[contains(text(), "Continue to Discord")] \
												| //div[contains(text(), "Accept Invite")]')))
	except Exception:
		driver.get('https://discord.com/channels/@me')
	else:
		logger.info('Invalid invite or account is in ban.')
		return

	while True:
		blacklist = get_blacklist('blacklist.txt')
		user_name = None
		try:
			user_name = next(users_to_mail)
			while True:
				if user_name in blacklist:
					user_name = next(users_to_mail)
				else:
					break
		except StopIteration:
			logger.error('Got the end of "user_to_mail.txt" file.')
			return

		if send_message(driver, user_name):
			blacklist.append(user_name)
			dump_blacklist('blacklist.txt', blacklist)

	_ = input('--------------')
	driver.quit()

@logger.catch
def main():
	global config
	config = get_config('config.json')
	proxies = get_proxy('proxy.txt')
	proxy_count = get_proxy_count('proxy.txt')
	accounts = get_accounts('accounts.txt')
	users_to_mail = None

	invite = input('Enter invite url: ') #https://discord.gg/PT5kfeQ6
	#next(accounts)
	make_request(proxies, next(accounts), users_to_mail, invite)
	'''
	max_workers = None
	if proxy_count < config['THREADS_QUANTITY']:
		max_workers = proxy_count
	else:
		max_workers = config['THREADS_QUANTITY']

	with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='Tread') as executor:
		for account in accounts:
			executor.submit(make_request, proxies, account, users_to_mail, invite)
	'''
	

if __name__ == '__main__':
	main()