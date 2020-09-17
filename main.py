import boto3 
import os
from datetime import datetime
import dateutil.tz

tz = dateutil.tz.gettz('US/Eastern')

# Specify hours in 24-hour format w/ above timezone.
# Crossover is specifying any activity before that hour is morning
# and anything after is evening.
hour_replace = {'morning' : 10, 'evening': 22, 'crossover': 13}

def buttonHandler(event, context):
	# if event['clickType'] == 'SINGLE':
	l = boto3.client('lambda')
	l.update_function_configuration(FunctionName = context.function_name, Environment={
		'Variables':{
			'LAST_PUSHED' : str(int(datetime.now(tz=tz).timestamp())),
			'SNS_TOPIC' : os.environ['SNS_TOPIC']
		}
	})
	# if event['clickType'] == 'DOUBLE':
	# 	l.update_function_configuration(FunctionName = context.function_name, Environment={
	# 		'Variables':{
	# 			'LAST_PUSHED' : '0',
	# 			'SNS_TOPIC' : os.environ['SNS_TOPIC']
	# 		}
	# 	})

def cronHandler(event, context): 
	if int(os.environ['LAST_PUSHED']) == 0:
		print("Not pushed since update.")
		return
	lp = int(os.environ['LAST_PUSHED'])
	lp = datetime.fromtimestamp(lp, tz=tz)
	now = datetime.now(tz=tz)
	today = datetime.now(tz=tz).replace(hour = 0, minute = 0, second = 0)
	morning = datetime.now(tz=tz).replace(hour = hour_replace['morning'], minute = 0, second = 0)
	evening = datetime.now(tz=tz).replace(hour = hour_replace['evening'], minute = 0, second = 0)
	crossover = datetime.now(tz=tz).replace(hour = hour_replace['crossover'], minute = 0, second = 0)
	print(lp)
	print(now)
	sns = boto3.client("sns")
	# MORNING CHECK
	if now > morning and lp < today:
		print("Morning pills not taken.")
		sns.publish(TopicArn = os.environ['SNS_TOPIC'],
			Message='Morning pills not taken.')
	elif lp > today and lp < crossover and now > evening:
		print("Evening pills not taken.")
		sns.publish(TopicArn = os.environ['SNS_TOPIC'],
			Message='Evening pills not taken.')
	else:
		print("Meds taken recently.")


def handler(event, context):
	if 'clickType' in event:
		return buttonHandler(event, context)
	else:
		return cronHandler(event, context)

