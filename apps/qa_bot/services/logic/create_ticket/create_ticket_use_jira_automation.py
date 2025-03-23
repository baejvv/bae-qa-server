import json
import logging
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


def create_ticket(payload):

    logging.info('payload: ', payload)
    date: str = datetime.now(timezone('Asia/seoul')).strftime('%Y%m%d')
    parent_summary: str = date + '-VOC' # 상위 항목 명

    slack_view = SlackCustomView(channel, project) # Generate slack view instance

    item: dict = payload.get('item')
    ts: str = item.get('ts') # 만약 이모지가 스레드 내부 댓글에 찍혔다면 이 변수는 메인 스레드 ts가 아님, 댓글 스레드 ts로 변환됨
    slack_reporter: str = payload.get('item_user') # 리액션이 추가된 스레드의 작성자 -> 티켓 보고자로 활용
    slack_assignee: str = payload.get('user') # 리액션을 추가한 사람 -> 티켓 담당자로 활용

    try:
        reporter_name: str; assignee_name: str
        reporter_name, assignee_name = slack_view.get_real_username(slack_reporter, slack_assignee) # reaction 추가 시, 추가한 사용자와 추가 대상 메시지의 사용자 정보 get
        loading_ts: str = slack_view.send_loading_message(assignee_name, ts) # 로딩 메시지 post
        link: str = slack_view.get_thread_link(ts) # 리액션이 달린 스레드 링크 get
        description: str = slack_view.thr_get_message(ts) # 메시지 원본 get, image 파일이 있다면 같이 가져온다.
    except SlackApiError as e:
        slack_view.send_fail_message(ts)
        slack_view.delete_loading_message(loading_ts)
        logging.error('Slack에러', e)

    # 티켓 제목(summary) 처리 로직, 설명은 스레드의 모든 내용이 들어감
    if '<' and '>' in description: # 이슈 제목에 멘션이 포함될 경우, userid 제거
        description: str = re.sub(r'<.*?>\s*', '', description)
    summary: str
    if '\n' in description:  # 개행문자가 포함될 경우 첫번째 줄만 이슈 제목으로 slicing
        summary = f'({date} 생성티켓) ' + description.split('\n')[0]
    else:
        summary = f'({date} 생성티켓) ' + description

    jira = JiraFlow()
    try:
        reporter: str = jira.get_jira_user_id(reporter_name)['users']['users'][0]['accountId'] # 보고자 정보 get
        assignee: str = jira.get_jira_user_id(assignee_name)['users']['users'][0]['accountId'] # 담당자 정보 get
    except JIRAError as e:
        slack_view.send_fail_message(ts)
        slack_view.delete_loading_message(loading_ts)
        logging.error('Jira 유저이름 가져오는 중 에러발생', e)

    data = {
        "summary": summary,
        "description": description,
        "reporter": reporter,
        "assignee": assignee,
        "slack_assignee_id": slack_assignee,
        "parent": parent_summary,
        "slack_ts": ts,
        "slack_loading_ts": loading_ts
    }

    try:
        requests.post(os.environ['CREATE_TICKET_RULES_URL'], data=json.dumps(data))
        logging.info(f'{summary} 티켓 등록 완료')
    except JIRAError or SlackApiError as e:
        logging.error('이슈 등록 실패', e)


def make_slack_message(data):

    slack_view = SlackCustomView(channel, project)
    jira_view = JiraFlow()

    issue_key: str = data.get('issueKey')
    ts: str = data.get('slackTs')
    loading_ts: str = data.get('slackLoadingTs')
    slack_assignee_id: str = data.get('slackAssigneeId')
    epic_message: str = data.get('epicMessage')
    # 컴포넌트 리스트 바인딩
    try:
        components: list = jira_view.get_components(project)
        if components:
            comps_options: list
            comps_options = [{"text": {"type": "plain_text", "text":  comp.name}, "value": comp.id} for comp in components]
        else:
            comps_options = [{"text": {"type": "plain_text", "text": "프로젝트 내 컴포넌트가 없습니다."}, "value": str(issue_key)}]
            logging.warning('컴포넌트 탐지 실패')
    except JIRAError as e:
        logging.error('컴포넌트 목록 가져오는중 에러', e)
        slack_view.send_fail_message(ts)
    # 스프린트 리스트 바인딩
    # try:
    #     sprints = jira_view.get_sprint(project)
    #     sprint_options = [{"text": {"type": "plain_text", "text": sprint.name}, "value": str(sprint.id)} for sprint in sprints]
    # except JIRAError:
    #     sprint_options = [{"text": {"type": "plain_text", "text": "프로젝트 내 스프린트가 없습니다."}, "value": "no_sprint"}]
    #     logging.warning('스프린트 탐지 실패, sprint: ', sprint_options)
    #     pass
    # 최종 메시지 전달
    try:
        slack_view.send_jira_issue_link(slack_assignee_id, epic_message, ts, issue_key, comps_options)
    except SlackApiError as e:
        logging.error('슬랙 완료 메시지 전송 중 에러', e)
        slack_view.send_fail_message(ts)
    finally:
        slack_view.delete_loading_message(loading_ts)