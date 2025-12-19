import requests
import json
import os
import time
import random
from pypushdeer import PushDeer

# --------------------------------------------
# 获取环境变量
# --------------------------------------------
sckey = os.environ.get("SENDKEY", "")
cookies_env = os.environ.get("COOKIES", "")
cookies = [c.strip() for c in cookies_env.split("&") if c.strip()]

# 推送内容初始化
title = ""
success, fail, repeats = 0, 0, 0
context = ""

# 签到地址和状态查询
check_in_url = "https://glados.space/api/user/checkin"
status_url = "https://glados.space/api/user/status"

referer = 'https://glados.space/console/checkin'
origin = "https://glados.space"
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"

payload = {'token': 'glados.one'}

if not cookies:
    print("未找到 COOKIES！请检查 Secrets 设置")
    title = "# 未找到 cookies!"
else:
    for idx, cookie in enumerate(cookies, 1):
        # 随机延迟，防风控
        time.sleep(random.uniform(1,3))

        try:
            # 签到请求
            checkin = requests.post(
                check_in_url,
                headers={
                    'cookie': cookie,
                    'referer': referer,
                    'origin': origin,
                    'user-agent': useragent,
                    'content-type': 'application/json;charset=UTF-8'
                },
                data=json.dumps(payload),
                timeout=10
            )

            # 查询账号状态
            state = requests.get(
                status_url,
                headers={
                    'cookie': cookie,
                    'referer': referer,
                    'origin': origin,
                    'user-agent': useragent
                },
                timeout=10
            )

            points = 0
            message_status = ""
            message_days = ""
            email = ""

            if checkin.status_code == 200 and state.status_code == 200:
                result = checkin.json()
                check_result = result.get('message', '')
                points = result.get('points', 0)

                state_result = state.json()
                leftdays = int(float(state_result['data'].get('leftDays', 0)))
                email = state_result['data'].get('email', 'unknown')

                if "Checkin! Got" in check_result:
                    success += 1
                    message_status = f"✅ 签到成功，会员点数 +{points}"
                elif "Checkin Repeats!" in check_result:
                    repeats += 1
                    message_status = "⚠ 重复签到，明天再来"
                else:
                    fail += 1
                    message_status = "❌ 签到失败，请检查 Cookie"
            else:
                fail += 1
                message_status = "❌ 请求失败或 Cookie 无效"

            message_days = f"{leftdays} 天" if 'leftdays' in locals() else "error"
            context += f"账号 {idx}: {email}, {message_status}, 剩余: {message_days}, 点数: {points}\n"

        except Exception as e:
            fail += 1
            context += f"账号 {idx}: 异常 {e}\n"

    # 汇总标题
    title = f"Glados 签到结果: 成功 {success}, 失败 {fail}, 重复 {repeats}"

# 推送
print("=== 推送内容 ===")
print(title)
print(context)

if sckey:
    try:
        pushdeer = PushDeer(pushkey=sckey)
        pushdeer.send_text(title, desp=context)
        print("✅ 推送成功")
    except Exception as e:
        print("❌ 推送失败:", e)
else:
    print("未设置 SENDKEY，跳过推送")
