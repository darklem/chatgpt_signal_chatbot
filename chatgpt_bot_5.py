import json
import requests
import time
import logging
import openai
import os
from dotenv import load_dotenv


load_dotenv()
my_number = os.getenv("MY_NUMBER")
exit_keyword = "Goodbye"
stop_sequence = "#"
conversations = {}

endpoint_openai = "https://api.openai.com/v1/completions"
endpoint_signal_api_rcv = f"http://localhost:8088/v1/receive/{my_number}"
endpoint_signal_api_send = "http://localhost:8088/v2/send"
human_delay = 5
too_many_error= "Too Many Requests"

logging.basicConfig(
    filename='bot_log.log', 
    encoding='utf-8',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

# headers_openai = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {api_key}",
#     }
headers_signal_api = {
        "Content-Type": "application/json"
}

def rcv_signal_msg():
    new_messages = {}
    try:
        response = requests.get(
            endpoint_signal_api_rcv,
            headers=headers_signal_api
        )
    except Exception as e:
        logging.warning(e)
        return {}

    response = json.loads(response.text)
    if not response:
        return {} 

    for envelope in response:
        if "dataMessage" in envelope["envelope"]:
            message = envelope["envelope"]["dataMessage"]["message"]
            source = envelope["envelope"]["source"]
            logging.info(f"Signal: new message received from {source}: {message}")
            if source in conversations:
                conversations[source] += message
            else:
                conversations[source] = message 
            new_messages[source] = conversations[source]
            logging.info("Signal: New messages received:")
            logging.info(new_messages)
    return new_messages 

def send_signal_msg(src_num, dst_num, message):
    signal_message = {
        "message": message,
        "number": src_num,
        "recipients": [ dst_num ]
    }
    try:
        response = requests.post(
            endpoint_signal_api_send,
            headers=headers_signal_api,
            json=signal_message
        )
    except Exception as e:
        logging.warning(e)
    logging.info(f"Signal: message sent to {dst_num}")

def generate_text(prompt, dst_number):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    connected = False
    while not connected:
        try:
            logging.info(f"Sending to chatgpt: {prompt}")
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"{prompt}",
                temperature=0.0,
                max_tokens=2048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0.0,
                # stop=[stop_sequence]
            )
            connected = True
        except Exception as e:
            logging.warning(e)
            if too_many_error in str(e):
                logging.warning("Chatgpt: Too much request for openai, waiting..")
                send_signal_msg(my_number, dst_number, "une seconde, j'arrive. Je vais faire pipi.")
                time.sleep(60)
            pass
    response =  response.choices[0].text
    logging.info(f"Chatgpt: answering [ {response.strip()} ]")
    return response.strip()

# def generate_text_post(prompt):
#     data = {
#         "prompt": prompt,
#         "model": "text-davinci-003",
#         "max_tokens": 2048,
#         "temperature": 0.9,
#         "top_p": 1,
#         "frequency_penalty": 0,
#         "presence_penalty": 0.0,
#         "stop": [stop_sequence]
#     }
#     connected = False
#     while not connected:
#         try:
#             logging.info(f"Sending to chatgpt: {prompt}")
#             response = requests.post(
#                 endpoint_openai,
#                 headers=headers_openai,
#                 json=data)
#             response.raise_for_status()
#             response = json.loads(response.text)
#             connected = True
#         except Exception as e:
#             logging.warning(e)
#             if too_many_error in str(e):
#                 logging.warning("Chatgpt: Too much request for openai, waiting..")
#                 send_signal_msg(my_number, target_number, "une seconde, j'arrive. Je vais faire pipi.")
#                 time.sleep(60)
#             pass

#     # Select last answer
#     response =  response["choices"][-1]["text"] + stop_sequence
#     print(prompt)
#     logging.info(f"Chatgpt: answering [ {response} ]")
#     return response


# Initializing the conversation
# send_signal_msg(my_number,target_number, signal_msg)


# Continuation of the conversation
logging.info(" --- Chatbot started ---")
while True:
    print(conversations)
    user_input = rcv_signal_msg()
    if not user_input: 
        continue

    for key,value in user_input.items():
        # Requesting the next response
        response = generate_text(value, key)
        # Sendind message to each user
        send_signal_msg(my_number,key,response)
        # Appending the response to the conversation
        conversations[key] += response
        logging.info(response)

    
    # if exit_keyword in user_input:
    #     send_signal_msg(my_number,target_number,"Ok, je me tais. Bye")
    #     break