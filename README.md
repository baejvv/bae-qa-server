# django-backend
## QA 팀 서버
- 반복되는 업무를 각종 툴의 SDK와 API를 사용하여 간소화 하는것을 목표로 만든 Django 웹서버입니다.
- 파이썬 버전은 3.11 이상을 권장합니다.

## 구현된 기능
* Slack에서 봇이 간단한 이모지 반응으로 Jira 티켓을 등록합니다.
* 티켓의 제목은 이모지가 찍힌 메시지, 내용은 해당 메시지의 링크로 등록됩니다.
* 만약 에픽 등록이 필요하다면, 에픽을 먼저 등록하고 티켓에 지정합니다.
* 앱이 추가된 채널에서 앱을 멘션하고 질문을 작성하면 chatGPT 엔진이 답변을 합니다 (beta)

```
existing_epics = jira.search_issues(f'project = {project} AND "Epic Name" ~ {epic_name}')
            epic_ncf, epic_lcf = jira_view.get_epic_customfield()
```
#### 등록하려는 Epic이 이미 등록된 경우
* 등록된 epic을 등록할 이슈 메서드에 인자로 할당

```
if existing_epics:
                epic = existing_epics[0]
                text = f'`{epic_name}` 에픽이 감지되어 자동 지정되었습니다.'
```
#### 등록하려는 Epic이 보드에 등록되지 않은 경우
* Epic을 먼저 등록하고, 등록할 이슈 메서드에 할당
```
else:
                epic = jira_view.create_epic(project, epic_ncf, epic_name, assginee, reporter)
                text = f'`{epic_name}` 에픽이 자동 생성되었습니다.'
```

## 주요 파일
+ QA_BOT
    + Slack에서 봇을 호출할 때, 그에 따른 각각의 evenet를 처리하도록 각 로직을 분기시켜 놓은 class입니다.

+ slack_custom.views.py, jira_custom.views.py 
    + SlackCustomView, JiraFlow class에서 Slack과 Jira 로직을 구현하여 Slack을 통해 간단한 이모지 반응으로 Jira티켓을 바로 등록할 수 있습니다. 


### slack bot 구현 시 주의사항
* 기본적으로 서버가 Django의 APIView기반 클래스 뷰로 설계되었으므로, 메인 view의 post를 엔드포인트로 라우팅하여 slack과 통신합니다.
* slack이 요청하는 event는 3초 이내에 응답을 해야하기 때문에, 각 로직은 post 하위 메서드로 구현하고, post에서 분기처리 후 Threading 처리하여 개발합니다.
* slack oauth와 관련된 token들은 private하지 못한 저장소에 노출 시 자동 refresh되므로, 환경 변수에 넣어두는것을 권장합니다.
