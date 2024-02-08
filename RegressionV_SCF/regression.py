import json 
import random
import datetime
import psycopg2
import yaml
import requests
import base64
import time

#constants
alpha_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+'
conn=''
env=''
auth_data=''

def get_auth_flow():
    global auth_data
    with open("./flow_defination/auth_flow_details.yml", "r") as stream:
        try:
            auth_data=yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return auth_data

def gen_auth_details(users):
    print("Generating the auth details for the user: ",end=" ")
    global env
    global auth_data
    if env=='':
        env=get_env()

    if auth_data=='':
        auth_data=get_auth_flow()

    user=env['users'][users]['role']
    print(user)
    #OPTION request to get the cookies
    url=auth_data[user]['cookies']['url']
    headers=auth_data[user]['cookies']['headers']
    payload=auth_data[user]['cookies']['payload']
    opt_response = requests.request("OPTIONS", url, headers=headers, data=payload)
    did_token = opt_response.cookies['did']

    #post authenticate request to get login ticket
    url=auth_data[user]['login_ticket']['url']
    headers=auth_data[user]['login_ticket']['headers']
    headers['cookie']=did_token
    payload=auth_data[user]['login_ticket']['payload']
    payload=payload[1]+env['users'][users]['email']+payload[3]+env['users'][users]['password']+payload[5]
    loginTicket_response = requests.request("POST", url, headers=headers, data=payload)
    auth0_token=loginTicket_response.cookies['auth0']
    login_ticket = loginTicket_response.json()['login_ticket']


    #post request to get the access token
    url=auth_data[user]['access_token']['url']
    url=url[1]+login_ticket+url[3]
    headers=auth_data[user]['access_token']['headers']
    headers['cookie']='auth0='+auth0_token+'; auth0_compat='+auth0_token+'; did='+did_token+'; did_compat='+did_token
    payload=auth_data[user]['access_token']['payload']
    access_response = requests.request("GET", url, headers=headers, data=payload,allow_redirects=False)
    access_token = "Bearer "+access_response.text.split("access_token=")[1].split("&scope")[0]
  

    #get the local user id from the access token
    id=access_token.split(".")[1]+"=="
    entity_data=json.loads(base64.b64decode(id))
    local_user_id=entity_data['https://mp-api-stg.vivriti.in/local_user_id']
    entity_id=entity_data['https://mp-api-stg.vivriti.in/entity_id']

    #post request to get the mfa token
    url=auth_data[user]['mfa_token']['url']
    url=url[1]+local_user_id+url[3]
    headers=auth_data[user]['mfa_token']['headers']
    headers['Authorization']=access_token
    payload=auth_data[user]['mfa_token']['payload']
    requests.request("PATCH", url, headers=headers, data=payload)

    #post request to get the mfa token verification
    url=auth_data[user]['mfa_token_verify']['url']
    url=url[1]+local_user_id+url[3]
    headers=auth_data[user]['mfa_token_verify']['headers']
    headers['Authorization']=access_token
    payload=auth_data[user]['mfa_token_verify']['payload']
    mfa_verify = requests.request("PATCH", url, headers=headers, data=payload)
    print(mfa_verify.json())
    mfa_token=mfa_verify.json()['mfa_token']

    #writing the auth details to a file
    data={users:{
        "auth0_token":auth0_token,
        "did_token":did_token,
        "access_token":access_token,
        "local_user_id":local_user_id,
        "mfa_token":mfa_token,
        "entity_id":entity_id
    }}
    with open('./auth_details.json', 'w') as f:
        json.dump(data, f, indent=4)

    return data



def get_env():
    global env
    with open("./environment/sit.yml", "r") as stream:
        try:
            env=yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return env

#database connection
def db_connection():
    global env
    if env=='':
        env=get_env()
    global conn
    conn = psycopg2.connect(
        dbname=env['database']['db-name'],
        user=env['database']['db-username'],
        password=env['database']['db-password'],
        host=env['database']['db-host'],
        port=env['database']['db-port']
    )
    return conn

def query_db(invoice):
    global conn
    if conn =='':
        conn=db_connection()
    cur=conn.cursor()
    cur.execute("SELECT * FROM invoices where invoice_number = %s", (invoice,))
    row=cur.fetchone()
    return row[0]

def request_compare(req_body,invoice_id,invoice_num):
    # Load JSON data from both files
    data2 = json.loads(req_body)

    with open('./data/responses/pfl_vf.json', 'r') as file2:
        req_data = json.load(file2)
        data1=req_data['request']
    data1['loanRefId']=invoice_id
    data1['loanBookingRequest']['loanDetail']['loanAccountNumber']=invoice_num
    data1['loanBookingRequest']['loanDetail']['applicationFormNumber']=invoice_num
    data1['loanBookingRequest']['loanDetail']['applicationFileNumber']=invoice_num
    data1['loanBookingRequest']['loanDetail']['loanDisbursalDetails'][0]['disbursalBreakUpDetails'][0]['disbursalPaymentDetails'][0]['sourcePaymentReferenceNumber']=invoice_id
    # Compare the data
    differences = find_differences(data1, data2, '')

    if not differences:
        print("No differences found in Request")
    else:
        # Print the differences
        print("Differences found in Request:")
        for key, value in differences.items():
            print(f"{key}: {value}")

def find_differences(data1, data2, prefix):
    differences = {}

   # Check if the data is a list
    if isinstance(data1, list) and isinstance(data2, list):
        for i, (item1, item2) in enumerate(zip(data1, data2)):
            new_prefix = f"{prefix}[{i}]"
            nested_diff = find_differences(item1, item2, new_prefix)
            differences.update(nested_diff)

    # Check if the data is a dictionary
    elif isinstance(data1, dict) and isinstance(data2, dict):
        # Check keys in data2
        for key in data2:
            new_prefix = f"{prefix}.{key}" if prefix else key

            # Check if the key is in data1
            if key not in data1:
                differences[new_prefix] = f"Key '{new_prefix}' is in file2 but not in file1"
            else:
                # Recursively compare values
                nested_diff = find_differences(data1[key], data2[key], new_prefix)
                differences.update(nested_diff)

        # Check keys in data1
        for key in data1:
            new_prefix = f"{prefix}.{key}" if prefix else key

            # Check if the key is in data2
            if key not in data2:
                differences[new_prefix] = f"Key '{new_prefix}' is in file1 but not in file2"

    # Check values
    elif data1 != data2:
        differences[prefix] = f"Value mismatch for key '{prefix}': {data1} != {data2}"

    return differences


def response_compare(res_body,invoice_id):
    # Load JSON data from both files
    data2 = res_body

    with open('./data/responses/pfl_vf.json', 'r') as file2:
        res_data = json.load(file2)
        data1=res_data['response']
    data1['payload']['requestReference']=invoice_id
    data1['payload']['paymentReferences'][0]['sourcePaymentReferenceNumber']=invoice_id
    # Compare the data
    differences = find_differences(data1, data2, '')

    if not differences:
        print("No differences found in Response")
    else:
        # Print the differences
        print("Differences found in Response:")
        for key, value in differences.items():
            print(f"{key}: {value}")

def request_logs(invoice_id,invoice_num):
    global conn
    if conn =='':
        conn=db_connection()
    cur=conn.cursor()
    cur.execute("SELECT * FROM integration_client_requests where loggable_id = %s order by updated_at desc", (str(invoice_id),)) #invoice_id
    row=cur.fetchone()
    cur.execute("SELECT * FROM request_logs where integration_client_request_id = %s order by updated_at desc", (row[0],))
    row=cur.fetchone()
    request_compare(row[2],invoice_id,invoice_num)
    response_compare(row[3],invoice_id)
    transaction_verify(row[3]['payload']['responseReference'],invoice_id) #invoice_id
   

def gen_invoice_number(client,program):
    auth=gen_auth_details(client)
    random_chars=''.join(random.choice(alpha_chars) for i in range(3))
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return random_chars+timestamp, auth

#Transaction record verification
def transaction_verify(lan_no,invoice_id):
    global conn
    if conn =='':
        conn=db_connection()
    cur=conn.cursor()

    #getting the invoice number from the invoice id
    cur.execute("select * from invoices where id=%s",(invoice_id,)) 
    row=cur.fetchone()
    invoice=row[5]
    #getting the transaction record from the transaction_pushes table using invoice number
    cur.execute("SELECT * FROM transaction_pushes where instrument_number = %s", (invoice,))
    row=cur.fetchone()
    if row[2]==779:
        print("Cleint details id is same")
    else:
        print("Client details id is not same")
    if row[6]==lan_no:
        print("Lan number is same")
    else:  
        print("Lan number is not same")
    if row[7]=='instrument_pushed':
        print("Transaction status is instrument_pushed")    
    else:   
        print("Transaction status is not instrument_pushed")


def approve_invoice(auth,invoice,data):
    invoice_id=query_db(invoice)
    data['invoice_verify']['products'][0]['ids']=[invoice_id]
    url = "https://tf-sit-01-api.go-yubi.in/invoices/verify"
    headers={
        'authorization':auth['anchor1']['access_token'],
        'current-entity-id': auth['anchor1']['entity_id'],
        'mfa-token':auth['anchor1']['mfa_token'],
        'content-type':'application/json'
        }

    approve_response=requests.request("PUT",url,headers=headers,data=json.dumps(data['invoice_verify']),allow_redirects=False)
    print(approve_response.json())
    print("Waiting for 20 seconds to get the logs")
    time.sleep(20)
    request_logs(invoice_id,invoice)
    

def create_invoice():
    invoice_num,auth=gen_invoice_number('anchor1','vf')
    print(invoice_num)
    with open('./data/requests/pfl_vf.json', 'r') as f:
        data = json.loads(f.read())
    data['create_invoice']['invoice[invoice_number]'] = invoice_num
    headers={
        'authorization':auth['anchor1']['access_token'],
        'current-entity-id': auth['anchor1']['entity_id'],
        'mfa-token':auth['anchor1']['mfa_token']}
    
    response=requests.request("POST",'https://tf-sit-01-api.go-yubi.in/invoices',headers=headers,data=data['create_invoice'],allow_redirects=False)
    approve_invoice(auth,invoice_num,data)
    


create_invoice()
