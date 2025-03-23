import re
import traceback
import openai
from apps.general_log_setup import *
from apps.qa_bot import ChatGPT
from apps.qa_bot import slack_method
from slack_sdk.errors import SlackApiError


def chat_gpt(event_message):
    Slack = slack_method.Client
    channel = event_message.get('channel')
    message = event_message.get('text')
    message = re.sub(r'<.*?>\s*', '', message)
    user = event_message.get('user')
    logging.info(f'{user}/유저 입력 msg : {message}')
    gpt_ts = event_message.get('ts')
    GPT = ChatGPT()

    try:
        GPT_answer = GPT.engine(message, channel, gpt_ts)
        logging.info(f'{user}/chatGPT 답변 : {GPT_answer}')
        GPT.send_answer_channel(channel, user, GPT_answer, gpt_ts)
    except SlackApiError as e:
        full_stack_error_msg = traceback.format_exc()
        Slack.send_fail_message(channel, user, gpt_ts, e)
        logging.exception(full_stack_error_msg)
    except openai.error.Timeout as e: # 30s Timeout
        e = str(e) + '\nRequest Timeout. 요청을 다시 전송합니다. (최대 3번)'
        logging.warning(e)
        Slack.send_fail_message(channel, user, gpt_ts, e)
        for i in range(3):
            GPT_answer = GPT.engine(message, channel, gpt_ts)
            logging.warning(f'{message}질문에 대한 Timeout 발생')
            GPT.send_answer_channel(channel, user, GPT_answer, gpt_ts)