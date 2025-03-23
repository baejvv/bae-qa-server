import traceback
import os
import re
import logging
from time import sleep
from slack_sdk.errors import SlackApiError
from apps.exception_handler import ThreadExecutionError
from apps.general_log_setup import *
from apps.qa_bot import channel, project
from apps.qa_bot.services.logic.create_ticket.slack.slack_method import *
from apps.qa_bot.services.logic.create_ticket.jira.jira_method import *

'''
이슈 완료 처리 로직
https://url 마스킹/bot/interactivity/
https://url 마스킹/bot/interactivity/
'''
# 지라에서 완료처리된 경우
def complete_in_jira(ticket_number):

    slack_view = SlackCustomView(channel, project) # Generate slack view instance

    # 이슈가 달린 ts 찾기
    try:
        search_result = slack_view.search_already_ticket_thread(ticket_number)
        print(search_result)
        reply_ts = search_result['messages']['matches'][0]['ts']
        thread_ts = slack_view.get_ts_with_thread_ts(reply_ts)
        ts = thread_ts['messages'][0]['thread_ts']

    except Exception:
        full_stack_error_msg = traceback.format_exc()
        logging.error(f"ts 서칭 중 에러 발생 : {full_stack_error_msg}")

    # # 이모지 처리
    # try:
    #     slack_view.delete_loading_reaction(ts) # 로딩 이모지 제거
    #     slack_view.add_done_reaction(ts) # 완료 이모지 추가
    # except Exception as e:
    #     full_stack_error_msg = traceback.format_exc()
    #     logging.error(f"이모지 처리 중 에러 발생 : {full_stack_error_msg}")

    # 메시지 처리
    try:
        # 이미 슬랙에서 완료처리된 이슈인 경우는 메시지 배달 X
        msg = ticket_number + "티켓을 완료처리"
        res = slack_view.search_already_thread(msg)
        matches = res['messages']['matches']
        if not matches:
            slack_view.send_jira_complete_message(ts, ticket_number)

            issue_link = os.environ['JIRA_URL'] + f'browse/{ticket_number}'
            slack_view.update_message(reply_ts, issue_link, 'Jira Automation')
        else:
            logging.info('이미 완료된 이슈')
            return
    except Exception:
        full_stack_error_msg = traceback.format_exc()
        logging.error(f"메시징 처리 중 에러 발생 : {full_stack_error_msg}")

# 스레드 내 완료버튼 이벤트 수신 시 모달 오픈 로직
def complete_in_slack(payload):

    slack_view = SlackCustomView(channel, project) # Generate slack view instance
    jira_view = JiraFlow() # Generate jira view instance

    ticket_number = payload['actions'][0]['value']
    trigger_id = payload['trigger_id']
    ts = payload['container']['thread_ts']

    issue = ticket_number # 호출 함수로부터 ticket_number를 넘겨 받음

    try:
        summary, description = jira_view.get_issue_info(issue) # 티켓의 제목과 내용을 가져온다.
        slack_view.open_complete_modal(trigger_id, summary, description, issue, ts) # 모달 오픈
    except JIRAError or SlackApiError:
        full_stack_error_msg = traceback.format_exc()
        logging.error(f"티켓 완료처리를 위한 정보 가져오는중 에러 발생 : {full_stack_error_msg}")

# 모달 뷰
def modal_process(payload):
    slack_view = SlackCustomView(channel, project)

    slack_user_id = payload['user']['id']
    metadata = json.loads(payload['view']['private_metadata'])

    ts = metadata['thread_ts']
    ticket_number = metadata['issue']
    input_message = payload['view']['state']['values']['inputBlock']['userInputText']['value']
    data = {
        "issues": [
            ticket_number
        ],
        "data": {
            "comment": input_message
        }
    }
    try:
        requests.post(url=os.environ['COMMENT_URL'], data=json.dumps(data))
        # jira_view.close_issue(ticket_number)
        # jira.add_comment(ticket_number, input_message)
    except JIRAError as e:
        full_stack_error_msg = traceback.format_exc()
        slack_view.send_fail_message(ts)
        logging.exception(f'완료처리를 위한 모달 오픈 중 에러 : {full_stack_error_msg}')


    slack_view.send_complete_message(ts, slack_user_id, ticket_number)
    logging.info('티켓 완료처리 성공')

    try:
        issue_link = os.environ['JIRA_URL'] + f'browse/{ticket_number}'
        origin_message = slack_view.search_already_thread(issue_link)
        origin_message_ts = origin_message['messages']['matches'][0]['ts']
        slack_view.update_message(origin_message_ts, issue_link, slack_user_id)

    except SlackApiError as e:
        full_stack_error_msg = traceback.format_exc()
        slack_view.send_fail_message(ts)
        logging.exception(f'이슈 등록 메시지 완료처리 메시지로 변환 실패 : {full_stack_error_msg}')

def add_component(payload):
    ticket_number: str = payload['actions'][0]['block_id']
    component_name = payload['actions'][0]['selected_option']['text']['text']
    data = {
        "issues": [
            ticket_number
        ],
        "data": {
            "component": component_name
        }
    }
    try:
        requests.post(url=os.environ['CHANGE_COMPONENT_RULES_URL'], data=json.dumps(data))
        logging.info('컴포넌트 추가 성공')
    except JIRAError as e:
        logging.error('컴포넌트 추가 웹훅 요청 실패: ', e)
    slack_view = SlackCustomView(channel, project)
    try:
        ts = payload['container']['thread_ts']
        slack_view.send_component_add_complete_message(ts, component_name, ticket_number)
    except SlackApiError as e:
        logging.warning('컴포넌트 추가 메시지 전송 실패', e)
        slack_view.send_fail_message(ts)

