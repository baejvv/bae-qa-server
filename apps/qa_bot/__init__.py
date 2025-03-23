import os

'''패키지 변수'''
# 티켓봇
channel = os.environ['CHANNEL']
project = os.environ['JIRA_PROJECT_KEY']
SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
SLACK_USER_TOKEN = os.environ['SLACK_USER_TOKEN']
SLACK_APP_TOKEN = os.environ['SLACK_APP_TOKEN']
SLACK_VERIFICATION_TOKEN = os.environ['SLACK_VERIFICATION_TOKEN']
SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']
JIRA_ID = os.environ['JIRA_ID']
JIRA_TOKEN = os.environ['JIRA_TOKEN']
JIRA_URL = os.environ['JIRA_URL']
# GPT
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# Package PATH
from apps.qa_bot.services.template import description_img
from apps.qa_bot.services.logic.create_ticket.parser import delete_file
from apps.qa_bot.services.logic.create_ticket.create_ticket_logic import i_jira_automation_create
from apps.qa_bot.services.logic.create_ticket.create_ticket_use_jira_automation import create_ticket, make_slack_message
from apps.qa_bot.services.logic.slack_interactivity.slack_interactivity_logic import complete_in_jira, complete_in_slack, modal_process, add_component
from apps.qa_bot.services.logic.create_ticket.slack import slack_method

from apps.qa_bot.services.logic.chatGPT.GPT_sdk import ChatGPT
from apps.qa_bot.services.logic.chatGPT.bot_in_gpt_logic import chat_gpt

# from apps.qa_bot.services.logic.statistics_slack_emoji.logic import slack_statistics


