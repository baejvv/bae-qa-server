from google_play_scraper import reviews, Sort
from datetime import datetime, timedelta, timezone

import requests
import pytz
import ssl
import logging

# SSL 패치
ssl._create_default_https_context = ssl._create_unverified_context

KST = timezone(timedelta(hours=9))

def get_review():
    now, yesterday, before_yesterday, three_days_ago, weekday = get_datetime_obj()
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    before_yesterday_str = before_yesterday.strftime('%Y-%m-%d')
    three_days_ago_str = three_days_ago.strftime('%Y-%m-%d')
    review_list = []
    template_str = ":android: *플레이스토어 기준 새로 등록된 리뷰*\n\n"
    try:
        result = reviews(
            'com.lguplus.mobile.kids',
            lang='ko',
            country='kr',
            sort=Sort.NEWEST,
            count=10 # 최근 리뷰 10개 파싱
        )
    except Exception as e:
        logging.error('플레이스토어 리뷰 파싱 실패: ', e)

    result_list = result[0]
    for review in result_list[:10]:
        review_date = review.get('at')
        review_date_str = review_date.astimezone(KST).strftime('%Y-%m-%d')

        if weekday == 0:
            # 2초 내 긁어오므로 간소화 없이 그냥 조건문 복붙
            if yesterday_str == review_date_str:
                content = review.get('content')
                app_version = review.get('appVersion')
                score = review.get('score')
                date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
                review_list.append((content, app_version, score, date))
            if before_yesterday_str == review_date_str:
                content = review.get('content')
                app_version = review.get('appVersion')
                score = review.get('score')
                date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
                review_list.append((content, app_version, score, date))
            if three_days_ago_str == review_date_str:
                content = review.get('content')
                app_version = review.get('appVersion')
                score = review.get('score')
                date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
                review_list.append((content, app_version, score, date))
    # 어제 날짜와 일치하는 리뷰가 있는 경우 값 추가
        elif review_date_str == yesterday_str:
            content = review.get('content')
            app_version = review.get('appVersion')
            score = review.get('score')
            date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
            review_list.append((content, app_version, score, date))

    #### 테스트용도 (최근 10개 리뷰 끌어오기)
        # elif review:
        #     content = review.get('content')
        #     app_version = review.get('appVersion')
        #     score = review.get('score')
        #     date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
        #     review_list.append((content, app_version, score, date))

    if not review_list:
        print('(플레이스토어)어제 혹은 주말 리뷰 없음')
        return
    else:
        for item in reversed(review_list):
            content = item[0]
            version = item[1]
            score = item[2]
            date = item[3]

            template_str += f"- 앱 평점 : {score}\n"
            template_str += f"- 리뷰 작성 당시 앱 버전 : {version}\n"
            template_str += f"- 리뷰 작성 날짜 : {date}\n"
            template_str += f"- 리뷰 내용 : {content}\n"
            template_str += "-------------------------------------\n"
    review_count = str(len(review_list))
    slack_webhook_url = 'https://hooks.slack.com/services/웹훅/링크/마스킹'
    # slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

    slack_data = {
        'text': template_str + f'\n*:android:개수 : {review_count}개*'
    }

    requests.post(slack_webhook_url, json=slack_data)


def get_datetime_obj():
    timezone = pytz.timezone('Asia/Seoul')
    now = datetime.now(timezone)
    print(now)
    yesterday = now - timedelta(days=1)
    before_yesterday = now - timedelta(days=2)
    three_days_ago =  now - timedelta(days=3)
    weekday = now.weekday()
    return now, yesterday, before_yesterday, three_days_ago, weekday

if __name__=="__main__":
    get_review()