import os
import google.generativeai as genai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

# Slack Tokens
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SUMMARY_CHANNEL = os.environ["SUMMARY_CHANNEL"]  # Channel ID like 'C12345'

# Gemini API Key
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
system_message = f'''You are a helpful and concise summarization bot. Your mission is to collect these daily reports to a single daily report. 
    Please ignore messages that are not the report format. 
    Bold text: wrap your text with asterisks (*): *bold*. 
    Below is the output report format, replace yyyy-MM-dd with the current date, try to follow the format as much as possible, no more additional text:\n
    
    *Daily Standup Report on yyyy-MM-dd*
    *1. What's done?*
    • Task 1
    • Task 2
    *2. What's next?*
    • Task 1
    • Task 2
    *3. What's blocked?*
    • Issue 1
    • Issue 2
    or
    • None
    *!!! Notes*
    • Note 1
    • Note 2
    or
    • None

    
    " What's done" is list of task we did yesterday. "What's next" is list of tasks we need to do today. "What's blocked" is list of issues that prevent us from completing our tasks. "Notes" is any additional information that you want to include in your report.
    We can ignore section "3. What's blocked?" and "!!! Notes" if there are no items.
    '''
model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=system_message)

app = App(token=SLACK_BOT_TOKEN)

def summarize_with_gemini(reports_text):
    #print(f"Summarizing text: {reports_text}")
    response = model.generate_content(reports_text)
    #print(response.text)
    return response.text.strip()

@app.event("app_mention")
def handle_app_mention(event, say, client):
    thread_ts = event.get("thread_ts")
    channel = event["channel"]
    if not thread_ts:
        say("Please mention me *in a thread* to summarize it.")
        return

    try:
        replies = client.conversations_replies(channel=channel, ts=thread_ts)
        messages = replies["messages"]
        thread_text = "\n----------------\n".join(f"{m.get('text', '')}" for m in messages[:-1])

        summary = summarize_with_gemini(thread_text)
        #say(summary)

        client.chat_postMessage(
            channel=SUMMARY_CHANNEL,
            text=summary
        )

    except SlackApiError as e:
        say(f"Error fetching thread: {e.response['error']}")
    except Exception as e:
        say(f"Error summarizing: {str(e)}")

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
