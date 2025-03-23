/**
 * selenium 프레임워크를 사용한 화상클래스 dev 수업방 진입 스크립트
 * IDE 또는 cli에서 실행 시 인풋값을 받아 탭을 열고 fake 학생을 입장시킨다.
 * 기본적으로 chrome에서 제공하는 webRTC 가상 장치(웹캠, 마이크) 를 사용하며, 기본 아웃풋을 사용.
 * 윈도우에서 배치파일로 실행시키기 위해 readline을 통한 인풋을 받아 유동적으로 탭을 열고 테스트 종료시 배치 내에서 프로그램을 종료하도록 설계.
 * 학생 url은 cid=multitestroom으로 두고 a{name}(별명) 과 a{uid}를 동일한 난수로 할당하도록 설계.
 * 선생님 수업방은 아래 url 참고.
 * https://learning.dev.i-nara.co.kr/video-class/teacher/room?name=test-nick+%EC%84%A0%EC%83%9D%EB%8B%98&cid=multitestroom&uid=teacher-uid&video=0&mute_video=false&audio=0&mute_audio=false&audio_output=0&course_id=171&all_mic=on
 */


const { Build, Key, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const readline = require('readline');
const { read } = require("selenium-webdriver/io");
// 학생 수업방 url.
const url = "https://url/마스킹/비공개/room?name=a{}&age=5&uid=a{}&cid=multitestroom&video=0&audio=0&mute_audio=true&audio_output=0&course_id="

// readline 인터페이스 생성
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

// url 내 uid와 name 할당 시 각기 다른 ec2 인스턴스에서 값이 중복되지 않도록 4자리의 랜덤한 난수를 만드는 함수
function generateRandomInt() {
    const randomInt = Math.floor(1000 + Math.random() * 9000);
    return randomInt;
}

// 브라우저 인스턴스 생성
// chrome 내장 webRTC 웹캠, 마이크 기본으로 사용
async function browser() {
    const service = new chrome.ServiceBuilder(require('chromedriver').path).build();
    let options = new chrome.Options();
    options.addArguments('--use-fake-device-for-media-stream');
    options.addArguments('--use-fake-ui-for-media-stream');
    // 크롬드라이버는 상수로 지정하면 세션이 각 브라우저별로 관리되고, 불변성이 필요없다면 세션 하나로 관리 가능.
    const driver = chrome.Driver.createSession(options, service);
    return driver;
}

// 메인 함수
async function testWebRTC() {


    rl.question("fake 유저의 개수를 입력 후 엔터를 눌러주세요. (최소 3, 최대 16) :", async (input) => {
        const tabs = parseInt(input);

        if (isNaN(tabs) || tabs < 3 || tabs > 16) {
            console.log("3에서 16사이의 숫자를 입력하세요.");
            rl.close();
            return;
        }

        // 브라우저 3개를 먼저 연다.
        const numBrowsers = 3; // 3개 고정
        const browsers = [];
        const tabsPerBrowser = Math.ceil(tabs / numBrowsers); // 각 브라우저에 열릴 탭의 수. 브라우저에 탭을 분산하기 위함

        for (let i = 0; i < numBrowsers; i++) {
            browsers.push(await browser()); // numBrowsers값에 맞게 브라우저 인스턴스 생성 함수 반복 호출
        }

        try {
            // 각 브라우저에 탭 오픈 (fake유저 수업방 진입)
            for (let i = 0; i < numBrowsers; i++) {
                const browser = browsers[i];
                const tabsToOpen = Math.min(tabsPerBrowser, tabs - i * tabsPerBrowser); // 입력받은 개수 기반 탭 오픈

                for (let tab = 0; tab < tabsToOpen; tab++) {
                    const fakeUserIndex = generateRandomInt(); // name, uid에 들어갈 난수 생성 함수 호출
                    const roomUrl = url.replace(/{}/g, fakeUserIndex); // url에 난수 추가
                    await browser.executeScript(`window.open('${roomUrl}', '_blank');`); // url 변수에 name(유저 별명), uid 인덱스 추가
                    console.log(`${i + 1}번째 브라우저에 열렸습니다 => ${roomUrl}`);
                    await new Promise(resolve => setTimeout(resolve, 3000)); // 브라우저 1개당 1개탭 열릴 시 3초 대기

                }
            }
            console.log("모든 fake 학생이 진입하였습니다.");
        } finally {
            // 엔터를 누르면 크롬드라이버 세션 종료
            rl.question("브라우저를 종료하시려면 엔터를 눌러주세요.", async () => {
                for (let browser of browsers) {
                    await browser.quit();
                } // TODO. quit()이 한번만 호출되도록 바꿀 수 있을듯 함(개별 드라이버 세션을 쓰므로)
                process.exit(0);
                rl.close();
            });
        }
    });
}
testWebRTC();
