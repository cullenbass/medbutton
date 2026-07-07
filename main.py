# both boto3 and dateutil come preinstalled in lambda runtimes
import boto3
import os
import json
from datetime import datetime
import dateutil.tz

tz = dateutil.tz.gettz('US/Eastern')

# Specify hours in 24-hour format w/ above timezone.
# Crossover is specifying any activity before that hour is morning
# and anything after is evening.
hour_replace = {'morning': 11, 'evening': 21, 'crossover': 13}


def button_handler(event, context):
	l = boto3.client('lambda')
	l.update_function_configuration(
		FunctionName=context.function_name,
		Environment={
			'Variables': {
				'LAST_PUSHED': str(int(datetime.now(tz=tz).timestamp())),
				'SNS_TOPIC': os.environ['SNS_TOPIC']
			}
		}
	)
	print('Button Pushed.')


def cron_handler(event, context):
	if int(os.environ['LAST_PUSHED']) == 0:
		print("Not pushed since update.")
		return
	lp = int(os.environ['LAST_PUSHED'])
	lp = datetime.fromtimestamp(lp, tz=tz)
	now = datetime.now(tz=tz)
	today = datetime.now(tz=tz).replace(hour=0, minute=0, second=0)
	morning = datetime.now(tz=tz).replace(hour=hour_replace['morning'], minute=0, second=0)
	evening = datetime.now(tz=tz).replace(hour=hour_replace['evening'], minute=0, second=0)
	crossover = datetime.now(tz=tz).replace(hour=hour_replace['crossover'], minute=0, second=0)
	print(lp)
	print(now)
	sns = boto3.client("sns")
	# MORNING CHECK
	if now > morning and lp < today:
		print("Morning pills not taken.")
		sns.publish(
			TopicArn=os.environ['SNS_TOPIC'],
			Message='Morning pills not taken.'
		)
	elif lp > today and lp < crossover and now > evening:
		print("Evening pills not taken.")
		sns.publish(
			TopicArn=os.environ['SNS_TOPIC'],
			Message='Evening pills not taken.'
		)
	else:
		print("Meds taken recently.")


def sms_handler(event, context):
	"""Handle incoming SMS messages via SNS. If message is 'PUSH', act like a button press."""
	for record in event.get('Records', []):
		sns_message = record['Sns']['Message']
		# Handle both JSON and plain-text SMS messages
		try:
			body = json.loads(sns_message)
		except (json.JSONDecodeError, TypeError):
			body = {}

		if isinstance(body, dict):
			message = body.get('messageBody', body.get('Body', '')).strip().upper()
			phone_number = body.get('originationNumber', body.get('PhoneNumber', 'unknown'))
		else:
			message = str(body).strip().upper()
			phone_number = 'unknown'

		if message == 'PUSH':
			print(f"SMS PUSH received from {phone_number}")
			button_handler(event, context)
		else:
			print(f"Ignoring SMS from {phone_number}: '{message}'")


def handler(event, context):
	if 'Records' in event:
		# SNS event (incoming SMS)
		return sms_handler(event, context)
	elif 'headers' in event:
		# IoT button / HTTP request
		return button_handler(event, context)
	else:
		# CloudWatch cron
		return cron_handler(event, context)