from auth import get_access_token
from graph import graph_get

def main():
    token = get_access_token()
    me = graph_get("/me", token)
    print("Hello from Microsoft Graph!")
    print(me)

if __name__ == "__main__":
    main()