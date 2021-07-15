from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from loguru import logger

from requests.exceptions import SSLError

import threading
import datetime
import zipfile
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
	try:
		with open(file_name, encoding='utf-8') as f:
			data = f.read()
	except Exception:
		return []
	else:
		logger.debug('Got profiles from blacklist.')
		return [i for i in data.split('\n') if i]

def dump_blacklist(file_name, data):
	try:
		with open(file_name, 'w') as f:
			f.write('\n'.join(data))
	except Exception:
		logger.warning('Failed to dump profiles to blacklist.')
	else:
		logger.debug('Dumped profiles to blacklist.')

def get_config(file_name):
	data = None
	try:
		with open(file_name) as f:
			data = json.loads(f.read())
	except FileNotFoundError:
		logger.error('Failed to open config file.')
		exit()
	else:
		logger.debug('Got settings from config file.')

	return data

def get_proxy(file_name):
	data = None
	try:
		with open(file_name) as f:
			data = f.read()
	except FileNotFoundError:
		logger.error(f'Failed to open file with proxies {file_name}.')
	else:
		logger.debug('Got proxies from file.')
		for proxy in data.split('\n'):
			yield proxy

def get_proxy_count(file_name):
	data = None
	try:
		with open(file_name) as f:
			data = f.read()
	except FileNotFoundError:
		logger.error(f'Failed to open file with proxies {file_name}.')
	else:
		logger.debug('Got proxies quantity.')
		return len(data.split('\n'))

def get_accounts(file_name):
	data = None
	try:
		with open(file_name) as f:
			data = f.read()
	except FileNotFoundError:
		logger.error(f'Failed to get accounts from file {file_name}.')
	else:
		logger.debug('Got accounts from file.')
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
	try:
		with open(file_name, encoding="utf-8") as f:
			data = f.read()
	except FileNotFoundError:
		logger.error(f'Failed to get users to mail from file {file_name}.')
	else:
		logger.debug('Got users to mail from file.')
		for user in data.split('\n'):
			yield {
					'name': user.split('#')[0],
					'id': user.split('#')[1]
			}

def get_message_text(file_name):
	data = None
	try:
		with open(file_name, encoding='Windows-1251') as f:
			data = f.read()
	except FileNotFoundError:
		logger.error(f'Failed to get message text from file {file_name}.')
	else:
		logger.debug('Got message text from file.')
		assert data
		return data

def send_message(driver, user):
	user = user['name']
	message = get_message_text('message.txt')
	if not message:
		logger.info('Empty message.')
		return False
	
	user_button = None
	nav_bar = None
	try:
		url = driver.current_url
		chanel_id = int(url.split('/')[-1])
		nav_bar = driver.find_element_by_xpath(f'//div[@id="members-{chanel_id}"]')
		nav_bar_data = nav_bar.find_elements_by_xpath('./div/div')

		for i in nav_bar_data:
			try:
				#_ = i.find_element_by_xpath(f'.//*[starts-with(@aria-label, "{user}") or text()="{user}" or contains(@aria-label, "{user}")]')
				#el = i.find_element_by_xpath('./div/div/div').get_attribute('innerHTML')
				el = i.find_element_by_xpath('./div/div/div').get_attribute('aria-label')
			except Exception:
				pass
			else:
				if user in el:
					user_button = i
					break
				pass
	except Exception:
		logger.info('Unnable to get users from navigation bar.')

	#clicking user button
	try:
		actions = ActionChains(driver)

		actions.move_to_element_with_offset(nav_bar, 20, 0)
		actions.perform()

		while not user_button.location_once_scrolled_into_view:
			driver.execute_script('window.scrollTo(0, Y)')

		actions.reset_actions()
		actions.click(user_button)
		actions.perform()
	except Exception:
		logger.info('Exception occured trying to locate and click user button.')
	'''
	try:
		#clicking personal photo to get to profile
		photo_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
													(By.XPATH, f'//div[@aria-label="{user}"]/div[@role="button"]')))

		actions = ActionChains(driver)
		actions.click(photo_btn)
		actions.perform()
		del actions

		#from profile opening chat
		user_chat = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
													(By.XPATH, '//div[@aria-label="Интерфейс профиля пользователя" \
																or @aria-label="User Profile Modal"]//button[@type="button"]')))
		actions = ActionChains(driver)
		actions.move_to_element(user_chat)
		actions.pause(0.2)
		actions.click(user_chat)
		actions.perform()
	except Exception:
		logger.info('Exception occured trying to open chat with user.')
	'''
	try:
		'''
		input_field = WebDriverWait(driver, 15).until(EC.presence_of_element_located(
												(By.XPATH, f'//div[@aria-label="Написать @{user}"] | //div[@aria-label="Message @{user}"]')))
		'''
		input_field = WebDriverWait(driver, 15).until(EC.presence_of_element_located(
												(By.XPATH, f'//input[@placeholder="Сообщение для @{user}"] | //input[@placeholder="Message @{user}"]')))
	except Exception:
		logger.info('Input field was not found.')
	else:
		for _ in range(3):
			#checking flood alert
			try:
				flood_warning = driver.find_element_by_xpath('//*[contains(text(), "You are sending")]')
			except Exception:
				pass
			else:
				time_to_sleep = config['TIME_OUT']
				logger.info(f'Got flood alert. Waiting {time_to_sleep} seconds.')
				time.sleep(time_to_sleep)

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
				logger.info(f'Message was sent successfully to user {user}.')

				global messages_sent
				messages_sent += 1

				return True

	logger.info('Message was not sent.')
	return False
	
def login(driver, account):
	try:
		driver.get('https://discord.com/login')
	except Exception:
		logger.error('An error occured during login page loading.')
		return False
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
		_ = WebDriverWait(driver, 45).until(EC.presence_of_element_located(
													(By.XPATH, '//div[@id="popout_3"]')))
	except Exception:
		logger.error('An error occured trying to log in.')
		return False
	else:
		email = account['email']
		logger.info(f'Successfully logged in account {email}.')
		return True

def enter_chanel_by_invite(driver, invite):
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
		driver.quit()
		return False

	try:
		_ = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
											(By.XPATH, '//div[contains(text(), "Continue to Discord")] \
												| //div[contains(text(), "Accept Invite")]')))
	except Exception:
		#driver.get('https://discord.com/channels/@me')
		pass
	else:
		logger.info('Invalid invite or account is in ban.')
		driver.quit()
		return False

	return True

def make_request(proxies, account, users_to_mail, invite):
	global accounts_used
	accounts_used += 1

	tread_name = threading.current_thread().name
	
	options = Options()
	options.add_experimental_option('excludeSwitches', ['enable-logging']) #disables webdriver loggs

	proxy = next(proxies)

	if config['HEADLESS_MODE']:
		logger.debug('Driver starts in headless mode.')
		options.add_argument("--headless")

	#driver initialisation
	driver = None
	try:
		driver = get_driver(options, proxy)
	except SSLError:
		logger.error('An error occured during driver creation.')
		try:
			driver.quit()
		except Exception:
			pass
		return False
	else:
		logger.debug('Web driver was created successfully.')
		#driver.set_page_load_timeout(15)
	
	#loging into account
	attempts = 2
	email = account['email']
	for i in range(1, attempts+1):
		if not login(driver, account):
			if i < attempts:
				logger.info(f'Retrying to log into account {email}.')
			else:
				logger.info(f'Failed to log into account {email} in {attempts} attempts.')
				driver.quit()
				return False
		else:
			break
	
	#trying to use invite
	if not enter_chanel_by_invite(driver, invite):
		return False
	
	#choosing user to send message
	while True:
		blacklist = get_blacklist('blacklist.txt')
		user_name = 'PearlFoe'
		
		try:
			user_name = next(users_to_mail)
			while True:
				if user_name in blacklist:
					user_name = next(users_to_mail)
				else:
					break
		except StopIteration:
			logger.warning('Got the end of users to mail list.')
			driver.quit()
			return False
		
		if send_message(driver, user_name):
			blacklist.append(user_name)
			dump_blacklist('blacklist.txt', blacklist)
			break

		time_out_between_messages = config['TIME_OUT_BETWEEN_MESSAGES']
		time.sleep(time_out_between_messages)

	time_out = config['TIME_OUT']
	time.sleep(time_out)

	_ = input('--------------')
	driver.quit()

def get_statistics(file_name):
	data = None
	try:
		with open(file_name) as f:
			data = json.loads(f.read())
	except Exception:
		return []
	else:
		logger.debug('Statistics loaded from file successfully.')
		return data

def dump_statistics(file_name, data):
	stats = get_statistics(file_name)
	try:
		stats.append(data)
		with open(file_name, 'w') as f:
			json.dump(stats, f)
	except Exception:
		logger.warning(f'Failed to dump statistics to file {file_name}.')
	else:
		logger.debug('Statistics umped to file successfully.')

def get_driver(options, proxy):
	PROXY_HOST = proxy.split('@')[1].split(':')[0]
	PROXY_PORT = proxy.split('@')[1].split(':')[1]
	PROXY_USER = proxy.split('@')[0].split(':')[0]
	PROXY_PASS = proxy.split('@')[0].split(':')[1]

	manifest_json = """
	{
	    "version": "1.0.0",
	    "manifest_version": 2,
	    "name": "Chrome Proxy",
	    "permissions": [
	        "proxy",
	        "tabs",
	        "unlimitedStorage",
	        "storage",
	        "<all_urls>",
	        "webRequest",
	        "webRequestBlocking"
	    ],
	    "background": {
	        "scripts": ["background.js"]
	    },
	    "minimum_chrome_version":"22.0.0"
	}
	"""

	background_js = """
	var config = {
	        mode: "fixed_servers",
	        rules: {
	        singleProxy: {
	            scheme: "http",
	            host: "%s",
	            port: parseInt(%s)
	        },
	        bypassList: ["localhost"]
	        }
	    };

	chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

	function callbackFn(details) {
	    return {
	        authCredentials: {
	            username: "%s",
	            password: "%s"
	        }
	    };
	}

	chrome.webRequest.onAuthRequired.addListener(
	            callbackFn,
	            {urls: ["<all_urls>"]},
	            ['blocking']
	);
	""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)


	pluginfile = 'proxy_auth_plugin.zip'

	with zipfile.ZipFile(pluginfile, 'w') as zp:
		zp.writestr("manifest.json", manifest_json)
		zp.writestr("background.js", background_js)
	options.add_extension(pluginfile)

	driver = webdriver.Chrome(options=options)
	return driver

@logger.catch
def main():
	global config
	global messages_sent
	global accounts_banned
	global accounts_used

	messages_sent = accounts_banned = accounts_used = 0

	config = get_config('config.json')
	proxies = get_proxy('proxy.txt')
	proxy_count = get_proxy_count('proxy.txt')
	accounts = get_accounts('accounts.txt')
	users_to_mail = get_users_to_mail('users_to_mail.txt')

	#getting invite url from user
	invite = input('Enter invite url: ')
	
	max_workers = None
	if proxy_count < config['THREADS_QUANTITY']:
		max_workers = proxy_count
	else:
		max_workers = config['THREADS_QUANTITY']

	account = next(accounts)
	make_request(proxies, account, users_to_mail, invite)

	'''
	with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='Tread') as executor:
		for account in accounts:
			e = executor.submit(make_request, proxies, account, users_to_mail, invite)
	'''	

	#saving statistics
	dt = datetime.datetime.now()
	stats = {
		'time': str(dt.time()),
		'date': str(dt.date()),
		'threads': max_workers,
		'messages_successfilly_sent':messages_sent,
		'accounts_banned': accounts_banned,
		'accounts_used': accounts_used,
		'avarage_messages_sent': int(messages_sent/accounts_used)
	}

	dump_statistics('statistics.json', stats)

if __name__ == '__main__':
	main()