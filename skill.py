from telegram.ext import Updater
import logging
import os
import boto3


users = [] # Pass telegram ids to which you would like to send messages from voice assistant 
bucket_name = 'bucket_name' # Change for your bucket name

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

session = boto3.session.Session(
    aws_access_key_id=os.environ['AWS_SERVER_PUBLIC_KEY'],
    aws_secret_access_key=os.environ['AWS_SERVER_SECRET_KEY']
)
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)

def handler(event, context):
    """
    Entry-point for Serverless Function.
    :param event: request payload.
    :param context: information about current execution context.
    :return: response to be serialized as JSON.
    """
    resp = 'Я передам Лене все, что вы скажете' # It says "I'll send %USERNAME% everything you say"

    updater = Updater(token=os.environ['TELEGRAM_TOKEN'], use_context=True)
    dispatcher = updater.dispatcher

    old_message_id = None
    try:
        obj = s3.get_object(Bucket=bucket_name, Key='last_message')
        old_message_id = int(obj['Body'].read().decode('utf-8'))
    except: # I'm sorry for this exception handling, but I don't have time to make it more right.
        pass
    
    last_message_id = None
    last_message_text = None
    try:
        update = dispatcher.bot.get_updates(offset=-1)
        last_message_id = update[-1].message.message_id
        last_message_text = update[-1].message.text

        s3.put_object(
            Bucket=bucket_name, 
            Key='last_message', 
            Body=str(last_message_id))
    except: # I'm sorry for this exception handling, but I don't have time to make it more right.
        pass

    last_message_response = ''
    if (old_message_id is not None) \
        and (last_message_id is not None)\
        and (old_message_id != last_message_id):
        last_message_response = 'Последнее сообщение от Лены: ' +  last_message_text +'. ' # It says "Last message from %USERNAME%:"

    
    if 'request' in event and \
            'original_utterance' in event['request'] \
            and len(event['request']['original_utterance']) > 0:
        text = event['request']['original_utterance']
        resp = ''
        for user in users:
            try:
                dispatcher.bot.send_message(chat_id=user, text=text)
            except: # I'm sorry for this exception handling, but I don't have time to make it more right.
                pass
        resp += 'Я передала: ' + text
    return {
        'version': event['version'],
        'session': event['session'],
        'response': {
            # Respond with the original request or welcome the user if this is the beginning of the dialog and the request has not yet been made.
            'text': last_message_response + resp,
            # Don't finish the session after this response.
            'end_session': 'false'
        },
    }