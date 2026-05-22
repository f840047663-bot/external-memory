---
name: email-sender
title: Hermes 自动邮件发送技能
description: 用QQ邮箱SMTP给大好人发邮件的配置和流程。
triggers:
  - 用户说"发邮件"
  - 需要把日报/周报/分析发送到 feng202210062126@qq.com
  - 需要把分析结果异步推送给大好人
---

# Email Sender — QQ邮箱SMTP自动发信

## 凭证（不要外泄）

| 项目 | 值 |
|:----|:----|
| 邮箱 | feng202210062126@qq.com |
| SMTP授权码 | eordxzfcwxadciag |
| SMTP服务器 | smtp.qq.com |
| 端口 | 465 (SSL) |

## 发邮件Python模板

```python
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def send_email(subject: str, body: str, to: str = 'feng202210062126@qq.com'):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = 'feng202210062126@qq.com'
    msg['To'] = to
    msg['Subject'] = Header(subject, 'utf-8')
    
    server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=30)
    server.login('feng202210062126@qq.com', 'eordxzfcwxadciag')
    server.send_message(msg)
    server.quit()
```

## 调用方式

```bash
python3 -c "
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ... 构造邮件内容 ...
msg = MIMEText('邮件正文', 'plain', 'utf-8')
msg['From'] = 'feng202210062126@qq.com'
msg['To'] = 'feng202210062126@qq.com'
msg['Subject'] = Header('主题', 'utf-8')

server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=30)
server.login('feng202210062126@qq.com', 'eordxzfcwxadciag')
server.send_message(msg)
server.quit()
"
```

## Pitfalls

- ⚠️ 不要带附件 — QQ邮箱SMTP对附件支持不稳定
- ⚠️ DNS解析失败时（此机器常见），设 `noproxy="*"` 绕过代理
- ⚠️ 授权码 `eordxzfcwxadciag` 存储在skill中勿泄漏到外部
- ⚠️ SMTP_SSL超时30秒，网络差时可能失败，重试一次即可
