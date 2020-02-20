#---Dependencies; must pip install these
import requests


#---These are part of the standard python library, no need to pip install
import pickle
import datetime
import json
import time


#---Config
url_list = ['https://jss.intersections.com:8443/healthCheck.html']
#The incoming webhook url from slack, google how to create this if you don't already have one
slack_webhook = ''


#---Slack Function
def notify_slack(message):
    body = json.dumps({'text': message})
    #body = json.dumps({'username': 'Website_Monitor', 'icon_emoji': ':chrislook:', 'text': message}) #Commented this out as I'm using the webhook and the username and Icon along with other properties are already predefined
    payload = requests.post(slack_webhook,data=body, verify=False) #Verify=false We Man in the Middle egress SSL/HTTPS traffic, remove if not using from Corp Network


#---URL Status Functions
def down(url):
    #Try unpickling the pickled file
    try:
        current_status_file = pickle.load(open("url_status.p", "rb"))
    #If not found, print the statement, assume url is down and send message to slack then exit the function
    except Exception as ex:
        print("The url_status.p file was not found. it will be recreated." + str(ex))
        notify_slack(url + " *is down!* :no_entry:")
        return
    #In the if status code not equal to 200 block below, the down function is evaluated before an entry is made in the dictionary. This statement accounts for that. Assume url is down and notify slack then exit the function.
    if url not in current_status_file:
        notify_slack(url + " *is down!* :no_entry:")
        return
    #If the status code not equal 200 and the last status was up, assume down and notify slack
    if (url in current_status_file) and (current_status_file[url]['status'] == "up"):
        notify_slack(url + " *is down!* :no_entry:")
    #If not any of the previous condition, assume the url was already down, don't notify
    else:
        print("already down, skipping notify")

def back_online(url):
    print("found " + url + " back online.")
    try:
        current_status_file = pickle.load(open("url_status.p", "rb"))
    except Exception as ex:
        print("The url_status.p file was not found. it will be recreated." + str(ex))
        return

    #If status code equal 200 and the last status was down, assume url is reachable and notify slack
    if (url in current_status_file) and (current_status_file[url]['status'] == "down"):
        it_was_down_time = current_status_file[url]['time']
        current_time = datetime.datetime.now()
        notify_slack(url + " *is back online!* :up:, it was down for" + str(current_time - it_was_down_time))
    #If none of the previous statements are evaluated, assume url is still/has been reachable, no notification
    else:
        print("skipping notifying that the url is online")


#---Execution
#Python checks to see the code you're running it's being run directly by python or if it's imported. If being run by python-
#for example in the terminal you type, python3 <some python file>, python will set __name__ to be equal to main.
#The "if __name__ == '__main__':" is used as sort of an entry point in the program/script. Telling python to run this block first(?)
if __name__ == '__main__':
    #The While true is here to keep this code block running indefinitely
    while True:
        #An empty dictionary to store the status of our urls
        url_status = {}
        for url in url_list:
            try:
                #Use requests lib to get status code of the url
                r = requests.get(url, timeout=10)
                #If status code isn't a 200, run this block
                if r.status_code != 200:
                    print(url + " is down.")
                    down(url)
                    url_status[url] = {'status': "down", 'time': datetime.datetime.now()}
                #If status code is 200, run this block
                else:
                    back_online(url)
                    url_status[url] = {'status': "up", 'time': datetime.datetime.now()}
                    time.sleep(10)
            #This block is to handle the connection timing out exception. Assume url is unreachable if connection times out       
            except requests.ConnectionError:
                print(url + " is down.")
                down(url)
                url_status[url] = {'status': "down", 'time': datetime.datetime.now()}

        #Dump the values stored in memory for the url_status dictionary to the url_status pickle file
        pickle.dump(url_status, open("url_status.p", "wb"))
