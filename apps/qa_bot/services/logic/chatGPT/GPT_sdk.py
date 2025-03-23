# OpenAI Python SDK 공식 문서 참조 (https://github.com/openai/openai-python)
import os
import logging
import openai
from apps.qa_bot import slack_method
from apps.qa_bot import OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
Client = slack_method.Client


class ChatGPT():

    def engine(self, text, channel, gpt_ts):

        openai.api_key = OPENAI_API_KEY
        try:
            engine = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "user", "content": text}],
                max_tokens=2048,
                timeout=30
            )
            logging.info(f'resources consumed : {engine.usage}')
            if int(engine.usage.total_tokens) > 1024:
                logging.warning(f'resources consumed over 1024 : {engine.usage.total_tokens}')
            return engine.choices[0].message.content.strip()

        except ValueError:
            try:
                engine = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=[{"role": "user", "content": text + '를 요약해서 알려줘.'}],
                    max_tokens=4096,
                    timeout=120
                )
                Client.chat_postMessage(
                    channel=channel,
                    text=f'질문+답변이 최대 token을 초과하여 답변이 요약됩니다.',
                    thread_ts=gpt_ts,
                )
                logging.warning(f'max tokens over / chatGPT Response : {engine}, user Question : {text}')
                return engine.choices[0].message.content.strip()
            except Exception:
                import traceback
                error = traceback.format_exc()
                logging.exception(f'ChatGPT API Request Error : {error}')
                return

    def send_answer_channel(self, channel, user, GPT_answer, gpt_ts):
        Client.chat_postMessage(
            channel=channel,
            text=f'<@{user}>님, ' + GPT_answer,
            thread_ts=gpt_ts,
        )