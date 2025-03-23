from app_store_scraper import AppStore, Podcast
from datetime import datetime, timedelta, timezone

import requests
import pytz

KST = timezone(timedelta(hours=9))

def get_review():
    now, yesterday, before_yesterday, three_days_ago, weekday = get_datetime_obj()
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    before_yesterday_str = before_yesterday.strftime('%Y-%m-%d')
    three_days_ago_str = three_days_ago.strftime('%Y-%m-%d')
    review_list = []
    template_str = ":apple: *앱스토어 기준 새로 등록된 리뷰*\n\n"

    result = AppStore(country="kr", app_name="아이들나라".encode('utf-8'), app_id='1521425764') # app_id 1521425764
    # 앱스토어의 경우 최신 순으로 sorting이 되지 않으므로 7일전 리뷰까지만 파싱, after 파라미터가 KST는 지원 안함
    result.review(how_many=10, after=datetime.now() - timedelta(days=30))
    result_list = result.reviews

    for review in result_list[:10]:
        review_date = review.get('date')
        review_date_str = review_date.astimezone(KST).strftime('%Y-%m-%d')

        if weekday == 0:
            # 2초 내 긁어오므로 간소화 없이 그냥 조건문 복붙
            if yesterday_str == review_date_str:
                title = review.get('title')
                review_content = review.get('review')
                rating = review.get('rating')
                review_date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
                review_list.append((title, review_content, rating, review_date))
            if before_yesterday_str == review_date_str:
                title = review.get('title')
                review_content = review.get('review')
                rating = review.get('rating')
                review_date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
                review_list.append((title, review_content, rating, review_date))
            if three_days_ago_str == review_date_str:
                title = review.get('title')
                review_content = review.get('review')
                rating = review.get('rating')
                review_date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
                review_list.append((title, review_content, rating, review_date))
        # 어제 날짜와 일치하는 리뷰가 있는 경우 값 추가
        elif review_date_str == yesterday_str:
            title = review.get('title')
            review_content = review.get('review')
            rating = review.get('rating')
            review_date = review_date.astimezone(KST).strftime('%Y년 %m월 %d일 %A %H:%M')
            review_list.append((title, review_content, rating, review_date))

    if not review_list:
        print('(앱스토어)어제 혹은 주말 리뷰 없음')
        return
    else:
        for item in reversed(review_list):
            title = item[0]
            review_content = item[1]
            rating = item[2]
            date = item[3]

            template_str += f"- 앱 평점 : {rating}\n"
            template_str += f"- 리뷰 제목 : {title}\n"
            template_str += f"- 리뷰 내용 : {review_content}\n"
            template_str += f"- 리뷰 작성 날짜 : {date}\n"
            template_str += "-------------------------------------\n"

    review_count = str(len(review_list))
    slack_webhook_url = 'https://hooks.slack.com/services/웹훅/링크/마스킹'
    # slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

    slack_data = {
        'text': template_str + f'\n*:apple:개수 : {review_count}개*'
    }

    requests.post(slack_webhook_url, json=slack_data)


def get_datetime_obj():
    timezone = pytz.timezone('Asia/Seoul')
    now = datetime.now(timezone)
    yesterday = now - timedelta(days=1)
    before_yesterday = now - timedelta(days=2)
    three_days_ago =  now - timedelta(days=3)
    weekday = now.weekday()
    return now, yesterday, before_yesterday, three_days_ago, weekday


if __name__=="__main__":
    get_review()