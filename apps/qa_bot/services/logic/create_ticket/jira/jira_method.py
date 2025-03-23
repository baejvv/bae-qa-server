import json
import os
import requests
from jira import JIRA, JIRAError
from apps.qa_bot import description_img, JIRA_ID, JIRA_URL, JIRA_TOKEN

# 지라 프로젝트명을 담을 배열
project_name_list = []
# 지라 프로젝트 키를 담을 배열
project_key_list = []

auth_JIRA = (JIRA_ID, JIRA_TOKEN)
jira = JIRA(JIRA_URL, basic_auth=auth_JIRA)


class JiraFlow():

    '''
    이곳에서 Jira-Python SDK 사용하여 파싱
    '''

    # 전체 프로젝트를 탐색하고 name과 key list를 반환하는 함수
    def get_jira_project(self) -> str:
        pjs = jira.projects()
        for i in pjs:
            project_name_list.append(i.name)
            project_key_list.append(i.key)
        return project_name_list, project_key_list

    # 유저가 선택한 프로젝트 name으로 key를 반환하는 함수
    def post_jira_project(self, user_select_project) -> str:
        key_index = project_name_list.index(user_select_project)
        project_key = project_key_list[key_index]
        return project_key


    def create_epic(self, pj, field, epic, assgn, repo) -> dict:
        ticket_dict = {
            'project': {'key': pj},
            'summary': epic,
            field: epic,
            'issuetype': {'name': '에픽'},
            'assignee': {'id': assgn},
            'reporter': {'id': repo}
        }
        res = jira.create_issue(fields=ticket_dict)
        return res

    # view에서 넘겨받은 정보를 토대로 jira 이슈 생성
    def create_jira_issue(self, pj, sum, desc, ts, assgn, repo, field, epic) -> dict:
        issue_dict = {
            'project': {'key': pj}, # jira project key
            'summary': sum, # str
            'description': f'관련 Slack 스레드 : {ts}\n\n{desc}', # str
            'issuetype': {'name': 'Bug'},  # str
            'assignee': {'id': assgn}, # jira user accountId
            'reporter': {'id': repo},
            field: epic.key
        }
        res = jira.create_issue(fields=issue_dict)
        return res

    # 이미지 추가
    def attach_jira_img(self, ticket, filename):
        try:
            file_obj = open(filename, 'rb')
            jira.add_attachment(issue=ticket, attachment=file_obj)
            file_obj.close()
        except JIRAError as e:
            print(f'Error attaching image to Jira ticket : {e}')


    def attach_img_to_description(self, ticket):

        headers = {
            "Accept": "application/json"
        }
        response = requests.request(
            "GET",
            os.environ['JIRA_URL'] + f'rest/api/3/issue/{ticket}',
            headers=headers,
            auth=auth_JIRA
        )
        issue = json.loads(response.text)
        issue_desc = issue['fields']['description']['content']
        issue_attach_url = issue['fields']['attachment'][0]['content']

        issue_desc.append(description_img(issue_attach_url))

        new_fields = json.dumps(issue_desc, sort_keys=True, indent=4, separators=(",", ": "))

        jira.issue(ticket).update(fields={'description': new_fields})

    # 실제 이름으로 Jira userId를 가져옴
    def get_jira_user_id(self, username) -> str:
        headers = {
            "Accept": "application/json"
        }
        response = requests.request(
            "GET",
            os.environ['JIRA_URL'] + 'rest/api/3/groupuserpicker',
            headers=headers,
            auth=auth_JIRA,
            params={
                "query": f"{username}"
            }
        )
        json_response = json.loads(response.text)
        return json_response

    # Epic Name이 할당된 customfield를 가져옴
    def get_epic_customfield(self) -> str:
        fields = jira.fields()
        for field in fields:
            if field['name'] == 'Epic Name':
                epic_name_field =  (field['id'])
        for field in fields:
            if field['name'] == 'Epic Link':
                epic_link_field =  (field['id'])
        return epic_name_field, epic_link_field

    # 특정 티켓의 제목과 내용을 가져온다.
    def get_issue_info(self, ticket_number):
        issue = jira.issue(ticket_number)
        summary = issue.fields.summary
        description = issue.fields.description
        return summary, description

    # 이슈를 닫는다.
    def close_issue(self, ticket_number):
        issue = jira.issue(ticket_number)
        transitions = jira.transitions(issue)
        close_transition_id = None
        for t in transitions:
            if '완료' in t['name'].lower():
                close_transition_id = t['id']
                break
        if close_transition_id:
            jira.transition_issue(issue, close_transition_id)
        else:
            raise Exception('완료 워크플로를 찾을 수 없음')

    # 티켓에 코멘트 추가
    def add_comment(self, ticket, msg):
        jira.add_comment(ticket, msg)

    # 티켓에 label 삽입
    # 레이블에는 공백을 추가할 수 없음, 파라미터로 받는 label의 str을 공백 없이 받아야 함.
    def add_label(self, ticket_number, label):
        issue = jira.issue(ticket_number)
        issue.update(
            fields={"labels": issue.fields.labels + [label]}
        )
        updated_issue = jira.issue(ticket_number)
        print("Updated Labels:", updated_issue.fields.labels)

    # 프로젝트의 components list get
    def get_components(self, project):
        components = jira.project_components(project)
        return components

    # 프로젝트의 sprint list get
    def get_sprint(self, project):
        boards = jira.boards(projectKeyOrID=project)
        sprints = []
        if boards:
            board_id = boards[0].id  # 첫 번째 보드 선택
            sprints = jira.sprints(board_id)
        return sprints
