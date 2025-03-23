import traceback
import os
import re
from datetime import datetime
from pytz import timezone
from json import JSONDecodeError
from slack_sdk.errors import SlackApiError
from apps.exception_handler import ThreadExecutionError
from apps.general_log_setup import *
from apps.qa_bot import channel, project, delete_file
from apps.qa_bot.services.logic.create_ticket.slack.slack_method import *
from apps.qa_bot.services.logic.create_ticket.jira.jira_method import *


'''
슬랙-지라 자동 티켓 등록 로직
로직 내 exception은 ThreadExecutionError로 반환
'''
def i_jira_automation_create(reaction_payload):

    delete_file()
    logging.info(reaction_payload)

    slack_view = SlackCustomView(channel, project) # Generate slack view instance
    jira_view = JiraFlow() # Generate jira view instance

    date = datetime.now(timezone('Asia/Seoul')).strftime('%Y%m%d')
    item = reaction_payload.get('item')
    ts = item.get('ts') # 만약 이모지가 스레드에 찍혔다면 이 변수는 메인 ts가 아님, 스레드 ts로 변환됨.
    item_user = reaction_payload.get('item_user') # 리액션이 추가된 스레드의 작성자
    user = reaction_payload.get('user') # 리액션을 추가한 사람

    try:
        username, item_username = slack_view.get_real_username(item_user, user) # reaction 추가 시, 추가한 사용자와 추가 대상 메시지의 사용자 정보 get
        loading_ts = slack_view.send_loading_message(username, ts) # 로딩 메시지 post
        link = slack_view.get_thread_link(ts) # 리액션이 달린 스레드 링크 get
        assginee = jira_view.get_jira_user_id(username)['users']['users'][0]['accountId'] # 담당자 정보 get
        reporter = jira_view.get_jira_user_id(item_username)['users']['users'][0]['accountId'] # 보고자 정보 get
        epic_name = date + '-VOC'
        msg_text, filename = slack_view.thr_get_message(ts) # 메시지 원본 get, image 파일이 있다면 같이 가져온다.
        logging.info(f'Slack info : {username, item_username, loading_ts, link, assginee, reporter, msg_text}')

    except (SlackApiError, JIRAError, JSONDecodeError, Exception) as e:
        full_stack_error_msg = traceback.format_exc()
        slack_view.send_fail_message(user, ts, e)
        slack_view.delete_loading_message(loading_ts)
        logging.exception(f'{username}/슬랙 정보 가져오는 중 Error : {full_stack_error_msg}')

    # 티켓 제목(summary) 처리 로직
    if filename is None:
        if '<' and '>' in msg_text: # 이슈 제목에 멘션이 포함될 경우, userid 제거
            msg_text = re.sub(r'<.*?>\s*', '', msg_text)
        if '\n' in msg_text: # 개행문자가 포함될 경우 첫번째 줄만 이슈 제목으로 slicing
            summary = f'({date} 생성티켓)' + msg_text.split('\n')[0]
        else:
            summary = msg_text

    elif filename is not None:
        if msg_text == '': # 이미지만 있는 스레드에 이모지가 찍힌 경우
            summary = f'({date} 생성티켓) 첨부 이미지 확인'

        elif msg_text != '': # 이미지와 텍스트가 공존하는 경우
            if '<' and '>' in msg_text:
                msg_text = re.sub(r'<.*?>\s*', '', msg_text)
            if '\n' in msg_text:
                summary = f'({date} 생성티켓)' + msg_text.split('\n')[0]
            else:
                summary = f'({date} 생성티켓) {msg_text}, 첨부 이미지 확인'

    # Epic 생성
    try:
        existing_epics = jira.search_issues(f'project = {project} AND "Epic Name" ~ {epic_name}')
        epic_ncf, epic_lcf = jira_view.get_epic_customfield()
        if existing_epics:
            epic = existing_epics[0]
            logging.info(f'{username}/에픽 자동 적용. 정보 : {existing_epics}')
            text = f'`{epic_name}` 에픽이 감지되어 자동 지정되었습니다.'
        else:
            epic = jira_view.create_epic(project, epic_ncf, epic_name, assginee, reporter)
            text = f'`{epic_name}` 에픽이 자동 생성되었습니다.'
            logging.info(f'{username}/에픽 생성. 정보 : {epic}')

    except Exception as e:
        full_stack_error_msg = traceback.format_exc()
        slack_view.send_fail_message(user, ts, e)
        slack_view.delete_loading_message(loading_ts)
        logging.exception(f'`{username}`/에픽 등록 적용 중 Error : {full_stack_error_msg}')

    # 티켓 생성
    try:
        ticket = jira_view.create_jira_issue(project, summary, msg_text, link, assginee, reporter, epic_lcf, epic)
        ticket_id = str(ticket)
        if filename is not None: # 이미지가 있다면 첨부파일로 등록
            jira_view.attach_jira_img(ticket_id, filename)
        slack_view.send_jira_issue_link(user, text, ts, project, ticket_id)
        slack_view.delete_loading_message(loading_ts) # 로딩 메시지 제거
        # slack_view.add_loading_reaction(ts, 'loading') # 로딩 리액션 추가

        logging.info(f'{username}/티켓 등록 완료: {ticket}')

    except SlackApiError as e:
        error = e.response['error']
        if error == 'already_reacted':
            logging.info('이미 로딩 이모지 추가되어있음')
            pass
        else:
            full_stack_error_msg = traceback.format_exc()
            slack_view.send_fail_message(user, ts, e)
            slack_view.delete_loading_message(loading_ts)
            logging.exception(f'{username}/슬랙 Error : {full_stack_error_msg}')

    except Exception as e:
        full_stack_error_msg = traceback.format_exc()
        slack_view.send_fail_message(user, ts, e)
        slack_view.delete_loading_message(loading_ts)
        logging.exception(f'{username}/티켓 등록 중 Error : {full_stack_error_msg}')

    delete_file()
