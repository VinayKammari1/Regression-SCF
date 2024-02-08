import requests
import base64
import json

print("OPTION request to get the cookies")
url = "https://auth.credavenue.in/co/authenticate"

payload={}
headers = {
  'access-control-request-headers': 'auth0-client,content-type',
  'access-control-request-method': 'POST',
  'origin': 'https://tf-sit-01.go-yubi.in',
  'referer': 'https://tf-sit-01.go-yubi.in'
}

opt_response = requests.request("OPTIONS", url, headers=headers, data=payload)
did_token = opt_response.cookies['did']

print("post authenticate request to get login ticket")

payload='client_id=8wX7KpwXzxugX1i7f0RHRLvbPxAtovra&username=ibanchort1@gmail.com&password=Think@123&realm=Username-Password-Authentication&credential_type=http%3A%2F%2Fauth0.com%2Foauth%2Fgrant-type%2Fpassword-realm'
headers = {
  'auth0-client': 'eyJuYW1lIjoiYXV0aDAtcmVhY3QiLCJ2ZXJzaW9uIjoiMS4xMS4wIn0=',
  'origin': 'https://tf-sit-01.go-yubi.in',
  'referer': 'https://tf-sit-01.go-yubi.in',
  'cookie': opt_response.cookies['did'],
  'Content-Type': 'application/x-www-form-urlencoded'
}

loginTicket_response = requests.request("POST", url, headers=headers, data=payload)
auth0_token=loginTicket_response.cookies['auth0']
loginTicket_response_j = loginTicket_response.json()


print("post request to get the access token")
print(f"login_ticket: {loginTicket_response_j['login_ticket']}")
url = "https://auth.credavenue.in/authorize?client_id=8wX7KpwXzxugX1i7f0RHRLvbPxAtovra&response_type=token id_token&redirect_uri=https://tf-sit-01.go-yubi.in&realm=Username-Password-Authentication&audience=https://mp-api-stg.vivriti.in&state=UVBmV2NXUXVSNDJzOUQxRy1YR0w2QUV4SEJHUVNuM3guVHRZRX5NeTJvWQ==&nonce=QjY0WlFkSG1TUTh1VG5XSV9kNlF2aGQ5eU5pOVdtb3BhNWJ2Zi1zNGkxWQ==&login_ticket="+loginTicket_response_j['login_ticket']+"&scope=openid profile email&$auth0Client=eyJuYW1lIjoiYXV0aDAtcmVhY3QiLCJ2ZXJzaW9uIjoiMS4xMS4wIn0="
print(f"URL for access token: {url}")
payload={}
files={}
headers = {
  'referer': 'https://tf-sit-01.go-yubi.in',
  'cookie': 'auth0='+loginTicket_response.cookies['auth0']+'; auth0_compat='+loginTicket_response.cookies['auth0']+'; did='+opt_response.cookies['did']+'; did_compat='+opt_response.cookies['did']
}

access_response = requests.request("GET", url, headers=headers, data=payload,allow_redirects=False)
access_token = "Bearer "+access_response.text.split("access_token=")[1].split("&scope")[0]
id=access_token.split(".")[1]+"=="
entity_id_bytes=base64.b64decode(id)
# entity_data=entity_id_bytes.decode('utf-8')
entity_data=json.loads(entity_id_bytes)
print(entity_data)
local_user_id=entity_data['https://mp-api-stg.vivriti.in/local_user_id']
entity_id=entity_data['https://mp-api-stg.vivriti.in/entity_id']

print("post request to get the mfa token")
url = "https://auth-sit-01-api.go-yubi.in/users/"+local_user_id+"/mfa?product_id=CRDPL"

payload = "{}"
headers = {
  'Authorization': access_token,
  'Content-Type': 'text/plain'
}

mfa_response = requests.request("PATCH", url, headers=headers, data=payload)

print("post request to get the mfa token verification")
url = "https://auth-sit-01-api.go-yubi.in/users/"+local_user_id+"/mfa_verify?"

payload='otp=999999&product_id=CRDPL'
headers = {
  'origin': 'https://tf-sit-01.go-yubi.in',
  'referer': 'https://tf-sit-01.go-yubi.in',
  'Authorization': access_token,
  'Content-Type': 'application/x-www-form-urlencoded'
}




mfa_verify = requests.request("PATCH", url, headers=headers, data=payload)
mfa_token=mfa_verify.json()['mfa_token']

print(mfa_token)


# #generating the invoice number and adding it to the request file
# with open('./data/requests/pfl_df.json', 'r') as f:
#     data = json.load(f)


# data['create_invoice']['invoice_number'] = 'vndkjCheckV1'

# #rewrite the request file with the invoice number
# with open('./data/requests/pfl_df.json', 'w') as f:
#     json.dump(data, f, indent=4)


# with open('./data/requests/pfl_df.json', 'r') as f:
#     data = json.load(f)
#     print(data)


# data={
# 		"status": "approved",
# 		"re_initiate": False,
# 		"is_initiated": True,
# 		"products": [
# 			{
# 				"program_group": "invoice",
# 				"ids": [34521]
# 			}
# 		]
# 	}


# url = "https://tf-sit-01-api.go-yubi.in/invoices/verify"
# headers={
#         'authorization':"Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik5rVkJNVEl6TkVaRFEwTTRRMEpEUkRaRU5FRTNRMEUzUmpReE5VVTJPRU01T1RaR09EazVOQSJ9.eyJodHRwczovL21wLWFwaS1zdGcudml2cml0aS5pbi9yb2xlcyI6WyJhZG1pbiJdLCJodHRwczovL21wLWFwaS1zdGcudml2cml0aS5pbi9ncm91cHMiOlsiY3VzdG9tZXIiXSwiaHR0cHM6Ly9tcC1hcGktc3RnLnZpdnJpdGkuaW4vc3ViZ3JvdXBzIjpbImFuY2hvciJdLCJodHRwczovL21wLWFwaS1zdGcudml2cml0aS5pbi9lbnRpdHlfaWQiOiI2M2ZjNzMxZDE4ZDQ0MDAwNTdhZGMzN2MiLCJodHRwczovL21wLWFwaS1zdGcudml2cml0aS5pbi9sb2NhbF91c2VyX2lkIjoiNjNmYzc0ZGFhN2JjODEwMDQxYjMwNTUwIiwiaHR0cHM6Ly9tcC1hcGktc3RnLnZpdnJpdGkuaW4vc2tpcF9NRkEiOmZhbHNlLCJodHRwczovL21wLWFwaS1zdGcudml2cml0aS5pbi9za2lwX2hybXMiOnRydWUsImlzcyI6Imh0dHBzOi8vYXV0aC5jcmVkYXZlbnVlLmluLyIsInN1YiI6ImF1dGgwfDYzZmM3NGRiM2NhYzc1OTlhM2U1ZDIwYiIsImF1ZCI6WyJodHRwczovL21wLWFwaS1zdGcudml2cml0aS5pbiIsImh0dHBzOi8vdml2cml0aS1tYXJrZXRwbGFjZS1zdGFnaW5nLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3MDcyMTIzODQsImV4cCI6MTcwNzI5ODc4NCwiYXpwIjoiOHdYN0twd1h6eHVnWDFpN2YwUkhSTHZiUHhBdG92cmEiLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIn0.MVajC2VleLwhGuf0LeHaRqfLsadibrODpzyRoJKujuHXSi4xwPINzB7UpqML2qnV4WUyjDuI9R5lZp_KGcX4xmrrEHugw1X7ctTMur-8g2WuAGof4F8nPNobo0Tdrxd6BZtQ5S2D-1OMjgpWSXbwC98uQAEbGlJh6EH8_PndCsYX4nCQL9wCNfXERRRULvG6OB7pEMMe1GKnnegw4U9z4TduZncgzd1gMW1kxX5GNL4WxMtFnIifZWA0ClQiMzhADPuLZuWjaOPZ0YY3626UENNFB4DZKd5Id650uuQDoNGs-s45cf0eDbJkg4bnzDoEDF9QtF1iEK-VRnrIy1a-wQ",
#         'current-entity-id': '63fc731d18d4400057adc37c',
#         'mfa-token':'eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiNjNmYzc0ZGFhN2JjODEwMDQxYjMwNTUwIiwiZXhwIjoxNzA3ODE3MjQ2LCJpYXQiOjE3MDcyMTI0NDYsInNlc3Npb24iOnsiYWJzX2V4cCI6MTcwNzgxNzI0NiwiaWRsZV90aW1lb3V0IjoyNTkyMDAsInBpbmdfZnJlcXVlbmN5Ijo0fX0.kZwCtU7MZkEC2nA6z9ZpXpo_dI4-1hLaB5pJCyLQd0A'}
# response=requests.request("POST",url,headers=headers,data=json.dumps(data),allow_redirects=False)
# print(response.json())

# di1={"di":{'key2':"Vinay","key2":"Check"},"key1":"Kumar"}
# di2={"di":{"key2":"Check",'key2':"Vinay"},"key1":"Kumar"}
# if di1==di2:
#     print("True")
# else:
#     print("False")

# import json

# def compare_json(file1_path, file2_path):
#     # Load JSON data from both files
#     with open(file1_path, 'r') as file1:
#         data1 = json.load(file1)

#     with open(file2_path, 'r') as file2:
#         data2 = json.load(file2)

#     # Compare the data
#     differences = find_differences(data1, data2, '')

#     # Print the differences
#     print("Differences:")
#     for key, value in differences.items():
#         print(f"{key}: {value}")

# def find_differences(data1, data2, prefix):
#     differences = {}

#     # Check if the data is a list
#     if isinstance(data1, list) and isinstance(data2, list):
#         for i, (item1, item2) in enumerate(zip(data1, data2)):
#             new_prefix = f"{prefix}[{i}]"
#             nested_diff = find_differences(item1, item2, new_prefix)
#             differences.update(nested_diff)

#     # Check if the data is a dictionary
#     elif isinstance(data1, dict) and isinstance(data2, dict):
#         # Check keys in data2
#         for key in data2:
#             new_prefix = f"{prefix}.{key}" if prefix else key

#             # Check if the key is in data1
#             if key not in data1:
#                 differences[new_prefix] = f"Key '{new_prefix}' is in file2 but not in file1"
#             else:
#                 # Recursively compare values
#                 nested_diff = find_differences(data1[key], data2[key], new_prefix)
#                 differences.update(nested_diff)

#         # Check keys in data1
#         for key in data1:
#             new_prefix = f"{prefix}.{key}" if prefix else key

#             # Check if the key is in data2
#             if key not in data2:
#                 differences[new_prefix] = f"Key '{new_prefix}' is in file1 but not in file2"

#     # Check values
#     elif data1 != data2:
#         differences[prefix] = f"Value mismatch for key '{prefix}': {data1} != {data2}"

#     return differences

# # # Example usage
# # compare_json('/Users/vinay.kammari1/Desktop/RegressionV_SCF/data/responses/pfl_vf.json', '/Users/vinay.kammari1/Desktop/RegressionV_SCF/json_actual.json')


# #     # payload='client_id=8wX7KpwXzxugX1i7f0RHRLvbPxAtovra&username=ibanchort1@gmail.com&password=Think@123&realm=Username-Password-Authentication&credential_type=http%3A%2F%2Fauth0.com%2Foauth%2Fgrant-type%2Fpassword-realm'

